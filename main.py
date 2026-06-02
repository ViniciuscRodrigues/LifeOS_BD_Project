import os
import re
from tokenize import generate_tokens

import google.generativeai as genai
import psycopg2
import psycopg2.extras
import requests
import webview
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Configure a sua chave de API

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "database": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASS"),
}


class LifeOSApp:
    def __init__(self):
        try:
            conn = self.get_connection()
            conn.close()
        except Exception as e:
            print(f"Erro ao conectar no banco: {e}")

    def get_connection(self):
        return psycopg2.connect(**DB_CONFIG)

    def ResetDatabase(self):
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
            with open(schema_path, "r", encoding="utf-8") as f:
                cur.execute(f.read())

            # Carga de Dados Iniciais (Item 7.e)
            cur.execute(
                "INSERT INTO usuario (nome, email) VALUES ('Admin', 'admin@ufsc.br');"
            )
            cur.execute(
                "INSERT INTO conta_bancaria (usuario_id, nome_banco, saldo_atual) VALUES (1, 'Carteira', 0);"
            )
            cur.execute(
                "INSERT INTO disciplina_projeto (usuario_id, nome, categoria, semestre_ativo) VALUES (1, 'Banco de Dados', 'Faculdade', '2024.1'), (1, 'Projeto ESP32', 'Pessoal', 'N/A');"
            )
            cur.execute(
                "INSERT INTO exercicio_fisico (nome, grupo_muscular) VALUES ('Supino Reto', 'Peito'), ('Agachamento', 'Pernas'), ('Corrida', 'Cardio');"
            )
            cur.execute(
                "INSERT INTO alimento_suplemento (nome, porcao_gramas, calorias, proteina_g, carboidrato_g, gordura_g) VALUES ('Whey Protein', 30, 120, 24, 3, 1), ('Frango Grelhado', 100, 165, 31, 0, 3);"
            )
            cur.execute(
                "INSERT INTO habito (usuario_id, nome, tipo, frequencia_alvo) VALUES (1, 'Ler 10 páginas', 'Meta', 7), (1, 'Menos de 2h de Jogos', 'Limite', 7);"
            )

            conn.commit()
            cur.close()
            conn.close()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def GetDashboardData(self):
        try:
            conn = self.get_connection()
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

            # Finanças
            cur.execute(
                "SELECT tipo, SUM(valor) as total FROM transacao_financeira WHERE conta_id = 1 GROUP BY tipo;"
            )
            totais = cur.fetchall()
            incomes, expenses = 0.0, 0.0
            for t in totais:
                if t["tipo"] == "Entrada":
                    incomes = float(t["total"])
                elif t["tipo"] == "Saida":
                    expenses = float(t["total"])
            balance = incomes - expenses

            cur.execute(
                "SELECT id, tipo, categoria, valor, data_transacao FROM transacao_financeira ORDER BY id DESC;"
            )
            transactions = [
                {
                    **tx,
                    "valor": float(tx["valor"]),
                    "data_transacao": str(tx["data_transacao"]),
                }
                for tx in cur.fetchall()
            ]

            cur.execute(
                "SELECT id, categoria, ticker_nome, valor_investido, taxa_yield, cotas FROM investimento ORDER BY id DESC;"
            )
            investments = [
                {
                    **inv,
                    "valor_investido": float(inv["valor_investido"]),
                    "taxa_yield": float(inv["taxa_yield"]),
                }
                for inv in cur.fetchall()
            ]

            # Catálogos (Para preencher os <select> do Frontend)
            cur.execute("SELECT id, nome FROM disciplina_projeto")
            cat_disciplinas = cur.fetchall()

            cur.execute("SELECT id, nome FROM exercicio_fisico")
            cat_exercicios = cur.fetchall()

            cur.execute("SELECT id, nome FROM alimento_suplemento")
            cat_alimentos = cur.fetchall()

            cur.execute("SELECT id, nome FROM habito")
            cat_habitos = cur.fetchall()

            # Históricos (JOINs para as listas do Frontend)
            cur.execute("""
                SELECT se.id, dp.nome as disciplina, se.duracao_minutos, se.topico_estudado, se.data_sessao
                FROM sessao_estudo se JOIN disciplina_projeto dp ON se.disciplina_id = dp.id ORDER BY se.id DESC;
            """)
            hist_estudos = [
                {**e, "data_sessao": str(e["data_sessao"])} for e in cur.fetchall()
            ]

            cur.execute("""
                SELECT st.id, ef.nome as exercicio, st.repeticoes, st.carga_kg, rt.data_treino
                FROM serie_treino st JOIN registro_treino rt ON st.registro_treino_id = rt.id
                JOIN exercicio_fisico ef ON st.exercicio_id = ef.id ORDER BY st.id DESC;
            """)
            hist_treinos = [
                {
                    **t,
                    "carga_kg": float(t["carga_kg"]),
                    "data_treino": str(t["data_treino"]),
                }
                for t in cur.fetchall()
            ]

            cur.execute("""
                SELECT cd.id, als.nome as alimento, cd.quantidade_porcoes, cd.data_consumo,
                       (als.calorias * cd.quantidade_porcoes) as calorias_totais,
                       (als.proteina_g * cd.quantidade_porcoes) as prot_totais
                FROM consumo_diario cd JOIN alimento_suplemento als ON cd.alimento_id = als.id ORDER BY cd.id DESC;
            """)
            hist_dieta = [
                {
                    **d,
                    "quantidade_porcoes": float(d["quantidade_porcoes"]),
                    "calorias_totais": float(d["calorias_totais"]),
                    "prot_totais": float(d["prot_totais"]),
                    "data_consumo": str(d["data_consumo"]),
                }
                for d in cur.fetchall()
            ]

            cur.execute("""
                SELECT rh.id, h.nome as habito, h.tipo, rh.status, rh.data_registro
                FROM registro_habito rh JOIN habito h ON rh.habito_id = h.id ORDER BY rh.id DESC;
            """)
            hist_habitos = [
                {**h, "data_registro": str(h["data_registro"])} for h in cur.fetchall()
            ]

            cur.close()
            conn.close()

            return {
                "balance": balance,
                "incomes": incomes,
                "expenses": expenses,
                "transactions": transactions,
                "investments": investments,
                "catalogs": {
                    "disciplinas": cat_disciplinas,
                    "exercicios": cat_exercicios,
                    "alimentos": cat_alimentos,
                    "habitos": cat_habitos,
                },
                "history": {
                    "estudos": hist_estudos,
                    "treinos": hist_treinos,
                    "dieta": hist_dieta,
                    "habitos": hist_habitos,
                },
            }
        except Exception as e:
            return {"error": str(e)}

    # --- MÉTODOS CRUD DE ESTUDOS ---
    def AddEstudo(self, disciplina_id, duracao, topico):
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO sessao_estudo (disciplina_id, duracao_minutos, topico_estudado) VALUES (%s, %s, %s)",
                (disciplina_id, int(duracao), topico),
            )
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print(e)
        return self.GetDashboardData()

    def DeleteEstudo(self, id):
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM sessao_estudo WHERE id = %s", (id,))
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print(e)
        return self.GetDashboardData()

    # --- MÉTODOS CRUD DE TREINOS ---
    def AddTreino(self, exercicio_id, repeticoes, carga):
        try:
            conn = self.get_connection()
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

            # Verifica se já existe um treino para hoje, se não, cria.
            cur.execute(
                "SELECT id FROM registro_treino WHERE usuario_id = 1 AND data_treino = CURRENT_DATE"
            )
            row = cur.fetchone()
            if row:
                registro_id = row["id"]
            else:
                cur.execute(
                    "INSERT INTO registro_treino (usuario_id, duracao_minutos) VALUES (1, 60) RETURNING id"
                )
                registro_id = cur.fetchone()["id"]

            cur.execute(
                "INSERT INTO serie_treino (registro_treino_id, exercicio_id, repeticoes, carga_kg) VALUES (%s, %s, %s, %s)",
                (registro_id, exercicio_id, int(repeticoes), float(carga)),
            )
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print(e)
        return self.GetDashboardData()

    def DeleteTreino(self, id):
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM serie_treino WHERE id = %s", (id,))
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print(e)
        return self.GetDashboardData()

    # --- MÉTODOS CRUD DE DIETA ---
    def AddDieta(self, alimento_id, porcoes):
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO consumo_diario (usuario_id, alimento_id, quantidade_porcoes) VALUES (1, %s, %s)",
                (alimento_id, float(porcoes)),
            )
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print(e)
        return self.GetDashboardData()

    def DeleteDieta(self, id):
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM consumo_diario WHERE id = %s", (id,))
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print(e)
        return self.GetDashboardData()

    # --- MÉTODOS CRUD DE HÁBITOS ---
    def AddHabito(self, habito_id, status):
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO registro_habito (habito_id, status) VALUES (%s, %s)",
                (habito_id, status),
            )
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print(e)
        return self.GetDashboardData()

    def DeleteHabito(self, id):
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM registro_habito WHERE id = %s", (id,))
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print(e)
        return self.GetDashboardData()

    # --- MÉTODOS ORIGINAIS (Finanças e APIs) ---
    def AddTransaction(self, tType, category, value):
        tipo_banco = "Entrada" if tType == "entrada" else "Saida"
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO transacao_financeira (conta_id, tipo, categoria, valor) VALUES (1, %s, %s, %s)",
                (tipo_banco, category, float(value)),
            )
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print(e)
        return self.GetDashboardData()

    def AddInvestment(self, category, name, invested, rate, price, quotas):
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO investimento (usuario_id, categoria, ticker_nome, valor_investido, taxa_yield, cotas) VALUES (1, %s, %s, %s, %s, %s)",
                (category, name, float(invested), float(rate), int(quotas)),
            )
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print(e)
        return self.GetDashboardData()

    def DeleteTransaction(self, tx_id):
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM transacao_financeira WHERE id = %s", (tx_id,))
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print(e)
        return self.GetDashboardData()

    def DeleteInvestment(self, inv_id):
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM investimento WHERE id = %s", (inv_id,))
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print(e)
        return self.GetDashboardData()

    def GetAIInsights(self):
        try:
            conn = self.get_connection()
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

            cur.execute(
                "SELECT tipo, categoria, valor FROM transacao_financeira ORDER BY id DESC LIMIT 10"
            )
            transacoes = cur.fetchall()
            cur.execute(
                "SELECT ticker_nome, valor_investido, categoria FROM investimento ORDER BY id DESC LIMIT 10"
            )
            investimentos = cur.fetchall()
            cur.execute(
                "SELECT dp.nome as disciplina, se.duracao_minutos, se.topico_estudado FROM sessao_estudo se JOIN disciplina_projeto dp ON se.disciplina_id = dp.id ORDER BY se.id DESC LIMIT 5"
            )
            estudos = cur.fetchall()
            cur.execute(
                "SELECT h.nome as habito, h.tipo, rh.status FROM registro_habito rh JOIN habito h ON rh.habito_id = h.id ORDER BY rh.id DESC LIMIT 5"
            )
            habitos = cur.fetchall()
            cur.execute(
                "SELECT als.nome as alimento, cd.quantidade_porcoes, als.calorias, als.proteina_g FROM consumo_diario cd JOIN alimento_suplemento als ON cd.alimento_id = als.id ORDER BY cd.id DESC LIMIT 5"
            )
            dieta = cur.fetchall()

            cur.close()
            conn.close()

            prompt = (
                "Você é o núcleo de Inteligência Artificial de um ecossistema LifeOS (Gerenciamento de Vida Inteligente).\n"
                "Sua tarefa é analisar os dados reais extraídos do PostgreSQL do usuário e fornecer um insight holístico integrado. "
                "Cruze as informações se notar correlações.\n"
                "Seja direto e objetivo. Escreva uma resposta bem estruturada de no máximo 5 ou 6 linhas.\n\n"
            )
            prompt += "\n[FINANÇAS RECENTES]:\n" + (
                "\n".join(
                    [
                        f"- {t['tipo']}: R$ {t['valor']} em '{t['categoria']}'"
                        for t in transacoes
                    ]
                )
                if transacoes
                else "Nenhuma transação.\n"
            )
            prompt += "\n[INVESTIMENTOS]:\n" + (
                "\n".join(
                    [
                        f"- {i['ticker_nome']}: R$ {i['valor_investido']}"
                        for i in investimentos
                    ]
                )
                if investimentos
                else "Nenhum investimento.\n"
            )
            prompt += "\n[ESTUDOS]:\n" + (
                "\n".join(
                    [
                        f"- '{e['disciplina']}': focado em '{e['topico_estudado']}' por {e['duracao_minutos']} min."
                        for e in estudos
                    ]
                )
                if estudos
                else "Nenhum estudo.\n"
            )
            prompt += "\n[HÁBITOS]:\n" + (
                "\n".join(
                    [f"- '{h['habito']}' -> Status: {h['status']}" for h in habitos]
                )
                if habitos
                else "Nenhum hábito.\n"
            )
            prompt += "\n[DIETA]:\n" + (
                "\n".join(
                    [
                        f"- {d['alimento']}: {d['quantidade_porcoes']} porção."
                        for d in dieta
                    ]
                )
                if dieta
                else "Nenhum consumo alimentar.\n"
            )

            model = genai.GenerativeModel("gemini-2.5-flash")
            resposta = model.generate_content(prompt)
            return {"response": resposta.text}
        except Exception as e:
            return {"error": str(e)}

    def FetchCDI(self):
        try:
            resp = requests.get(
                "https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados/ultimos/1?formato=json",
                timeout=5,
            )
            if resp.status_code == 200 and resp.json():
                return {"rate": float(resp.json()[0]["valor"]) - 0.10}
            return {"error": "Indisponível"}
        except:
            return {"error": "Falha de conexão"}

    def FetchTicker(self, ticker):
        try:
            resp = requests.get(
                f"https://statusinvest.com.br/fundos-imobiliarios/{str(ticker).strip().lower()}",
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=5,
            )
            html = resp.text
            price_re = re.search(
                r'Valor atual do ativo.*?<strong[^>]*class="value"[^>]*>\s*([\d,\.]+)\s*</strong>',
                html,
                re.DOTALL,
            )
            dy_re = re.search(
                r'Dividend Yield com base.*?<strong[^>]*class="value"[^>]*>\s*([\d,\.]+)\s*</strong>',
                html,
                re.DOTALL,
            )
            if price_re:
                return {
                    "price": float(
                        price_re.group(1).replace(".", "").replace(",", ".")
                    ),
                    "yield": float(dy_re.group(1).replace(".", "").replace(",", "."))
                    if dy_re
                    else 0.0,
                }
            return {"error": "Cotação não encontrada"}
        except:
            return {"error": "Falha na busca"}


if __name__ == "__main__":
    app = LifeOSApp()

    # ATENÇÃO: Mantido como instruído para limpar e carregar base todas as vezes
    app.ResetDatabase()

    webview.create_window(
        "LifeOS - Gestor Total", "index.html", js_api=app, width=1100, height=800
    )
    webview.start()
