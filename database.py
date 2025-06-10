# database.py
import sqlite3
from datetime import datetime

DB_NAME = 'transacoes.db' # Mudamos o nome para refletir a nova estrutura

def iniciar_db():
    """Cria a tabela de transações com uma coluna 'tipo'."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Mudamos a tabela para 'transacoes' e adicionamos o campo 'tipo'
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        descricao TEXT NOT NULL,
        valor REAL NOT NULL,
        tipo TEXT NOT NULL, -- 'entrada' ou 'saida'
        data TIMESTAMP NOT NULL,
        usuario_id TEXT NOT NULL
    )
    """)
    conn.commit()
    conn.close()

def adicionar_transacao(descricao, valor, tipo, usuario_id):
    """Adiciona uma nova transação (entrada ou saída)."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO transacoes (descricao, valor, tipo, data, usuario_id) VALUES (?, ?, ?, ?, ?)",
        (descricao, valor, tipo, datetime.now(), usuario_id)
    )
    conn.commit()
    conn.close()
    print(f"Banco de dados: Transação adicionada: {tipo} - {descricao}, R$ {valor}")

# >>> NOVO: Função para remover uma transação <<<
def remover_transacao(transacao_id):
    """Remove uma transação pelo seu ID."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM transacoes WHERE id = ?", (transacao_id,))
    conn.commit()
    conn.close()
    print(f"Banco de dados: Transação removida: ID {transacao_id}")