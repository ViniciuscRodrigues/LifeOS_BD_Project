import os
import re
import json # <-- Importação do JSON para ler os dados da IA

import google.generativeai as genai
import psycopg2
import psycopg2.extras
import requests
import webview
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

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

            cur.execute("INSERT INTO usuario (nome, email) VALUES ('Admin', 'admin@ufsc.br');")
            cur.execute("INSERT INTO conta_bancaria (usuario_id, nome_banco, saldo_atual) VALUES (1, 'Carteira', 0);")

            # Dados base essenciais mantidos para evitar falhas em abas que o usuário ainda não alimentou
            cur.execute("INSERT INTO disciplina_projeto (usuario_id, nome, categoria, semestre_ativo) VALUES (1, 'Banco de Dados', 'Faculdade', '2024.1');")
            cur.execute("INSERT INTO habito (usuario_id, nome, tipo, frequencia_alvo) VALUES (1, 'Beber 2L de Água', 'Meta', 7);")

            conn.commit()
            cur.close()
            conn.close()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # Função Auxiliar para processar retornos de IA em formato Estruturado
    def _parse_gemini_json(self, prompt):
        try:
            model = genai.GenerativeModel("gemini-2.5-flash")
            resposta = model.generate_content(prompt)
            text = resposta.text.strip()

            # Remove marcadores markdown (```json ... ```) se a IA adicionar
            if text.startswith("```"):
                lines = text.split('\n')
                if lines[0].startswith("
http://googleusercontent.com/immersive_entry_chip/0
http://googleusercontent.com/immersive_entry_chip/1

O fluxo agora é maravilhoso: Quando você digita "Peito de frango" e "150g" e aperta para Consumir, a interface avisa "⏳ Calculando Macros...", a requisição viaja até o backend Python, que manda um prompt estruturado para a Google API (Gemini). A API retorna um JSON matemático contendo as proteínas e calorias multiplicadas exatamente por 150g, e o Python insere os dados no PostgreSQL e te devolve o cartão preenchido na tela, exibindo um balão verde com a mensagem gerada. Tudo isso respeitando a arquitetura das 13 tabelas que criámos!
