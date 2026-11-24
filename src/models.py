# src/models.py - VERSÃO FINAL COM SANITIZAÇÃO E CRUD COMPLETO
import sqlite3
import os
import json
from typing import List, Dict, Any, Optional
from contextlib import contextmanager
import hashlib

# ============================================================================
# CONFIGURAÇÃO DO BANCO
# ============================================================================

DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'equipamentos_v3.db')


@contextmanager
def get_db_connection():
    """Context manager para conexão com o banco de dados SQLite."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def get_db_path() -> str:
    return DB_PATH


def verificar_banco_existe() -> bool:
    return os.path.exists(DB_PATH)


# ============================================================================
# SANITIZAÇÃO DE VALORES (CRÍTICO - resolve o erro "type 'dict' is not supported")
# ============================================================================

def _sanitizar_valor(valor: Any) -> Any:
    """Converte valores não escalares (dict, list) para tipos aceitos pelo SQLite."""
    if valor is None:
        return None
    if isinstance(valor, (str, int, float, bytes)):
        return valor
    if isinstance(valor, dict):
        if 'value' in valor:
            return _sanitizar_valor(valor['value'])
        if 'id' in valor:
            return _sanitizar_valor(valor['id'])
        if 'nome' in valor:
            return _sanitizar_valor(valor['nome'])
        if 'nome_completo' in valor:
            return _sanitizar_valor(valor['nome_completo'])
        return json.dumps(valor, ensure_ascii=False)
    if isinstance(valor, list):
        if len(valor) == 0:
            return None
        if len(valor) == 1:
            return _sanitizar_valor(valor[0])
        return ','.join(str(_sanitizar_valor(v)) for v in valor)
    return str(valor)


def _coercionar_int(valor: Any) -> Optional[int]:
    """Converte valor para int, retornando None se inválido."""
    if valor is None or valor == '':
        return None
    try:
        return int(valor)
    except (ValueError, TypeError):
        return None


# ============================================================================
# AUTENTICAÇÃO
# ============================================================================

def hash_senha(senha: str) -> str:
    return hashlib.sha256(senha.encode('utf-8')).hexdigest()


def verificar_credenciais(email: str, senha: str) -> Optional[Dict[str, Any]]:
    senha_hash = hash_senha(senha)
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.id, u.nome_completo, u.email, u.perfil_id, p.nome as perfil, u.status
            FROM usuarios u
            JOIN perfis_usuario p ON u.perfil_id = p.id
            WHERE u.email = ? AND u.senha_hash = ? AND u.status = 'Ativo'
        """, (email, senha_hash))
        usuario = cursor.fetchone()
        return dict(usuario) if usuario else None


def criar_usuario_inicial():
    """Cria usuário administrador inicial se não existir"""
    senha_admin = "admin123"
    senha_hash = hash_senha(senha_admin)
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM usuarios WHERE email = 'admin@ctcinfra.com.br'")
        if cursor.fetchone()[0] == 0:
            cursor.execute("SELECT id FROM perfis_usuario WHERE nome = 'Administrador'")
            perfil = cursor.fetchone()
            if not perfil:
                cursor.execute("INSERT INTO perfis_usuario (nome, nivel_acesso, descricao) VALUES ('Administrador', 4, 'Acesso total ao sistema')")
                perfil_id = cursor.lastrowid
            else:
                perfil_id = perfil['id']
            cursor.execute("INSERT INTO usuarios (nome_completo, email, senha_hash, perfil_id, status) VALUES (?, ?, ?, ?, 'Ativo')",
                          ('ADMINISTRADOR', 'admin@ctcinfra.com.br', senha_hash, perfil_id))
            conn.commit()


# ============================================================================
# CRUD DE EMPRESAS
# ============================================================================

def buscar_empresas(filtros: Optional[Dict[str, Any]] = None) -> List[sqlite3.Row]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = "SELECT id, nome, cnpj, tipo, contato FROM empresas WHERE 1=1"
        params = []
        if filtros:
            if filtros.get('nome'):
                query += " AND nome LIKE ?"
                params.append(f"%{filtros['nome']}%")
            if filtros.get('tipo'):
                query += " AND tipo = ?"
                params.append(filtros['tipo'])
        query += " ORDER BY nome"
        cursor.execute(query, params)
        return cursor.fetchall()


def obter_empresa(empresa_id: int) -> Optional[Dict[str, Any]]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM empresas WHERE id = ?", (empresa_id,))
        resultado = cursor.fetchone()
        return dict(resultado) if resultado else None


def criar_empresa(dados: Dict[str, Any]) -> int:
    if not dados.get('nome'):
        raise ValueError("Campo 'nome' é obrigatório")
    if not dados.get('tipo') or dados['tipo'] not in ('propria', 'fornecedor'):
        raise ValueError("Campo 'tipo' deve ser 'propria' ou 'fornecedor'")
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO empresas (nome, cnpj, tipo, contato)
            VALUES (?, ?, ?, ?)
        """, (_sanitizar_valor(dados['nome']).strip(), _sanitizar_valor(dados.get('cnpj')),
              _sanitizar_valor(dados['tipo']), _sanitizar_valor(dados.get('contato'))))
        conn.commit()
        return cursor.lastrowid


def atualizar_empresa(empresa_id: int, dados: Dict[str, Any]) -> bool:
    permitidos = {'nome', 'cnpj', 'tipo', 'contato'}
    campos = {k: _sanitizar_valor(v) for k, v in dados.items() if k in permitidos}
    if not campos:
        return False
    if 'nome' in campos:
        campos['nome'] = campos['nome'].strip()
    set_clause = ", ".join([f"{k} = ?" for k in campos.keys()])
    params = list(campos.values()) + [empresa_id]
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"UPDATE empresas SET {set_clause} WHERE id = ?", params)
        conn.commit()
        return cursor.rowcount > 0


def excluir_empresa(empresa_id: int) -> bool:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM ativos WHERE proprietario_id = ?", (empresa_id,))
        if cursor.fetchone()[0] > 0:
            raise ValueError("Não é possível excluir: existem ativos vinculados a esta empresa")
        cursor.execute("SELECT COUNT(*) FROM contratos_locacao WHERE empresa_id = ?", (empresa_id,))
        if cursor.fetchone()[0] > 0:
            raise ValueError("Não é possível excluir: existem contratos vinculados a esta empresa")
        cursor.execute("DELETE FROM empresas WHERE id = ?", (empresa_id,))
        conn.commit()
        return cursor.rowcount > 0


# ============================================================================
# CRUD DE USUÁRIOS
# ============================================================================

def buscar_usuarios(filtros: Optional[Dict[str, Any]] = None) -> List[sqlite3.Row]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = """
            SELECT u.id, u.nome_completo, u.email, u.matricula, u.status,
                   c.nome as cargo_nome, s.nome as setor_nome, l.nome as local_nome, p.nome as perfil_nome
            FROM usuarios u
            LEFT JOIN cargos c ON u.cargo_id = c.id
            LEFT JOIN setores s ON u.setor_id = s.id
            LEFT JOIN locais l ON u.local_padrao_id = l.id
            LEFT JOIN perfis_usuario p ON u.perfil_id = p.id
            WHERE 1=1
        """
        params = []
        if filtros:
            if filtros.get('nome'):
                query += " AND u.nome_completo LIKE ?"
                params.append(f"%{filtros['nome']}%")
            if filtros.get('status'):
                query += " AND u.status = ?"
                params.append(filtros['status'])
            if filtros.get('setor_id'):
                query += " AND u.setor_id = ?"
                params.append(filtros['setor_id'])
        query += " ORDER BY u.nome_completo"
        cursor.execute(query, params)
        return cursor.fetchall()


def obter_usuario(usuario_id: int) -> Optional[Dict[str, Any]]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.id, u.nome_completo, u.email, u.matricula, u.cargo_id,
                   u.setor_id, u.local_padrao_id, u.perfil_id, u.status
            FROM usuarios u WHERE u.id = ?
        """, (usuario_id,))
        resultado = cursor.fetchone()
        return dict(resultado) if resultado else None


def criar_usuario(dados: Dict[str, Any]) -> int:
    obrigatorios = ['nome_completo', 'email', 'perfil_id']
    for campo in obrigatorios:
        if not dados.get(campo):
            raise ValueError(f"Campo obrigatório '{campo}' não fornecido")
    senha = dados.get('senha', 'mudar123')
    senha_hash = hash_senha(str(_sanitizar_valor(senha)))
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO usuarios (nome_completo, email, matricula, senha_hash,
                                  cargo_id, setor_id, local_padrao_id, perfil_id, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            _sanitizar_valor(dados['nome_completo']).strip(),
            _sanitizar_valor(dados['email']).strip().lower(),
            _sanitizar_valor(dados.get('matricula')),
            senha_hash,
            _coercionar_int(dados.get('cargo_id')),
            _coercionar_int(dados.get('setor_id')),
            _coercionar_int(dados.get('local_padrao_id')),
            _coercionar_int(dados['perfil_id']),
            _sanitizar_valor(dados.get('status', 'Ativo'))
        ))
        conn.commit()
        return cursor.lastrowid


def atualizar_usuario(usuario_id: int, dados: Dict[str, Any]) -> bool:
    permitidos = {'nome_completo', 'email', 'matricula', 'cargo_id', 'setor_id', 'local_padrao_id', 'perfil_id', 'status'}
    campos = {}
    for k, v in dados.items():
        if k in permitidos:
            if k in ('cargo_id', 'setor_id', 'local_padrao_id', 'perfil_id'):
                campos[k] = _coercionar_int(v)
            else:
                campos[k] = _sanitizar_valor(v)
    if not campos:
        return False
    if 'email' in campos and campos['email']:
        campos['email'] = campos['email'].strip().lower()
    if 'nome_completo' in campos and campos['nome_completo']:
        campos['nome_completo'] = campos['nome_completo'].strip()
    set_clause = ", ".join([f"{k} = ?" for k in campos.keys()])
    params = list(campos.values()) + [usuario_id]
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"UPDATE usuarios SET {set_clause} WHERE id = ?", params)
        conn.commit()
        return cursor.rowcount > 0


def excluir_usuario(usuario_id: int) -> bool:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM ativos WHERE usuario_atual_id = ?", (usuario_id,))
        if cursor.fetchone()[0] > 0:
            raise ValueError("Não é possível excluir: existem ativos vinculados a este usuário.")
        cursor.execute("DELETE FROM usuarios WHERE id = ?", (usuario_id,))
        conn.commit()
        return cursor.rowcount > 0


# ============================================================================
# CRUD DE SETORES
# ============================================================================

def buscar_setores(filtros: Optional[Dict[str, Any]] = None) -> List[sqlite3.Row]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = "SELECT id, nome, sigla, descricao, ativo FROM setores WHERE 1=1"
        params = []
        if filtros and filtros.get('nome'):
            query += " AND nome LIKE ?"
            params.append(f"%{filtros['nome']}%")
        query += " ORDER BY nome"
        cursor.execute(query, params)
        return cursor.fetchall()


def obter_setor(setor_id: int) -> Optional[Dict[str, Any]]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome, sigla, descricao, ativo FROM setores WHERE id = ?", (setor_id,))
        resultado = cursor.fetchone()
        return dict(resultado) if resultado else None


def criar_setor(dados: Dict[str, Any]) -> int:
    if not dados.get('nome'):
        raise ValueError("Campo 'nome' é obrigatório")
    with get_db_connection() as conn:
        cursor = conn.cursor()
        sigla = _sanitizar_valor(dados.get('sigla', ''))
        cursor.execute("""
            INSERT INTO setores (nome, sigla, descricao, ativo) VALUES (?, ?, ?, ?)
        """, (
            _sanitizar_valor(dados['nome']).strip(),
            sigla.strip().upper() if sigla else None,
            _sanitizar_valor(dados.get('descricao', '')).strip() or None,
            _coercionar_int(dados.get('ativo', 1))
        ))
        conn.commit()
        return cursor.lastrowid


def atualizar_setor(setor_id: int, dados: Dict[str, Any]) -> bool:
    campos = {}
    for k, v in dados.items():
        if k in {'nome', 'sigla', 'descricao', 'ativo'}:
            campos[k] = _sanitizar_valor(v)
    if not campos:
        return False
    if 'sigla' in campos and campos['sigla']:
        campos['sigla'] = campos['sigla'].strip().upper()
    if 'nome' in campos and campos['nome']:
        campos['nome'] = campos['nome'].strip()
    set_clause = ", ".join([f"{k} = ?" for k in campos.keys()])
    params = list(campos.values()) + [setor_id]
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"UPDATE setores SET {set_clause} WHERE id = ?", params)
        conn.commit()
        return cursor.rowcount > 0


def excluir_setor(setor_id: int) -> bool:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM usuarios WHERE setor_id = ?", (setor_id,))
        if cursor.fetchone()[0] > 0:
            raise ValueError("Não é possível excluir: existem usuários vinculados a este setor")
        cursor.execute("DELETE FROM setores WHERE id = ?", (setor_id,))
        conn.commit()
        return cursor.rowcount > 0


# ============================================================================
# CRUD DE LOCAIS FÍSICOS
# ============================================================================

def buscar_locais(filtros: Optional[Dict[str, Any]] = None) -> List[sqlite3.Row]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = "SELECT id, nome, codigo, ambiente, predio, setor, tipo_local, ativo FROM locais WHERE 1=1"
        params = []
        if filtros:
            if filtros.get('nome'):
                query += " AND nome LIKE ?"
                params.append(f"%{filtros['nome']}%")
            if filtros.get('ambiente'):
                query += " AND ambiente = ?"
                params.append(filtros['ambiente'])
            if filtros.get('setor'):
                query += " AND setor = ?"
                params.append(filtros['setor'])
        query += " ORDER BY nome"
        cursor.execute(query, params)
        return cursor.fetchall()


def obter_local(local_id: int) -> Optional[Dict[str, Any]]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome, codigo, ambiente, predio, setor, tipo_local, ativo FROM locais WHERE id = ?", (local_id,))
        resultado = cursor.fetchone()
        return dict(resultado) if resultado else None


def criar_local(dados: Dict[str, Any]) -> int:
    obrigatorios = ['nome', 'codigo', 'ambiente', 'setor']
    for campo in obrigatorios:
        if not dados.get(campo):
            raise ValueError(f"Campo '{campo}' é obrigatório")
    ambiente = _sanitizar_valor(dados['ambiente'])
    predio = _sanitizar_valor(dados.get('predio'))
    if ambiente == 'obra' and not predio:
        raise ValueError("Campo 'predio' é obrigatório quando ambiente = 'obra'")
    if ambiente != 'obra' and predio:
        raise ValueError("Campo 'predio' deve ser nulo quando ambiente != 'obra'")
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO locais (nome, codigo, ambiente, predio, setor, tipo_local, ativo)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            _sanitizar_valor(dados['nome']).strip(),
            _sanitizar_valor(dados['codigo']).strip(),
            ambiente,
            predio,
            _sanitizar_valor(dados['setor']).strip(),
            _sanitizar_valor(dados.get('tipo_local', '')).strip() or None,
            _coercionar_int(dados.get('ativo', 1))
        ))
        conn.commit()
        return cursor.lastrowid


def atualizar_local(local_id: int, dados: Dict[str, Any]) -> bool:
    campos = {}
    for k, v in dados.items():
        if k in {'nome', 'codigo', 'ambiente', 'predio', 'setor', 'tipo_local', 'ativo'}:
            campos[k] = _sanitizar_valor(v)
    if not campos:
        return False
    amb = campos.get('ambiente')
    pred = campos.get('predio')
    if amb == 'obra' and not pred:
        raise ValueError("Campo 'predio' é obrigatório quando ambiente = 'obra'")
    if amb and amb != 'obra' and pred:
        raise ValueError("Campo 'predio' deve ser nulo quando ambiente != 'obra'")
    set_clause = ", ".join([f"{k} = ?" for k in campos.keys()])
    params = list(campos.values()) + [local_id]
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"UPDATE locais SET {set_clause} WHERE id = ?", params)
        conn.commit()
        return cursor.rowcount > 0


def excluir_local(local_id: int) -> bool:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM ativos WHERE local_atual_id = ?", (local_id,))
        if cursor.fetchone()[0] > 0:
            raise ValueError("Não é possível excluir: existem ativos vinculados a este local")
        cursor.execute("DELETE FROM locais WHERE id = ?", (local_id,))
        conn.commit()
        return cursor.rowcount > 0


# ============================================================================
# CRUD DE ATIVOS (COM SANITIZAÇÃO)
# ============================================================================

def buscar_ativos(filtros: Optional[Dict[str, Any]] = None) -> List[sqlite3.Row]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = """
        SELECT a.*, e.nome as proprietario_nome, u.nome_completo as usuario_nome,
        l.nome as local_nome, l.ambiente as local_ambiente, l.predio as local_predio, l.setor as local_setor,
        (SELECT valor FROM atributos_ativos WHERE ativo_id = a.id AND chave = 'host_name' LIMIT 1) as hostname
        FROM ativos a
        LEFT JOIN empresas e ON a.proprietario_id = e.id
        LEFT JOIN usuarios u ON a.usuario_atual_id = u.id
        LEFT JOIN locais l ON a.local_atual_id = l.id
        WHERE 1=1
        """
        params = []
        if filtros:
            for campo in ['tipo_ativo', 'categoria', 'status']:
                val = filtros.get(campo)
                if val:
                    if isinstance(val, list):
                        ph = ','.join(['?'] * len(val))
                        query += f" AND a.{campo} IN ({ph})"
                        params.extend(val)
                    else:
                        query += f" AND a.{campo} = ?"
                        params.append(val)
            if filtros.get('codigo_ativo'):
                query += " AND a.codigo_ativo LIKE ?"
                params.append(f"%{filtros['codigo_ativo']}%")
            if filtros.get('descricao'):
                query += " AND a.descricao LIKE ?"
                params.append(f"%{filtros['descricao']}%")
            if filtros.get('ambiente_local'):
                query += " AND l.ambiente = ?"
                params.append(filtros['ambiente_local'])
            if filtros.get('predio'):
                query += " AND l.predio = ?"
                params.append(filtros['predio'])
            if filtros.get('setor_local'):
                query += " AND l.setor = ?"
                params.append(filtros['setor_local'])
            if filtros.get('proprietario'):
                query += " AND e.nome = ?"
                params.append(filtros['proprietario'])
            if filtros.get('usuario'):
                query += " AND u.nome_completo LIKE ?"
                params.append(f"%{filtros['usuario']}%")
            if filtros.get('hostname'):
                query += " AND hostname LIKE ?"
                params.append(f"%{filtros['hostname']}%")
                
        query += " ORDER BY a.codigo_ativo"
        cursor.execute(query, params)
        return cursor.fetchall()

def criar_ativo(dados: Dict[str, Any]) -> int:
    """Cria um novo ativo (com sanitização robusta)"""
    obrigatorios = ['codigo_ativo', 'tipo_ativo', 'categoria']
    for campo in obrigatorios:
        if not dados.get(campo):
            raise ValueError(f"Campo obrigatório '{campo}' não fornecido")

    codigo_ativo = _sanitizar_valor(dados['codigo_ativo']).strip()
    patrimonio = _sanitizar_valor(dados.get('patrimonio'))
    numero_serie = _sanitizar_valor(dados.get('numero_serie'))
    tipo_ativo = _sanitizar_valor(dados['tipo_ativo'])
    categoria = _sanitizar_valor(dados['categoria']).strip()
    descricao = _sanitizar_valor(dados.get('descricao'))
    status = _sanitizar_valor(dados.get('status', 'Devolvido'))
    projeto = _sanitizar_valor(dados.get('projeto'))
    data_aquisicao = _sanitizar_valor(dados.get('data_aquisicao'))
    observacoes = _sanitizar_valor(dados.get('observacoes'))

    proprietario_id = _coercionar_int(dados.get('proprietario_id'))
    usuario_atual_id = _coercionar_int(dados.get('usuario_atual_id'))
    local_atual_id = _coercionar_int(dados.get('local_atual_id'))

    if status == 'Em uso' and usuario_atual_id is None:
        raise ValueError("Ativos com status 'Em uso' devem ter um usuário vinculado")

    tipos_validos = ('hardware', 'periferico', 'rede', 'software', 'mobiliario', 'servico', 'radio')
    if tipo_ativo not in tipos_validos:
        raise ValueError(f"tipo_ativo inválido: '{tipo_ativo}'")

    status_validos = ('Em uso', 'Devolvido', 'Desmobilizado', 'Em Desmobilização',
                      'Em Estoque', 'Com Defeito', 'Transferido', 'Em Manutenção')
    if status not in status_validos:
        raise ValueError(f"status inválido: '{status}'")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO ativos (codigo_ativo, patrimonio, numero_serie, tipo_ativo, categoria,
                               descricao, status, proprietario_id, usuario_atual_id, local_atual_id,
                               projeto, data_aquisicao, observacoes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            codigo_ativo, patrimonio, numero_serie, tipo_ativo, categoria,
            descricao, status, proprietario_id, usuario_atual_id, local_atual_id,
            projeto, data_aquisicao, observacoes
        ))
        ativo_id = cursor.lastrowid

        if dados.get('atributos') and isinstance(dados['atributos'], dict):
            for chave, valor in dados['atributos'].items():
                if valor is not None and valor != '':
                    cursor.execute(
                        "INSERT OR REPLACE INTO atributos_ativos (ativo_id, chave, valor) VALUES (?, ?, ?)",
                        (ativo_id, str(chave), str(_sanitizar_valor(valor)))
                    )
        conn.commit()
        return ativo_id


def atualizar_ativo(ativo_id: int, dados: Dict[str, Any]) -> bool:
    """Atualiza os dados de um ativo (com sanitização)"""
    permitidos_texto = {'codigo_ativo', 'patrimonio', 'numero_serie', 'tipo_ativo', 'categoria',
                        'descricao', 'status', 'projeto', 'data_aquisicao', 'observacoes'}
    permitidos_int = {'proprietario_id', 'usuario_atual_id', 'local_atual_id'}

    campos = {}
    for k, v in dados.items():
        if k in permitidos_texto:
            campos[k] = _sanitizar_valor(v)
        elif k in permitidos_int:
            campos[k] = _coercionar_int(v)

    if not campos:
        return False

    novo_status = campos.get('status')
    novo_usuario = campos.get('usuario_atual_id')
    if novo_status == 'Em uso':
        if novo_usuario is None:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT usuario_atual_id FROM ativos WHERE id = ?", (ativo_id,))
                row = cursor.fetchone()
                if not row or row['usuario_atual_id'] is None:
                    raise ValueError("Ativos com status 'Em uso' devem ter um usuário vinculado")

    if 'tipo_ativo' in campos:
        tipos_validos = ('hardware', 'periferico', 'rede', 'software', 'mobiliario', 'servico', 'radio')
        if campos['tipo_ativo'] not in tipos_validos:
            raise ValueError(f"tipo_ativo inválido: '{campos['tipo_ativo']}'")

    if 'status' in campos:
        status_validos = ('Em uso', 'Devolvido', 'Desmobilizado', 'Em Desmobilização',
                          'Em Estoque', 'Com Defeito', 'Transferido', 'Em Manutenção')
        if campos['status'] not in status_validos:
            raise ValueError(f"status inválido: '{campos['status']}'")

    set_clause = ", ".join([f"{k} = ?" for k in campos.keys()])
    params = list(campos.values()) + [ativo_id]

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"UPDATE ativos SET {set_clause}, data_atualizacao=CURRENT_TIMESTAMP WHERE id = ?", params)
        conn.commit()
        return cursor.rowcount > 0


def excluir_ativo(ativo_id: int) -> bool:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM ativos WHERE id = ?", (ativo_id,))
        conn.commit()
        return cursor.rowcount > 0


# ============================================================================
# ATRIBUTOS DINÂMICOS
# ============================================================================

def obter_atributos_ativo(ativo_id: int) -> Dict[str, str]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT chave, valor FROM atributos_ativos WHERE ativo_id = ?", (ativo_id,))
        return {row['chave']: row['valor'] for row in cursor.fetchall()}


def atualizar_atributos_ativo(ativo_id: int, atributos: Dict[str, str]) -> None:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM atributos_ativos WHERE ativo_id = ?", (ativo_id,))
        for chave, valor in atributos.items():
            if valor is not None:
                cursor.execute("INSERT INTO atributos_ativos (ativo_id, chave, valor) VALUES (?, ?, ?)",
                              (ativo_id, str(chave), str(_sanitizar_valor(valor))))
        conn.commit()


# ============================================================================
# DROPDOWNS E AUXILIARES
# ============================================================================

def obter_valores_distintos_locais() -> Dict[str, List[str]]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        return {
            'ambientes': [r[0] for r in cursor.execute("SELECT DISTINCT ambiente FROM locais ORDER BY ambiente").fetchall()],
            'predios': [r[0] for r in cursor.execute("SELECT DISTINCT predio FROM locais WHERE predio IS NOT NULL ORDER BY predio").fetchall()],
            'setores': [r[0] for r in cursor.execute("SELECT DISTINCT setor FROM locais ORDER BY setor").fetchall()]
        }


def obter_valores_distintos_ativos() -> Dict[str, List[str]]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        return {
            'tipos_ativo': [r[0] for r in cursor.execute("SELECT DISTINCT tipo_ativo FROM ativos ORDER BY tipo_ativo").fetchall()],
            'categorias': [r[0] for r in cursor.execute("SELECT DISTINCT categoria FROM ativos ORDER BY categoria").fetchall()],
            'status': [r[0] for r in cursor.execute("SELECT DISTINCT status FROM ativos ORDER BY status").fetchall()],
            'proprietarios': [r[0] for r in cursor.execute("SELECT DISTINCT nome FROM empresas ORDER BY nome").fetchall()]
        }


def buscar_cargos_dropdown() -> List[sqlite3.Row]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome FROM cargos ORDER BY nome")
        return cursor.fetchall()


def buscar_perfis_dropdown() -> List[sqlite3.Row]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome FROM perfis_usuario ORDER BY nivel_acesso DESC")
        return cursor.fetchall()


def contar_ativos() -> int:
    with get_db_connection() as conn:
        return conn.execute("SELECT COUNT(*) FROM ativos").fetchone()[0]


def contar_ativos_por_status() -> List[sqlite3.Row]:
    with get_db_connection() as conn:
        return conn.execute("SELECT status, COUNT(*) as total FROM ativos GROUP BY status").fetchall()


# ============================================================================
# DASHBOARD - FUNÇÕES DE AGREGAÇÃO
# ============================================================================

def contar_usuarios_ativos() -> int:
    """Retorna o total de usuários ativos"""
    with get_db_connection() as conn:
        return conn.execute("SELECT COUNT(*) FROM usuarios WHERE status = 'Ativo'").fetchone()[0]


def contar_usuarios_inativos() -> int:
    """Retorna o total de usuários inativos"""
    with get_db_connection() as conn:
        return conn.execute("SELECT COUNT(*) FROM usuarios WHERE status = 'Inativo'").fetchone()[0]


def contar_empresas() -> int:
    """Retorna o total de empresas cadastradas"""
    with get_db_connection() as conn:
        return conn.execute("SELECT COUNT(*) FROM empresas").fetchone()[0]


def contar_locais_ativos() -> int:
    """Retorna o total de locais ativos"""
    with get_db_connection() as conn:
        return conn.execute("SELECT COUNT(*) FROM locais WHERE ativo = 1").fetchone()[0]


def contar_setores_ativos() -> int:
    """Retorna o total de setores ativos"""
    with get_db_connection() as conn:
        return conn.execute("SELECT COUNT(*) FROM setores WHERE ativo = 1").fetchone()[0]


def contar_ativos_por_tipo() -> List[sqlite3.Row]:
    """Retorna contagem de ativos por tipo"""
    with get_db_connection() as conn:
        return conn.execute(
            "SELECT tipo_ativo, COUNT(*) as total FROM ativos GROUP BY tipo_ativo ORDER BY total DESC"
        ).fetchall()


def contar_ativos_por_categoria() -> List[sqlite3.Row]:
    """Retorna contagem de ativos por categoria (top 10)"""
    with get_db_connection() as conn:
        return conn.execute(
            "SELECT categoria, COUNT(*) as total FROM ativos GROUP BY categoria ORDER BY total DESC LIMIT 10"
        ).fetchall()


def contar_ativos_por_proprietario() -> List[sqlite3.Row]:
    """Retorna contagem de ativos por empresa proprietária"""
    with get_db_connection() as conn:
        return conn.execute("""
            SELECT e.nome as proprietario_nome, COUNT(a.id) as total
            FROM ativos a
            LEFT JOIN empresas e ON a.proprietario_id = e.id
            GROUP BY e.nome
            ORDER BY total DESC
            LIMIT 10
        """).fetchall()


def contar_ativos_por_local() -> List[sqlite3.Row]:
    """Retorna contagem de ativos por local (top 10)"""
    with get_db_connection() as conn:
        return conn.execute("""
            SELECT l.nome as local_nome, COUNT(a.id) as total
            FROM ativos a
            LEFT JOIN locais l ON a.local_atual_id = l.id
            GROUP BY l.nome
            ORDER BY total DESC
            LIMIT 10
        """).fetchall()


def buscar_ativos_recentes(limite: int = 5) -> List[sqlite3.Row]:
    """Retorna os últimos ativos cadastrados"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.*, e.nome as proprietario_nome, u.nome_completo as usuario_nome,
                   l.nome as local_nome
            FROM ativos a
            LEFT JOIN empresas e ON a.proprietario_id = e.id
            LEFT JOIN usuarios u ON a.usuario_atual_id = u.id
            LEFT JOIN locais l ON a.local_atual_id = l.id
            ORDER BY a.id DESC
            LIMIT ?
        """, (limite,))
        return cursor.fetchall()


def buscar_ativos_com_defeito() -> List[sqlite3.Row]:
    """Retorna ativos com status 'Com Defeito'"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.*, e.nome as proprietario_nome, u.nome_completo as usuario_nome,
                   l.nome as local_nome
            FROM ativos a
            LEFT JOIN empresas e ON a.proprietario_id = e.id
            LEFT JOIN usuarios u ON a.usuario_atual_id = u.id
            LEFT JOIN locais l ON a.local_atual_id = l.id
            WHERE a.status = 'Com Defeito'
            ORDER BY a.data_atualizacao DESC
        """)
        return cursor.fetchall()


def buscar_ativos_sem_usuario() -> List[sqlite3.Row]:
    """Retorna ativos 'Em uso' sem usuário vinculado (inconsistência)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.*, e.nome as proprietario_nome, l.nome as local_nome
            FROM ativos a
            LEFT JOIN empresas e ON a.proprietario_id = e.id
            LEFT JOIN locais l ON a.local_atual_id = l.id
            WHERE a.status = 'Em uso' AND (a.usuario_atual_id IS NULL OR a.usuario_atual_id = '')
            ORDER BY a.id DESC
        """)
        return cursor.fetchall()

# ============================================================================
# CONTRATOS E SOLICITAÇÕES
# ============================================================================

def buscar_contratos_locacao(filtros: Optional[Dict[str, Any]] = None) -> List[sqlite3.Row]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = "SELECT c.*, e.nome as fornecedor_nome FROM contratos_locacao c LEFT JOIN empresas e ON c.empresa_id = e.id WHERE 1=1"
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
        cursor.execute(query + " ORDER BY c.data_inicio DESC", params)
        return cursor.fetchall()


def vincular_ativo_contrato(ativo_id: int, contrato_id: int) -> bool:
    try:
        with get_db_connection() as conn:
            conn.execute("INSERT INTO ativos_contratos (ativo_id, contrato_id) VALUES (?, ?)", (ativo_id, contrato_id))
            conn.commit()
            return True
    except sqlite3.IntegrityError:
        return False


def desvincular_ativo_contrato(ativo_id: int, contrato_id: int) -> bool:
    with get_db_connection() as conn:
        conn.execute("DELETE FROM ativos_contratos WHERE ativo_id = ? AND contrato_id = ?", (ativo_id, contrato_id))
        conn.commit()
        return True


def obter_contratos_do_ativo(ativo_id: int) -> List[sqlite3.Row]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.*, e.nome as fornecedor_nome FROM ativos_contratos ac
            JOIN contratos_locacao c ON ac.contrato_id = c.id
            JOIN empresas e ON c.empresa_id = e.id WHERE ac.ativo_id = ?
        """, (ativo_id,))
        return cursor.fetchall()


def criar_solicitacao(dados: Dict[str, Any]) -> int:
    obrigatorios = ['tipo_solicitacao', 'descricao', 'setor_solicitante_id', 'gestor_solicitante_id']
    for campo in obrigatorios:
        if not dados.get(campo):
            raise ValueError(f"Campo obrigatório '{campo}' não fornecido")
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO solicitacoes (tipo_solicitacao, descricao, quantidade, especificacoes,
                                      setor_solicitante_id, gestor_solicitante_id, prioridade)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            _sanitizar_valor(dados['tipo_solicitacao']),
            _sanitizar_valor(dados['descricao']),
            _coercionar_int(dados.get('quantidade', 1)),
            _sanitizar_valor(dados.get('especificacoes')),
            _coercionar_int(dados['setor_solicitante_id']),
            _coercionar_int(dados['gestor_solicitante_id']),
            _sanitizar_valor(dados.get('prioridade', 'Media'))
        ))
        conn.commit()
        return cursor.lastrowid


def buscar_solicitacoes(filtros: Optional[Dict[str, Any]] = None) -> List[sqlite3.Row]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = """
            SELECT s.*, st.nome as setor_solicitante_nome, g.nome_completo as gestor_solicitante_nome,
                   ap.nome_completo as aprovador_nome, ex.nome_completo as executor_nome
            FROM solicitacoes s
            LEFT JOIN setores st ON s.setor_solicitante_id = st.id
            LEFT JOIN usuarios g ON s.gestor_solicitante_id = g.id
            LEFT JOIN usuarios ap ON s.aprovador_id = ap.id
            LEFT JOIN usuarios ex ON s.executor_id = ex.id WHERE 1=1
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
        cursor.execute(query + " ORDER BY s.data_solicitacao DESC", params)
        return cursor.fetchall()