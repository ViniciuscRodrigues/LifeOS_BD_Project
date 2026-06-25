import json
import os
import re

import google.generativeai as genai
import psycopg2
import psycopg2.extras
import requests
import webview
from dotenv import load_dotenv

os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--log-level=3"

env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path)

api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
else:
    print("❌ ERRO CRÍTICO: GEMINI_API_KEY não foi encontrada no arquivo .env!")

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "database": os.getenv("DB_NAME", "lifeos_db"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASS"),
}


class LifeOSApp:
    def __init__(self):
        try:
            conn = self.get_connection()
            conn.close()
            print("✅ Conexão com PostgreSQL estabelecida.")
        except Exception as e:
            print(f"❌ Erro ao conectar no banco: {e}")

    def get_connection(self):
        return psycopg2.connect(**DB_CONFIG)

    def ResetDatabase(self):
        try:
            conn = self.get_connection()
            cur = conn.cursor()

            schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
            with open(schema_path, "r", encoding="utf-8") as f:
                cur.execute(f.read())

            cur.execute(
                "ALTER TABLE serie_treino ADD COLUMN IF NOT EXISTS calorias_gastas DECIMAL(6,2) DEFAULT 0;"
            )
            cur.execute(
                "ALTER TABLE sessao_estudo ADD COLUMN IF NOT EXISTS descricao_topico TEXT;"
            )

            cur.execute(
                "INSERT INTO usuario (nome, email) VALUES ('Admin', 'admin@ufsc.br');"
            )
            cur.execute(
                "INSERT INTO conta_bancaria (usuario_id, nome_banco, saldo_atual) VALUES (1, 'Carteira', 0);"
            )

            conn.commit()
            cur.close()
            conn.close()
            return {"success": True}
        except Exception as e:
            print(f"Erro no Reset: {e}")
            return {"success": False, "error": str(e)}

    def _parse_gemini_json(self, prompt):
        try:
            model = genai.GenerativeModel("gemini-2.5-flash")
            resposta = model.generate_content(prompt)
            text = resposta.text.strip()
            text = re.sub(r"```json\s*", "", text)
            text = re.sub(r"```\s*", "", text)
            return json.loads(text)
        except Exception as e:
            print(f"Erro no parse da IA: {e}")
            return None

    def GetDashboardData(self):
        try:
            conn = self.get_connection()
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

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
                "SELECT id, tipo, categoria, valor, data_transacao FROM transacao_financeira WHERE conta_id = 1 ORDER BY id DESC;"
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
                "SELECT id, categoria, ticker_nome, valor_investido, taxa_yield, cotas FROM investimento WHERE usuario_id = 1 ORDER BY id DESC;"
            )
            investments = [
                {
                    **inv,
                    "valor_investido": float(inv["valor_investido"]),
                    "taxa_yield": float(inv["taxa_yield"]),
                }
                for inv in cur.fetchall()
            ]

            cur.execute("""
                SELECT se.id, dp.nome as disciplina, se.topico_estudado, se.descricao_topico, se.duracao_minutos
                FROM sessao_estudo se JOIN disciplina_projeto dp ON se.disciplina_id = dp.id
                ORDER BY se.id DESC;
            """)
            estudos = cur.fetchall()

            cur.execute("""
                SELECT rt.id, ef.nome as exercicio, st.repeticoes, st.carga_kg, st.calorias_gastas
                FROM registro_treino rt
                JOIN serie_treino st ON rt.id = st.registro_treino_id
                JOIN exercicio_fisico ef ON st.exercicio_id = ef.id
                ORDER BY rt.id DESC;
            """)
            treinos = [
                {
                    **t,
                    "carga_kg": float(t["carga_kg"]),
                    "calorias_gastas": float(t.get("calorias_gastas") or 0.0),
                }
                for t in cur.fetchall()
            ]

            cur.execute("""
                SELECT cd.id, al.nome as alimento, cd.quantidade_porcoes,
                (cd.quantidade_porcoes * al.calorias) as calorias_totais,
                (cd.quantidade_porcoes * al.proteina_g) as prot_totais
                FROM consumo_diario cd
                JOIN alimento_suplemento al ON cd.alimento_id = al.id
                ORDER BY cd.id DESC;
            """)
            dieta = [
                {
                    **d,
                    "quantidade_porcoes": float(d["quantidade_porcoes"]),
                    "calorias_totais": float(d["calorias_totais"]),
                    "prot_totais": float(d["prot_totais"]),
                }
                for d in cur.fetchall()
            ]

            cur.execute("""
                SELECT h.id, h.nome,
                EXISTS(SELECT 1 FROM registro_habito rh WHERE rh.habito_id = h.id AND rh.data_registro = CURRENT_DATE AND rh.status = 'Concluido') as concluido_hoje
                FROM habito h WHERE h.usuario_id = 1 ORDER BY h.id;
            """)
            habitos_diarios = cur.fetchall()

            cur.close()
            conn.close()

            patrimonio_total = balance + sum(
                inv["valor_investido"] for inv in investments
            )
            horas_estudo = sum(e["duracao_minutos"] for e in estudos) / 60.0

            return {
                "balance": balance,
                "incomes": incomes,
                "expenses": expenses,
                "summary": {
                    "patrimonio_total": patrimonio_total,
                    "horas_estudo": round(horas_estudo, 1),
                    "treinos_realizados": len(treinos),
                    "taxa_habitos": len(
                        [h for h in habitos_diarios if h["concluido_hoje"]]
                    ),
                    "grafico_investimentos": [
                        {"data": "Hoje", "total_acumulado": patrimonio_total}
                    ],
                },
                "transactions": transactions,
                "investments": investments,
                "history": {
                    "estudos": estudos,
                    "treinos": treinos,
                    "dieta": dieta,
                    "habitos_diarios": habitos_diarios,
                },
            }
        except Exception as e:
            print(f"Erro no GetDashboardData: {e}")
            return {"error": str(e)}

    # ================= CRUD FINANÇAS (Com barreira "abs()") =================
    def AddTransaction(self, tType, category, value):
        tipo_banco = "Entrada" if tType == "entrada" else "Saida"
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            # Uso de abs() previne totalmente a injeção de valores negativos no BD
            cur.execute(
                "INSERT INTO transacao_financeira (conta_id, tipo, categoria, valor) VALUES (1, %s, %s, %s)",
                (tipo_banco, category, abs(float(value))),
            )
            conn.commit()
            cur.close()
            conn.close()
        except:
            pass
        return self.GetDashboardData()

    def DeleteTransaction(self, tx_id):
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM transacao_financeira WHERE id = %s", (tx_id,))
            conn.commit()
            cur.close()
            conn.close()
        except:
            pass
        return self.GetDashboardData()

    def AddInvestment(self, category, name, invested, rate, price, quotas):
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO investimento (usuario_id, categoria, ticker_nome, valor_investido, taxa_yield, cotas) VALUES (1, %s, %s, %s, %s, %s)",
                (
                    category,
                    name,
                    abs(float(invested)),
                    abs(float(rate)),
                    abs(int(quotas)),
                ),
            )
            conn.commit()
            cur.close()
            conn.close()
        except:
            pass
        return self.GetDashboardData()

    def DeleteInvestment(self, inv_id):
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM investimento WHERE id = %s", (inv_id,))
            conn.commit()
            cur.close()
            conn.close()
        except:
            pass
        return self.GetDashboardData()

    # ================= ESTUDOS =================
    def AddEstudoLivre(self, materia, topico, descricao, duracao):
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            cur.execute(
                "SELECT id FROM disciplina_projeto WHERE LOWER(nome) = LOWER(%s) AND usuario_id = 1 LIMIT 1",
                (materia,),
            )
            res = cur.fetchone()
            if res:
                disc_id = res[0]
            else:
                cur.execute(
                    "INSERT INTO disciplina_projeto (usuario_id, nome, categoria, semestre_ativo) VALUES (1, %s, 'Estudos', 'Atual') RETURNING id;",
                    (materia.title(),),
                )
                disc_id = cur.fetchone()[0]

            cur.execute(
                "INSERT INTO sessao_estudo (disciplina_id, duracao_minutos, topico_estudado, descricao_topico) VALUES (%s, %s, %s, %s)",
                (disc_id, abs(int(duracao)), topico, descricao),
            )
            conn.commit()
            cur.close()
            conn.close()
            return self.GetDashboardData()
        except Exception as e:
            print(e)
            return {"error": str(e)}

    def DeleteEstudo(self, id):
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM sessao_estudo WHERE id = %s", (id,))
            conn.commit()
            cur.close()
            conn.close()
        except:
            pass
        return self.GetDashboardData()

    # ================= TREINO + IA =================
    def AddTreinoIA(self, peso, altura, exercicio_nome, reps, carga):
        try:
            prompt = f"""
            Atue como um fisiologista esportivo. Estime o gasto calórico TOTAL (em kcal) de uma pessoa de {abs(float(peso))}kg e {abs(float(altura))}cm
            realizando APENAS UMA SÉRIE de {abs(int(reps))} repetições do exercício '{exercicio_nome}' levantando {abs(float(carga))}kg de carga.
            Retorne APENAS um objeto JSON estrito com a chave "calorias" contendo o valor numérico (float).
            """

            resultado = self._parse_gemini_json(prompt)
            calorias_gastas = (
                float(resultado["calorias"])
                if resultado and "calorias" in resultado
                else 0.0
            )

            conn = self.get_connection()
            cur = conn.cursor()

            cur.execute(
                "SELECT id FROM exercicio_fisico WHERE LOWER(nome) = LOWER(%s) LIMIT 1",
                (exercicio_nome,),
            )
            res = cur.fetchone()
            if res:
                ex_id = res[0]
            else:
                cur.execute(
                    "INSERT INTO exercicio_fisico (nome, grupo_muscular) VALUES (%s, 'Geral') RETURNING id;",
                    (exercicio_nome.title(),),
                )
                ex_id = cur.fetchone()[0]

            cur.execute(
                "SELECT id FROM registro_treino WHERE usuario_id = 1 AND data_treino = CURRENT_DATE LIMIT 1;"
            )
            rt_res = cur.fetchone()
            if rt_res:
                treino_id = rt_res[0]
            else:
                cur.execute(
                    "INSERT INTO registro_treino (usuario_id, duracao_minutos) VALUES (1, 60) RETURNING id;"
                )
                treino_id = cur.fetchone()[0]

            cur.execute(
                "INSERT INTO serie_treino (registro_treino_id, exercicio_id, repeticoes, carga_kg, calorias_gastas) VALUES (%s, %s, %s, %s, %s)",
                (treino_id, ex_id, abs(int(reps)), abs(float(carga)), calorias_gastas),
            )

            conn.commit()
            cur.close()
            conn.close()
            return self.GetDashboardData()
        except Exception as e:
            print(e)
            return {"error": str(e)}

    def DeleteTreino(self, id):
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM serie_treino WHERE id = %s", (id,))
            conn.commit()
            cur.close()
            conn.close()
        except:
            pass
        return self.GetDashboardData()

    # ================= HÁBITOS =================
    def CreateHabito(self, nome):
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO habito (usuario_id, nome, tipo, frequencia_alvo) VALUES (1, %s, 'Meta', 7)",
                (nome,),
            )
            conn.commit()
            cur.close()
            conn.close()
            return self.GetDashboardData()
        except Exception as e:
            return {"error": str(e)}

    def ToggleHabito(self, habito_id, is_checked):
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            cur.execute(
                "DELETE FROM registro_habito WHERE habito_id = %s AND data_registro = CURRENT_DATE",
                (habito_id,),
            )
            if is_checked:
                cur.execute(
                    "INSERT INTO registro_habito (habito_id, data_registro, status) VALUES (%s, CURRENT_DATE, 'Concluido')",
                    (habito_id,),
                )
            conn.commit()
            cur.close()
            conn.close()
            return self.GetDashboardData()
        except Exception as e:
            return {"error": str(e)}

    def DeleteHabito(self, id):
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM habito WHERE id = %s", (id,))
            conn.commit()
            cur.close()
            conn.close()
        except:
            pass
        return self.GetDashboardData()

    # ================= DIETA =================
    def AddDietaIA(self, alimento_nome, gramas):
        try:
            prompt = f"""
            Atue como um nutricionista rigoroso. Forneça os macronutrientes para exatamente 100g de '{alimento_nome}'.
            Retorne APENAS um objeto JSON estrito com as seguintes chaves numéricas:
            "calorias" (int), "proteina_g" (float), "carboidrato_g" (float), "gordura_g" (float).
            Não inclua nenhum outro texto.
            """
            macros = self._parse_gemini_json(prompt)
            if not macros:
                return {"error": "A IA não conseguiu interpretar o alimento."}

            conn = self.get_connection()
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO alimento_suplemento (nome, porcao_gramas, calorias, proteina_g, carboidrato_g, gordura_g)
                VALUES (%s, 100, %s, %s, %s, %s) RETURNING id;
            """,
                (
                    alimento_nome.title(),
                    abs(int(macros["calorias"])),
                    abs(float(macros["proteina_g"])),
                    abs(float(macros["carboidrato_g"])),
                    abs(float(macros["gordura_g"])),
                ),
            )
            alimento_id = cur.fetchone()[0]

            qtd_porcoes = abs(float(gramas)) / 100.0
            cur.execute(
                "INSERT INTO consumo_diario (usuario_id, alimento_id, quantidade_porcoes) VALUES (1, %s, %s);",
                (alimento_id, qtd_porcoes),
            )
            conn.commit()
            cur.close()
            conn.close()
            return self.GetDashboardData()
        except Exception as e:
            return {"error": str(e)}

    def DeleteDieta(self, id):
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM consumo_diario WHERE id = %s", (id,))
            conn.commit()
            cur.close()
            conn.close()
        except:
            pass
        return self.GetDashboardData()

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
            price_re = re.search(
                r'Valor atual do ativo.*?<strong[^>]*class="value"[^>]*>\s*([\d,\.]+)\s*</strong>',
                resp.text,
                re.DOTALL,
            )
            dy_re = re.search(
                r'Dividend Yield com base.*?<strong[^>]*class="value"[^>]*>\s*([\d,\.]+)\s*</strong>',
                resp.text,
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

    def GetAIInsights(self):
        try:
            dados_atuais = self.GetDashboardData()
            resumo = f"Treinos: {dados_atuais['summary']['treinos_realizados']}. Hábitos diários OK: {dados_atuais['summary']['taxa_habitos']}."
            model = genai.GenerativeModel("gemini-2.5-flash")
            resposta = model.generate_content(
                f"Aja como um mentor. Baseado nestes dados: {resumo}, escreva 2 frases curtas sobre a rotina dele."
            )
            return {"response": resposta.text.strip()}
        except Exception as e:
            return {"error": f"Erro na IA: {str(e)}"}


if __name__ == "__main__":
    app = LifeOSApp()
    app.ResetDatabase()

    webview.create_window(
        "LifeOS - Banco de Dados", "index.html", js_api=app, width=1100, height=800
    )
    webview.start()
