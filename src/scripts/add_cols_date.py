# src/scripts/add_cols_date.py
import sqlite3
import os

# Caminho relativo à RAIZ do projeto
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(PROJECT_ROOT, "data", "equipamentos.db")

print(f"🔍 Caminho do banco: {DB_PATH}")
if not os.path.exists(DB_PATH):
    raise FileNotFoundError(f"Banco não encontrado em: {DB_PATH}")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Adiciona as colunas (uma por vez, com try/except)
for col in [
    ("data_recebimento", "TEXT"),
    ("data_devolucao", "TEXT"),
    ("valor_locacao", "REAL"),
    ("status", "TEXT DEFAULT 'Em uso'")
]:
    try:
        cursor.execute(f"ALTER TABLE equipamentos ADD COLUMN {col[0]} {col[1]};")
        print(f"✅ Coluna '{col[0]}' adicionada.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print(f"ℹ️  Coluna '{col[0]}' já existe.")
        else:
            print(f"⚠️  Erro ao adicionar '{col[0]}': {e}")

# Atualiza status existente
cursor.execute("UPDATE equipamentos SET status = 'Em uso' WHERE status IS NULL;")

conn.commit()
conn.close()
print("✅ Banco atualizado com sucesso.")