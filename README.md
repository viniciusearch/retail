# Sistema completo para gestão de ativos de TI

Sistema com funcionalidades para cadastro, atualização, visualização, exclusão e relatórios de equipamentos.

## 📋 Funcionalidades

- Cadastro de equipamentos com campos técnicos (patrimônio, tipo, descritivo, número de série, etc.)
- Atualização em lote de status (**Em uso** / **Devolvido**)
- Exclusão individual e em lote de ativos
- Visualização detalhada com modal editável
- Filtros avançados por tipo, status, patrimônio, usuário, local, etc.
- Exportação de relatórios em **CSV** e **PDF**
- Dashboard interativo com gráficos e métricas
- Ordenação e reorganização de colunas (**DataTables + ColReorder**)
- Busca integrada com DataTables
- Cadastro rápido via modal em qualquer página

## 🛠️ Tecnologias Utilizadas

- **Backend**: Python 3.8+, Flask  
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5, DataTables  
- **Banco de dados**: SQLite  
- **Bibliotecas**: Chart.js, jsPDF, jQuery  

## 📥 Pré-requisitos

- Python 3.8 ou superior  
- `pip` (gerenciador de pacotes do Python)

## 🚀 Instalação

### Linux / macOS

```bash
# 1. Clone o repositório
git clone https://github.com/seu-usuario/sistema-equipamentos.git
cd sistema-equipamentos

# 2. Crie um ambiente virtual (recomendado)
python3 -m venv venv
source venv/bin/activate  # Linux/macOS

# 3. Instale as dependências
pip install -r requirements.txt
```

### Windows

```cmd
# 1. Clone o repositório
git clone https://github.com/seu-usuario/sistema-equipamentos.git
cd sistema-equipamentos

# 2. Crie um ambiente virtual (recomendado)
python -m venv venv
venv\Scripts\activate

# 3. Instale as dependências
pip install -r requirements.txt
```
## 🔧 Arquivos de Configuração
- requirements.txt
- app.py (exemplo)
- init_db.py (exemplo)  
 
 Exemplo de init_db.py:

```python
import sqlite3
import os

DB_PATH = 'data/equipamentos.db'

# Cria diretório se não existir
os.makedirs('data', exist_ok=True)

# Cria tabela
conn = sqlite3.connect(DB_PATH)
# ... (lógica de criação da tabela)
```

## 🌐 Acesso à Aplicação
Após iniciar a aplicação, acesse:

Local: http://localhost:5000  
Codespace: https://[seu-codespace]-5000.app.github.dev

## 🗂️ Estrutura de Diretórios

```dir
sistema-equipamentos/
├── app.py                 # Ponto de entrada da aplicação
├── init_db.py             # Script de inicialização do banco
├── requirements.txt       # Dependências do Python
├── data/
│   └── equipamentos.db    # Banco de dados SQLite
├── src/
│   ├── routes.py          # Rotas da API
│   ├── models.py          # Lógica de acesso ao banco
│   └── web.py             # Rotas web
```

## 🎯 Uso Básico
- Acesse o dashboard para visão geral dos equipamentos
- Clique em "Novo Ativo" para cadastrar equipamentos
- Use a página "Gerenciar" para:
    - Filtrar equipamentos por diversos critérios
    - Atualizar status em lote
    - Excluir ativos indesejados
    - Exportar relatórios
- Clique no ícone de olho para visualizar/editar detalhes
- Use o campo de busca para encontrar equipamentos rapidamente

## 🔒 Segurança
- Exclusão permanente requer confirmação explícita
- Validação de campos obrigatórios no frontend e backend
- Proteção contra duplicação de patrimônio
- Métodos HTTP apropriados (DELETE para exclusão, PATCH para atualização)

## 📊 Relatórios Disponíveis
### CSV
- Todos os campos do equipamento
- Compatível com Excel e planilhas
### PDF
- Agrupado por tipo de equipamento
- Inclui Descritivo, Patrimônio e Número de Série
- Formato profissional para impressão

## 🔄 Atualizações Futuras
- Paginação na API (server-side)
- Histórico de alterações
- Backup automático do banco
- Autenticação de usuários

## 🆘 Suporte
Para problemas de instalação ou uso:

- Verifique se todas as dependências estão instaladas
- Confirme se o banco de dados foi inicializado
- Consulte o console do navegador para erros JavaScript
- Verifique o terminal para erros do servidor