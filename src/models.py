# src/models.py
import sqlite3
import os

# Caminho absoluto para o banco (funciona em qualquer ambiente)
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'equipamentos.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # permite acesso por nome da coluna
    return conn

def buscar_equipamentos(filtros: dict):
    query = "SELECT * FROM equipamentos WHERE 1=1"
    params = []

    if filtros.get("tipo"):
        query += " AND tipo LIKE ?"
        params.append(f"%{filtros['tipo']}%")
    if filtros.get("usuario"):
        query += " AND usuario LIKE ?"
        params.append(f"%{filtros['usuario']}%")
    if filtros.get("patrimonio"):
        query += " AND patrimonio LIKE ?"
        params.append(f"%{filtros['patrimonio']}%")
    if filtros.get("serie"):
        query += " AND numero_serie LIKE ?"
        params.append(f"%{filtros['serie']}%")
    if filtros.get("setor"):
        query += " AND setor LIKE ?"
        params.append(f"%{filtros['setor']}%")
    if filtros.get("local"):
        query += " AND local_atual LIKE ?"
        params.append(f"%{filtros['local']}%")
    if filtros.get("status"):
        query += " AND status = ?"
        params.append(filtros['status'])

    query += " ORDER BY usuario, tipo"

    with get_db_connection() as conn:
        return conn.execute(query, params).fetchall()

def atualizar_equipamento(patrimonio: str, dados: dict):
    if not dados:
        return False
        
    set_clause = ", ".join([f"{k} = ?" for k in dados.keys()])
    params = list(dados.values()) + [patrimonio]

    query = f"UPDATE equipamentos SET {set_clause} WHERE patrimonio = ?"
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.rowcount > 0