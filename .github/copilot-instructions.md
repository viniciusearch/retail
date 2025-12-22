## Visão geral

Este repositório implementa uma ferramenta leve e offline para controlar ativos de TI e gerar termos em PDF. A lógica principal fica em `src/` (entrada em `src/main.py`) e a geração de PDF deve usar `fpdf2` conforme indicado em [README.md](README.md).

## Objetivo do agente

Ajude a manter e evoluir uma aplicação Python que: busca/filtra equipamentos, persiste/consulta dados locais (em `data/`) e gera PDFs em `output/` via `src/pdf_generator.py`.

## Padrões e expectativas locais
- Código em Python 3.8+; dependência única documentada: `fpdf2` (instalar com `pip install fpdf2`).
- Estrutura de módulos: `src/main.py` (entrypoint), `src/db_manager.py` (acesso/transformação de dados), `src/pdf_generator.py` (montagem e salvamento de PDFs).
- Projeto é 100% offline — não adicionar chamadas externas nem dependências que exigem internet por runtime.

## Fluxo de dados (alto nível)
- Entrada: arquivos/registro em `data/` (CSV/JSON/DB local) — agente deve inspecionar esse diretório antes de mudanças.
- Processamento: `src/db_manager.py` realiza consultas/filtragens; `src/main.py` orquestra UI/CLI e chama `pdf_generator` para criar o termo.
- Saída: PDFs gerados em `output/` com nome contendo timestamp e tipo de ação (entrega/devolução).

## Exemplos concretos para mudanças
- Ao adicionar uma função de filtro, atualize `src/db_manager.py` e escreva uma função de teste manual (pequeno script) que consome `data/`.
- Ao alterar layout de PDF, modifique `src/pdf_generator.py` e verifique que o arquivo gerado aparece em `output/` com timestamp.

## Fluxo de desenvolvimento e comandos úteis
- Instalar dependências: `pip install fpdf2`
- Executar (esperado): `python src/main.py` ou `python -m src.main` (verificar se `src/main.py` tem guard `if __name__ == "__main__"`).
- Não há suíte de testes definida; adicionar testes unitários é aceitável, mas prefira pequenas mudanças incrementais e verificação local com arquivos em `data/`.

## Convenções específicas deste repositório
- Prefira mudanças pequenas e comentadas no `README.md` em português e inglês (o README atual contém ambas).
- Mantenha compatibilidade com Windows (paths, encoding). Evitar dependências que exijam permissões administrativas.

## Integrações e pontos sensíveis
- Gerador de PDF: `fpdf2` — modificar layout apenas via `src/pdf_generator.py`.
- Persistência local: inspecionar `data/` antes de sobrescrever; não presumir um DB remoto.

## Comportamentos a evitar
- Não adicionar chamadas de rede nem uso de serviços externos.
- Não mudar a compatibilidade de versão do Python sem justificar (projeto documenta 3.8+).

## Perguntas rápidas ao autor (quando incerto)
- Onde estão os arquivos de dados de exemplo em `data/`? (ex.: CSV vs JSON)
- Deseja suporte multiplataforma além de Windows (Linux/macOS)?

Se quiser, eu posso adaptar estas instruções (resumir, traduzir, ou incluir exemplos de codificação). Diga o que ajustar.
