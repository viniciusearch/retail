# src/models.py - VERSÃO REFATORADA
import sqlite3
import os
from typing import List, Dict, Any, Optional, Tuple

# Caminho absoluto para o banco (funciona em qualquer ambiente)
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'equipamentos.db')

def get_db_connection():
    """Retorna uma conexão com o banco de dados SQLite"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # permite acesso por nome da coluna
    return conn

# ============================================================================
# FUNÇÕES PRINCIPAIS DE CRUD
# ============================================================================

def buscar_equipamentos(filtros: Dict[str, List[str]]) -> List[sqlite3.Row]:
    """
    Busca equipamentos com filtros básicos (mantida para compatibilidade)
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        query = "SELECT * FROM equipamentos WHERE 1=1"
        params = []
        
        if filtros.get("patrimonio"):
            # Para patrimônio, usamos OR porque é busca específica
            placeholders = " OR ".join(["patrimonio = ?"] * len(filtros["patrimonio"]))
            query += f" AND ({placeholders})"
            params.extend(filtros["patrimonio"])
        else:
            # Para outros filtros, usamos IN
            for campo in ["tipo", "status", "local_atual", "setor", "usuario"]:
                if filtros.get(campo):
                    placeholders = ",".join(["?"] * len(filtros[campo]))
                    query += f" AND {campo} IN ({placeholders})"
                    params.extend(filtros[campo])
            
            if filtros.get("serie"):
                placeholders = ",".join(["?"] * len(filtros["serie"]))
                query += f" AND numero_serie IN ({placeholders})"
                params.extend(filtros["serie"])
        
        cursor.execute(query, params)
        return cursor.fetchall()

def buscar_equipamentos_avancado(
    filtros: Optional[Dict[str, Any]] = None, 
    pagina: int = 1, 
    por_pagina: int = 50, 
    ordenar_por: str = 'patrimonio', 
    ordenar_direcao: str = 'ASC'
) -> Tuple[List[sqlite3.Row], int]:
    """
    Busca avançada com filtros complexos e paginação
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        query = "SELECT * FROM equipamentos WHERE 1=1"
        params = []
        
        if filtros:
            # Busca por termo geral (procura em múltiplos campos)
            if filtros.get('q'):
                termo = f"%{filtros['q']}%"
                query += """
                    AND (patrimonio LIKE ? 
                    OR descritivo LIKE ? 
                    OR numero_serie LIKE ?
                    OR usuario LIKE ?
                    OR host LIKE ?
                    OR local_atual LIKE ?
                    OR tipo LIKE ?)
                """
                params.extend([termo] * 7)
            
            # Filtros exatos
            campos_exatos = ['tipo', 'status', 'setor', 'centro_custo', 'obra_projeto', 'funcao', 'cargo']
            for campo in campos_exatos:
                valor = filtros.get(campo)
                if valor:
                    if isinstance(valor, list) and len(valor) > 0:
                        placeholders = ', '.join(['?'] * len(valor))
                        query += f" AND {campo} IN ({placeholders})"
                        params.extend(valor)
                    elif valor:
                        query += f" AND {campo} = ?"
                        params.append(valor)
            
            # Filtros de texto parcial
            campos_parcial = ['usuario', 'local_atual', 'descritivo', 'patrimonio', 'serie', 'teamviewer_id', 'host']
            for campo in campos_parcial:
                valor = filtros.get(campo)
                if valor:
                    query += f" AND {campo} LIKE ?"
                    params.append(f"%{valor}%")
            
            # Filtros de data
            if filtros.get('data_recebimento_inicio'):
                query += " AND date(data_recebimento) >= date(?)"
                params.append(filtros['data_recebimento_inicio'])
            
            if filtros.get('data_recebimento_fim'):
                query += " AND date(data_recebimento) <= date(?)"
                params.append(filtros['data_recebimento_fim'])
            
            # Filtros de valor
            if filtros.get('valor_min'):
                query += " AND valor_locacao >= ?"
                params.append(float(filtros['valor_min']))
            
            if filtros.get('valor_max'):
                query += " AND valor_locacao <= ?"
                params.append(float(filtros['valor_max']))
        
        # Ordenação
        campos_validos = ['id', 'tipo', 'descritivo', 'centro_custo', 'patrimonio', 
                         'numero_serie', 'local_atual', 'setor', 'usuario', 'funcao',
                         'obra_projeto', 'data_recebimento', 'data_devolucao', 
                         'valor_locacao', 'status', 'cargo', 'host']
        
        if ordenar_por in campos_validos:
            query += f" ORDER BY {ordenar_por} {ordenar_direcao}"
        else:
            query += " ORDER BY patrimonio ASC"
        
        # Paginação
        if por_pagina > 0:
            offset = (pagina - 1) * por_pagina
            query += " LIMIT ? OFFSET ?"
            params.extend([por_pagina, offset])
        
        cursor.execute(query, params)
        resultados = cursor.fetchall()
        
        # Conta total
        if por_pagina > 0:
            # Query de contagem simplificada
            count_params = []
            count_query = "SELECT COUNT(*) FROM equipamentos WHERE 1=1"
            
            if filtros and filtros.get('q'):
                count_query += """
                    AND (patrimonio LIKE ? 
                    OR descritivo LIKE ? 
                    OR numero_serie LIKE ?
                    OR usuario LIKE ?
                    OR host LIKE ?
                    OR local_atual LIKE ?
                    OR tipo LIKE ?)
                """
                count_params.extend([f"%{filtros['q']}%"] * 7)
            
            cursor.execute(count_query, count_params)
            total = cursor.fetchone()[0]
        else:
            total = len(resultados)
        
        return resultados, total

def atualizar_equipamento(patrimonio: str, dados: Dict[str, Any]) -> bool:
    """
    Atualiza os dados de um equipamento
    """
    campos_permitidos = {
        "status", "data_recebimento", "data_devolucao", "valor_locacao", 
        "local_atual", "usuario", "teamviewer_id", "cargo", "host", 
        "descritivo", "centro_custo", "numero_serie", "setor", "obra_projeto", 
        "observacao", "tipo", "funcao"
    }
    
    # Filtra apenas os campos válidos
    dados_filtrados = {k: v for k, v in dados.items() if k in campos_permitidos}
    
    if not dados_filtrados:
        return False

    set_clause = ", ".join([f"{k} = ?" for k in dados_filtrados.keys()])
    params = list(dados_filtrados.values()) + [patrimonio]

    query = f"UPDATE equipamentos SET {set_clause} WHERE patrimonio = ?"
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return cursor.rowcount > 0

# ============================================================================
# FUNÇÕES DE FILTROS E ESTATÍSTICAS
# ============================================================================

def obter_valores_distintos(campo: str) -> List[str]:
    """
    Retorna valores distintos de um campo para usar em filtros
    """
    campos_permitidos = ['tipo', 'status', 'centro_custo', 'setor', 
                        'funcao', 'cargo', 'obra_projeto', 'local_atual', 'usuario']
    
    if campo not in campos_permitidos:
        return []
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT DISTINCT {campo} 
            FROM equipamentos 
            WHERE {campo} IS NOT NULL 
            AND {campo} != ''
            ORDER BY {campo}
        """)
        return [row[0] for row in cursor.fetchall()]

def obter_estatisticas_gerais() -> Dict[str, Any]:
    """
    Retorna estatísticas gerais dos equipamentos
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Total por status
        cursor.execute("""
            SELECT status, COUNT(*) as total 
            FROM equipamentos 
            GROUP BY status 
            ORDER BY total DESC
        """)
        por_status = cursor.fetchall()
        
        # Total por tipo
        cursor.execute("""
            SELECT tipo, COUNT(*) as total 
            FROM equipamentos 
            WHERE tipo IS NOT NULL AND tipo != ''
            GROUP BY tipo 
            ORDER BY total DESC
        """)
        por_tipo = cursor.fetchall()
        
        # Total por centro de custo
        cursor.execute("""
            SELECT centro_custo, COUNT(*) as total 
            FROM equipamentos 
            WHERE centro_custo IS NOT NULL AND centro_custo != ''
            GROUP BY centro_custo 
            ORDER BY total DESC
        """)
        por_centro_custo = cursor.fetchall()
        
        # Equipamentos sem centro de custo
        cursor.execute("""
            SELECT COUNT(*) as total_sem_cc
            FROM equipamentos
            WHERE centro_custo IS NULL OR centro_custo = ''
        """)
        sem_centro_custo = cursor.fetchone()[0]
        
        return {
            'por_status': por_status,
            'por_tipo': por_tipo,
            'por_centro_custo': por_centro_custo,
            'sem_centro_custo': sem_centro_custo
        }

# ============================================================================
# FUNÇÕES ESPECÍFICAS PARA CENTRO DE CUSTO
# ============================================================================

def listar_centros_custo() -> List[sqlite3.Row]:
    """
    Retorna todos os centros de custo com estatísticas básicas
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                centro_custo,
                COUNT(*) as total_equipamentos,
                COUNT(CASE WHEN status = 'Em uso' THEN 1 END) as em_uso,
                COUNT(CASE WHEN status = 'Disponível' THEN 1 END) as disponivel,
                COUNT(CASE WHEN status = 'Manutenção' THEN 1 END) as manutencao,
                COUNT(CASE WHEN status = 'Baixado' THEN 1 END) as baixado,
                SUM(CASE WHEN valor_locacao IS NOT NULL THEN valor_locacao ELSE 0 END) as valor_total
            FROM equipamentos
            WHERE centro_custo IS NOT NULL 
            AND centro_custo != ''
            GROUP BY centro_custo
            ORDER BY total_equipamentos DESC
        """)
        
        return cursor.fetchall()

def buscar_equipamentos_por_centro_custo(
    centro_custo: str, 
    filtros: Optional[Dict[str, Any]] = None,
    pagina: int = 1,
    por_pagina: int = 100
) -> Tuple[List[sqlite3.Row], int]:
    """
    Lista equipamentos de um centro de custo específico
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        query = "SELECT * FROM equipamentos WHERE centro_custo = ?"
        params = [centro_custo]
        
        if filtros:
            # Status
            if filtros.get('status'):
                query += " AND status = ?"
                params.append(filtros['status'])
            
            # Tipo
            if filtros.get('tipo'):
                query += " AND tipo = ?"
                params.append(filtros['tipo'])
            
            # Usuário (busca parcial)
            if filtros.get('usuario'):
                query += " AND usuario LIKE ?"
                params.append(f"%{filtros['usuario']}%")
            
            # Local
            if filtros.get('local'):
                query += " AND local_atual LIKE ?"
                params.append(f"%{filtros['local']}%")
            
            # Setor
            if filtros.get('setor'):
                query += " AND setor = ?"
                params.append(filtros['setor'])
        
        # Ordenação
        ordenar_por = filtros.get('ordenar_por', 'patrimonio') if filtros else 'patrimonio'
        ordenar_direcao = filtros.get('ordenar_direcao', 'ASC') if filtros else 'ASC'
        
        campos_validos = ['patrimonio', 'tipo', 'usuario', 'local_atual', 'setor', 
                         'status', 'data_recebimento', 'valor_locacao']
        
        if ordenar_por in campos_validos:
            query += f" ORDER BY {ordenar_por} {ordenar_direcao}"
        else:
            query += " ORDER BY patrimonio ASC"
        
        # Paginação
        if por_pagina > 0:
            offset = (pagina - 1) * por_pagina
            query += " LIMIT ? OFFSET ?"
            params.extend([por_pagina, offset])
        
        cursor.execute(query, params)
        resultados = cursor.fetchall()
        
        # Conta total
        count_query = "SELECT COUNT(*) FROM equipamentos WHERE centro_custo = ?"
        count_params = [centro_custo]
        
        if filtros and filtros.get('status'):
            count_query += " AND status = ?"
            count_params.append(filtros['status'])
        
        cursor.execute(count_query, count_params)
        total = cursor.fetchone()[0]
        
        return resultados, total

def obter_resumo_centro_custo(centro_custo: str) -> Optional[Dict[str, Any]]:
    """
    Retorna resumo detalhado de um centro de custo
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Verifica se o centro de custo existe
        cursor.execute("SELECT COUNT(*) FROM equipamentos WHERE centro_custo = ?", (centro_custo,))
        total_equipamentos = cursor.fetchone()[0]
        
        if total_equipamentos == 0:
            return None
        
        # Informações gerais
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT tipo) as tipos_diferentes,
                COUNT(DISTINCT usuario) as usuarios_diferentes,
                COUNT(DISTINCT setor) as setores_diferentes,
                MIN(data_recebimento) as primeira_data,
                MAX(data_recebimento) as ultima_data,
                SUM(CASE WHEN valor_locacao IS NOT NULL THEN valor_locacao ELSE 0 END) as investimento_total,
                AVG(valor_locacao) as valor_medio
            FROM equipamentos
            WHERE centro_custo = ?
        """, (centro_custo,))
        
        info_geral = cursor.fetchone()
        
        # Distribuição por status
        cursor.execute("""
            SELECT 
                status,
                COUNT(*) as quantidade,
                SUM(CASE WHEN valor_locacao IS NOT NULL THEN valor_locacao ELSE 0 END) as valor_total
            FROM equipamentos
            WHERE centro_custo = ?
            GROUP BY status
            ORDER BY quantidade DESC
        """, (centro_custo,))
        
        distribuicao_status = cursor.fetchall()
        
        # Distribuição por tipo
        cursor.execute("""
            SELECT 
                tipo,
                COUNT(*) as quantidade,
                SUM(CASE WHEN valor_locacao IS NOT NULL THEN valor_locacao ELSE 0 END) as valor_total,
                AVG(valor_locacao) as valor_medio
            FROM equipamentos
            WHERE centro_custo = ?
            AND tipo IS NOT NULL AND tipo != ''
            GROUP BY tipo
            ORDER BY quantidade DESC
            LIMIT 10
        """, (centro_custo,))
        
        distribuicao_tipo = cursor.fetchall()
        
        return {
            'total_equipamentos': total_equipamentos,
            'info_geral': info_geral,
            'distribuicao_status': distribuicao_status,
            'distribuicao_tipo': distribuicao_tipo
        }

def obter_equipamentos_mais_valiosos_centro_custo(
    centro_custo: str, 
    limite: int = 5
) -> List[sqlite3.Row]:
    """
    Retorna os equipamentos mais valiosos de um centro de custo
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                patrimonio,
                tipo,
                descritivo,
                usuario,
                local_atual,
                valor_locacao,
                status
            FROM equipamentos
            WHERE centro_custo = ?
            AND valor_locacao IS NOT NULL
            ORDER BY valor_locacao DESC
            LIMIT ?
        """, (centro_custo, limite))
        
        return cursor.fetchall()

def obter_equipamentos_recentes_centro_custo(
    centro_custo: str, 
    limite: int = 10
) -> List[sqlite3.Row]:
    """
    Retorna os equipamentos mais recentes de um centro de custo
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                patrimonio,
                tipo,
                descritivo,
                usuario,
                data_recebimento,
                status
            FROM equipamentos
            WHERE centro_custo = ?
            AND data_recebimento IS NOT NULL
            ORDER BY data_recebimento DESC
            LIMIT ?
        """, (centro_custo, limite))
        
        return cursor.fetchall()

# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def contar_equipamentos_centro_custo(centro_custo: str) -> int:
    """Retorna o total de equipamentos de um centro de custo"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM equipamentos WHERE centro_custo = ?", (centro_custo,))
        return cursor.fetchone()[0]

def verificar_centro_custo_existe(centro_custo: str) -> bool:
    """Verifica se um centro de custo existe"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM equipamentos WHERE centro_custo = ? LIMIT 1", (centro_custo,))
        return cursor.fetchone() is not None