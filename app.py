# app.py
import os
import sqlite3
from flask import Flask, request, jsonify
from flask_cors import CORS
# Importamos as novas funções do banco de dados
from database import adicionar_transacao, remover_transacao, iniciar_db

app = Flask(__name__)
CORS(app) 

iniciar_db()

# Rota para ADICIONAR uma transação (recebe 'tipo' do front-end)
@app.route('/api/transacoes', methods=['POST'])
def api_adicionar_transacao():
    dados = request.get_json()
    # Agora verificamos se o 'tipo' também foi enviado
    if not dados or 'descricao' not in dados or 'valor' not in dados or 'tipo' not in dados:
        return jsonify({"erro": "Dados incompletos"}), 400

    try:
        # Adicionamos o 'tipo' ao adicionar a transação
        adicionar_transacao(dados['descricao'], float(dados['valor']), dados['tipo'], 'web_user')
        return jsonify({"sucesso": "Transação adicionada!"}), 201
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

# Rota para OBTER todas as transações
@app.route('/api/transacoes', methods=['GET'])
def api_obter_transacoes():
    try:
        conn = sqlite3.connect('transacoes.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM transacoes ORDER BY data DESC")
        transacoes = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify(transacoes)
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

# >>> NOVO: Rota para REMOVER uma transação <<<
@app.route('/api/transacoes/<int:transacao_id>', methods=['DELETE'])
def api_remover_transacao(transacao_id):
    try:
        remover_transacao(transacao_id)
        return jsonify({"sucesso": "Transação removida!"}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500
    
@app.route('/')
def index():
    return "API de Gestão Financeira está funcionando!"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)