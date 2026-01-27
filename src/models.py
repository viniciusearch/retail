# src/models.py - VERSÃO ATUALIZADA PARA NOVA ARQUITETURA
import sqlite3
import os
from typing import List, Dict, Any, Optional, Tuple
import hashlib

# Caminho absoluto para o banco (funciona em qualquer ambiente)
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'equipamentos_v2.db')

def get_db_connection():
    """Retorna uma conexão com o banco de dados SQLite"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # permite acesso por nome da coluna
    return conn

# ============================================================================  
# FUNÇÕES DE AUTENTICAÇÃO
# ============================================================================  

def hash_senha(senha: str) -> str:
    """
    Gera hash SHA256 da senha
    """
    return hashlib.sha256(senha.encode('utf-8')).hexdigest()

def verificar_credenciais(email: str, senha: str) -> Optional[Dict[str, Any]]:
    """
    Verifica as credenciais do usuário e retorna seus dados se válido
    """
    senha_hash = hash_senha(senha)
    
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

def criar_usuario_inicial():
    """
    Cria usuário administrador inicial se não existir
    """
    senha_admin = "admin123"  # Senha padrão - deve ser alterada após primeiro login
    senha_hash = hash_senha(senha_admin)
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Verifica se já existe usuário administrador
        cursor.execute("SELECT COUNT(*) FROM usuarios WHERE email = 'admin@empresa.com'")
        if cursor.fetchone()[0] == 0:
            # Insere usuário administrador
            cursor.execute("""
                INSERT INTO usuarios 
                (nome_completo, email, senha_hash, perfil_id, status)
                VALUES (?, ?, ?, ?, ?)
            """, ('Administrador', 'admin@empresa.com', senha_hash, 1, 'Ativo'))
            
            conn.commit()
            print("Usuário administrador criado:")
            print(f"Email: admin@empresa.com")
            print(f"Senha: {senha_admin}")
            print("⚠️  Altere a senha após o primeiro login!")

# ============================================================================  
# FUNÇÕES PRINCIPAIS DE CRUD PARA ATIVOS
# ============================================================================  

def buscar_ativos(filtros: Optional[Dict[str, Any]] = None) -> List[sqlite3.Row]:
    """
    Busca ativos com filtros avançados
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Query base com joins
        query = """
            SELECT 
                a.*,
                e.nome as proprietario_nome,
                u.nome_completo as usuario_nome,
                l.nome as local_nome,
                l.ambiente as local_ambiente,
                l.predio as local_predio,
                l.setor as local_setor
            FROM ativos a
            LEFT JOIN empresas e ON a.proprietario_id = e.id
            LEFT JOIN usuarios u ON a.usuario_atual_id = u.id  
            LEFT JOIN locais l ON a.local_atual_id = l.id
            WHERE 1=1
        """
        params = []
        
        if filtros:
            # Filtros por tipo de ativo
            if filtros.get('tipo_ativo'):
                if isinstance(filtros['tipo_ativo'], list):
                    placeholders = ','.join(['?'] * len(filtros['tipo_ativo']))
                    query += f" AND a.tipo_ativo IN ({placeholders})"
                    params.extend(filtros['tipo_ativo'])
                else:
                    query += " AND a.tipo_ativo = ?"
                    params.append(filtros['tipo_ativo'])
            
            # Filtros por categoria
            if filtros.get('categoria'):
                if isinstance(filtros['categoria'], list):
                    placeholders = ','.join(['?'] * len(filtros['categoria']))
                    query += f" AND a.categoria IN ({placeholders})"
                    params.extend(filtros['categoria'])
                else:
                    query += " AND a.categoria = ?"
                    params.append(filtros['categoria'])
            
            # Filtros por status
            if filtros.get('status'):
                if isinstance(filtros['status'], list):
                    placeholders = ','.join(['?'] * len(filtros['status']))
                    query += f" AND a.status IN ({placeholders})"
                    params.extend(filtros['status'])
                else:
                    query += " AND a.status = ?"
                    params.append(filtros['status'])
            
            # Filtros por código de ativo (busca parcial)
            if filtros.get('codigo_ativo'):
                query += " AND a.codigo_ativo LIKE ?"
                params.append(f"%{filtros['codigo_ativo']}%")
            
            # Filtros por descrição (busca parcial)
            if filtros.get('descricao'):
                query += " AND a.descricao LIKE ?"
                params.append(f"%{filtros['descricao']}%")
            
            # Filtros por ambiente de local
            if filtros.get('ambiente_local'):
                query += " AND l.ambiente = ?"
                params.append(filtros['ambiente_local'])
            
            # Filtros por prédio (só para obra)
            if filtros.get('predio'):
                query += " AND l.predio = ?"
                params.append(filtros['predio'])
            
            # Filtros por setor de local
            if filtros.get('setor_local'):
                query += " AND l.setor = ?"
                params.append(filtros['setor_local'])
            
            # Filtros por proprietário
            if filtros.get('proprietario'):
                query += " AND e.nome = ?"
                params.append(filtros['proprietario'])
            
            # Filtros por usuário
            if filtros.get('usuario'):
                query += " AND u.nome_completo LIKE ?"
                params.append(f"%{filtros['usuario']}%")
        
        query += " ORDER BY a.codigo_ativo"
        cursor.execute(query, params)
        return cursor.fetchall()

def criar_ativo(dados: Dict[str, Any]) -> int:
    """
    Cria um novo ativo
    """
    campos_obrigatorios = ['codigo_ativo', 'tipo_ativo', 'categoria']
    for campo in campos_obrigatorios:
        if not dados.get(campo):
            raise ValueError(f"Campo obrigatório '{campo}' não fornecido")
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Insere ativo principal
        campos_ativo = ['codigo_ativo', 'tipo_ativo', 'categoria', 'descricao', 'status', 
                       'proprietario_id', 'usuario_atual_id', 'local_atual_id', 'projeto', 
                       'data_aquisicao', 'observacoes']
        
        valores_ativo = [dados.get(campo) for campo in campos_ativo]
        
        placeholders = ','.join(['?'] * len(campos_ativo))
        campos_str = ','.join(campos_ativo)
        
        cursor.execute(f"INSERT INTO ativos ({campos_str}) VALUES ({placeholders})", valores_ativo)
        ativo_id = cursor.lastrowid
        
        # Insere atributos dinâmicos
        if dados.get('atributos'):
            for chave, valor in dados['atributos'].items():
                if valor is not None:
                    cursor.execute(
                        "INSERT INTO atributos_ativos (ativo_id, chave, valor) VALUES (?, ?, ?)",
                        (ativo_id, chave, str(valor))
                    )
        
        conn.commit()
        return ativo_id

def atualizar_ativo(ativo_id: int, dados: Dict[str, Any]) -> bool:
    """
    Atualiza os dados de um ativo
    """
    campos_permitidos = {
        'codigo_ativo', 'tipo_ativo', 'categoria', 'descricao', 'status',
        'proprietario_id', 'usuario_atual_id', 'local_atual_id', 'projeto',
        'data_aquisicao', 'observacoes'
    }
    
    # Filtra apenas os campos válidos
    dados_filtrados = {k: v for k, v in dados.items() if k in campos_permitidos}
    
    if not dados_filtrados:
        return False

    set_clause = ", ".join([f"{k} = ?" for k in dados_filtrados.keys()])
    params = list(dados_filtrados.values()) + [ativo_id]

    query = f"UPDATE ativos SET {set_clause} WHERE id = ?"
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return cursor.rowcount > 0

def excluir_ativo(ativo_id: int) -> bool:
    """
    Exclui um ativo (com CASCADE nos atributos)
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM ativos WHERE id = ?", (ativo_id,))
        conn.commit()
        return cursor.rowcount > 0

# ============================================================================  
# FUNÇÕES PARA ATRIBUTOS DINÂMICOS
# ============================================================================  

def obter_atributos_ativo(ativo_id: int) -> Dict[str, str]:
    """
    Retorna todos os atributos de um ativo
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT chave, valor FROM atributos_ativos WHERE ativo_id = ?", (ativo_id,))
        return {row['chave']: row['valor'] for row in cursor.fetchall()}

def atualizar_atributos_ativo(ativo_id: int, atributos: Dict[str, str]) -> None:
    """
    Atualiza os atributos de um ativo
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Primeiro, remove todos os atributos existentes
        cursor.execute("DELETE FROM atributos_ativos WHERE ativo_id = ?", (ativo_id,))
        
        # Depois, insere os novos
        for chave, valor in atributos.items():
            if valor is not None:
                cursor.execute(
                    "INSERT INTO atributos_ativos (ativo_id, chave, valor) VALUES (?, ?, ?)",
                    (ativo_id, chave, str(valor))
                )
        
        conn.commit()

# ============================================================================  
# FUNÇÕES DE FILTROS E LISTAS CONTROLADAS
# ============================================================================  

def obter_valores_distintos_locais() -> Dict[str, List[str]]:
    """
    Retorna valores distintos para filtros de locais
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Ambientes
        cursor.execute("SELECT DISTINCT ambiente FROM locais ORDER BY ambiente")
        ambientes = [row[0] for row in cursor.fetchall()]
        
        # Prédios (só para obra)
        cursor.execute("SELECT DISTINCT predio FROM locais WHERE predio IS NOT NULL ORDER BY predio")
        predios = [row[0] for row in cursor.fetchall()]
        
        # Setores
        cursor.execute("SELECT DISTINCT setor FROM locais ORDER BY setor")
        setores = [row[0] for row in cursor.fetchall()]
        
        return {
            'ambientes': ambientes,
            'predios': predios,
            'setores': setores
        }

def obter_valores_distintos_ativos() -> Dict[str, List[str]]:
    """
    Retorna valores distintos para filtros de ativos
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Tipos de ativo
        cursor.execute("SELECT DISTINCT tipo_ativo FROM ativos WHERE tipo_ativo IS NOT NULL ORDER BY tipo_ativo")
        tipos_ativo = [row[0] for row in cursor.fetchall()]
        
        # Categorias
        cursor.execute("SELECT DISTINCT categoria FROM ativos WHERE categoria IS NOT NULL ORDER BY categoria")
        categorias = [row[0] for row in cursor.fetchall()]
        
        # Status
        cursor.execute("SELECT DISTINCT status FROM ativos WHERE status IS NOT NULL ORDER BY status")
        status = [row[0] for row in cursor.fetchall()]
        
        # Proprietários
        cursor.execute("SELECT DISTINCT nome FROM empresas ORDER BY nome")
        proprietarios = [row[0] for row in cursor.fetchall()]
        
        return {
            'tipos_ativo': tipos_ativo,
            'categorias': categorias,
            'status': status,
            'proprietarios': proprietarios
        }

# ============================================================================  
# FUNÇÕES PARA CONTRATOS DE LOCAÇÃO
# ============================================================================  

def buscar_contratos_locacao(filtros: Optional[Dict[str, Any]] = None) -> List[sqlite3.Row]:
    """
    Busca contratos de locação com filtros
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        query = """
            SELECT 
                c.*,
                e.nome as fornecedor_nome
            FROM contratos_locacao c
            LEFT JOIN empresas e ON c.empresa_id = e.id
            WHERE 1=1
        """
        params = []
        
        if filtros:
            if filtros.get('numero_contrato'):
                query += " AND c.numero_contrato LIKE ?"
                params.append(f"%{filtros['numero_contrato']}%")
            
            if filtros.get('fornecedor'):
                query += " AND e.nome = ?"
                params.append(filtros['fornecedor'])
            
            if filtros.get('status'):
                query += " AND c.status = ?"
                params.append(filtros['status'])
        
        query += " ORDER BY c.data_inicio DESC"
        cursor.execute(query, params)
        return cursor.fetchall()

def vincular_ativo_contrato(ativo_id: int, contrato_id: int) -> bool:
    """
    Vincula um ativo a um contrato de locação
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO ativos_contratos (ativo_id, contrato_id) VALUES (?, ?)",
                (ativo_id, contrato_id)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

def desvincular_ativo_contrato(ativo_id: int, contrato_id: int) -> bool:
    """
    Remove o vínculo entre ativo e contrato
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM ativos_contratos WHERE ativo_id = ? AND contrato_id = ?",
            (ativo_id, contrato_id)
        )
        conn.commit()
        return cursor.rowcount > 0

def obter_contratos_do_ativo(ativo_id: int) -> List[sqlite3.Row]:
    """
    Retorna todos os contratos vinculados a um ativo
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                c.*,
                e.nome as fornecedor_nome
            FROM ativos_contratos ac
            JOIN contratos_locacao c ON ac.contrato_id = c.id
            JOIN empresas e ON c.empresa_id = e.id
            WHERE ac.ativo_id = ?
        """, (ativo_id,))
        return cursor.fetchall()

# ============================================================================  
# FUNÇÕES PARA SOLICITAÇÕES
# ============================================================================  

def criar_solicitacao(dados: Dict[str, Any]) -> int:
    """
    Cria uma nova solicitação
    """
    campos_obrigatorios = ['tipo_solicitacao', 'descricao', 'setor_solicitante_id', 'gestor_solicitante_id']
    for campo in campos_obrigatorios:
        if not dados.get(campo):
            raise ValueError(f"Campo obrigatório '{campo}' não fornecido")
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        campos = ['tipo_solicitacao', 'descricao', 'quantidade', 'especificacoes',
                 'setor_solicitante_id', 'gestor_solicitante_id', 'prioridade']
        valores = [dados.get(campo) for campo in campos]
        
        placeholders = ','.join(['?'] * len(campos))
        campos_str = ','.join(campos)
        
        cursor.execute(f"INSERT INTO solicitacoes ({campos_str}) VALUES ({placeholders})", valores)
        conn.commit()
        return cursor.lastrowid

def buscar_solicitacoes(filtros: Optional[Dict[str, Any]] = None) -> List[sqlite3.Row]:
    """
    Busca solicitações com filtros
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        query = """
            SELECT 
                s.*,
                setor.nome as setor_solicitante_nome,
                gestor.nome_completo as gestor_solicitante_nome,
                aprovador.nome_completo as aprovador_nome,
                executor.nome_completo as executor_nome
            FROM solicitacoes s
            LEFT JOIN setores setor ON s.setor_solicitante_id = setor.id
            LEFT JOIN usuarios gestor ON s.gestor_solicitante_id = gestor.id
            LEFT JOIN usuarios aprovador ON s.aprovador_id = aprovador.id
            LEFT JOIN usuarios executor ON s.executor_id = executor.id
            WHERE 1=1
        """
        params = []
        
        if filtros:
            if filtros.get('status'):
                query += " AND s.status = ?"
                params.append(filtros['status'])
            
            if filtros.get('setor_solicitante_id'):
                query += " AND s.setor_solicitante_id = ?"
                params.append(filtros['setor_solicitante_id'])
            
            if filtros.get('gestor_solicitante_id'):
                query += " AND s.gestor_solicitante_id = ?"
                params.append(filtros['gestor_solicitante_id'])
        
        query += " ORDER BY s.data_solicitacao DESC"
        cursor.execute(query, params)
        return cursor.fetchall()

# ============================================================================  
# FUNÇÕES AUXILIARES
# ============================================================================  

def contar_ativos() -> int:
    """Retorna o total de ativos"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM ativos")
        return cursor.fetchone()[0]

def contar_ativos_por_status() -> List[sqlite3.Row]:
    """Retorna contagem de ativos por status"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT status, COUNT(*) as total FROM ativos GROUP BY status")
        return cursor.fetchall()

# ============================================================================  
# INICIALIZAÇÃO
# ============================================================================  

# Cria usuário administrador inicial ao importar o módulo
criar_usuario_inicial()