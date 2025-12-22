# src/routes.py
from flask import Blueprint, jsonify, request
from models import buscar_equipamentos, atualizar_equipamento  # ← sem ponto

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

@api_bp.route('/equipamentos/<patrimonio>', methods=['PATCH'])
def atualizar(patrimonio):
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Corpo JSON vazio"}), 400

    # Só permite campos que existem na tabela
    campos_permitidos = {"status", "data_recebimento", "data_devolucao", "valor_locacao", "local_atual", "usuario"}
    dados = {k: v for k, v in dados.items() if k in campos_permitidos}

    if not dados:
        return jsonify({"erro": "Nenhum campo válido para atualizar"}), 400

    if atualizar_equipamento(patrimonio, dados):
        return jsonify({"mensagem": "Equipamento atualizado"}), 200
    else:
        return jsonify({"erro": "Equipamento não encontrado"}), 404