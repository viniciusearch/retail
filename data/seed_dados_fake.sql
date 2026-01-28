-- Empresas (proprietária + fornecedores)
INSERT INTO empresas (nome, tipo) VALUES
('Minha Empresa', 'propria'),
('CTC INFRA', 'fornecedor'),
('ARKLOK', 'fornecedor'),
('A2WORKS', 'fornecedor');

-- Cargos básicos
INSERT INTO cargos (nome) VALUES
('ENGENHEIRO CIVIL SR'),
('ARQUITETO PL'),
('TECNICO DE SEGURANCA DO TRABALHO'),
('GERENTE DE PROJETOS'),
('COORDENADOR DE TI'),
('ANALISTA DE SUPORTE'),
('ENCARREGADO DE ALMOXARIFADO'),
('ASSISTENTE ADMINISTRATIVO');

-- Setores
INSERT INTO setores (nome) VALUES
('ENGENHARIA'),
('ARQUITETURA'),
('SSMA'),
('TI'),
('ADMINISTRATIVO'),
('ALMOXARIFADO'),
('PROJETOS');

-- Locais (hierarquia correta - RESPEITANDO A RESTRIÇÃO CHECK)
-- Canteiro (ambiente != 'obra' → predio = NULL)
INSERT INTO locais (nome, codigo, ambiente, predio, setor, tipo_local) VALUES
('SMS TERRENO', 'CANTEIRO-SMS', 'canteiro', NULL, 'SSMA', 'canteiro'),
('ALMOXARIFADO TERRENO', 'CANTEIRO-ALMOX', 'canteiro', NULL, 'ALMOXARIFADO', 'almoxarifado');

-- Obra TB09 (ambiente = 'obra' → predio = 'TB09')
INSERT INTO locais (nome, codigo, ambiente, predio, setor, tipo_local) VALUES
('SMS OBRA TB09', 'TB09-SMS', 'obra', 'TB09', 'SSMA', 'escritorio'),
('ENGENHARIA TB09', 'TB09-ENG', 'obra', 'TB09', 'ENGENHARIA', 'escritorio'),
('ARQUITETURA TB09', 'TB09-ARQ', 'obra', 'TB09', 'ARQUITETURA', 'escritorio'),
('TI TB09', 'TB09-TI', 'obra', 'TB09', 'TI', 'ti'),
('ADMINISTRACAO TB09', 'TB09-ADM', 'obra', 'TB09', 'ADMINISTRATIVO', 'escritorio');

-- Obra TB10 (ambiente = 'obra' → predio = 'TB10')
INSERT INTO locais (nome, codigo, ambiente, predio, setor, tipo_local) VALUES
('SMS OBRA TB10', 'TB10-SMS', 'obra', 'TB10', 'SSMA', 'escritorio'),
('ENGENHARIA TB10', 'TB10-ENG', 'obra', 'TB10', 'ENGENHARIA', 'escritorio'),
('ARQUITETURA TB10', 'TB10-ARQ', 'obra', 'TB10', 'ARQUITETURA', 'escritorio');

-- Sede (ambiente != 'obra' → predio = NULL)
INSERT INTO locais (nome, codigo, ambiente, predio, setor, tipo_local) VALUES
('SEDE GERAL', 'SEDE-GERAL', 'sede', NULL, 'GERAL', 'escritorio');

-- Perfis de usuário
INSERT INTO perfis_usuario (nome, nivel_acesso) VALUES
('Administrador', 4),
('Gestor', 3),
('Tecnico', 2),
('Usuario', 1);

-- Usuários fake
INSERT INTO usuarios (nome_completo, email, cargo_id, setor_id, local_padrao_id, perfil_id) VALUES
('CARLOS MENDES', 'carlos.mendes@empresa.com', 1, 1, 4, 3),  -- Engenheiro TB09
('ANA SILVA', 'ana.silva@empresa.com', 2, 2, 5, 3),        -- Arquiteta TB09  
('ROBERTO SANTOS', 'roberto.santos@empresa.com', 3, 3, 1, 2), -- Técnico SSMA
('MARIANA COSTA', 'mariana.costa@empresa.com', 4, 6, 10, 3), -- Gerente Sede
('LUCAS OLIVEIRA', 'lucas.oliveira@empresa.com', 5, 4, 6, 2), -- TI TB09
('FERNANDA LIMA', 'fernanda.lima@empresa.com', 7, 6, 1, 2),  -- Almoxarifado
('PAULO RODRIGUES', 'paulo.rodrigues@empresa.com', 8, 5, 7, 1); -- Assistente TB09

-- Ativos fake - Hardware
INSERT INTO ativos (codigo_ativo, tipo_ativo, categoria, descricao, status, proprietario_id, usuario_atual_id, local_atual_id, projeto, data_aquisicao, observacoes) VALUES
('NB-PAT001', 'hardware', 'Notebook', 'LENOVO THINKPAD E14 I5 16GB SSD', 'Em uso', 1, 1, 4, 'SCALA DATACENTER TB09', '2024-01-15', NULL),
('NB-PAT002', 'hardware', 'Notebook', 'DELL LATITUDE 5420 I7 32GB SSD', 'Em uso', 1, 2, 5, 'SCALA DATACENTER TB09', '2024-01-20', NULL),
('TAB-PAT003', 'hardware', 'Tablet', 'IPAD AIR 10.9" 64GB WIFI', 'Em uso', 1, 3, 1, 'SCALA DATACENTER TB09', '2024-02-01', NULL),
('DT-PAT004', 'hardware', 'Desktop', 'DELL OPTIPLEX 7090 I5 16GB SSD', 'Em uso', 1, 5, 6, 'SCALA DATACENTER TB09', '2024-01-10', NULL),
('MON-PAT005', 'periferico', 'Monitor', 'DELL P2422H 24" FULL HD', 'Em uso', 1, 1, 4, 'SCALA DATACENTER TB09', '2024-01-15', NULL),
('MON-PAT006', 'periferico', 'Monitor', 'DELL P2422H 24" FULL HD', 'Em uso', 1, 2, 5, 'SCALA DATACENTER TB09', '2024-01-20', NULL),
('MON-PAT007', 'periferico', 'Monitor', 'DELL P2422H 24" FULL HD', 'Em uso', 1, 5, 6, 'SCALA DATACENTER TB09', '2024-01-10', NULL);

-- Ativos fake - Software (Licenças)
INSERT INTO ativos (codigo_ativo, tipo_ativo, categoria, descricao, status, proprietario_id, usuario_atual_id, local_atual_id, projeto, data_aquisicao, observacoes) VALUES
('LIC-AUTOCAD-001', 'software', 'AutoCAD', 'AUTOCAD 2024 LICENÇA PERPÉTUA', 'Em uso', 1, 1, 4, 'SCALA DATACENTER TB09', '2024-01-15', NULL),
('LIC-REVIT-001', 'software', 'Revit', 'REVIT 2024 LICENÇA ANUAL', 'Em uso', 1, 2, 5, 'SCALA DATACENTER TB09', '2024-01-20', NULL),
('LIC-SKETCHUP-001', 'software', 'SketchUp Pro', 'SKETCHUP PRO 2024 LICENÇA ANUAL', 'Em uso', 1, 2, 5, 'SCALA DATACENTER TB09', '2024-01-20', NULL);

-- Ativos fake - Mobiliário
INSERT INTO ativos (codigo_ativo, tipo_ativo, categoria, descricao, status, proprietario_id, usuario_atual_id, local_atual_id, projeto, data_aquisicao, observacoes) VALUES
('MOB-CAD-001', 'mobiliario', 'Cadeira', 'CADEIRA ERGONÔMICA EXECUTIVA PRETA', 'Em uso', 1, 1, 4, 'SCALA DATACENTER TB09', '2024-01-15', NULL),
('MOB-CAD-002', 'mobiliario', 'Cadeira', 'CADEIRA ERGONÔMICA EXECUTIVA PRETA', 'Em uso', 1, 2, 5, 'SCALA DATACENTER TB09', '2024-01-20', NULL),
('MOB-MESA-001', 'mobiliario', 'Mesa', 'MESA DE DESENHO TÉCNICO 120X80CM', 'Em uso', 1, 2, 5, 'SCALA DATACENTER TB09', '2024-01-20', NULL);

-- Ativos fake - Equipamentos de Campo
INSERT INTO ativos (codigo_ativo, tipo_ativo, categoria, descricao, status, proprietario_id, usuario_atual_id, local_atual_id, projeto, data_aquisicao, observacoes) VALUES
('EQP-ESTACAO-001', 'hardware', 'Estação Total', 'LEICA TS16 ESTAÇÃO TOTAL ROBÓTICA', 'Em uso', 2, 1, 4, 'SCALA DATACENTER TB09', '2024-02-01', 'LOCADO - CONTRATO CT2024-001'),
('EQP-NIVEL-001', 'hardware', 'Nível Digital', 'LEICA LS15 NÍVEL DIGITAL AUTOMÁTICO', 'Em uso', 2, 1, 4, 'SCALA DATACENTER TB09', '2024-02-01', 'LOCADO - CONTRATO CT2024-001');

-- Ativos fake - Disponíveis (Devolvidos)
INSERT INTO ativos (codigo_ativo, tipo_ativo, categoria, descricao, status, proprietario_id, usuario_atual_id, local_atual_id, projeto, data_aquisicao, observacoes) VALUES
('NB-PAT008', 'hardware', 'Notebook', 'HP ELITEBOOK 840 G8 I5 16GB SSD', 'Devolvido', 1, NULL, 1, NULL, '2024-01-25', 'DISPONÍVEL PARA NOVA ATRIBUIÇÃO'),
('MON-PAT009', 'periferico', 'Monitor', 'LG 27UK850-W 27" 4K', 'Devolvido', 1, NULL, 1, NULL, '2024-01-25', 'DISPONÍVEL PARA NOVA ATRIBUIÇÃO');

-- Ativos fake - Desmobilizados
INSERT INTO ativos (codigo_ativo, tipo_ativo, categoria, descricao, status, proprietario_id, usuario_atual_id, local_atual_id, projeto, data_aquisicao, observacoes) VALUES
('NB-PAT010', 'hardware', 'Notebook', 'DELL LATITUDE E7470 I5 8GB SSD', 'Desmobilizado', 1, NULL, NULL, NULL, '2022-06-10', 'DANIFICADO - DESCARTADO EM 2024-03-15');

-- Atributos específicos para ativos
-- Notebook CARLOS MENDES
INSERT INTO atributos_ativos (ativo_id, chave, valor) VALUES
(1, 'numero_serie', 'SN123456789'),
(1, 'host_name', 'DESKTOP-CARLOS'),
(1, 'teamviewer_id', '123 456 789');

-- Notebook ANA SILVA  
INSERT INTO atributos_ativos (ativo_id, chave, valor) VALUES
(2, 'numero_serie', 'SN987654321'),
(2, 'host_name', 'DESKTOP-ANA'),
(2, 'teamviewer_id', '987 654 321');

-- Tablet ROBERTO SANTOS
INSERT INTO atributos_ativos (ativo_id, chave, valor) VALUES
(3, 'numero_serie', 'SN555666777'),
(3, 'imei', '356938035643809'),
(3, 'chip', 'TIM 99999-9999');

-- Licenças
INSERT INTO atributos_ativos (ativo_id, chave, valor) VALUES
(8, 'chave_licenca', 'XXXX-XXXX-XXXX-XXXX'),
(8, 'versao', '2024'),
(8, 'data_expiracao', '2029-01-15'),
(8, 'tipo_licenca', 'Perpétua');

INSERT INTO atributos_ativos (ativo_id, chave, valor) VALUES
(9, 'chave_licenca', 'YYYY-YYYY-YYYY-YYYY'),
(9, 'versao', '2024'),
(9, 'data_expiracao', '2025-01-20'),
(9, 'tipo_licenca', 'Anual');

-- Contratos de locação
INSERT INTO contratos_locacao (numero_contrato, empresa_id, data_inicio, data_fim, valor_total, periodo_cobranca, duracao_meses) VALUES
('CT2024-001', 2, '2024-02-01', '2025-01-31', 24000.00, 'anual', 12);

-- Vincular ativos ao contrato
INSERT INTO ativos_contratos (ativo_id, contrato_id) VALUES
(13, 1),
(14, 1);

-- Solicitações fake
INSERT INTO solicitacoes (tipo_solicitacao, descricao, quantidade, setor_solicitante_id, gestor_solicitante_id, status, prioridade) VALUES
('hardware', 'Notebook para novo engenheiro', 1, 1, 4, 'Pendente', 'Alta'),
('software', 'Licença AutoCAD adicional', 1, 2, 4, 'Aprovado', 'Media'),
('periferico', 'Monitores 4K para arquitetura', 2, 2, 4, 'Pendente', 'Media');