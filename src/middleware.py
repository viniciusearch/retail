# src/middleware.py
from flask import request, redirect, url_for, flash
import sqlite3
import os

def get_db_path():
    """Retorna o caminho absoluto do banco de dados"""
    # Caminho relativo ao diretório raiz do projeto
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'equipamentos_v2.db')

def get_db_connection():
    """Conexão com o banco de dados"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def verificar_banco_existe():
    """Verifica se o arquivo do banco de dados existe"""
    return os.path.exists(get_db_path())

def verificar_tabelas_existentes():
    """Verifica se as tabelas necessárias existem no banco"""
    if not verificar_banco_existe():
        return False
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Verifica se pelo menos uma tabela do sistema existe
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('empresas', 'locais', 'cargos', 'ativos', 'usuarios')")
            return len(cursor.fetchall()) > 0
    except:
        return False

def verificar_configuracao_minima():
    """
    Verifica se o sistema tem configuração mínima para funcionar
    Retorna True se estiver configurado, False caso contrário
    """
    # Se o banco não existe ou não tem tabelas, considera como não configurado
    if not verificar_tabelas_existentes():
        return False
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Verifica se há pelo menos uma empresa configurada
            cursor.execute("SELECT COUNT(*) FROM empresas")
            empresas_count = cursor.fetchone()[0]
            
            # Verifica se há pelo menos um local configurado  
            cursor.execute(" SELECT COUNT(*) FROM locais")
            locais_count = cursor.fetchone()[0]
            
            # Verifica se há pelo menos um cargo configurado
            cursor.execute("SELECT COUNT(*) FROM cargos")
            cargos_count = cursor.fetchone()[0]
            
            # Sistema está configurado se tiver pelo menos:
            # - 1 empresa (proprietária ou fornecedora)
            # - 1 local físico  
            # - 1 cargo
            return empresas_count > 0 and locais_count > 0 and cargos_count > 0
            
    except sqlite3.OperationalError:
        # Tabelas não existem ainda
        return False
    except Exception as e:
        print(f"Erro ao verificar configuração: {e}")
        return False

def verificar_dados_ativos():
    """
    Verifica se há ativos cadastrados no sistema
    Retorna True se houver ativos, False caso contrário
    """
    if not verificar_tabelas_existentes():
        return False
        
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM ativos")
            ativos_count = cursor.fetchone()[0]
            return ativos_count > 0
    except sqlite3.OperationalError:
        # Tabela ativos não existe ainda
        return False
    except Exception as e:
        print(f"Erro ao verificar ativos: {e}")
        return False

def verificar_dados_usuarios():
    """
    Verifica se há usuários cadastrados no sistema
    Retorna True se houver usuários, False caso contrário
    """
    if not verificar_tabelas_existentes():
        return False
        
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM usuarios")
            usuarios_count = cursor.fetchone()[0]
            return usuarios_count > 0
    except sqlite3.OperationalError:
        # Tabela usuarios não existe ainda
        return False
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
    # Removido '/dashboard' - tratado diretamente no web.py
]

# Rotas que requerem usuários cadastrados  
ROTAS_REQUEREM_USUARIOS = [
    '/usuarios',
    '/solicitacoes',
    '/solicitacoes/nova'
]