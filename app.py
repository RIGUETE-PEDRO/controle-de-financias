# app.py - VERSÃO FINAL E ORGANIZADA

import os
import io
from flask import Flask, request, jsonify, render_template, make_response
from flask_cors import CORS
from datetime import datetime
import openpyxl
from openpyxl.styles import Font, PatternFill

# Importa TODAS as funções do nosso novo database.py (que usa PostgreSQL)
from database import *

app = Flask(__name__)
CORS(app) 
iniciar_db() # Esta função agora prepara as tabelas no PostgreSQL

# --- ROTA PRINCIPAL (SERVE O SITE) ---
@app.route('/')
def index():
    return render_template('index.html')

# --- ROTAS DA API PARA TRANSAÇÕES ---
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
    try:
        adicionar_transacao(dados['descricao'], float(dados['valor']), dados['tipo'], dados['data'], dados['usuario'], dados.get('meta_id'))
        return jsonify({"sucesso": "Transação adicionada!"}), 201
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route('/api/transacoes/<int:transacao_id>', methods=['DELETE'])
def api_remover_transacao(transacao_id):
    try:
        remover_transacao(transacao_id)
        return jsonify({"sucesso": "Transação removida!"}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

# --- ROTAS DA API PARA METAS ---
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
    try:
        criar_meta(dados['nome'], float(dados['percentual']), dados['usuario'])
        return jsonify({"sucesso": "Meta criada!"}), 201
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route('/api/metas/<int:meta_id>', methods=['DELETE'])
def api_remover_meta(meta_id):
    try:
        remover_meta(meta_id)
        return jsonify({"sucesso": "Meta removida!"}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500
        
# --- ROTAS DA API PARA RELATÓRIOS ---
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
    
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="4F4F4F", end_color="4F4F4F", fill_type="solid")
    green_font = Font(color="008000", bold=True)
    red_font = Font(color="FF0000", bold=True)

    headers = ["Data", "Tipo", "Descrição", "Valor"]
    sheet.append(headers)
    for cell in sheet[1]:
        cell.font = header_font
        cell.fill = header_fill

    total_entradas, total_saidas = 0, 0
    for t in transacoes:
        valor = float(t['valor']) # Garantimos que o valor é um número
        # A data já vem como objeto date do PostgreSQL
        data_formatada = t['data'].strftime('%d/%m/%Y')
        tipo = t['tipo'].capitalize()
        row_data = [data_formatada, tipo, t['descricao'], valor]
        sheet.append(row_data)
        
        last_row = sheet.max_row
        valor_cell = sheet[f'D{last_row}']
        
        if t['tipo'] == 'entrada':
            total_entradas += valor
            valor_cell.font = green_font
        else:
            total_saidas += valor
            valor_cell.font = red_font

    sheet.append([])
    sheet.append(["", "", "Total Entradas:", total_entradas])
    sheet.append(["", "", "Total Saídas:", total_saidas])
    sheet.append(["", "", "Saldo do Período:", total_entradas - total_saidas])

    buffer = io.BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    response = make_response(buffer.getvalue())
    response.headers['Content-Disposition'] = f'attachment; filename=relatorio_{usuario}_{data_de}_a_{data_ate}.xlsx'
    response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    return response

@app.route('/api/relatorio/pizza', methods=['GET'])
def api_gerar_relatorio_pizza():
    usuario = request.args.get('usuario')
    mes = request.args.get('mes') # Espera um formato 'YYYY-MM'
    if not all([usuario, mes]):
        return jsonify({"erro": "Usuário e mês são obrigatórios"}), 400
    dados_grafico = obter_gastos_por_categoria(usuario, mes)
    return jsonify(dados_grafico)