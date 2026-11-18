# src/middleware.py
from flask import request, redirect, url_for, flash
from models import get_db_connection, verificar_banco_existe

def verificar_tabelas_existentes():
    """Verifica se as tabelas necessárias existem no banco"""
    if not verificar_banco_existe():
        return False
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('empresas', 'locais', 'cargos', 'ativos', 'usuarios')")
            return len(cursor.fetchall()) > 0
    except:
        return False

def verificar_configuracao_minima():
    """Verifica se o sistema tem configuração mínima para funcionar"""
    if not verificar_tabelas_existentes():
        return False
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
    if not verificar_tabelas_existentes():
        return False
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM ativos")
            return cursor.fetchone()[0] > 0
    except Exception as e:
        print(f"Erro ao verificar ativos: {e}")
        return False

def verificar_dados_usuarios():
    """Verifica se há usuários cadastrados no sistema"""
    if not verificar_tabelas_existentes():
        return False
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM usuarios")
            return cursor.fetchone()[0] > 0
    except Exception as e:
        print(f"Erro ao verificar usuários: {e}")
        return False