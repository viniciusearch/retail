# src/routes.py - VERSÃO ATUALIZADA PARA NOVA ARQUITETURA
import sqlite3
import csv
import io
from datetime import datetime
from io import StringIO
from flask import Blueprint, jsonify, request, Response, session, redirect, url_for

# Importe as funções do models atualizado
from models import (
    get_db_connection,
    buscar_ativos,
    criar_ativo,
    atualizar_ativo,
    excluir_ativo,
    obter_atributos_ativo,
    atualizar_atributos_ativo,
    obter_valores_distintos_locais,
    obter_valores_distintos_ativos,
    buscar_contratos_locacao,
    vincular_ativo_contrato,
    desvincular_ativo_contrato,
    obter_contratos_do_ativo,
    criar_solicitacao,
    buscar_solicitacoes,
    contar_ativos,
    contar_ativos_por_status,
    verificar_credenciais  # Adicionar esta importação
)

api_bp = Blueprint('api', __name__)

# ============================================================================  
# ROTAS BÁSICAS DE ATIVOS
# ============================================================================  

@api_bp.route('/ativos', methods=['GET'])
def buscar_ativos_api():
    """
    Busca ativos com filtros avançados
    """
    filtros = {}
    
    # Filtros básicos
    campos_filtro = ['tipo_ativo', 'categoria', 'status', 'codigo_ativo', 'descricao', 
                    'ambiente_local', 'predio', 'setor_local', 'proprietario', 'usuario']
    
    for campo in campos_filtro:
        valor = request.args.get(campo)
        if valor:
            if ',' in valor:
                filtros[campo] = [v.strip() for v in valor.split(',') if v.strip()]
            else:
                filtros[campo] = valor
    
    resultados = buscar_ativos(filtros)
    return jsonify([dict(row) for row in resultados])

@api_bp.route('/ativos/<int:ativo_id>', methods=['GET'])
def obter_ativo(ativo_id):
    """
    Retorna um ativo específico com seus relacionamentos
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
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
                WHERE a.id = ?
            """, (ativo_id,))
            
            ativo = cursor.fetchone()
            
            if not ativo:
                return jsonify({"erro": "Ativo não encontrado"}), 404
            
            return jsonify(dict(ativo))
            
    except Exception as e:
        return jsonify({"erro": f"Erro ao buscar ativo: {str(e)}"}), 500

@api_bp.route('/ativos', methods=['POST'])
def criar_ativo_api():
    """
    Cria um novo ativo
    """
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Dados JSON obrigatórios"}), 400
    
    try:
        ativo_id = criar_ativo(dados)
        return jsonify({
            "mensagem": "Ativo cadastrado com sucesso",
            "id": ativo_id,
            "codigo_ativo": dados.get('codigo_ativo')
        }), 201
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except sqlite3.IntegrityError as e:
        if 'UNIQUE constraint failed' in str(e) and 'codigo_ativo' in str(e):
            return jsonify({"erro": "Código de ativo já existe"}), 409
        return jsonify({"erro": "Erro de integridade ao salvar"}), 400
    except Exception as e:
        return jsonify({"erro": f"Erro interno: {str(e)}"}), 500

@api_bp.route('/ativos/<int:ativo_id>', methods=['PATCH'])
def atualizar_ativo_api(ativo_id):
    """
    Atualiza os dados de um ativo
    """
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Corpo JSON vazio"}), 400

    if atualizar_ativo(ativo_id, dados):
        return jsonify({"mensagem": "Ativo atualizado"}), 200
    else:
        return jsonify({"erro": "Ativo não encontrado"}), 404

@api_bp.route('/ativos/<int:ativo_id>', methods=['DELETE'])
def deletar_ativo_api(ativo_id):
    """
    Exclui um ativo
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM ativos WHERE id = ?", (ativo_id,))
            if not cursor.fetchone():
                return jsonify({"erro": "Ativo não encontrado"}), 404
            
            cursor.execute("DELETE FROM ativos WHERE id = ?", (ativo_id,))
            conn.commit()
            
        return jsonify({"mensagem": f"Ativo {ativo_id} excluído com sucesso"}), 200
    except Exception as e:
        return jsonify({"erro": f"Erro ao excluir: {str(e)}"}), 500

# ============================================================================  
# ROTAS DE ATRIBUTOS DINÂMICOS
# ============================================================================  

@api_bp.route('/ativos/<int:ativo_id>/atributos', methods=['GET'])
def obter_atributos_ativo_api(ativo_id):
    """
    Retorna os atributos dinâmicos de um ativo
    """
    try:
        atributos = obter_atributos_ativo(ativo_id)
        return jsonify(atributos)
    except Exception as e:
        return jsonify({"erro": f"Erro ao buscar atributos: {str(e)}"}), 500

@api_bp.route('/ativos/<int:ativo_id>/atributos', methods=['PUT'])
def atualizar_atributos_ativo_api(ativo_id):
    """
    Atualiza os atributos dinâmicos de um ativo
    """
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Dados JSON obrigatórios"}), 400
    
    try:
        atualizar_atributos_ativo(ativo_id, dados)
        return jsonify({"mensagem": "Atributos atualizados com sucesso"}), 200
    except Exception as e:
        return jsonify({"erro": f"Erro ao atualizar atributos: {str(e)}"}), 500

# ============================================================================  
# ROTAS DE CONTRATOS DE LOCAÇÃO
# ============================================================================  

@api_bp.route('/contratos-locacao', methods=['GET'])
def buscar_contratos_locacao_api():
    """
    Busca contratos de locação com filtros
    """
    filtros = {}
    
    if request.args.get('numero_contrato'):
        filtros['numero_contrato'] = request.args.get('numero_contrato')
    if request.args.get('fornecedor'):
        filtros['fornecedor'] = request.args.get('fornecedor')
    if request.args.get('status'):
        filtros['status'] = request.args.get('status')
    
    resultados = buscar_contratos_locacao(filtros)
    return jsonify([dict(row) for row in resultados])

@api_bp.route('/contratos-locacao', methods=['POST'])
def criar_contrato_locacao_api():
    """
    Cria um novo contrato de locação
    """
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Dados JSON obrigatórios"}), 400
    
    campos_obrigatorios = ['numero_contrato', 'empresa_id', 'data_inicio', 'valor_total', 'periodo_cobranca']
    for campo in campos_obrigatorios:
        if not dados.get(campo):
            return jsonify({"erro": f"Campo obrigatório '{campo}' não fornecido"}), 400
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            campos = ['numero_contrato', 'empresa_id', 'data_inicio', 'data_fim', 
                     'valor_total', 'periodo_cobranca', 'duracao_meses', 'observacoes']
            valores = [dados.get(campo) for campo in campos]
            
            placeholders = ','.join(['?'] * len(campos))
            campos_str = ','.join(campos)
            
            cursor.execute(f"INSERT INTO contratos_locacao ({campos_str}) VALUES ({placeholders})", valores)
            contrato_id = cursor.lastrowid
            conn.commit()
            
        return jsonify({
            "mensagem": "Contrato de locação criado com sucesso",
            "id": contrato_id
        }), 201
        
    except sqlite3.IntegrityError as e:
        if 'UNIQUE constraint failed' in str(e) and 'numero_contrato' in str(e):
            return jsonify({"erro": "Número de contrato já existe"}), 409
        return jsonify({"erro": "Erro de integridade ao salvar"}), 400
    except Exception as e:
        return jsonify({"erro": f"Erro interno: {str(e)}"}), 500

@api_bp.route('/ativos/<int:ativo_id>/contratos/<int:contrato_id>', methods=['POST'])
def vincular_ativo_contrato_api(ativo_id, contrato_id):
    """
    Vincula um ativo a um contrato de locação
    """
    try:
        if vincular_ativo_contrato(ativo_id, contrato_id):
            return jsonify({"mensagem": "Ativo vinculado ao contrato com sucesso"}), 200
        else:
            return jsonify({"erro": "Falha ao vincular ativo ao contrato"}), 400
    except Exception as e:
        return jsonify({"erro": f"Erro ao vincular: {str(e)}"}), 500

@api_bp.route('/ativos/<int:ativo_id>/contratos/<int:contrato_id>', methods=['DELETE'])
def desvincular_ativo_contrato_api(ativo_id, contrato_id):
    """
    Remove o vínculo entre ativo e contrato
    """
    try:
        if desvincular_ativo_contrato(ativo_id, contrato_id):
            return jsonify({"mensagem": "Vínculo removido com sucesso"}), 200
        else:
            return jsonify({"erro": "Falha ao remover vínculo"}), 400
    except Exception as e:
        return jsonify({"erro": f"Erro ao remover vínculo: {str(e)}"}), 500

@api_bp.route('/ativos/<int:ativo_id>/contratos', methods=['GET'])
def obter_contratos_do_ativo_api(ativo_id):
    """
    Retorna todos os contratos vinculados a um ativo
    """
    try:
        contratos = obter_contratos_do_ativo(ativo_id)
        return jsonify([dict(row) for row in contratos])
    except Exception as e:
        return jsonify({"erro": f"Erro ao buscar contratos: {str(e)}"}), 500

# ============================================================================  
# ROTAS DE SOLICITAÇÕES
# ============================================================================  

@api_bp.route('/solicitacoes', methods=['GET'])
def buscar_solicitacoes_api():
    """
    Busca solicitações com filtros
    """
    filtros = {}
    
    if request.args.get('status'):
        filtros['status'] = request.args.get('status')
    if request.args.get('setor_solicitante_id'):
        filtros['setor_solicitante_id'] = request.args.get('setor_solicitante_id')
    if request.args.get('gestor_solicitante_id'):
        filtros['gestor_solicitante_id'] = request.args.get('gestor_solicitante_id')
    
    resultados = buscar_solicitacoes(filtros)
    return jsonify([dict(row) for row in resultados])

@api_bp.route('/solicitacoes', methods=['POST'])
def criar_solicitacao_api():
    """
    Cria uma nova solicitação
    """
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Dados JSON obrigatórios"}), 400
    
    try:
        solicitacao_id = criar_solicitacao(dados)
        return jsonify({
            "mensagem": "Solicitação criada com sucesso",
            "id": solicitacao_id
        }), 201
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception as e:
        return jsonify({"erro": f"Erro interno: {str(e)}"}), 500

# ============================================================================  
# ROTAS DE LISTAS CONTROLADAS (PARA DROPDOWNS)
# ============================================================================  

@api_bp.route('/locais', methods=['GET'])
def listar_locais():
    """
    Lista todos os locais para uso em dropdowns
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, nome, codigo, ambiente, predio, setor FROM locais ORDER BY nome")
            locais = cursor.fetchall()
            return jsonify([dict(row) for row in locais])
    except Exception as e:
        return jsonify({"erro": f"Erro ao buscar locais: {str(e)}"}), 500

@api_bp.route('/empresas', methods=['GET'])
def listar_empresas():
    """
    Lista todas as empresas para uso em dropdowns
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, nome, tipo FROM empresas ORDER BY nome")
            empresas = cursor.fetchall()
            return jsonify([dict(row) for row in empresas])
    except Exception as e:
        return jsonify({"erro": f"Erro ao buscar empresas: {str(e)}"}), 500

@api_bp.route('/usuarios', methods=['GET'])
def listar_usuarios():
    """
    Lista todos os usuários para uso em dropdowns
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, nome_completo, email FROM usuarios WHERE status = 'Ativo' ORDER BY nome_completo")
            usuarios = cursor.fetchall()
            return jsonify([dict(row) for row in usuarios])
    except Exception as e:
        return jsonify({"erro": f"Erro ao buscar usuários: {str(e)}"}), 500

@api_bp.route('/cargos', methods=['GET'])
def listar_cargos():
    """
    Lista todos os cargos para uso em dropdowns
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, nome FROM cargos ORDER BY nome")
            cargos = cursor.fetchall()
            return jsonify([dict(row) for row in cargos])
    except Exception as e:
        return jsonify({"erro": f"Erro ao buscar cargos: {str(e)}"}), 500

@api_bp.route('/setores', methods=['GET'])
def listar_setores():
    """
    Lista todos os setores para uso em dropdowns
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, nome FROM setores ORDER BY nome")
            setores = cursor.fetchall()
            return jsonify([dict(row) for row in setores])
    except Exception as e:
        return jsonify({"erro": f"Erro ao buscar setores: {str(e)}"}), 500

# ============================================================================  
# ROTAS DE FILTROS E LISTAS CONTROLADAS
# ============================================================================  

@api_bp.route('/filtros/locais', methods=['GET'])
def obter_filtros_locais():
    """
    Retorna valores distintos para filtros de locais
    """
    try:
        valores = obter_valores_distintos_locais()
        return jsonify(valores)
    except Exception as e:
        return jsonify({"erro": f"Erro ao buscar filtros de locais: {str(e)}"}), 500

@api_bp.route('/filtros/ativos', methods=['GET'])
def obter_filtros_ativos():
    """
    Retorna valores distintos para filtros de ativos
    """
    try:
        valores = obter_valores_distintos_ativos()
        return jsonify(valores)
    except Exception as e:
        return jsonify({"erro": f"Erro ao buscar filtros de ativos: {str(e)}"}), 500

# ============================================================================  
# ROTAS DE ESTATÍSTICAS E DASHBOARD
# ============================================================================  

@api_bp.route('/estatisticas/ativos', methods=['GET'])
def estatisticas_ativos():
    """
    Retorna estatísticas gerais dos ativos
    """
    try:
        total = contar_ativos()
        por_status = contar_ativos_por_status()
        
        return jsonify({
            'sucesso': True,
            'estatisticas': {
                'total_ativos': total,
                'por_status': [{'status': row[0], 'total': row[1]} for row in por_status]
            }
        })
    except Exception as e:
        return jsonify({"erro": f"Erro ao buscar estatísticas: {str(e)}"}), 500

# ============================================================================  
# ROTAS DE EXPORTAÇÃO
# ============================================================================  

@api_bp.route('/ativos/exportar', methods=['GET'])
def exportar_ativos():
    """
    Exporta ativos para CSV baseado em filtros
    """
    try:
        # Coleta filtros da query string
        filtros = {}
        campos_filtro = ['tipo_ativo', 'categoria', 'status', 'ambiente_local', 'predio', 'setor_local']
        for campo in campos_filtro:
            valor = request.args.get(campo, '').strip()
            if valor:
                filtros[campo] = valor
        
        # Busca ativos
        resultados = buscar_ativos(filtros)
        
        if not resultados:
            return jsonify({
                'sucesso': False,
                'erro': 'Nenhum ativo encontrado para exportar'
            }), 404
        
        # Cria CSV
        output = StringIO()
        writer = csv.writer(output)
        
        # Cabeçalho
        cabecalho = [
            'codigo_ativo', 'tipo_ativo', 'categoria', 'descricao', 'status',
            'proprietario_nome', 'usuario_nome', 'local_nome', 'projeto',
            'data_aquisicao', 'observacoes'
        ]
        writer.writerow(cabecalho)
        
        # Dados
        for row in resultados:
            linha = [
                row['codigo_ativo'],
                row['tipo_ativo'],
                row['categoria'],
                row['descricao'],
                row['status'],
                row['proprietario_nome'],
                row['usuario_nome'],
                row['local_nome'],
                row['projeto'],
                row['data_aquisicao'],
                row['observacoes']
            ]
            writer.writerow([str(value) if value is not None else '' for value in linha])
        
        # Configura resposta
        filename = f'ativos_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
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
            cursor.execute("SELECT COUNT(*) FROM ativos")
            total = cursor.fetchone()[0]
            
            cursor.execute("SELECT MAX(data_aquisicao) FROM ativos")
            ultima_atualizacao = cursor.fetchone()[0]
        
        return jsonify({
            'status': 'online',
            'mensagem': 'API operacional',
            'total_ativos': total,
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

# ============================================================================  
# ROTA DE UPLOAD EM LOTE
# ============================================================================  

@api_bp.route('/ativos/lote', methods=['POST'])
def processar_lote_ativos():
    """Processa upload em lote de ativos"""
    if 'file' not in request.files:
        return jsonify({"erro": "Nenhum arquivo enviado"}), 400
    
    arquivo = request.files['file']
    if arquivo.filename == '':
        return jsonify({"erro": "Arquivo sem nome"}), 400
    
    if not arquivo.filename.endswith('.csv'):
        return jsonify({"erro": "Apenas arquivos CSV são permitidos"}), 400
    
    try:
        stream = io.StringIO(arquivo.stream.read().decode("UTF-8-sig"))
        csv_input = csv.DictReader(stream)
        
        if 'codigo_ativo' not in csv_input.fieldnames:
            return jsonify({"erro": "Coluna 'codigo_ativo' obrigatória no CSV"}), 400
        
        resultados = {"sucesso": 0, "erros": [], "detalhes": []}
        
        for linha_num, linha in enumerate(csv_input, start=2):
            try:
                codigo_ativo = linha.get('codigo_ativo', '').strip()
                if not codigo_ativo:
                    resultados["erros"].append(f"Linha {linha_num}: Código de ativo obrigatório")
                    continue
                
                # Prepara dados para criação
                dados = {
                    'codigo_ativo': codigo_ativo,
                    'tipo_ativo': linha.get('tipo_ativo', '').strip(),
                    'categoria': linha.get('categoria', '').strip(),
                    'descricao': linha.get('descricao', '').strip() or None,
                    'status': linha.get('status', 'Em uso').strip(),
                    'projeto': linha.get('projeto', '').strip() or None,
                    'data_aquisicao': linha.get('data_aquisicao', '').strip() or None,
                    'observacoes': linha.get('observacoes', '').strip() or None
                }
                
                # Valida campos obrigatórios
                campos_obrigatorios = ['tipo_ativo', 'categoria', 'status']
                for campo in campos_obrigatorios:
                    if not dados[campo]:
                        raise ValueError(f"Campo obrigatório '{campo}' não informado")
                
                # Busca IDs para relacionamentos
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    
                    # Proprietário
                    proprietario_nome = linha.get('proprietario_nome', '').strip()
                    if proprietario_nome:
                        cursor.execute("SELECT id FROM empresas WHERE nome = ?", (proprietario_nome,))
                        proprietario = cursor.fetchone()
                        if proprietario:
                            dados['proprietario_id'] = proprietario[0]
                        else:
                            raise ValueError(f"Proprietário '{proprietario_nome}' não encontrado")
                    else:
                        # Usa empresa proprietária padrão
                        cursor.execute("SELECT id FROM empresas WHERE tipo = 'propria' LIMIT 1")
                        proprietario = cursor.fetchone()
                        dados['proprietario_id'] = proprietario[0] if proprietario else 1
                    
                    # Local
                    local_nome = linha.get('local_nome', '').strip()
                    if local_nome:
                        cursor.execute("SELECT id FROM locais WHERE nome = ?", (local_nome,))
                        local = cursor.fetchone()
                        if local:
                            dados['local_atual_id'] = local[0]
                        else:
                            raise ValueError(f"Local '{local_nome}' não encontrado")
                    else:
                        raise ValueError("Local obrigatório")
                    
                    # Usuário (opcional)
                    usuario_nome = linha.get('usuario_nome', '').strip()
                    if usuario_nome:
                        cursor.execute("SELECT id FROM usuarios WHERE nome_completo = ?", (usuario_nome,))
                        usuario = cursor.fetchone()
                        if usuario:
                            dados['usuario_atual_id'] = usuario[0]
                    
                    # Remove campos de texto que foram convertidos para IDs
                    dados.pop('proprietario_nome', None)
                    dados.pop('local_nome', None)
                    dados.pop('usuario_nome', None)
                
                # Cria o ativo
                ativo_id = criar_ativo(dados)
                resultados["sucesso"] += 1
                resultados["detalhes"].append(f"Criado: {codigo_ativo}")
                
                # Processa atributos específicos
                atributos = {}
                campos_atributos = ['numero_serie', 'host_name', 'teamviewer_id', 'imei', 'chip', 
                                  'chave_licenca', 'versao', 'data_expiracao', 'tipo_licenca', 
                                  'polegadas', 'resolucao', 'ip_impressora', 'toner_preto', 'toner_cores']
                
                for campo in campos_atributos:
                    valor = linha.get(campo, '').strip()
                    if valor:
                        atributos[campo] = valor
                
                if atributos:
                    atualizar_atributos_ativo(ativo_id, atributos)
                
            except Exception as e:
                resultados["erros"].append(f"Linha {linha_num} ({codigo_ativo}): {str(e)}")
        
        return jsonify({
            "mensagem": f"Upload concluído: {resultados['sucesso']} ativos criados com sucesso",
            "resultados": resultados
        }), 200
        
    except UnicodeDecodeError:
        return jsonify({"erro": "Erro ao ler arquivo CSV. Use codificação UTF-8"}), 400
    except Exception as e:
        return jsonify({"erro": f"Erro ao processar: {str(e)}"}), 500

# ============================================================================  
# ROTAS DE AUTENTICAÇÃO
# ============================================================================  

@api_bp.route('/login', methods=['POST'])
def login_api():
    """
    Autentica usuário e retorna informações do perfil
    """
    dados = request.get_json()
    if not dados or not dados.get('email') or not dados.get('password'):
        return jsonify({"erro": "Email e senha são obrigatórios"}), 400
    
    email = dados['email']
    password = dados['password']
    
    try:
        usuario = verificar_credenciais(email, password)
        if usuario:
            return jsonify({
                "sucesso": True,
                "usuario": {
                    "id": usuario['id'],
                    "nome": usuario['nome_completo'],
                    "email": usuario['email'],
                    "perfil": usuario['perfil']
                }
            }), 200
        else:
            return jsonify({"erro": "Email ou senha inválidos"}), 401
    except Exception as e:
        return jsonify({"erro": f"Erro na autenticação: {str(e)}"}), 500

@api_bp.route('/logout', methods=['POST'])
def logout_api():
    """
    Encerra sessão do usuário
    """
    return jsonify({"sucesso": True, "mensagem": "Logout realizado com sucesso"}), 200