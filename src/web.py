# src/web.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
import sqlite3
import os

def get_db_connection():
    """Conexão com o banco de dados"""
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'equipamentos_v2.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def verificar_configuracao_minima():
    """Verifica se o sistema tem configuração mínima para funcionar"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM empresas")
            empresas_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM locais")
            locais_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM cargos")
            cargos_count = cursor.fetchone()[0]
            return empresas_count > 0 and locais_count > 0 and cargos_count > 0
    except Exception as e:
        print(f"Erro ao verificar configuração: {e}")
        return False

def verificar_dados_ativos():
    """Verifica se há ativos cadastrados no sistema"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM ativos")
            ativos_count = cursor.fetchone()[0]
            return ativos_count > 0
    except Exception as e:
        print(f"Erro ao verificar ativos: {e}")
        return False

def verificar_dados_usuarios():
    """Verifica se há usuários cadastrados no sistema"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM usuarios")
            usuarios_count = cursor.fetchone()[0]
            return usuarios_count > 0
    except Exception as e:
        print(f"Erro ao verificar usuários: {e}")
        return False

# Rotas que requerem configuração mínima
ROTAS_REQUEREM_CONFIG = [
    '/ativos',
    '/ativos/cadastrar', 
    '/ativos/lote',
    '/contratos',
    '/contratos/cadastrar',
    '/solicitacoes',
    '/solicitacoes/nova',
    '/usuarios',
    '/relatorios'
]

# Rotas que requerem ativos cadastrados
ROTAS_REQUEREM_ATIVOS = [
    '/ativos',
    '/relatorios'
]

# Rotas que requerem usuários cadastrados  
ROTAS_REQUEREM_USUARIOS = [
    '/usuarios',
    '/solicitacoes',
    '/solicitacoes/nova'
]

web_bp = Blueprint('web', __name__, template_folder='templates', static_folder='static')

@web_bp.before_app_request
def verificar_acesso_paginas():
    """Middleware que verifica acesso às páginas antes de cada requisição"""
    caminho = request.path
    
    # Ignora rotas de API, assets e páginas permitidas
    if (caminho.startswith('/api/') or 
        caminho.startswith('/static/') or
        caminho in ['/configuracoes', '/dashboard', '/', '/health']):
        return
    
    # Verifica configuração mínima
    if caminho in ROTAS_REQUEREM_CONFIG:
        if not verificar_configuracao_minima():
            flash('⚠️ Configure as listas básicas antes de acessar esta página.', 'warning')
            return redirect(url_for('web.configuracoes'))
    
    # Verifica se há ativos cadastrados
    if caminho in ROTAS_REQUEREM_ATIVOS:
        if not verificar_dados_ativos():
            flash('📊 Cadastre seus primeiros ativos para visualizar esta página.', 'info')
            return redirect(url_for('web.cadastrar_ativo'))
    
    # Verifica se há usuários cadastrados
    if caminho in ROTAS_REQUEREM_USUARIOS:
        if not verificar_dados_usuarios():
            flash('👥 Configure os usuários do sistema antes de acessar esta funcionalidade.', 'info')
            return redirect(url_for('web.configuracoes'))

@web_bp.route('/')
def home():
    """Página inicial com links para diferentes áreas do sistema"""
    return render_template('home.html')

@web_bp.route('/dashboard')
def dashboard():
    """Dashboard principal com visão geral dos ativos"""
    # Verifica se há dados para mostrar dashboard dinâmico
    if verificar_dados_ativos():
        return render_template('dashboard_dinamico.html')
    else:
        return render_template('dashboard.html')

@web_bp.route('/ativos')
def gerenciar_ativos():
    """Página principal de gerenciamento de ativos"""
    return render_template('gerenciar_ativos.html')

@web_bp.route('/ativos/cadastrar')
def cadastrar_ativo():
    """Formulário para cadastro de novo ativo"""
    return render_template('cadastrar_ativo.html')

@web_bp.route('/ativos/<int:ativo_id>')
def detalhes_ativo(ativo_id):
    """Detalhes de um ativo específico"""
    return render_template('detalhes_ativo.html', ativo_id=ativo_id)

@web_bp.route('/ativos/lote')
def upload_lote():
    """Upload em lote de ativos via CSV"""
    return render_template('upload_lote.html')

@web_bp.route('/contratos')
def gerenciar_contratos():
    """Página de gerenciamento de contratos de locação"""
    return render_template('gerenciar_contratos.html')

@web_bp.route('/contratos/cadastrar')
def cadastrar_contrato():
    """Formulário para cadastro de novo contrato de locação"""
    return render_template('cadastrar_contrato.html')

@web_bp.route('/solicitacoes')
def gerenciar_solicitacoes():
    """Página de gerenciamento de solicitações de novos ativos"""
    return render_template('gerenciar_solicitacoes.html')

@web_bp.route('/solicitacoes/nova')
def nova_solicitacao():
    """Formulário para nova solicitação de ativos"""
    return render_template('nova_solicitacao.html')

@web_bp.route('/usuarios')
def gerenciar_usuarios():
    """Página de gerenciamento de usuários (apenas para administradores)"""
    return render_template('gerenciar_usuarios.html')

@web_bp.route('/relatorios')
def relatorios():
    """Página de relatórios e exportações"""
    return render_template('relatorios.html')

@web_bp.route('/configuracoes')
def configuracoes():
    """Página de configurações do sistema (listas controladas, etc.)"""
    return render_template('configuracoes.html')

# Rotas de compatibilidade (mantidas temporariamente)
@web_bp.route('/home')
def dashboard_compat():
    return redirect(url_for('web.dashboard'))

@web_bp.route('/gerenciar')
def gerenciar_compat():
    return redirect(url_for('web.gerenciar_ativos'))

@web_bp.route('/cadastrar')
def cadastrar_compat():
    return redirect(url_for('web.cadastrar_ativo'))

@web_bp.route('/lote')
def lote_compat():
    return redirect(url_for('web.upload_lote'))