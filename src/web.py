# src/web.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
import sqlite3
import os

# Importações do Flask-Login (serão usadas após inicialização)
login_user = None
logout_user = None
login_required = None
current_user = None

def init_flask_login():
    """Inicializa as funções do Flask-Login"""
    global login_user, logout_user, login_required, current_user
    from flask_login import login_user as _login_user
    from flask_login import logout_user as _logout_user  
    from flask_login import login_required as _login_required
    from flask_login import current_user as _current_user
    
    login_user = _login_user
    logout_user = _logout_user
    login_required = _login_required
    current_user = _current_user

def get_db_connection():
    """Conexão com o banco de dados"""
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'equipamentos_v2.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def verificar_credenciais(email, senha):
    """
    Verifica as credenciais do usuário e retorna seus dados se válido
    """
    import hashlib
    senha_hash = hashlib.sha256(senha.encode('utf-8')).hexdigest()
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                u.id,
                u.nome_completo,
                u.email,
                u.perfil_id,
                p.nome as perfil,
                u.status
            FROM usuarios u
            JOIN perfis_usuario p ON u.perfil_id = p.id
            WHERE u.email = ? AND u.senha_hash = ? AND u.status = 'Ativo'
        """, (email, senha_hash))
        
        usuario = cursor.fetchone()
        return dict(usuario) if usuario else None

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
    # Inicializa Flask-Login se ainda não foi feito
    if login_user is None:
        init_flask_login()
    
    caminho = request.path
    
    # Ignora rotas de API, assets, login e páginas públicas
    if (caminho.startswith('/api/') or 
        caminho.startswith('/static/') or
        caminho in ['/configuracoes', '/dashboard', '/', '/health', '/login']):
        return
    
    # Verifica se usuário está autenticado (exceto login)
    try:
        if not current_user.is_authenticated and caminho != '/login':
            return redirect(url_for('web.login'))
    except:
        # Se houver qualquer erro com current_user, redireciona para login
        return redirect(url_for('web.login'))
    
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

# ============================================================================  
# ROTAS DE AUTENTICAÇÃO
# ============================================================================  

@web_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login"""
    # Inicializa Flask-Login se ainda não foi feito
    if login_user is None:
        init_flask_login()
    
    try:
        if current_user.is_authenticated:
            return redirect(url_for('web.dashboard'))
    except:
        pass  # Ignora erros na verificação de autenticação
    
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        # Verifica credenciais
        usuario = verificar_credenciais(email, password)
        if usuario:
            from flask_login import UserMixin
            class User(UserMixin):
                def __init__(self, id, nome_completo, email, perfil, status):
                    self.id = id
                    self.nome_completo = nome_completo
                    self.email = email
                    self.perfil = perfil
                    self.status = status
            
            user = User(
                id=usuario['id'],
                nome_completo=usuario['nome_completo'],
                email=usuario['email'],
                perfil=usuario['perfil'],
                status=usuario['status']
            )
            login_user(user)
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('web.dashboard'))
        else:
            flash('Email ou senha inválidos.', 'error')
    
    return render_template('login.html')

@web_bp.route('/logout')
def logout():
    """Logout do usuário"""
    if logout_user is None:
        init_flask_login()
    
    try:
        logout_user()
        flash('Você foi desconectado.', 'info')
    except:
        pass  # Ignora erros no logout
    
    return redirect(url_for('web.login'))

# ============================================================================  
# DECORADOR DE LOGIN REQUERIDO
# ============================================================================  

def login_required_wrapper(func):
    """Decorador personalizado para login required"""
    def wrapper(*args, **kwargs):
        if login_required is None:
            init_flask_login()
        
        try:
            if not current_user.is_authenticated:
                return redirect(url_for('web.login'))
        except:
            return redirect(url_for('web.login'))
        
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

# ============================================================================  
# ROTAS PRINCIPAIS (PROTEGIDAS)
# ============================================================================  

@web_bp.route('/')
@login_required_wrapper
def home():
    """Página inicial com links para diferentes áreas do sistema"""
    return render_template('home.html')

@web_bp.route('/dashboard')
@login_required_wrapper
def dashboard():
    """Dashboard principal com visão geral dos ativos"""
    # Verifica se há dados para mostrar dashboard dinâmico
    if verificar_dados_ativos():
        return render_template('dashboard_dinamico.html')
    else:
        return render_template('dashboard.html')

@web_bp.route('/ativos')
@login_required_wrapper
def gerenciar_ativos():
    """Página principal de gerenciamento de ativos"""
    return render_template('gerenciar_ativos.html')

@web_bp.route('/ativos/cadastrar')
@login_required_wrapper
def cadastrar_ativo():
    """Formulário para cadastro de novo ativo"""
    return render_template('cadastrar_ativo.html')

@web_bp.route('/ativos/<int:ativo_id>')
@login_required_wrapper
def detalhes_ativo(ativo_id):
    """Detalhes de um ativo específico"""
    return render_template('detalhes_ativo.html', ativo_id=ativo_id)

@web_bp.route('/ativos/lote')
@login_required_wrapper
def upload_lote():
    """Upload em lote de ativos via CSV"""
    return render_template('upload_lote.html')

@web_bp.route('/contratos')
@login_required_wrapper
def gerenciar_contratos():
    """Página de gerenciamento de contratos de locação"""
    return render_template('gerenciar_contratos.html')

@web_bp.route('/contratos/cadastrar')
@login_required_wrapper
def cadastrar_contrato():
    """Formulário para cadastro de novo contrato de locação"""
    return render_template('cadastrar_contrato.html')

@web_bp.route('/solicitacoes')
@login_required_wrapper
def gerenciar_solicitacoes():
    """Página de gerenciamento de solicitações de novos ativos"""
    return render_template('gerenciar_solicitacoes.html')

@web_bp.route('/solicitacoes/nova')
@login_required_wrapper
def nova_solicitacao():
    """Formulário para nova solicitação de ativos"""
    return render_template('nova_solicitacao.html')

@web_bp.route('/usuarios')
@login_required_wrapper
def gerenciar_usuarios():
    """Página de gerenciamento de usuários (apenas para administradores)"""
    return render_template('gerenciar_usuarios.html')

@web_bp.route('/relatorios')
@login_required_wrapper
def relatorios():
    """Página de relatórios e exportações"""
    return render_template('relatorios.html')

@web_bp.route('/configuracoes')
@login_required_wrapper
def configuracoes():
    """Página de configurações do sistema (listas controladas, etc.)"""
    return render_template('configuracoes.html')

# Rotas de compatibilidade (mantidas temporariamente)
@web_bp.route('/home')
@login_required_wrapper
def dashboard_compat():
    return redirect(url_for('web.dashboard'))

@web_bp.route('/gerenciar')
@login_required_wrapper
def gerenciar_compat():
    return redirect(url_for('web.gerenciar_ativos'))

@web_bp.route('/cadastrar')
@login_required_wrapper
def cadastrar_compat():
    return redirect(url_for('web.cadastrar_ativo'))

@web_bp.route('/lote')
@login_required_wrapper
def lote_compat():
    return redirect(url_for('web.upload_lote'))