# Field Equipment Tracker

A lightweight, offline tool for civil engineering sites to manage IT equipment assignments (laptops, printers, plotters) and generate printable responsibility terms upon delivery or return.

## Purpose
Replace manual Excel tracking with a fast, searchable interface and automated PDF term generation—designed for Tier-1 support staff with no internet, admin rights, or server access.

## Features
- **Search** by:  
  - Serial Number  
  - Asset ID (Patrimônio)  
  - User Name  
  - Cost Center / Sector / Current Location  
- **View full equipment record**:  
  `Model`, `Serial`, `Asset ID`, `TeamViewer ID`, `User`, `Role`, `Cost Center`, `Sector`, `Current Location`, `Notes`  
- **Generate printable PDF term** on delivery/return:  
  - Pre-filled with equipment and user data  
  - Signature fields for user and technician  
  - Auto-saved with timestamp and action type  
- **100% offline** – runs on local Windows notebook (no cloud, no domain)

## Requirements
- Windows 10/11 (standard site notebook)  
- Python 3.8+  
- `pip install fpdf2`

## Setup
1. Clone this repo  
2. Place your initial equipment list in `data/equipamentos.db` (or import from Excel once via script)  
3. Run:  
   ```bash
   python src/main.py

   # Field Equipment Tracker

Ferramenta leve e offline para canteiros de obra controlarem equipamentos de TI (notebooks, impressoras, plotters) e gerarem termos de responsabilidade impressos na entrega ou devolução.

## Objetivo
Substituir o controle manual em planilha por uma interface rápida, com busca simples e geração automática de termo em PDF — feita para suporte N1, sem internet, sem acesso administrativo e sem dependência de servidores.

## Funcionalidades
- **Busca por**:  
  - Número de Série  
  - Patrimônio  
  - Nome do Usuário  
  - Centro de Custo / Setor / Local Atual  
- **Exibe todos os dados do equipamento**:  
  `Modelo`, `Série`, `Patrimônio`, `ID do TeamViewer`, `Usuário`, `Função`, `Centro de Custo`, `Setor`, `Local Atual`, `Observação`  
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