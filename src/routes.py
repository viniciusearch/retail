# src/routes.py - VERSÃO REFATORADA
import sqlite3
import csv
import io
from datetime import datetime
from io import StringIO
from flask import Blueprint, jsonify, request, Response

# Importe as funções do models refatorado
from models import (
    get_db_connection,
    buscar_equipamentos,
    buscar_equipamentos_avancado,
    atualizar_equipamento,
    obter_valores_distintos,
    obter_estatisticas_gerais,
    listar_centros_custo,
    buscar_equipamentos_por_centro_custo,
    obter_resumo_centro_custo,
    obter_equipamentos_mais_valiosos_centro_custo,
    obter_equipamentos_recentes_centro_custo,
    contar_equipamentos_centro_custo,
    verificar_centro_custo_existe
)

api_bp = Blueprint('api', __name__)

# ============================================================================
# ROTAS BÁSICAS DE EQUIPAMENTOS
# ============================================================================

@api_bp.route('/equipamentos', methods=['GET'])
def buscar():
    """
    Busca equipamentos com filtros básicos (mantida para compatibilidade)
    """
    filtros = {
        "tipo": request.args.getlist("tipo"),
        "usuario": request.args.getlist("usuario"),
        "patrimonio": request.args.getlist("patrimonio"),
        "serie": request.args.getlist("serie"),
        "setor": request.args.getlist("setor"),
        "local": request.args.getlist("local"),
        "status": request.args.getlist("status")
    }
    
    # Remove listas vazias
    filtros = {k: [v for v in valores if v] for k, valores in filtros.items() if valores}
    
    resultados = buscar_equipamentos(filtros)
    return jsonify([dict(row) for row in resultados])

@api_bp.route('/equipamentos', methods=['POST'])
def criar_equipamento():
    dados = request.get_json()
    if not dados or not dados.get('patrimonio'):
        return jsonify({"erro": "Patrimônio é obrigatório"}), 400

    campos_permitidos = {
        "patrimonio", "tipo", "descritivo", "centro_custo", "numero_serie",
        "local_atual", "setor", "usuario", "cargo", "obra_projeto",
        "observacao", "data_recebimento", "data_devolucao", "valor_locacao",
        "status", "teamviewer_id", "host", "funcao"
    }

    # Filtra apenas os campos válidos
    dados_filtrados = {k: v for k, v in dados.items() if k in campos_permitidos}

    if not dados_filtrados.get('patrimonio'):
        return jsonify({"erro": "Patrimônio é obrigatório"}), 400

    # Define status padrão se não informado
    if 'status' not in dados_filtrados:
        dados_filtrados['status'] = 'Em uso'

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            colunas = ', '.join(dados_filtrados.keys())
            placeholders = ', '.join(['?'] * len(dados_filtrados))
            query = f"INSERT INTO equipamentos ({colunas}) VALUES ({placeholders})"
            cursor.execute(query, list(dados_filtrados.values()))
            conn.commit()
        return jsonify({
            "mensagem": "Equipamento cadastrado com sucesso",
            "patrimonio": dados_filtrados['patrimonio']
        }), 201
    except sqlite3.IntegrityError as e:
        if 'UNIQUE constraint failed' in str(e) and 'patrimonio' in str(e):
            return jsonify({"erro": "Patrimônio já existe"}), 409
        return jsonify({"erro": "Erro de integridade ao salvar"}), 400
    except Exception as e:
        return jsonify({"erro": f"Erro interno: {str(e)}"}), 500

@api_bp.route('/equipamentos/<patrimonio>', methods=['PATCH'])
def atualizar(patrimonio):
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Corpo JSON vazio"}), 400

    campos_permitidos = {
        "status", "numero_serie", "data_recebimento", "descritivo", 
        "data_devolucao", "valor_locacao", "local_atual", "usuario", 
        "teamviewer_id", "cargo", "host", "centro_custo", "setor", 
        "obra_projeto", "observacao", "tipo", "funcao"
    }
    
    dados = {k: v for k, v in dados.items() if k in campos_permitidos}

    if not dados:
        return jsonify({"erro": "Nenhum campo válido para atualizar"}), 400

    if atualizar_equipamento(patrimonio, dados):
        return jsonify({"mensagem": "Equipamento atualizado"}), 200
    else:
        return jsonify({"erro": "Equipamento não encontrado"}), 404

@api_bp.route('/equipamentos/<patrimonio>', methods=['DELETE'])
def deletar_equipamento(patrimonio):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT patrimonio FROM equipamentos WHERE patrimonio = ?", (patrimonio,))
            if not cursor.fetchone():
                return jsonify({"erro": "Equipamento não encontrado"}), 404
            
            cursor.execute("DELETE FROM equipamentos WHERE patrimonio = ?", (patrimonio,))
            conn.commit()
            
        return jsonify({"mensagem": f"Equipamento {patrimonio} excluído com sucesso"}), 200
    except Exception as e:
        return jsonify({"erro": f"Erro ao excluir: {str(e)}"}), 500

@api_bp.route('/equipamentos/lote', methods=['POST'])
def processar_lote():
    if 'file' not in request.files:
        return jsonify({"erro": "Nenhum arquivo enviado"}), 400
    
    arquivo = request.files['file']
    acao = request.form.get('acao', '').lower()
    
    if arquivo.filename == '':
        return jsonify({"erro": "Arquivo sem nome"}), 400
    
    if not arquivo.filename.endswith('.csv'):
        return jsonify({"erro": "Apenas arquivos CSV são permitidos"}), 400
    
    if acao not in ['create', 'update', 'delete']:
        return jsonify({"erro": "Ação inválida. Use: create, update ou delete"}), 400
    
    try:
        stream = io.StringIO(arquivo.stream.read().decode("UTF-8-sig"))
        csv_input = csv.DictReader(stream)
        
        if 'patrimonio' not in csv_input.fieldnames:
            return jsonify({"erro": "Coluna 'patrimonio' obrigatória no CSV"}), 400
        
        resultados = {"sucesso": 0, "erros": [], "detalhes": []}
        
        for linha_num, linha in enumerate(csv_input, start=2):
            try:
                patrimonio = linha.get('patrimonio', '').strip()
                if not patrimonio:
                    resultados["erros"].append(f"Linha {linha_num}: Patrimônio obrigatório")
                    continue
                
                if acao == 'create':
                    dados = {k: v.strip() for k, v in linha.items() if k != 'patrimonio' and v.strip()}
                    if not dados.get('tipo'):
                        raise ValueError("Tipo é obrigatório para criação")
                    dados['patrimonio'] = patrimonio
                    if 'status' not in dados:
                        dados['status'] = 'Em uso'
                    
                    with get_db_connection() as conn:
                        cursor = conn.cursor()
                        colunas = list(dados.keys())
                        valores = list(dados.values())
                        query = f"INSERT INTO equipamentos ({', '.join(colunas)}) VALUES ({', '.join(['?'] * len(valores))})"
                        cursor.execute(query, valores)
                        conn.commit()
                    resultados["sucesso"] += 1
                    resultados["detalhes"].append(f"Criado: {patrimonio}")
                    
                elif acao == 'update':
                    dados = {k: v.strip() for k, v in linha.items() if k != 'patrimonio' and v.strip()}
                    if not dados:
                        raise ValueError("Nenhum campo para atualizar")
                    if not atualizar_equipamento(patrimonio, dados):
                        raise ValueError("Equipamento não encontrado")
                    resultados["sucesso"] += 1
                    resultados["detalhes"].append(f"Atualizado: {patrimonio}")
                    
                elif acao == 'delete':
                    with get_db_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("SELECT patrimonio FROM equipamentos WHERE patrimonio = ?", (patrimonio,))
                        if not cursor.fetchone():
                            raise ValueError("Equipamento não encontrado")
                        cursor.execute("DELETE FROM equipamentos WHERE patrimonio = ?", (patrimonio,))
                        conn.commit()
                    resultados["sucesso"] += 1
                    resultados["detalhes"].append(f"Excluído: {patrimonio}")
            
            except Exception as e:
                resultados["erros"].append(f"Linha {linha_num} ({patrimonio}): {str(e)}")
        
        return jsonify({
            "mensagem": f"{acao.capitalize()} concluído: {resultados['sucesso']} operações bem-sucedidas",
            "resultados": resultados
        }), 200
        
    except UnicodeDecodeError:
        return jsonify({"erro": "Erro ao ler arquivo CSV. Use codificação UTF-8"}), 400
    except Exception as e:
        return jsonify({"erro": f"Erro ao processar: {str(e)}"}), 500

# ============================================================================
# ROTAS DE PESQUISA E FILTROS AVANÇADOS
# ============================================================================

@api_bp.route('/equipamentos/filtros/<campo>', methods=['GET'])
def obter_valores_filtro(campo):
    """
    Retorna valores distintos para um campo específico
    Ex: GET /api/equipamentos/filtros/tipo
    Ex: GET /api/equipamentos/filtros/centro_custo
    """
    try:
        valores = obter_valores_distintos(campo)
        
        return jsonify({
            'sucesso': True,
            'campo': campo,
            'valores': valores,
            'total': len(valores)
        })
        
    except Exception as e:
        return jsonify({
            'sucesso': False,
            'erro': f'Erro ao buscar valores para {campo}: {str(e)}'
        }), 500

@api_bp.route('/equipamentos/pesquisa', methods=['GET'])
def pesquisa_avancada():
    """
    Pesquisa avançada com múltiplos filtros
    Ex: GET /api/equipamentos/pesquisa?q=notebook&centro_custo=TI&status=Em uso
    """
    try:
        # Parâmetros de paginação
        pagina = int(request.args.get('pagina', 1))
        por_pagina = int(request.args.get('por_pagina', 50))
        ordenar_por = request.args.get('ordenar_por', 'patrimonio')
        ordenar_direcao = request.args.get('ordenar_direcao', 'ASC').upper()
        
        # Constrói filtros
        filtros = {}
        
        # Termo de busca geral
        termo = request.args.get('q', '').strip()
        if termo:
            filtros['q'] = termo
        
        # Campos de filtro
        campos_filtro = ['tipo', 'status', 'centro_custo', 'setor', 'local_atual', 
                        'usuario', 'patrimonio', 'serie', 'host', 'descritivo',
                        'funcao', 'cargo', 'obra_projeto']
        
        for campo in campos_filtro:
            valor = request.args.get(campo, '').strip()
            if valor:
                if ',' in valor:
                    filtros[campo] = [v.strip() for v in valor.split(',') if v.strip()]
                else:
                    filtros[campo] = valor
        
        # Filtros de data
        data_inicio = request.args.get('data_inicio', '').strip()
        data_fim = request.args.get('data_fim', '').strip()
        
        if data_inicio:
            filtros['data_recebimento_inicio'] = data_inicio
        if data_fim:
            filtros['data_recebimento_fim'] = data_fim
        
        # Filtros de valor
        valor_min = request.args.get('valor_min', '').strip()
        valor_max = request.args.get('valor_max', '').strip()
        
        if valor_min:
            try:
                filtros['valor_min'] = float(valor_min)
            except ValueError:
                pass
        
        if valor_max:
            try:
                filtros['valor_max'] = float(valor_max)
            except ValueError:
                pass
        
        # Executa busca
        resultados, total = buscar_equipamentos_avancado(
            filtros=filtros,
            pagina=pagina,
            por_pagina=por_pagina,
            ordenar_por=ordenar_por,
            ordenar_direcao=ordenar_direcao
        )
        
        total_paginas = (total + por_pagina - 1) // por_pagina if por_pagina > 0 else 0
        
        return jsonify({
            'sucesso': True,
            'resultados': [dict(row) for row in resultados],
            'paginacao': {
                'pagina': pagina,
                'por_pagina': por_pagina,
                'total': total,
                'total_paginas': total_paginas
            },
            'filtros_aplicados': filtros
        })
        
    except Exception as e:
        return jsonify({
            'sucesso': False,
            'erro': f'Erro na pesquisa: {str(e)}'
        }), 500

@api_bp.route('/equipamentos/estatisticas', methods=['GET'])
def estatisticas():
    """
    Retorna estatísticas gerais dos equipamentos
    Ex: GET /api/equipamentos/estatisticas
    """
    try:
        stats = obter_estatisticas_gerais()
        
        # Calcula total geral
        total_geral = sum(row[1] for row in stats['por_status'])
        
        return jsonify({
            'sucesso': True,
            'estatisticas': {
                'por_status': [{'status': row[0], 'total': row[1]} for row in stats['por_status']],
                'por_tipo': [{'tipo': row[0], 'total': row[1]} for row in stats['por_tipo']],
                'por_centro_custo': [{'centro_custo': row[0], 'total': row[1]} for row in stats['por_centro_custo']],
                'sem_centro_custo': stats['sem_centro_custo'],
                'total_geral': total_geral
            }
        })
        
    except Exception as e:
        return jsonify({
            'sucesso': False,
            'erro': f'Erro ao buscar estatísticas: {str(e)}'
        }), 500

# ============================================================================
# ROTAS ESPECÍFICAS PARA CENTRO DE CUSTO
# ============================================================================

@api_bp.route('/centros-custo', methods=['GET'])
def listar_centros_custo():
    """
    Lista todos os centros de custo com estatísticas
    Ex: GET /api/centros-custo
    """
    try:
        centros = listar_centros_custo()
        
        return jsonify({
            'sucesso': True,
            'centros_custo': [
                {
                    'centro_custo': row[0],
                    'total_equipamentos': row[1],
                    'em_uso': row[2],
                    'disponivel': row[3],
                    'manutencao': row[4],
                    'baixado': row[5],
                    'valor_total': float(row[6]) if row[6] else 0
                } for row in centros
            ],
            'total_centros': len(centros),
            'total_equipamentos_com_cc': sum(row[1] for row in centros)
        })
        
    except Exception as e:
        return jsonify({
            'sucesso': False,
            'erro': f'Erro ao listar centros de custo: {str(e)}'
        }), 500

@api_bp.route('/centros-custo/<centro_custo>', methods=['GET'])
def detalhar_centro_custo(centro_custo):
    """
    Detalhes de um centro de custo específico
    Ex: GET /api/centros-custo/A2WORKS
    """
    try:
        resumo = obter_resumo_centro_custo(centro_custo)
        
        if not resumo:
            return jsonify({
                'sucesso': False,
                'erro': f'Centro de custo "{centro_custo}" não encontrado'
            }), 404
        
        info_geral = resumo['info_geral']
        
        return jsonify({
            'sucesso': True,
            'centro_custo': centro_custo,
            'total_equipamentos': resumo['total_equipamentos'],
            'informacoes': {
                'tipos_diferentes': info_geral[0],
                'usuarios_diferentes': info_geral[1],
                'setores_diferentes': info_geral[2],
                'primeira_data': info_geral[3],
                'ultima_data': info_geral[4],
                'investimento_total': float(info_geral[5]) if info_geral[5] else 0,
                'valor_medio': float(info_geral[6]) if info_geral[6] else 0
            },
            'distribuicao_status': [
                {'status': row[0], 'quantidade': row[1], 'valor_total': float(row[2]) if row[2] else 0}
                for row in resumo['distribuicao_status']
            ],
            'distribuicao_tipo': [
                {'tipo': row[0], 'quantidade': row[1], 'valor_total': float(row[2]) if row[2] else 0, 'valor_medio': float(row[3]) if row[3] else 0}
                for row in resumo['distribuicao_tipo']
            ]
        })
        
    except Exception as e:
        return jsonify({
            'sucesso': False,
            'erro': f'Erro ao detalhar centro de custo: {str(e)}'
        }), 500

@api_bp.route('/centros-custo/<centro_custo>/equipamentos', methods=['GET'])
def listar_equipamentos_por_centro_custo(centro_custo):
    """
    Lista equipamentos de um centro de custo com filtros
    Ex: GET /api/centros-custo/A2WORKS/equipamentos?status=Em uso&pagina=1
    """
    try:
        # Parâmetros de filtro
        filtros = {}
        
        campos_filtro = ['status', 'tipo', 'usuario', 'local', 'setor']
        for campo in campos_filtro:
            valor = request.args.get(campo, '').strip()
            if valor:
                filtros[campo] = valor
        
        # Parâmetros de paginação e ordenação
        pagina = int(request.args.get('pagina', 1))
        por_pagina = int(request.args.get('por_pagina', 100))
        ordenar_por = request.args.get('ordenar_por', 'patrimonio')
        ordenar_direcao = request.args.get('ordenar_direcao', 'ASC')
        
        filtros['ordenar_por'] = ordenar_por
        filtros['ordenar_direcao'] = ordenar_direcao
        
        # Verifica se o centro de custo existe
        if not verificar_centro_custo_existe(centro_custo):
            return jsonify({
                'sucesso': False,
                'erro': f'Centro de custo "{centro_custo}" não encontrado'
            }), 404
        
        # Busca equipamentos
        resultados, total = buscar_equipamentos_por_centro_custo(
            centro_custo=centro_custo,
            filtros=filtros,
            pagina=pagina,
            por_pagina=por_pagina
        )
        
        total_paginas = (total + por_pagina - 1) // por_pagina if por_pagina > 0 else 0
        
        return jsonify({
            'sucesso': True,
            'centro_custo': centro_custo,
            'equipamentos': [dict(row) for row in resultados],
            'paginacao': {
                'pagina': pagina,
                'por_pagina': por_pagina,
                'total': total,
                'total_paginas': total_paginas
            },
            'filtros_aplicados': {
                k: v for k, v in filtros.items() 
                if k not in ['ordenar_por', 'ordenar_direcao']
            },
            'ordenacao': {
                'campo': ordenar_por,
                'direcao': ordenar_direcao
            }
        })
        
    except Exception as e:
        return jsonify({
            'sucesso': False,
            'erro': f'Erro ao listar equipamentos: {str(e)}'
        }), 500

@api_bp.route('/centros-custo/<centro_custo>/equipamentos/valiosos', methods=['GET'])
def equipamentos_valiosos_centro_custo(centro_custo):
    """
    Retorna os equipamentos mais valiosos de um centro de custo
    Ex: GET /api/centros-custo/A2WORKS/equipamentos/valiosos?limite=5
    """
    try:
        limite = int(request.args.get('limite', 5))
        
        # Verifica se o centro de custo existe
        if not verificar_centro_custo_existe(centro_custo):
            return jsonify({
                'sucesso': False,
                'erro': f'Centro de custo "{centro_custo}" não encontrado'
            }), 404
        
        equipamentos = obter_equipamentos_mais_valiosos_centro_custo(centro_custo, limite)
        
        valor_total = sum(float(row[5] or 0) for row in equipamentos)
        
        return jsonify({
            'sucesso': True,
            'centro_custo': centro_custo,
            'equipamentos_mais_valiosos': [
                {
                    'patrimonio': row[0],
                    'tipo': row[1],
                    'descritivo': row[2],
                    'usuario': row[3],
                    'local_atual': row[4],
                    'valor_locacao': float(row[5]) if row[5] else 0,
                    'status': row[6]
                } for row in equipamentos
            ],
            'total': len(equipamentos),
            'valor_total': valor_total
        })
        
    except Exception as e:
        return jsonify({
            'sucesso': False,
            'erro': f'Erro ao buscar equipamentos valiosos: {str(e)}'
        }), 500

@api_bp.route('/centros-custo/<centro_custo>/equipamentos/recentes', methods=['GET'])
def equipamentos_recentes_centro_custo(centro_custo):
    """
    Retorna os equipamentos mais recentes de um centro de custo
    Ex: GET /api/centros-custo/A2WORKS/equipamentos/recentes
    """
    try:
        limite = int(request.args.get('limite', 10))
        
        # Verifica se o centro de custo existe
        if not verificar_centro_custo_existe(centro_custo):
            return jsonify({
                'sucesso': False,
                'erro': f'Centro de custo "{centro_custo}" não encontrado'
            }), 404
        
        equipamentos = obter_equipamentos_recentes_centro_custo(centro_custo, limite)
        
        return jsonify({
            'sucesso': True,
            'centro_custo': centro_custo,
            'equipamentos_recentes': [
                {
                    'patrimonio': row[0],
                    'tipo': row[1],
                    'descritivo': row[2],
                    'usuario': row[3],
                    'data_recebimento': row[4],
                    'status': row[5]
                } for row in equipamentos
            ],
            'total': len(equipamentos)
        })
        
    except Exception as e:
        return jsonify({
            'sucesso': False,
            'erro': f'Erro ao buscar equipamentos recentes: {str(e)}'
        }), 500

# ============================================================================
# ROTAS DE EXPORTAÇÃO
# ============================================================================

@api_bp.route('/equipamentos/exportar', methods=['GET'])
def exportar_equipamentos():
    """
    Exporta equipamentos para CSV baseado em filtros
    Ex: GET /api/equipamentos/exportar?centro_custo=TI&status=Em uso
    """
    try:
        # Coleta filtros da query string
        filtros = {}
        
        campos_filtro = ['tipo', 'status', 'centro_custo', 'setor', 'local_atual', 'usuario']
        for campo in campos_filtro:
            valor = request.args.get(campo, '').strip()
            if valor:
                filtros[campo] = valor
        
        # Busca todos os equipamentos (sem paginação)
        resultados, _ = buscar_equipamentos_avancado(filtros=filtros, por_pagina=0)
        
        if not resultados:
            return jsonify({
                'sucesso': False,
                'erro': 'Nenhum equipamento encontrado para exportar'
            }), 404
        
        # Cria CSV
        output = StringIO()
        writer = csv.writer(output)
        
        # Cabeçalho
        if resultados:
            cabecalho = resultados[0].keys()
            writer.writerow(cabecalho)
            
            # Dados
            for row in resultados:
                writer.writerow([str(value) if value is not None else '' for value in row])
        
        # Configura resposta
        filename = f'equipamentos_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename={filename}',
                'Content-Type': 'text/csv; charset=utf-8'
            }
        )
        
    except Exception as e:
        return jsonify({
            'sucesso': False,
            'erro': f'Erro ao exportar: {str(e)}'
        }), 500

@api_bp.route('/centros-custo/<centro_custo>/equipamentos/exportar', methods=['GET'])
def exportar_equipamentos_centro_custo(centro_custo):
    """
    Exporta equipamentos de um centro de custo para CSV
    Ex: GET /api/centros-custo/A2WORKS/equipamentos/exportar
    """
    try:
        # Verifica se o centro de custo existe
        if not verificar_centro_custo_existe(centro_custo):
            return jsonify({
                'sucesso': False,
                'erro': f'Centro de custo "{centro_custo}" não encontrado'
            }), 404
        
        # Busca todos os equipamentos do centro de custo
        resultados, total = buscar_equipamentos_por_centro_custo(
            centro_custo=centro_custo,
            por_pagina=0  # 0 = sem paginação
        )
        
        if total == 0:
            return jsonify({
                'sucesso': False,
                'erro': f'Nenhum equipamento encontrado para o centro de custo "{centro_custo}"'
            }), 404
        
        # Cria CSV
        output = StringIO()
        writer = csv.writer(output)
        
        # Cabeçalho
        if resultados:
            cabecalho = resultados[0].keys()
            writer.writerow(cabecalho)
            
            # Dados
            for row in resultados:
                writer.writerow([str(value) if value is not None else '' for value in row])
        
        # Configura resposta
        filename = f'equipamentos_{centro_custo}_{datetime.now().strftime("%Y%m%d")}.csv'
        
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename={filename}',
                'Content-Type': 'text/csv; charset=utf-8'
            }
        )
        
    except Exception as e:
        return jsonify({
            'sucesso': False,
            'erro': f'Erro ao exportar equipamentos: {str(e)}'
        }), 500

# ============================================================================
# ROTAS DE RELATÓRIOS E DASHBOARD
# ============================================================================

@api_bp.route('/centros-custo/<centro_custo>/relatorio', methods=['GET'])
def relatorio_centro_custo(centro_custo):
    """
    Gera relatório completo de um centro de custo
    Ex: GET /api/centros-custo/A2WORKS/relatorio
    """
    try:
        # Verifica se o centro de custo existe
        resumo = obter_resumo_centro_custo(centro_custo)
        
        if not resumo:
            return jsonify({
                'sucesso': False,
                'erro': f'Centro de custo "{centro_custo}" não encontrado'
            }), 404
        
        total_equipamentos = resumo['total_equipamentos']
        info_geral = resumo['info_geral']
        
        # Obtém equipamentos valiosos
        equipamentos_valiosos = obter_equipamentos_mais_valiosos_centro_custo(centro_custo, 10)
        
        # Obtém equipamentos recentes
        equipamentos_recentes = obter_equipamentos_recentes_centro_custo(centro_custo, 10)
        
        # Obtém distribuição por mês (últimos 12 meses)
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    strftime('%Y-%m', data_recebimento) as mes,
                    COUNT(*) as quantidade,
                    SUM(CASE WHEN valor_locacao IS NOT NULL THEN valor_locacao ELSE 0 END) as valor_total
                FROM equipamentos
                WHERE centro_custo = ?
                AND data_recebimento IS NOT NULL
                AND data_recebimento >= date('now', '-12 months')
                GROUP BY strftime('%Y-%m', data_recebimento)
                ORDER BY mes DESC
            """, (centro_custo,))
            
            evolucao_mensal = cursor.fetchall()
        
        return jsonify({
            'sucesso': True,
            'relatorio': {
                'centro_custo': centro_custo,
                'data_geracao': datetime.now().isoformat(),
                'resumo_geral': {
                    'total_equipamentos': total_equipamentos,
                    'tipos_diferentes': info_geral[0],
                    'usuarios_diferentes': info_geral[1],
                    'setores_diferentes': info_geral[2],
                    'investimento_total': float(info_geral[5]) if info_geral[5] else 0,
                    'valor_medio': float(info_geral[6]) if info_geral[6] else 0,
                    'periodo': f"{info_geral[3]} a {info_geral[4]}" if info_geral[3] and info_geral[4] else "N/A"
                },
                'distribuicao_status': [
                    {
                        'status': row[0],
                        'quantidade': row[1],
                        'percentual': round((row[1] / total_equipamentos * 100), 1) if total_equipamentos > 0 else 0,
                        'valor_total': float(row[2]) if row[2] else 0
                    } for row in resumo['distribuicao_status']
                ],
                'distribuicao_tipo': [
                    {
                        'tipo': row[0],
                        'quantidade': row[1],
                        'percentual': round((row[1] / total_equipamentos * 100), 1) if total_equipamentos > 0 else 0,
                        'valor_total': float(row[2]) if row[2] else 0,
                        'valor_medio': float(row[3]) if row[3] else 0
                    } for row in resumo['distribuicao_tipo']
                ],
                'equipamentos_mais_valiosos': [
                    {
                        'patrimonio': row[0],
                        'tipo': row[1],
                        'descritivo': row[2],
                        'valor_locacao': float(row[5]) if row[5] else 0,
                        'usuario': row[3],
                        'status': row[6]
                    } for row in equipamentos_valiosos
                ],
                'equipamentos_recentes': [
                    {
                        'patrimonio': row[0],
                        'tipo': row[1],
                        'descritivo': row[2],
                        'data_recebimento': row[4],
                        'usuario': row[3]
                    } for row in equipamentos_recentes
                ],
                'evolucao_mensal': [
                    {
                        'mes': row[0],
                        'quantidade': row[1],
                        'valor_total': float(row[2]) if row[2] else 0
                    } for row in evolucao_mensal
                ]
            }
        })
        
    except Exception as e:
        return jsonify({
            'sucesso': False,
            'erro': f'Erro ao gerar relatório: {str(e)}'
        }), 500

@api_bp.route('/dashboard/centros-custo', methods=['GET'])
def dashboard_centros_custo():
    """
    Dashboard com resumo dos centros de custo
    Ex: GET /api/dashboard/centros-custo
    """
    try:
        centros = listar_centros_custo()
        
        # Calcula totais
        total_centros = len(centros)
        total_equipamentos_com_cc = sum(row[1] for row in centros)
        valor_total_investido = sum(float(row[6] or 0) for row in centros)
        
        # Top 5 centros com mais equipamentos
        top_5_centros = [
            {
                'centro_custo': row[0],
                'total_equipamentos': row[1],
                'em_uso': row[2],
                'valor_total': float(row[6]) if row[6] else 0
            }
            for row in centros[:5]
        ]
        
        # Distribuição por status (consolidado)
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    status,
                    COUNT(*) as total,
                    SUM(CASE WHEN valor_locacao IS NOT NULL THEN valor_locacao ELSE 0 END) as valor_total
                FROM equipamentos
                WHERE centro_custo IS NOT NULL AND centro_custo != ''
                GROUP BY status
                ORDER BY total DESC
            """)
            
            distribuicao_status = cursor.fetchall()
        
        return jsonify({
            'sucesso': True,
            'dashboard': {
                'resumo_geral': {
                    'total_centros_custo': total_centros,
                    'total_equipamentos_com_cc': total_equipamentos_com_cc,
                    'valor_total_investido': valor_total_investido,
                    'centro_medio_equipamentos': round(total_equipamentos_com_cc / total_centros, 1) if total_centros > 0 else 0
                },
                'top_5_centros': top_5_centros,
                'distribuicao_status': [
                    {
                        'status': row[0],
                        'total': row[1],
                        'valor_total': float(row[2]) if row[2] else 0
                    }
                    for row in distribuicao_status
                ]
            }
        })
        
    except Exception as e:
        return jsonify({
            'sucesso': False,
            'erro': f'Erro ao gerar dashboard: {str(e)}'
        }), 500

# ============================================================================
# ROTAS DE SAÚDE DO SISTEMA
# ============================================================================

@api_bp.route('/health', methods=['GET'])
def health_check():
    """
    Verifica status da API
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM equipamentos")
            total = cursor.fetchone()[0]
            
            cursor.execute("SELECT MAX(data_recebimento) FROM equipamentos")
            ultima_atualizacao = cursor.fetchone()[0]
        
        return jsonify({
            'status': 'online',
            'mensagem': 'API operacional',
            'total_equipamentos': total,
            'ultima_atualizacao': ultima_atualizacao,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'mensagem': 'Erro na API',
            'erro': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500