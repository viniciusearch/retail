# src/web.py
from flask import Blueprint, render_template, request, redirect, url_for

web_bp = Blueprint('web', __name__, template_folder='templates')

@web_bp.route('/')
def home():
    return render_template('index.html')

@web_bp.route('/atualizar')
def atualizar():
    return render_template('atualizar.html')

@web_bp.route('/devolvidos')
def devolvidos():
    return render_template('devolvidos.html')

@web_bp.route('/buscar')
def buscar_pagina():
    return render_template('buscar.html')

@web_bp.route('/listar')
def listar_pagina():
    # Opcional: passar os filtros para o template (se quiser pré-preencher)
    tipo = request.args.get('tipo', '')
    status = request.args.get('status', '')
    return render_template('listar.html', tipo=tipo, status=status)

@web_bp.route('/gerenciar')
def gerenciar():
    return render_template('equipamentos.html')

@web_bp.route('/cadastrar')
def cadastrar():
    return render_template('cadastrar.html')