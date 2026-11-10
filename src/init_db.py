#!/usr/bin/env python3
"""
Script para zerar e recriar o banco de dados do sistema CTC INFRA
Executar na raiz do projeto: python init_db.py
"""

import os
import sqlite3

# Caminho do banco
DB_DIR = os.path.join(os.path.dirname(__file__), 'data')
DB_PATH = os.path.join(DB_DIR, 'equipamentos_v2.db')

# Caminho dos scripts SQL
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'src', 'schema_v3.sql')
SEED_PATH = os.path.join(os.path.dirname(__file__), 'src', 'seed_inicial.sql')


def criar_diretorio_data():
    """Cria o diretório data se não existir"""
    if not os.path.exists(DB_DIR):
        os.makedirs(DB_DIR)
        print(f"✅ Diretório criado: {DB_DIR}")


def zerar_banco():
    """Remove o banco de dados existente"""
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"🗑️  Banco de dados removido: {DB_PATH}")
    else:
        print(f"ℹ️  Nenhum banco encontrado em: {DB_PATH}")


def criar_banco():
    """Cria o banco de dados com schema e seed"""
    criar_diretorio_data()
    
    # Verifica se os arquivos SQL existem
    if not os.path.exists(SCHEMA_PATH):
        print(f"❌ ERRO: Arquivo não encontrado: {SCHEMA_PATH}")
        return False
    
    if not os.path.exists(SEED_PATH):
        print(f"❌ ERRO: Arquivo não encontrado: {SEED_PATH}")
        return False
    
    # Conecta ao banco (cria se não existir)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Executa o schema
        print(f"\n📋 Executando schema: {SCHEMA_PATH}")
        with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        cursor.executescript(schema_sql)
        print("✅ Schema executado com sucesso")
        
        # Executa o seed
        print(f"\n🌱 Executando seed: {SEED_PATH}")
        with open(SEED_PATH, 'r', encoding='utf-8') as f:
            seed_sql = f.read()
        cursor.executescript(seed_sql)
        print("✅ Seed executado com sucesso")
        
        conn.commit()
        
        # Verifica os dados
        print("\n📊 Verificação dos dados:")
        tabelas = ['empresas', 'cargos', 'setores', 'locais', 
                   'perfis_usuario', 'usuarios', 'ativos', 'atributos_ativos']
        
        for tabela in tabelas:
            cursor.execute(f"SELECT COUNT(*) FROM {tabela}")
            count = cursor.fetchone()[0]
            print(f"  • {tabela}: {count} registros")
        
        print(f"\n✅ Banco criado com sucesso em: {DB_PATH}")
        print("\n🔐 Credenciais de acesso:")
        print("   Email: admin@ctcinfra.com.br")
        print("   Senha: admin123")
        print("\n⚠️  IMPORTANTE: Altere a senha após o primeiro login!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO ao criar banco: {str(e)}")
        conn.rollback()
        return False
    finally:
        conn.close()


if __name__ == '__main__':
    print("=" * 70)
    print("  CTC INFRA - Sistema de Gestão de Ativos")
    print("  Script de Inicialização do Banco de Dados")
    print("=" * 70)
    
    # Confirmação antes de zerar
    if os.path.exists(DB_PATH):
        print(f"\n⚠️  ATENÇÃO: O banco atual será REMOVIDO!")
        print(f"   Caminho: {DB_PATH}")
        confirm = input("\n   Deseja continuar? (s/N): ").strip().lower()
        if confirm != 's':
            print("❌ Operação cancelada.")
            exit(0)
    
    # Zera e recria
    zerar_banco()
    sucesso = criar_banco()
    
    if sucesso:
        print("\n" + "=" * 70)
        print("  ✅ Sistema pronto para uso!")
        print("  Execute: python src/app.py")
        print("=" * 70)
    else:
        print("\n" + "=" * 70)
        print("  ❌ Falha ao criar o banco. Verifique os erros acima.")
        print("=" * 70)
        exit(1)