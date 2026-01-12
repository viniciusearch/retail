# src/routes.py
import sqlite3
from flask import Blueprint, jsonify, request
from models import buscar_equipamentos, atualizar_equipamento, get_db_connection

api_bp = Blueprint('api', __name__)

@api_bp.route('/equipamentos', methods=['GET'])
def buscar():
    filtros = {
        "tipo": request.args.get("tipo"),
        "usuario": request.args.get("usuario"),
        "patrimonio": request.args.get("patrimonio"),
        "serie": request.args.get("serie"),
        "setor": request.args.get("setor"),
        "local": request.args.get("local"),
        "status": request.args.get("status")
    }
    # Remove valores None ou vazios
    filtros = {k: v for k, v in filtros.items() if v}
    
    resultados = buscar_equipamentos(filtros)
    return jsonify([dict(row) for row in resultados])

@api_bp.route('/equipamentos', methods=['POST'])
def criar_equipamento():
    dados = request.get_json()
    if not dados or not dados.get('patrimonio'):
        return jsonify({"erro": "Patrimônio é obrigatório"}), 400

    # Lista de campos permitidos para criação (baseado na tabela + novos como 'host')
    campos_permitidos = {
        "patrimonio", "tipo", "descritivo", "centro_custo", "numero_serie",
        "local_atual", "setor", "usuario", "cargo", "obra_projeto",
        "observacao", "data_recebimento", "data_devolucao", "valor_locacao",
        "status", "teamviewer_id", "host"
    }

    # Filtra apenas os campos válidos
    dados_filtrados = {k: v for k, v in dados.items() if k in campos_permitidos}

    if not dados_filtrados.get('patrimonio'):
        return jsonify({"erro": "Patrimônio é obrigatório"}), 400

    # Define status padrão se não informado
    if 'status' not in dados_filtrados:
        dados_filtrados['status'] = 'Em uso'

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            colunas = ', '.join(dados_filtrados.keys())
            placeholders = ', '.join(['?'] * len(dados_filtrados))
            query = f"INSERT INTO equipamentos ({colunas}) VALUES ({placeholders})"
            cursor.execute(query, list(dados_filtrados.values()))
            conn.commit()
        return jsonify({
            "mensagem": "Equipamento cadastrado com sucesso",
            "patrimonio": dados_filtrados['patrimonio']
        }), 201
    except sqlite3.IntegrityError as e:
        if 'UNIQUE constraint failed' in str(e) and 'patrimonio' in str(e):
            return jsonify({"erro": "Patrimônio já existe"}), 409
        return jsonify({"erro": "Erro de integridade ao salvar"}), 400
    except Exception as e:
        return jsonify({"erro": f"Erro interno: {str(e)}"}), 500

@api_bp.route('/equipamentos/<patrimonio>', methods=['PATCH'])
def atualizar(patrimonio):
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Corpo JSON vazio"}), 400

    # Só permite campos que existem na tabela
    campos_permitidos = {"status","numero_serie","data_recebimento","descritivo", "data_devolucao", "valor_locacao", "local_atual", "usuario", "teamviewer_id", "cargo", "host", "centro_custo", "setor", "obra_projeto", "observacao"}
    dados = {k: v for k, v in dados.items() if k in campos_permitidos}

    if not dados:
        return jsonify({"erro": "Nenhum campo válido para atualizar"}), 400

    if atualizar_equipamento(patrimonio, dados):
        return jsonify({"mensagem": "Equipamento atualizado"}), 200
    else:
        return jsonify({"erro": "Equipamento não encontrado"}), 404