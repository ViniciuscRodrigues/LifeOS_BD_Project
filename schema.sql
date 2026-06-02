DROP TABLE IF EXISTS registro_habito CASCADE;
DROP TABLE IF EXISTS habito CASCADE;
DROP TABLE IF EXISTS consumo_diario CASCADE;
DROP TABLE IF EXISTS alimento_suplemento CASCADE;
DROP TABLE IF EXISTS serie_treino CASCADE;
DROP TABLE IF EXISTS registro_treino CASCADE;
DROP TABLE IF EXISTS exercicio_fisico CASCADE;
DROP TABLE IF EXISTS sessao_estudo CASCADE;
DROP TABLE IF EXISTS disciplina_projeto CASCADE;
DROP TABLE IF EXISTS investimento CASCADE;
DROP TABLE IF EXISTS transacao_financeira CASCADE;
DROP TABLE IF EXISTS conta_bancaria CASCADE;
DROP TABLE IF EXISTS usuario CASCADE;

CREATE TABLE usuario (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE conta_bancaria (
    id SERIAL PRIMARY KEY,
    usuario_id INT REFERENCES usuario(id) ON DELETE CASCADE,
    nome_banco VARCHAR(100) NOT NULL,
    saldo_atual DECIMAL(12,2) DEFAULT 0.00
);

CREATE TABLE transacao_financeira (
    id SERIAL PRIMARY KEY,
    conta_id INT REFERENCES conta_bancaria(id) ON DELETE CASCADE,
    tipo VARCHAR(20) NOT NULL CHECK (tipo IN ('Entrada', 'Saida')),
    categoria VARCHAR(50) NOT NULL,
    valor DECIMAL(12,2) NOT NULL,
    data_transacao DATE NOT NULL DEFAULT CURRENT_DATE
);

CREATE TABLE investimento (
    id SERIAL PRIMARY KEY,
    usuario_id INT REFERENCES usuario(id) ON DELETE CASCADE,
    categoria VARCHAR(50) NOT NULL,
    ticker_nome VARCHAR(50) NOT NULL,
    valor_investido DECIMAL(12,2) DEFAULT 0.00,
    taxa_yield DECIMAL(8,2) DEFAULT 0.00,
    cotas INT DEFAULT 0,
    data_aporte DATE DEFAULT CURRENT_DATE
);

CREATE TABLE disciplina_projeto (
    id SERIAL PRIMARY KEY,
    usuario_id INT REFERENCES usuario(id) ON DELETE CASCADE,
    nome VARCHAR(100) NOT NULL,
    categoria VARCHAR(50) NOT NULL,
    semestre_ativo VARCHAR(20)
);

CREATE TABLE sessao_estudo (
    id SERIAL PRIMARY KEY,
    disciplina_id INT REFERENCES disciplina_projeto(id) ON DELETE CASCADE,
    data_sessao DATE NOT NULL DEFAULT CURRENT_DATE,
    duracao_minutos INT NOT NULL,
    topico_estudado VARCHAR(255)
);

CREATE TABLE exercicio_fisico (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    grupo_muscular VARCHAR(50) NOT NULL
);

CREATE TABLE registro_treino (
    id SERIAL PRIMARY KEY,
    usuario_id INT REFERENCES usuario(id) ON DELETE CASCADE,
    data_treino DATE NOT NULL DEFAULT CURRENT_DATE,
    duracao_minutos INT
);

CREATE TABLE serie_treino (
    id SERIAL PRIMARY KEY,
    registro_treino_id INT REFERENCES registro_treino(id) ON DELETE CASCADE,
    exercicio_id INT REFERENCES exercicio_fisico(id) ON DELETE CASCADE,
    repeticoes INT NOT NULL,
    carga_kg DECIMAL(5,2) NOT NULL
);

CREATE TABLE alimento_suplemento (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    porcao_gramas DECIMAL(6,2) NOT NULL,
    calorias INT NOT NULL,
    proteina_g DECIMAL(6,2) NOT NULL,
    carboidrato_g DECIMAL(6,2) NOT NULL,
    gordura_g DECIMAL(6,2) NOT NULL
);

CREATE TABLE consumo_diario (
    id SERIAL PRIMARY KEY,
    usuario_id INT REFERENCES usuario(id) ON DELETE CASCADE,
    alimento_id INT REFERENCES alimento_suplemento(id) ON DELETE CASCADE,
    data_consumo DATE NOT NULL DEFAULT CURRENT_DATE,
    quantidade_porcoes DECIMAL(5,2) NOT NULL
);

CREATE TABLE habito (
    id SERIAL PRIMARY KEY,
    usuario_id INT REFERENCES usuario(id) ON DELETE CASCADE,
    nome VARCHAR(100) NOT NULL,
    tipo VARCHAR(20) NOT NULL CHECK (tipo IN ('Meta', 'Limite')),
    frequencia_alvo INT NOT NULL
);

CREATE TABLE registro_habito (
    id SERIAL PRIMARY KEY,
    habito_id INT REFERENCES habito(id) ON DELETE CASCADE,
    data_registro DATE NOT NULL DEFAULT CURRENT_DATE,
    status VARCHAR(20) NOT NULL CHECK (status IN ('Concluido', 'Falhou', 'Pendente'))
);
