# database.py
import sqlite3
from datetime import datetime

DB_NAME = 'transacoes.db'

def iniciar_db():
    """Cria as tabelas transacoes e metas, e adiciona a coluna meta_id se não existir."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Tabela de Transações
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        descricao TEXT NOT NULL,
        valor REAL NOT NULL,
        tipo TEXT NOT NULL,
        data TIMESTAMP NOT NULL,
        usuario_id TEXT NOT NULL,
        meta_id INTEGER,
        FOREIGN KEY (meta_id) REFERENCES metas (id)
    )
    """)
    
    # Tabela de Metas
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS metas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        percentual REAL NOT NULL,
        usuario_id TEXT NOT NULL
    )
    """)
    
    # Adiciona a coluna 'meta_id' de forma segura para não quebrar execuções antigas
    try:
        cursor.execute("SELECT meta_id FROM transacoes LIMIT 1")
    except sqlite3.OperationalError:
        print("Adicionando coluna 'meta_id' à tabela de transações...")
        cursor.execute("ALTER TABLE transacoes ADD COLUMN meta_id INTEGER REFERENCES metas(id)")
    
    conn.commit()
    conn.close()

# --- Funções de Transação ---

def adicionar_transacao(descricao, valor, tipo, data_str, usuario_id, meta_id=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO transacoes (descricao, valor, tipo, data, usuario_id, meta_id) VALUES (?, ?, ?, ?, ?, ?)",
        (descricao, valor, tipo, data_str, usuario_id, meta_id)
    )
    conn.commit()
    conn.close()

def remover_transacao(transacao_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM transacoes WHERE id = ?", (transacao_id,))
    conn.commit()
    conn.close()

def obter_transacoes_por_usuario(usuario_id):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM transacoes WHERE usuario_id = ? ORDER BY data DESC", (usuario_id,))
    transacoes = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return transacoes

# database.py

# ... (resto do arquivo) ...

def obter_transacoes_por_periodo(usuario_id, data_inicio, data_fim):
    """Busca transações dentro de um intervalo de datas de forma robusta."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    # --- MODIFICADO: Usando a função date() do SQL para uma comparação mais segura ---
    cursor.execute(
        "SELECT * FROM transacoes WHERE usuario_id = ? AND date(data) BETWEEN date(?) AND date(?) ORDER BY data ASC",
        (usuario_id, data_inicio, data_fim)
    )
    transacoes = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return transacoes

# --- Funções de Meta ---

def criar_meta(nome, percentual, usuario_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO metas (nome, percentual, usuario_id) VALUES (?, ?, ?)", (nome, percentual, usuario_id))
    conn.commit()
    conn.close()

def obter_metas_por_usuario(usuario_id):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM metas WHERE usuario_id = ? ORDER BY nome", (usuario_id,))
    metas = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return metas

def remover_meta(meta_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM metas WHERE id = ?", (meta_id,))
    conn.commit()
    conn.close()

    # database.py

# ... (resto do arquivo) ...

def obter_gastos_por_categoria(usuario_id, ano_mes):
    """Soma os gastos por categoria (meta) para um determinado mês/ano (formato 'YYYY-MM')."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    # Esta query agrupa as transações por meta e soma seus valores
    query = """
        SELECT m.nome as categoria, SUM(t.valor) as total
        FROM transacoes t
        JOIN metas m ON t.meta_id = m.id
        WHERE t.usuario_id = ? AND strftime('%Y-%m', t.data) = ? AND t.tipo = 'saida'
        GROUP BY m.nome
        HAVING total > 0
    """
    cursor.execute(query, (usuario_id, ano_mes))
    dados_grafico = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return dados_grafico