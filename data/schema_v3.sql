-- ============================================================================
-- SCHEMA V3 - SISTEMA DE GESTÃO DE ATIVOS CTC INFRA
-- Versão atualizada com:
-- - Campos patrimonio e numero_serie separados
-- - Status expandidos para realidade da obra
-- - Tipo 'radio' para Walkie-Talkies
-- - Tabela historico_ativos para rastreamento
-- - Setores com sigla, descricao e status ativo
-- - Locais com status ativo
-- ============================================================================

-- ============================================================================
-- TABELAS BASE (CADASTROS)
-- ============================================================================

CREATE TABLE empresas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT UNIQUE NOT NULL,
    cnpj TEXT,
    tipo TEXT NOT NULL CHECK (tipo IN ('propria', 'fornecedor')),
    contato TEXT,
    data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE cargos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT UNIQUE NOT NULL,
    descricao TEXT,
    data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE setores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT UNIQUE NOT NULL,
    descricao TEXT,
    sigla TEXT UNIQUE,
    ativo INTEGER DEFAULT 1,
    data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE locais (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT UNIQUE NOT NULL,
    codigo TEXT UNIQUE NOT NULL,
    ambiente TEXT NOT NULL CHECK (ambiente IN ('obra', 'canteiro', 'sede')),
    predio TEXT,
    setor TEXT NOT NULL,
    tipo_local TEXT,
    ativo INTEGER DEFAULT 1,
    data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP,
    CHECK (
        (ambiente = 'obra' AND predio IS NOT NULL) OR
        (ambiente != 'obra' AND predio IS NULL)
    )
);

-- ============================================================================
-- USUÁRIOS E PERFIS (RBAC)
-- ============================================================================

CREATE TABLE perfis_usuario (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT UNIQUE NOT NULL,
    nivel_acesso INTEGER NOT NULL,
    descricao TEXT
);

CREATE TABLE usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome_completo TEXT NOT NULL,
    email TEXT UNIQUE,
    matricula TEXT UNIQUE,
    senha_hash TEXT,
    cargo_id INTEGER,
    setor_id INTEGER,
    local_padrao_id INTEGER,
    perfil_id INTEGER NOT NULL,
    status TEXT DEFAULT 'Ativo' CHECK (status IN ('Ativo', 'Inativo', 'Bloqueado')),
    data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP,
    ultimo_acesso DATETIME,
    FOREIGN KEY (cargo_id) REFERENCES cargos (id),
    FOREIGN KEY (setor_id) REFERENCES setores (id),
    FOREIGN KEY (local_padrao_id) REFERENCES locais (id),
    FOREIGN KEY (perfil_id) REFERENCES perfis_usuario (id)
);

-- ============================================================================
-- ATIVOS (EQUIPAMENTOS, LICENÇAS, MOBILIÁRIO, WALKIE-TALKIES, ETC.)
-- ============================================================================

CREATE TABLE ativos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo_ativo TEXT UNIQUE NOT NULL,
    patrimonio TEXT,
    numero_serie TEXT,
    tipo_ativo TEXT NOT NULL CHECK (tipo_ativo IN (
        'hardware', 'periferico', 'rede', 'software', 
        'mobiliario', 'servico', 'radio'
    )),
    categoria TEXT NOT NULL,
    descricao TEXT,
    status TEXT NOT NULL DEFAULT 'Em uso' CHECK (status IN (
        'Em uso', 'Devolvido', 'Desmobilizado',
        'Em Desmobilização', 'Em Estoque', 'Com Defeito',
        'Transferido', 'Em Manutenção'
    )),
    proprietario_id INTEGER NOT NULL,
    usuario_atual_id INTEGER,
    local_atual_id INTEGER,
    projeto TEXT,
    data_aquisicao TEXT,
    data_status TEXT DEFAULT CURRENT_TIMESTAMP,
    observacoes TEXT,
    data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (proprietario_id) REFERENCES empresas (id),
    FOREIGN KEY (usuario_atual_id) REFERENCES usuarios (id),
    FOREIGN KEY (local_atual_id) REFERENCES locais (id),
    CHECK ((status = 'Em uso' AND usuario_atual_id IS NOT NULL) OR (status != 'Em uso'))
);

CREATE TABLE atributos_ativos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ativo_id INTEGER NOT NULL,
    chave TEXT NOT NULL,
    valor TEXT,
    data_atualizacao DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ativo_id) REFERENCES ativos (id) ON DELETE CASCADE,
    UNIQUE(ativo_id, chave)
);

-- ============================================================================
-- CONTRATOS DE LOCAÇÃO
-- ============================================================================

CREATE TABLE contratos_locacao (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero_contrato TEXT UNIQUE NOT NULL,
    empresa_id INTEGER NOT NULL,
    data_inicio TEXT NOT NULL,
    data_fim TEXT,
    valor_total REAL NOT NULL,
    periodo_cobranca TEXT NOT NULL CHECK (periodo_cobranca IN ('mensal', 'semestral', 'anual', 'personalizado')),
    duracao_meses INTEGER,
    status TEXT DEFAULT 'Ativo' CHECK (status IN ('Ativo', 'Encerrado', 'Cancelado', 'Suspense')),
    observacoes TEXT,
    data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (empresa_id) REFERENCES empresas (id)
);

CREATE TABLE ativos_contratos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ativo_id INTEGER NOT NULL,
    contrato_id INTEGER NOT NULL,
    data_vinculo TEXT DEFAULT CURRENT_TIMESTAMP,
    data_desvinculo TEXT,
    FOREIGN KEY (ativo_id) REFERENCES ativos (id) ON DELETE CASCADE,
    FOREIGN KEY (contrato_id) REFERENCES contratos_locacao (id) ON DELETE CASCADE,
    UNIQUE(ativo_id, contrato_id)
);

-- ============================================================================
-- SOLICITAÇÕES DE ATIVOS
-- ============================================================================

CREATE TABLE solicitacoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo_solicitacao TEXT NOT NULL,
    descricao TEXT NOT NULL,
    quantidade INTEGER DEFAULT 1,
    especificacoes TEXT,
    setor_solicitante_id INTEGER NOT NULL,
    gestor_solicitante_id INTEGER NOT NULL,
    status TEXT DEFAULT 'Pendente' CHECK (status IN (
        'Pendente', 'Aprovado', 'Em Processamento', 
        'Concluido', 'Rejeitado', 'Cancelado'
    )),
    prioridade TEXT DEFAULT 'Media' CHECK (prioridade IN ('Baixa', 'Media', 'Alta', 'Urgente')),
    data_solicitacao TEXT DEFAULT CURRENT_TIMESTAMP,
    data_aprovacao TEXT,
    data_conclusao TEXT,
    aprovador_id INTEGER,
    executor_id INTEGER,
    justificativa TEXT,
    FOREIGN KEY (setor_solicitante_id) REFERENCES setores (id),
    FOREIGN KEY (gestor_solicitante_id) REFERENCES usuarios (id),
    FOREIGN KEY (aprovador_id) REFERENCES usuarios (id),
    FOREIGN KEY (executor_id) REFERENCES usuarios (id)
);

-- ============================================================================
-- HISTÓRICO DE MOVIMENTAÇÕES (RASTREAMENTO)
-- ============================================================================

CREATE TABLE historico_ativos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ativo_id INTEGER NOT NULL,
    tipo_movimentacao TEXT NOT NULL CHECK (tipo_movimentacao IN (
        'atribuicao', 'devolucao', 'transferencia', 'desmobilizacao',
        'manutencao', 'retorno', 'alteracao_status'
    )),
    usuario_origem_id INTEGER,
    usuario_destino_id INTEGER,
    local_origem_id INTEGER,
    local_destino_id INTEGER,
    status_anterior TEXT,
    status_novo TEXT,
    observacoes TEXT,
    data_movimentacao DATETIME DEFAULT CURRENT_TIMESTAMP,
    responsavel_id INTEGER,
    FOREIGN KEY (ativo_id) REFERENCES ativos (id) ON DELETE CASCADE,
    FOREIGN KEY (usuario_origem_id) REFERENCES usuarios (id),
    FOREIGN KEY (usuario_destino_id) REFERENCES usuarios (id),
    FOREIGN KEY (local_origem_id) REFERENCES locais (id),
    FOREIGN KEY (local_destino_id) REFERENCES locais (id),
    FOREIGN KEY (responsavel_id) REFERENCES usuarios (id)
);

-- ============================================================================
-- ÍNDICES PARA PERFORMANCE
-- ============================================================================

CREATE INDEX idx_ativos_status ON ativos(status);
CREATE INDEX idx_ativos_tipo ON ativos(tipo_ativo);
CREATE INDEX idx_ativos_categoria ON ativos(categoria);
CREATE INDEX idx_ativos_proprietario ON ativos(proprietario_id);
CREATE INDEX idx_ativos_usuario ON ativos(usuario_atual_id);
CREATE INDEX idx_ativos_local ON ativos(local_atual_id);
CREATE INDEX idx_ativos_codigo ON ativos(codigo_ativo);
CREATE INDEX idx_ativos_patrimonio ON ativos(patrimonio);
CREATE INDEX idx_ativos_numero_serie ON ativos(numero_serie);
CREATE INDEX idx_ativos_projeto ON ativos(projeto);
CREATE INDEX idx_atributos_ativo ON atributos_ativos(ativo_id);
CREATE INDEX idx_atributos_chave ON atributos_ativos(chave);
CREATE INDEX idx_locais_ambiente ON locais(ambiente);
CREATE INDEX idx_locais_predio ON locais(predio);
CREATE INDEX idx_locais_setor ON locais(setor);
CREATE INDEX idx_locais_ativo ON locais(ativo);
CREATE INDEX idx_setores_ativo ON setores(ativo);
CREATE INDEX idx_setores_nome ON setores(nome);
CREATE INDEX idx_setores_sigla ON setores(sigla);
CREATE INDEX idx_solicitacoes_status ON solicitacoes(status);
CREATE INDEX idx_solicitacoes_setor ON solicitacoes(setor_solicitante_id);
CREATE INDEX idx_historico_ativo ON historico_ativos(ativo_id);
CREATE INDEX idx_historico_data ON historico_ativos(data_movimentacao);
CREATE INDEX idx_historico_tipo ON historico_ativos(tipo_movimentacao);
CREATE INDEX idx_usuarios_email ON usuarios(email);
CREATE INDEX idx_usuarios_setor ON usuarios(setor_id);
CREATE INDEX idx_usuarios_status ON usuarios(status);
CREATE INDEX idx_contratos_status ON contratos_locacao(status);
CREATE INDEX idx_contratos_empresa ON contratos_locacao(empresa_id);