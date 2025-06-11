# app.py
import os
import sqlite3
import io
import openpyxl
from flask import Flask, request, jsonify, render_template, make_response
from flask_cors import CORS
from datetime import datetime
from database import * # Importa todas as funções do nosso arquivo database

app = Flask(__name__)
CORS(app) 
iniciar_db()

@app.route('/')
def index():
    return render_template('index.html')

# --- ROTAS DE TRANSAÇÃO ---
@app.route('/api/transacoes', methods=['GET'])
def api_obter_transacoes():
    usuario = request.args.get('usuario')
    if not usuario: return jsonify({"erro": "Usuário é obrigatório"}), 400
    transacoes = obter_transacoes_por_usuario(usuario)
    return jsonify(transacoes)

@app.route('/api/transacoes', methods=['POST'])
def api_adicionar_transacao():
    dados = request.get_json()
    if not all(k in dados for k in ['descricao', 'valor', 'tipo', 'usuario', 'data']):
        return jsonify({"erro": "Dados incompletos"}), 400
    adicionar_transacao(dados['descricao'], float(dados['valor']), dados['tipo'], dados['data'], dados['usuario'], dados.get('meta_id'))
    return jsonify({"sucesso": "Transação adicionada!"}), 201

@app.route('/api/transacoes/<int:transacao_id>', methods=['DELETE'])
def api_remover_transacao(transacao_id):
    remover_transacao(transacao_id)
    return jsonify({"sucesso": "Transação removida!"}), 200

# --- ROTAS DE META ---
@app.route('/api/metas', methods=['GET'])
def api_obter_metas():
    usuario = request.args.get('usuario')
    if not usuario: return jsonify({"erro": "Usuário é obrigatório"}), 400
    metas = obter_metas_por_usuario(usuario)
    return jsonify(metas)

@app.route('/api/metas', methods=['POST'])
def api_criar_meta():
    dados = request.get_json()
    if not all(k in dados for k in ['nome', 'percentual', 'usuario']):
        return jsonify({"erro": "Dados incompletos"}), 400
    criar_meta(dados['nome'], float(dados['percentual']), dados['usuario'])
    return jsonify({"sucesso": "Meta criada!"}), 201

@app.route('/api/metas/<int:meta_id>', methods=['DELETE'])
def api_remover_meta(meta_id):
    remover_meta(meta_id)
    return jsonify({"sucesso": "Meta removida!"}), 200

# --- ROTA DE RELATÓRIO ---
@app.route('/api/relatorio', methods=['GET'])
def api_gerar_relatorio():
    usuario = request.args.get('usuario')
    data_de = request.args.get('de')
    data_ate = request.args.get('ate')

    if not all([usuario, data_de, data_ate]):
        return jsonify({"erro": "Usuário e período são obrigatórios"}), 400

    transacoes = obter_transacoes_por_periodo(usuario, data_de, data_ate)
    
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = f"Relatório de {usuario}"
    sheet.append(["Data", "Tipo", "Descrição", "Valor"])
    # ... (lógica de preenchimento do Excel) ...
    # Salva o arquivo em memória e força o download no navegador
    buffer = io.BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    response = make_response(buffer.getvalue())
    response.headers['Content-Disposition'] = f'attachment; filename=relatorio_{usuario}_{data_de}_a_{data_ate}.xlsx'
    response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    return response

# if __name__ == '__main__': ...