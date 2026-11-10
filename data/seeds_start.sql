-- ============================================================================
-- SEED MÍNIMO - DADOS ESSENCIAIS PARA INICIAR O SISTEMA
-- ============================================================================

-- ============================================================================
-- EMPRESAS (apenas CTC INFRA por enquanto)
-- ============================================================================
INSERT INTO empresas (nome, tipo) VALUES
('CTC INFRA', 'propria');

-- ============================================================================
-- CARGOS (lista básica - expandir conforme demanda)
-- ============================================================================
INSERT INTO cargos (nome, descricao) VALUES
('ENGENHEIRO DE SEGURANCA DO TRABALHO', 'Engenheiro SSMA'),
('TECNICO DE SEGURANCA DO TRABALHO', 'Técnico SSMA'),
('ENGENHEIRO CIVIL', 'Engenharia'),
('ANALISTA DE SUPORTE', 'TI'),
('ASSISTENTE ADMINISTRATIVO', 'Administrativo'),
('ENCARREGADO DE ALMOXARIFADO', 'Almoxarifado');

-- ============================================================================
-- SETORES (lista básica baseada no CSV real)
-- ============================================================================
INSERT INTO setores (nome, descricao, sigla) VALUES
('ENGENHARIA', 'Departamento de Engenharia', 'ENG'),
('SSMA', 'Segurança, Saúde e Meio Ambiente', 'SSMA'),
('PRODUCAO', 'Departamento de Produção', 'PROD'),
('ADMINISTRATIVO', 'Departamento Administrativo', 'ADM'),
('GERENCIA', 'Gerência da Obra', 'GER'),
('QUALIDADE', 'Controle de Qualidade', 'QUAL'),
('TI', 'Tecnologia da Informação', 'TI'),
('ALMOXARIFADO', 'Almoxarifado', 'ALM');

-- ============================================================================
-- LOCAIS FÍSICOS (locais básicos para começar)
-- ============================================================================

-- Canteiro (ambiente = 'canteiro' → predio = NULL)
INSERT INTO locais (nome, codigo, ambiente, predio, setor, tipo_local) VALUES
('SMS TERRENO', 'CAN-SMS', 'canteiro', NULL, 'SSMA', 'canteiro'),
('ALMOXARIFADO TERRENO', 'CAN-ALM', 'canteiro', NULL, 'ALMOXARIFADO', 'almoxarifado');

-- Obra TB09 (ambiente = 'obra' → predio = 'TB09')
INSERT INTO locais (nome, codigo, ambiente, predio, setor, tipo_local) VALUES
('SMS OBRA TB09', 'TB09-SMS', 'obra', 'TB09', 'SSMA', 'escritorio'),
('PRODUCAO TB09', 'TB09-PROD', 'obra', 'TB09', 'PRODUCAO', 'escritorio'),
('CUSTOS E MEDICOES', 'TB09-CM', 'obra', 'TB09', 'ENGENHARIA', 'escritorio'),
('GERENCIA TB09', 'TB09-GER', 'obra', 'TB09', 'GERENCIA', 'escritorio'),
('CPD TI', 'TB09-TI', 'obra', 'TB09', 'TI', 'ti'),
('SUPRIMENTOS', 'TB09-SUP', 'obra', 'TB09', 'ADMINISTRATIVO', 'escritorio');

-- Sede (ambiente = 'sede' → predio = NULL)
INSERT INTO locais (nome, codigo, ambiente, predio, setor, tipo_local) VALUES
('CTC SEDE', 'SEDE-CTC', 'sede', NULL, 'ENGENHARIA', 'escritorio');

-- ============================================================================
-- PERFIS DE USUÁRIO
-- ============================================================================
INSERT INTO perfis_usuario (nome, nivel_acesso, descricao) VALUES
('Administrador', 4, 'Acesso total ao sistema'),
('Gestor', 3, 'Acesso a relatórios e aprovações'),
('Tecnico', 2, 'Acesso operacional'),
('Usuario', 1, 'Acesso básico');

-- ============================================================================
-- USUÁRIO ADMINISTRADOR INICIAL
-- ============================================================================
-- Email: admin@ctcinfra.com.br
-- Senha: admin123
INSERT INTO usuarios (nome_completo, email, senha_hash, perfil_id, status) VALUES
('ADMINISTRADOR', 'admin@ctcinfra.com.br', 
 '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9', 
 1, 'Ativo');

-- ============================================================================
-- VERIFICAÇÃO
-- ============================================================================
-- Após executar, verifique com:
-- SELECT COUNT(*) FROM empresas;      -- Deve retornar 1
-- SELECT COUNT(*) FROM setores;       -- Deve retornar 8
-- SELECT COUNT(*) FROM locais;        -- Deve retornar 11
-- SELECT COUNT(*) FROM usuarios;      -- Deve retornar 1
-- SELECT COUNT(*) FROM ativos;        -- Deve retornar 0 (banco limpo)