# database.py - VERSÃO FINAL PARA POSTGRESQL

import os
import psycopg2
from psycopg2.extras import RealDictCursor # Usado para retornar resultados como dicionários

# A URL de conexão virá das variáveis de ambiente que configuramos na Render
DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    """Cria e retorna uma nova conexão com o banco de dados PostgreSQL."""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except psycopg2.OperationalError as e:
        print(f"ERRO CRÍTICO: Não foi possível conectar ao banco de dados PostgreSQL: {e}")
        # Em um app real, você poderia ter mais lógica de erro aqui.
        raise

def iniciar_db():
    """Cria as tabelas no banco de dados PostgreSQL se elas não existirem."""
    conn = get_db_connection()
    # Usar 'with' garante que a conexão e o cursor sejam fechados corretamente
    with conn.cursor() as cur:
        # Usamos SERIAL PRIMARY KEY para auto-incremento no PostgreSQL
        cur.execute("""
        CREATE TABLE IF NOT EXISTS transacoes (
            id SERIAL PRIMARY KEY,
            descricao TEXT NOT NULL,
            valor NUMERIC(10, 2) NOT NULL,
            tipo TEXT NOT NULL,
            data DATE NOT NULL,
            usuario_id TEXT NOT NULL,
            meta_id INTEGER
        );
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS metas (
            id SERIAL PRIMARY KEY,
            nome TEXT NOT NULL,
            percentual NUMERIC(5, 2) NOT NULL,
            usuario_id TEXT NOT NULL
        );
        """)
        # Adicionamos a FK após a criação de ambas as tabelas
        # Esta parte pode dar erro se já existir, mas em um banco novo funcionará.
        try:
            cur.execute("""
            ALTER TABLE transacoes
            ADD CONSTRAINT fk_metas
            FOREIGN KEY (meta_id) 
            REFERENCES metas(id)
            ON DELETE SET NULL;
            """)
        except psycopg2.errors.DuplicateObject:
            # A restrição já existe, o que é normal em execuções subsequentes.
            pass

    conn.commit()
    conn.close()
    print("Banco de dados PostgreSQL e tabelas verificados/criados com sucesso.")

def _executar_query(query, params=(), fetch=None):
    """Função auxiliar para executar queries de forma segura."""
    conn = get_db_connection()
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query, params)
        if fetch == 'um':
            resultado = cur.fetchone()
        elif fetch == 'todos':
            resultado = cur.fetchall()
        else:
            resultado = None
    conn.commit()
    conn.close()
    return resultado

# --- Funções de Transação ---

def adicionar_transacao(descricao, valor, tipo, data_str, usuario_id, meta_id=None):
    sql = "INSERT INTO transacoes (descricao, valor, tipo, data, usuario_id, meta_id) VALUES (%s, %s, %s, %s, %s, %s)"
    _executar_query(sql, (descricao, valor, tipo, data_str, usuario_id, meta_id))

def remover_transacao(transacao_id):
    _executar_query("DELETE FROM transacoes WHERE id = %s", (transacao_id,))

def obter_transacoes_por_usuario(usuario_id):
    return _executar_query("SELECT * FROM transacoes WHERE usuario_id = %s ORDER BY data DESC, id DESC", (usuario_id,), fetch='todos')

def obter_transacoes_por_periodo(usuario_id, data_inicio, data_fim):
    sql = "SELECT * FROM transacoes WHERE usuario_id = %s AND data BETWEEN %s AND %s ORDER BY data ASC"
    return _executar_query(sql, (usuario_id, data_inicio, data_fim), fetch='todos')

# --- Funções de Meta ---

def criar_meta(nome, percentual, usuario_id):
    _executar_query("INSERT INTO metas (nome, percentual, usuario_id) VALUES (%s, %s, %s)", (nome, percentual, usuario_id))

def obter_metas_por_usuario(usuario_id):
    return _executar_query("SELECT * FROM metas WHERE usuario_id = %s ORDER BY nome", (usuario_id,), fetch='todos')

def remover_meta(meta_id):
    # Antes de remover a meta, desvinculamos das transações para não dar erro
    _executar_query("UPDATE transacoes SET meta_id = NULL WHERE meta_id = %s", (meta_id,))
    # Agora removemos a meta
    _executar_query("DELETE FROM metas WHERE id = %s", (meta_id,))

def obter_gastos_por_categoria(usuario_id, ano_mes):
    query = """
        SELECT m.nome as categoria, SUM(t.valor) as total
        FROM transacoes t
        JOIN metas m ON t.meta_id = m.id
        WHERE t.usuario_id = %s AND TO_CHAR(t.data, 'YYYY-MM') = %s AND t.tipo = 'saida'
        GROUP BY m.nome
        HAVING SUM(t.valor) > 0
    """
    return _executar_query(query, (usuario_id, ano_mes), fetch='todos')