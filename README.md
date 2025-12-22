# Field Equipment Tracker

A lightweight, offline tool for civil engineering sites to manage IT assets (notebooks, desktops, monitors, Small PCs, printers, plotters) and generate printable responsibility terms upon delivery or return.

## Purpose
Replace manual Excel tracking with a fast, searchable interface and automated PDF term generation—designed for Tier-1 support staff with no internet, admin rights, or server access.

## Features
- **Search by multiple criteria**:  
  - Equipment type (`Notebook`, `Desktop`, `Monitor`, `Small PC`, etc.)  
  - Cost Center  
  - Current Location  
  - Sector  
  - User Name  
  - User Role  
- **View full equipment record**:  
  `Model`, `Serial Number`, `Asset ID`, `TeamViewer ID`, `User`, `Role`, `Cost Center`, `Sector`, `Current Location`, `Notes`  
- **Generate printable PDF term** on delivery/return:  
  - Pre-filled with equipment and user data  
  - Signature fields for user and technician  
  - Auto-saved with timestamp and action type  
- **100% offline** – runs on local Windows notebook (no cloud, no domain)

## Requirements
- Windows 10/11 (standard site notebook)  
- Python 3.8+  
- Install once:  
  ```bash
  pip install fpdf2

  
---

### 🇧🇷 **(Português)**

```markdown
# Field Equipment Tracker

Ferramenta leve e offline para canteiros de obra controlarem ativos de TI (notebooks, desktops, monitores, Small PCs, impressoras, plotters) e gerarem termos de responsabilidade impressos na entrega ou devolução.

## Objetivo
Substituir o controle manual em planilha por uma interface rápida, com busca simples e geração automática de termo em PDF — feita para suporte N1, sem internet, sem acesso administrativo e sem dependência de servidores.

## Funcionalidades
- **Busca por múltiplos critérios**:  
  - Tipo de equipamento (`Notebook`, `Desktop`, `Monitor`, `Small PC`, etc.)  
  - Centro de Custo  
  - Local Atual  
  - Setor  
  - Nome do Usuário  
  - Função do Usuário  
- **Exibe todos os dados do equipamento**:  
  `Modelo`, `Número de Série`, `Patrimônio`, `ID do TeamViewer`, `Usuário`, `Função`, `Centro de Custo`, `Setor`, `Local Atual`, `Observação`  
- **Gera PDF do termo na hora**:  
  - Dados pré-preenchidos  
  - Campos para assinatura do usuário e do técnico  
  - Salvo com data, hora e tipo de ação (entrega/devolução)  
- **Totalmente offline** – roda no notebook da obra (Windows 10/11)

## Requisitos
- Notebook com Windows 10/11  
- Python 3.8+  
- Executar uma vez:  
  ```bash
  pip install fpdf2