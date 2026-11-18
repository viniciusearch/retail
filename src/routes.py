# src/routes.py - VERSÃO FINAL COMPLETA
import sqlite3
import csv
import io
from datetime import datetime
from io import StringIO
from flask import Blueprint, jsonify, request, Response

from models import (
    get_db_connection,
    # Ativos
    buscar_ativos, criar_ativo, atualizar_ativo, excluir_ativo,
    obter_atributos_ativo, atualizar_atributos_ativo,
    contar_ativos, contar_ativos_por_status,
    # Empresas
    buscar_empresas, obter_empresa, criar_empresa, atualizar_empresa, excluir_empresa,
    # Setores
    buscar_setores, obter_setor, criar_setor, atualizar_setor, excluir_setor,
    # Locais
    buscar_locais, obter_local, criar_local, atualizar_local, excluir_local,
    # Usuários
    buscar_usuarios, obter_usuario, criar_usuario, atualizar_usuario, excluir_usuario,
    # Contratos e Solicitações
    buscar_contratos_locacao, vincular_ativo_contrato, desvincular_ativo_contrato, obter_contratos_do_ativo,
    criar_solicitacao, buscar_solicitacoes,
    # Autenticação
    verificar_credenciais
)

api_bp = Blueprint('api', __name__)

# ============================================================================
# 1. ATIVOS
# ============================================================================

@api_bp.route('/ativos', methods=['GET'])
def buscar_ativos_api():
    filtros = {}
    campos_filtro = ['tipo_ativo', 'categoria', 'status', 'codigo_ativo', 'descricao',
                    'ambiente_local', 'predio', 'setor_local', 'proprietario', 'usuario']
    for campo in campos_filtro:
        valor = request.args.get(campo)
        if valor:
            if ',' in valor:
                filtros[campo] = [v.strip() for v in valor.split(',') if v.strip()]
            else:
                filtros[campo] = valor
    return jsonify([dict(row) for row in buscar_ativos(filtros)])


@api_bp.route('/ativos/<int:ativo_id>', methods=['GET'])
def obter_ativo(ativo_id):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT a.*, e.nome as proprietario_nome, u.nome_completo as usuario_nome,
                       l.nome as local_nome, l.ambiente as local_ambiente, l.predio as local_predio, l.setor as local_setor
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
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Dados JSON obrigatórios"}), 400
    try:
        ativo_id = criar_ativo(dados)
        return jsonify({"mensagem": "Ativo cadastrado com sucesso", "id": ativo_id, "codigo_ativo": dados.get('codigo_ativo')}), 201
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
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Corpo JSON vazio"}), 400
    try:
        if atualizar_ativo(ativo_id, dados):
            return jsonify({"mensagem": "Ativo atualizado"}), 200
        return jsonify({"erro": "Ativo não encontrado"}), 404
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception as e:
        return jsonify({"erro": f"Erro interno: {str(e)}"}), 500


@api_bp.route('/ativos/<int:ativo_id>', methods=['DELETE'])
def deletar_ativo_api(ativo_id):
    try:
        if excluir_ativo(ativo_id):
            return jsonify({"mensagem": f"Ativo {ativo_id} excluído com sucesso"}), 200
        return jsonify({"erro": "Ativo não encontrado"}), 404
    except Exception as e:
        return jsonify({"erro": f"Erro ao excluir: {str(e)}"}), 500


@api_bp.route('/ativos/<int:ativo_id>/atributos', methods=['GET'])
def obter_atributos_ativo_api(ativo_id):
    try:
        return jsonify(obter_atributos_ativo(ativo_id))
    except Exception as e:
        return jsonify({"erro": f"Erro ao buscar atributos: {str(e)}"}), 500


@api_bp.route('/ativos/<int:ativo_id>/atributos', methods=['PUT'])
def atualizar_atributos_ativo_api(ativo_id):
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Dados JSON obrigatórios"}), 400
    try:
        atualizar_atributos_ativo(ativo_id, dados)
        return jsonify({"mensagem": "Atributos atualizados com sucesso"}), 200
    except Exception as e:
        return jsonify({"erro": f"Erro ao atualizar atributos: {str(e)}"}), 500


# ============================================================================
# 2. EMPRESAS
# ============================================================================

@api_bp.route('/empresas', methods=['GET'])
def listar_empresas():
    try:
        if request.args.get('dropdown') == 'true':
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, nome, tipo FROM empresas ORDER BY nome")
                return jsonify([dict(row) for row in cursor.fetchall()])
        filtros = {}
        if request.args.get('nome'):
            filtros['nome'] = request.args.get('nome')
        if request.args.get('tipo'):
            filtros['tipo'] = request.args.get('tipo')
        return jsonify([dict(row) for row in buscar_empresas(filtros)])
    except Exception as e:
        return jsonify({"erro": f"Erro ao buscar empresas: {str(e)}"}), 500


@api_bp.route('/empresas/<int:empresa_id>', methods=['GET'])
def obter_empresa_api(empresa_id):
    try:
        resultado = obter_empresa(empresa_id)
        return jsonify(resultado) if resultado else (jsonify({"erro": "Empresa não encontrada"}), 404)
    except Exception as e:
        return jsonify({"erro": f"Erro ao buscar empresa: {str(e)}"}), 500


@api_bp.route('/empresas', methods=['POST'])
def criar_empresa_api():
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Dados JSON obrigatórios"}), 400
    try:
        empresa_id = criar_empresa(dados)
        return jsonify({"mensagem": "Empresa criada com sucesso", "id": empresa_id, "nome": dados.get('nome')}), 201
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except sqlite3.IntegrityError:
        return jsonify({"erro": "Já existe uma empresa com este nome"}), 409
    except Exception as e:
        return jsonify({"erro": f"Erro interno: {str(e)}"}), 500


@api_bp.route('/empresas/<int:empresa_id>', methods=['PUT'])
def atualizar_empresa_api(empresa_id):
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Corpo JSON vazio"}), 400
    try:
        if atualizar_empresa(empresa_id, dados):
            return jsonify({"mensagem": "Empresa atualizada"}), 200
        return jsonify({"erro": "Empresa não encontrada"}), 404
    except sqlite3.IntegrityError:
        return jsonify({"erro": "Nome de empresa já existe"}), 409
    except Exception as e:
        return jsonify({"erro": f"Erro interno: {str(e)}"}), 500


@api_bp.route('/empresas/<int:empresa_id>', methods=['DELETE'])
def excluir_empresa_api(empresa_id):
    try:
        if excluir_empresa(empresa_id):
            return jsonify({"mensagem": "Empresa excluída"}), 200
        return jsonify({"erro": "Empresa não encontrada"}), 404
    except ValueError as e:
        return jsonify({"erro": str(e)}), 409
    except Exception as e:
        return jsonify({"erro": f"Erro ao excluir: {str(e)}"}), 500


# ============================================================================
# 3. SETORES
# ============================================================================

@api_bp.route('/setores', methods=['GET'])
def listar_setores():
    try:
        if request.args.get('dropdown') == 'true':
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, nome, sigla FROM setores WHERE ativo = 1 ORDER BY nome")
                return jsonify([dict(row) for row in cursor.fetchall()])
        filtros = {'nome': request.args.get('nome')} if request.args.get('nome') else {}
        return jsonify([dict(row) for row in buscar_setores(filtros)])
    except Exception as e:
        return jsonify({"erro": f"Erro ao buscar setores: {str(e)}"}), 500


@api_bp.route('/setores/<int:setor_id>', methods=['GET'])
def obter_setor_api(setor_id):
    try:
        resultado = obter_setor(setor_id)
        return jsonify(resultado) if resultado else (jsonify({"erro": "Setor não encontrado"}), 404)
    except Exception as e:
        return jsonify({"erro": f"Erro ao buscar setor: {str(e)}"}), 500


@api_bp.route('/setores', methods=['POST'])
def criar_setor_api():
    dados = request.get_json()
    if not dados or not dados.get('nome'):
        return jsonify({"erro": "Campo 'nome' é obrigatório"}), 400
    try:
        return jsonify({"mensagem": "Setor criado com sucesso", "id": criar_setor(dados)}), 201
    except sqlite3.IntegrityError:
        return jsonify({"erro": "Nome ou sigla de setor já existe"}), 409
    except Exception as e:
        return jsonify({"erro": f"Erro interno: {str(e)}"}), 500


@api_bp.route('/setores/<int:setor_id>', methods=['PUT'])
def atualizar_setor_api(setor_id):
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Corpo JSON vazio"}), 400
    try:
        if atualizar_setor(setor_id, dados):
            return jsonify({"mensagem": "Setor atualizado"}), 200
        return jsonify({"erro": "Setor não encontrado"}), 404
    except sqlite3.IntegrityError:
        return jsonify({"erro": "Nome ou sigla de setor já existe"}), 409
    except Exception as e:
        return jsonify({"erro": f"Erro interno: {str(e)}"}), 500


@api_bp.route('/setores/<int:setor_id>', methods=['DELETE'])
def excluir_setor_api(setor_id):
    try:
        if excluir_setor(setor_id):
            return jsonify({"mensagem": "Setor excluído"}), 200
        return jsonify({"erro": "Setor não encontrado"}), 404
    except ValueError as e:
        return jsonify({"erro": str(e)}), 409
    except Exception as e:
        return jsonify({"erro": f"Erro ao excluir: {str(e)}"}), 500


# ============================================================================
# 4. LOCAIS
# ============================================================================

@api_bp.route('/locais', methods=['GET'])
def listar_locais():
    try:
        if request.args.get('dropdown') == 'true':
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, nome, codigo, ambiente, predio, setor FROM locais WHERE ativo = 1 ORDER BY nome")
                return jsonify([dict(row) for row in cursor.fetchall()])
        filtros = {k: request.args.get(k) for k in ['nome', 'codigo', 'ambiente', 'predio', 'setor'] if request.args.get(k)}
        return jsonify([dict(row) for row in buscar_locais(filtros)])
    except Exception as e:
        return jsonify({"erro": f"Erro ao buscar locais: {str(e)}"}), 500


@api_bp.route('/locais/<int:local_id>', methods=['GET'])
def obter_local_api(local_id):
    try:
        resultado = obter_local(local_id)
        return jsonify(resultado) if resultado else (jsonify({"erro": "Local não encontrado"}), 404)
    except Exception as e:
        return jsonify({"erro": f"Erro ao buscar local: {str(e)}"}), 500


@api_bp.route('/locais', methods=['POST'])
def criar_local_api():
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Dados JSON obrigatórios"}), 400
    for campo in ['nome', 'codigo', 'ambiente', 'setor']:
        if not dados.get(campo):
            return jsonify({"erro": f"Campo '{campo}' é obrigatório"}), 400
    try:
        return jsonify({"mensagem": "Local criado com sucesso", "id": criar_local(dados)}), 201
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except sqlite3.IntegrityError:
        return jsonify({"erro": "Código ou Nome de local já existe"}), 409
    except Exception as e:
        return jsonify({"erro": f"Erro interno: {str(e)}"}), 500


@api_bp.route('/locais/<int:local_id>', methods=['PUT'])
def atualizar_local_api(local_id):
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Corpo JSON vazio"}), 400
    try:
        if atualizar_local(local_id, dados):
            return jsonify({"mensagem": "Local atualizado"}), 200
        return jsonify({"erro": "Local não encontrado"}), 404
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except sqlite3.IntegrityError:
        return jsonify({"erro": "Código ou Nome de local já existe"}), 409
    except Exception as e:
        return jsonify({"erro": f"Erro interno: {str(e)}"}), 500


@api_bp.route('/locais/<int:local_id>', methods=['DELETE'])
def excluir_local_api(local_id):
    try:
        if excluir_local(local_id):
            return jsonify({"mensagem": "Local excluído"}), 200
        return jsonify({"erro": "Local não encontrado"}), 404
    except ValueError as e:
        return jsonify({"erro": str(e)}), 409
    except Exception as e:
        return jsonify({"erro": f"Erro ao excluir: {str(e)}"}), 500


# ============================================================================
# 5. USUÁRIOS
# ============================================================================

@api_bp.route('/usuarios', methods=['GET'])
def listar_usuarios():
    try:
        if request.args.get('dropdown') == 'true':
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, nome_completo FROM usuarios WHERE status = 'Ativo' ORDER BY nome_completo")
                return jsonify([dict(row) for row in cursor.fetchall()])
        filtros = {}
        if request.args.get('nome'):
            filtros['nome'] = request.args.get('nome')
        if request.args.get('status'):
            filtros['status'] = request.args.get('status')
        if request.args.get('setor_id'):
            filtros['setor_id'] = int(request.args.get('setor_id'))
        return jsonify([dict(row) for row in buscar_usuarios(filtros)])
    except Exception as e:
        return jsonify({"erro": f"Erro ao buscar usuários: {str(e)}"}), 500


@api_bp.route('/usuarios/<int:usuario_id>', methods=['GET'])
def obter_usuario_api(usuario_id):
    try:
        resultado = obter_usuario(usuario_id)
        return jsonify(resultado) if resultado else (jsonify({"erro": "Usuário não encontrado"}), 404)
    except Exception as e:
        return jsonify({"erro": f"Erro ao buscar usuário: {str(e)}"}), 500


@api_bp.route('/usuarios', methods=['POST'])
def criar_usuario_api():
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Dados JSON obrigatórios"}), 400
    try:
        usuario_id = criar_usuario(dados)
        return jsonify({"mensagem": "Usuário criado com sucesso", "id": usuario_id, "nome": dados.get('nome_completo')}), 201
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except sqlite3.IntegrityError as e:
        if 'email' in str(e):
            return jsonify({"erro": "E-mail já está em uso"}), 409
        if 'matricula' in str(e):
            return jsonify({"erro": "Matrícula já está em uso"}), 409
        return jsonify({"erro": "Erro de integridade ao salvar"}), 400
    except Exception as e:
        return jsonify({"erro": f"Erro interno: {str(e)}"}), 500


@api_bp.route('/usuarios/<int:usuario_id>', methods=['PUT'])
def atualizar_usuario_api(usuario_id):
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Corpo JSON vazio"}), 400
    try:
        if atualizar_usuario(usuario_id, dados):
            return jsonify({"mensagem": "Usuário atualizado com sucesso"}), 200
        return jsonify({"erro": "Usuário não encontrado"}), 404
    except sqlite3.IntegrityError as e:
        if 'email' in str(e):
            return jsonify({"erro": "E-mail já está em uso"}), 409
        if 'matricula' in str(e):
            return jsonify({"erro": "Matrícula já está em uso"}), 409
        return jsonify({"erro": "Erro de integridade ao atualizar"}), 400
    except Exception as e:
        return jsonify({"erro": f"Erro interno: {str(e)}"}), 500


@api_bp.route('/usuarios/<int:usuario_id>', methods=['DELETE'])
def excluir_usuario_api(usuario_id):
    try:
        if excluir_usuario(usuario_id):
            return jsonify({"mensagem": "Usuário excluído com sucesso"}), 200
        return jsonify({"erro": "Usuário não encontrado"}), 404
    except ValueError as e:
        return jsonify({"erro": str(e)}), 409
    except Exception as e:
        return jsonify({"erro": f"Erro ao excluir: {str(e)}"}), 500


# ============================================================================
# 6. CARGOS E PERFIS (DROPDOWNS)
# ============================================================================

@api_bp.route('/cargos', methods=['GET'])
def listar_cargos():
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT id, nome FROM cargos ORDER BY nome" if request.args.get('dropdown') == 'true' else "SELECT id, nome, descricao FROM cargos ORDER BY nome"
            cursor.execute(query)
            return jsonify([dict(row) for row in cursor.fetchall()])
    except Exception as e:
        return jsonify({"erro": f"Erro ao buscar cargos: {str(e)}"}), 500


@api_bp.route('/perfis', methods=['GET'])
def listar_perfis():
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT id, nome FROM perfis_usuario ORDER BY nivel_acesso DESC" if request.args.get('dropdown') == 'true' else "SELECT id, nome, nivel_acesso, descricao FROM perfis_usuario ORDER BY nivel_acesso DESC"
            cursor.execute(query)
            return jsonify([dict(row) for row in cursor.fetchall()])
    except Exception as e:
        return jsonify({"erro": f"Erro ao buscar perfis: {str(e)}"}), 500


# ============================================================================
# 7. CONTRATOS E SOLICITAÇÕES
# ============================================================================

@api_bp.route('/contratos-locacao', methods=['GET'])
def buscar_contratos_locacao_api():
    filtros = {k: request.args.get(k) for k in ['numero_contrato', 'fornecedor', 'status'] if request.args.get(k)}
    return jsonify([dict(row) for row in buscar_contratos_locacao(filtros)])


@api_bp.route('/solicitacoes', methods=['GET'])
def buscar_solicitacoes_api():
    filtros = {'status': request.args.get('status')} if request.args.get('status') else {}
    return jsonify([dict(row) for row in buscar_solicitacoes(filtros)])


# ============================================================================
# 8. EXPORTAÇÃO E UPLOAD
# ============================================================================

@api_bp.route('/ativos/exportar', methods=['GET'])
def exportar_ativos():
    try:
        filtros = {k: request.args.get(k, '').strip() for k in ['tipo_ativo', 'categoria', 'status', 'ambiente_local', 'predio', 'setor_local'] if request.args.get(k)}
        resultados = buscar_ativos(filtros)
        if not resultados:
            return jsonify({'sucesso': False, 'erro': 'Nenhum ativo encontrado'}), 404
        output = StringIO()
        writer = csv.writer(output)
        cabecalho = ['codigo_ativo', 'tipo_ativo', 'categoria', 'descricao', 'status', 'proprietario_nome', 'usuario_nome', 'local_nome', 'projeto']
        writer.writerow(cabecalho)
        for row in resultados:
            writer.writerow([str(row.get(c, '')) if row.get(c) is not None else '' for c in cabecalho])
        filename = f'ativos_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        return Response(output.getvalue(), mimetype='text/csv', headers={'Content-Disposition': f'attachment; filename={filename}'})
    except Exception as e:
        return jsonify({'sucesso': False, 'erro': f'Erro ao exportar: {str(e)}'}), 500


@api_bp.route('/ativos/lote', methods=['POST'])
def processar_lote_ativos():
    if 'file' not in request.files:
        return jsonify({"erro": "Nenhum arquivo enviado"}), 400
    arquivo = request.files['file']
    if not arquivo.filename.endswith('.csv'):
        return jsonify({"erro": "Apenas arquivos CSV são permitidos"}), 400
    try:
        stream = io.StringIO(arquivo.stream.read().decode("UTF-8-sig"))
        csv_input = csv.DictReader(stream, delimiter=';')
        if 'DESCRITIVO' not in csv_input.fieldnames:
            return jsonify({"erro": "Formato de CSV inválido. Use o modelo da obra."}), 400
        resultados = {"sucesso": 0, "erros": [], "detalhes": []}
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cache_empresas = {r['nome']: r['id'] for r in cursor.execute("SELECT id, nome FROM empresas").fetchall()}
            cache_locais = {r['nome']: r['id'] for r in cursor.execute("SELECT id, nome FROM locais").fetchall()}
            cache_usuarios = {r['nome_completo']: r['id'] for r in cursor.execute("SELECT id, nome_completo FROM usuarios").fetchall()}
            for linha_num, linha in enumerate(csv_input, start=2):
                try:
                    descritivo = linha.get('DESCRITIVO', '').strip()
                    if not descritivo:
                        continue
                    pat_serie = linha.get('PATRIMONIO_NUMERO_SERIE', '').strip()
                    patrimonio, numero_serie = None, None
                    if '/' in pat_serie:
                        partes = [p.strip() for p in pat_serie.split('/')]
                        if len(partes) >= 1 and partes[0].upper() not in ['SEM PATR', '']:
                            patrimonio = partes[0]
                        if len(partes) >= 2 and partes[1].upper() not in ['SEM SN', 'SEM Nº SERIE', '']:
                            numero_serie = partes[1]
                    elif pat_serie and pat_serie.upper() not in ['SEM PATR', 'SEM SN']:
                        numero_serie = pat_serie
                    centro_custo = linha.get('CENTRO CUSTO', '').strip()
                    empresa_id = cache_empresas.get(centro_custo)
                    if not empresa_id:
                        cursor.execute("SELECT id FROM empresas WHERE nome LIKE ?", (f"%{centro_custo}%",))
                        res = cursor.fetchone()
                        empresa_id = res[0] if res else None
                    if not empresa_id:
                        raise ValueError(f"Proprietário '{centro_custo}' não encontrado")
                    local_nome = linha.get('LOCAL ATUAL', '').strip()
                    local_id = cache_locais.get(local_nome)
                    if not local_id:
                        raise ValueError(f"Local '{local_nome}' não cadastrado no sistema")
                    usuario_nome = linha.get('USUÁRIO', '').strip()
                    usuario_id = cache_usuarios.get(usuario_nome)
                    desc_upper = descritivo.upper()
                    tipo_ativo, categoria = 'hardware', 'Outros'
                    if 'NOTEBOOK' in desc_upper:
                        categoria = 'Notebook'
                    elif 'MONITOR' in desc_upper:
                        tipo_ativo, categoria = 'periferico', 'Monitor'
                    elif 'SMARTPHONE' in desc_upper:
                        categoria = 'Smartphone'
                    elif 'TABLET' in desc_upper:
                        categoria = 'Tablet'
                    elif 'IMPRESSORA' in desc_upper:
                        tipo_ativo, categoria = 'periferico', 'Impressora'
                    elif 'RADIO' in desc_upper or 'WALKIE' in desc_upper:
                        tipo_ativo, categoria = 'radio', 'Walkie-Talkie'
                    obs = linha.get('OBSERVAÇÃO', '').strip().upper()
                    status = 'Desmobilizado' if 'DESMOBILIZADO' in obs else 'Em Estoque' if 'ESTOQUE' in obs else 'Com Defeito' if 'DEFEITO' in obs else 'Em uso'
                    codigo_ativo = f"{categoria[:3].upper()}-{linha_num}"
                    cursor.execute("""
                        INSERT INTO ativos (codigo_ativo, patrimonio, numero_serie, tipo_ativo, categoria,
                                           descricao, status, proprietario_id, usuario_atual_id, local_atual_id,
                                           projeto, observacoes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (codigo_ativo, patrimonio, numero_serie, tipo_ativo, categoria, descritivo, status, empresa_id, usuario_id, local_id, linha.get('OBRA / PROJETO'), obs))
                    ativo_id = cursor.lastrowid
                    if 'IMEI' in linha and linha['IMEI']:
                        cursor.execute("INSERT INTO atributos_ativos (ativo_id, chave, valor) VALUES (?, ?, ?)", (ativo_id, 'imei', linha['IMEI']))
                    resultados["sucesso"] += 1
                except Exception as e:
                    resultados["erros"].append(f"Linha {linha_num}: {str(e)}")
            conn.commit()
        return jsonify({"mensagem": f"Processamento concluído: {resultados['sucesso']} importados.", "resultados": resultados}), 200
    except Exception as e:
        return jsonify({"erro": f"Erro ao processar: {str(e)}"}), 500


# ============================================================================
# 9. SAÚDE E AUTENTICAÇÃO
# ============================================================================

@api_bp.route('/health', methods=['GET'])
def health_check():
    try:
        with get_db_connection() as conn:
            total = conn.execute("SELECT COUNT(*) FROM ativos").fetchone()[0]
        return jsonify({'status': 'online', 'total_ativos': total})
    except Exception as e:
        return jsonify({'status': 'error', 'erro': str(e)}), 500


@api_bp.route('/login', methods=['POST'])
def login_api():
    dados = request.get_json()
    if not dados or not dados.get('email') or not dados.get('password'):
        return jsonify({"erro": "Email e senha são obrigatórios"}), 400
    try:
        usuario = verificar_credenciais(dados['email'], dados['password'])
        if usuario:
            return jsonify({"sucesso": True, "usuario": usuario}), 200
        return jsonify({"erro": "Email ou senha inválidos"}), 401
    except Exception as e:
        return jsonify({"erro": f"Erro na autenticação: {str(e)}"}), 500