# src/scripts/import_csv_to_db.py
import sqlite3
import csv
import os

DB_PATH = "data/equipamentos.db"
CSV_PATH = "data/equipamentos.csv"

os.makedirs("data", exist_ok=True)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS equipamentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo TEXT,
    descritivo TEXT,
    centro_custo TEXT,
    patrimonio TEXT,
    numero_serie TEXT UNIQUE,
    local_atual TEXT,
    setor TEXT,
    usuario TEXT,
    funcao TEXT,
    obra_projeto TEXT,
    observacao TEXT
)
""")

# Lê o CSV com o separador ";" e codificação correta
with open(CSV_PATH, "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f, delimiter=";")  # <-- delimiter=";" é essencial

    for row in reader:
        # Pula linhas vazias
        if not row.get("PATRIMONIO_NUMERO_SERIE", "").strip():
            continue

        # Separa Patrimônio / Número de Série
        pat_serie = row.get("PATRIMONIO_NUMERO_SERIE", "").strip()
        if "/" in pat_serie:
            partes = pat_serie.split("/", 1)
            patrimonio = partes[0].strip()
            numero_serie = partes[1].strip()
        else:
            patrimonio = pat_serie
            numero_serie = ""

        # Determina tipo com base no DESCRITIVO
        desc = (row.get("DESCRITIVO") or "").lower()
        if "notebook" in desc:
            tipo = "Notebook"
        elif "desktop" in desc or "gabinete" in desc or "small pc" in desc:
            tipo = "Desktop"
        elif "monitor" in desc:
            tipo = "Monitor"
        elif "tablet" in desc:
            tipo = "Tablet"
        elif "impressora" in desc or "plotter" in desc:
            tipo = "Plotter/Impressora"
        else:
            tipo = "Outro"

        cursor.execute("""
        INSERT OR REPLACE INTO equipamentos
        (tipo, descritivo, centro_custo, patrimonio, numero_serie,
         local_atual, setor, usuario, funcao, obra_projeto, observacao)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            tipo,
            row.get("DESCRITIVO"),
            row.get("CENTRO CUSTO"),
            patrimonio,
            numero_serie,
            row.get("LOCAL ATUAL"),
            row.get("SETOR"),
            row.get("USUÁRIO"),
            row.get("FUNÇÃO"),
            row.get("OBRA / PROJETO"),
            row.get("OBSERVAÇÃO")
        ))

conn.commit()
conn.close()
print("✅ Banco populado com sucesso.")