-- Tabela de empresas (proprietárias ou fornecedoras)
CREATE TABLE empresas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT UNIQUE NOT NULL,
    cnpj TEXT,
    tipo TEXT NOT NULL CHECK (tipo IN ('propria', 'fornecedor')),
    contato TEXT
);

-- Cargos dos usuários
CREATE TABLE cargos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT UNIQUE NOT NULL
);

-- Setores da empresa
CREATE TABLE setores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT UNIQUE NOT NULL
);

-- Locais físicos com hierarquia: ambiente → [prédio] → setor
CREATE TABLE locais (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT UNIQUE NOT NULL,
    codigo TEXT UNIQUE NOT NULL,
    ambiente TEXT NOT NULL CHECK (ambiente IN ('obra', 'canteiro', 'sede')),
    predio TEXT,  -- Preenchido SOMENTE se ambiente = 'obra'
    setor TEXT NOT NULL,
    tipo_local TEXT,
    CHECK (
        (ambiente = 'obra' AND predio IS NOT NULL) OR 
        (ambiente != 'obra' AND predio IS NULL)
    )
);

-- Perfis de usuário (RBAC)
CREATE TABLE perfis_usuario (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT UNIQUE NOT NULL,
    nivel_acesso INTEGER NOT NULL
);

-- Usuários do sistema
CREATE TABLE usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome_completo TEXT NOT NULL,
    email TEXT UNIQUE,
    matricula TEXT UNIQUE,
    cargo_id INTEGER,
    setor_id INTEGER,
    local_padrao_id INTEGER,
    perfil_id INTEGER NOT NULL,
    status TEXT DEFAULT 'Ativo',
    FOREIGN KEY (cargo_id) REFERENCES cargos (id),
    FOREIGN KEY (setor_id) REFERENCES setores (id),
    FOREIGN KEY (local_padrao_id) REFERENCES locais (id),
    FOREIGN KEY (perfil_id) REFERENCES perfis_usuario (id)
);

-- Ativos (equipamentos, licenças, mobiliário, etc.)
CREATE TABLE ativos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo_ativo TEXT UNIQUE NOT NULL,
    tipo_ativo TEXT NOT NULL CHECK (tipo_ativo IN ('hardware', 'periferico', 'rede', 'software', 'mobiliario', 'servico')),
    categoria TEXT NOT NULL,
    descricao TEXT,
    status TEXT NOT NULL DEFAULT 'Em uso' CHECK (status IN ('Em uso', 'Devolvido', 'Desmobilizado')),
    proprietario_id INTEGER NOT NULL,
    usuario_atual_id INTEGER,
    local_atual_id INTEGER,
    projeto TEXT,
    data_aquisicao TEXT,
    data_status TEXT DEFAULT CURRENT_TIMESTAMP,
    observacoes TEXT,
    FOREIGN KEY (proprietario_id) REFERENCES empresas (id),
    FOREIGN KEY (usuario_atual_id) REFERENCES usuarios (id),
    FOREIGN KEY (local_atual_id) REFERENCES locais (id),
    CHECK ((status = 'Em uso' AND usuario_atual_id IS NOT NULL) OR (status != 'Em uso'))
);

-- Atributos dinâmicos por ativo (imei, teamviewer_id, ip, etc.)
CREATE TABLE atributos_ativos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ativo_id INTEGER NOT NULL,
    chave TEXT NOT NULL,
    valor TEXT,
    FOREIGN KEY (ativo_id) REFERENCES ativos (id) ON DELETE CASCADE,
    UNIQUE(ativo_id, chave)
);

-- Contratos de locação
CREATE TABLE contratos_locacao (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero_contrato TEXT UNIQUE NOT NULL,
    empresa_id INTEGER NOT NULL,
    data_inicio TEXT NOT NULL,
    data_fim TEXT,
    valor_total REAL NOT NULL,
    periodo_cobranca TEXT NOT NULL CHECK (periodo_cobranca IN ('mensal', 'semestral', 'anual', 'personalizado')),
    duracao_meses INTEGER,
    status TEXT DEFAULT 'Ativo' CHECK (status IN ('Ativo', 'Encerrado', 'Cancelado')),
    observacoes TEXT,
    FOREIGN KEY (empresa_id) REFERENCES empresas (id)
);

-- Relacionamento muitos-para-muitos: ativos ↔ contratos
CREATE TABLE ativos_contratos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ativo_id INTEGER NOT NULL,
    contrato_id INTEGER NOT NULL,
    data_vinculo TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ativo_id) REFERENCES ativos (id) ON DELETE CASCADE,
    FOREIGN KEY (contrato_id) REFERENCES contratos_locacao (id) ON DELETE CASCADE,
    UNIQUE(ativo_id, contrato_id)
);

-- Solicitações de novos ativos
CREATE TABLE solicitacoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo_solicitacao TEXT NOT NULL,
    descricao TEXT NOT NULL,
    quantidade INTEGER DEFAULT 1,
    especificacoes TEXT,
    setor_solicitante_id INTEGER NOT NULL,
    gestor_solicitante_id INTEGER NOT NULL,
    status TEXT DEFAULT 'Pendente' CHECK (status IN ('Pendente', 'Aprovado', 'Em Processamento', 'Concluido', 'Rejeitado')),
    prioridade TEXT DEFAULT 'Media' CHECK (prioridade IN ('Baixa', 'Media', 'Alta', 'Urgente')),
    data_solicitacao TEXT DEFAULT CURRENT_TIMESTAMP,
    aprovador_id INTEGER,
    executor_id INTEGER,
    FOREIGN KEY (setor_solicitante_id) REFERENCES setores (id),
    FOREIGN KEY (gestor_solicitante_id) REFERENCES usuarios (id),
    FOREIGN KEY (aprovador_id) REFERENCES usuarios (id),
    FOREIGN KEY (executor_id) REFERENCES usuarios (id)
);

-- Índices para performance
CREATE INDEX idx_ativos_status ON ativos(status);
CREATE INDEX idx_ativos_tipo ON ativos(tipo_ativo);
CREATE INDEX idx_ativos_proprietario ON ativos(proprietario_id);
CREATE INDEX idx_ativos_usuario ON ativos(usuario_atual_id);
CREATE INDEX idx_solicitacoes_status ON solicitacoes(status);
CREATE INDEX idx_locais_ambiente ON locais(ambiente);
CREATE INDEX idx_locais_predio ON locais(predio);