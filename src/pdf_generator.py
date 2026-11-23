# src/pdf_generator.py - RELATÓRIO COM 6 COLUNAS
from fpdf import FPDF
from datetime import datetime


class RelatorioAtivosPDF(FPDF):
    """Gerador de relatório PDF para lista de ativos (6 colunas)"""

    def __init__(self, filtros_aplicados=None):
        super().__init__(orientation='P', unit='mm', format='A4')  # Retrato
        self.filtros_aplicados = filtros_aplicados or {}
        self.set_auto_page_break(auto=True, margin=20)

    def header(self):
        # Cabeçalho em todas as páginas
        self.set_font('Helvetica', 'B', 16)
        self.cell(0, 10, 'Relatório de Ativos - CTC INFRA', align='C', new_x="LMARGIN", new_y="NEXT")

        self.set_font('Helvetica', '', 10)
        data_hora = datetime.now().strftime('%d/%m/%Y %H:%M')
        self.cell(0, 6, f'Gerado em: {data_hora}', align='C', new_x="LMARGIN", new_y="NEXT")

        if self.filtros_aplicados:
            self.ln(2)
            self.set_font('Helvetica', 'I', 9)
            filtros_texto = ' | '.join([f'{k}: {v}' for k, v in self.filtros_aplicados.items() if v])
            if filtros_texto:
                self.cell(0, 5, f'Filtros: {filtros_texto}', align='C', new_x="LMARGIN", new_y="NEXT")

        self.ln(3)
        self.set_draw_color(0, 0, 0)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(3)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Página {self.page_no()}/{{nb}}', align='C')

    def _imprimir_cabecalho_tabela(self, colunas):
        """Imprime o cabeçalho da tabela"""
        self.set_font('Helvetica', 'B', 9)
        self.set_fill_color(41, 128, 185)  # Azul corporativo
        self.set_text_color(255, 255, 255)

        for col in colunas:
            self.cell(col['width'], 8, col['header'], border=1, fill=True, align='C')
        self.ln()

        # Restaura cor do texto
        self.set_text_color(0, 0, 0)

    def adicionar_tabela(self, ativos):
        """Adiciona a tabela de ativos ao PDF (6 colunas)"""
        if not ativos:
            self.set_font('Helvetica', 'I', 12)
            self.cell(0, 10, 'Nenhum ativo encontrado com os filtros aplicados.', align='C', new_x="LMARGIN", new_y="NEXT")
            return

        # ✅ Definição das 6 colunas (larguras em mm) - A4 retrato = 190mm útil
        # Total: 30 + 40 + 30 + 25 + 40 + 25 = 190mm
        colunas = [
            {'header': 'Código', 'width': 30, 'field': 'codigo_ativo', 'align': 'L'},
            {'header': 'Categoria', 'width': 40, 'field': 'categoria', 'align': 'L'},
            {'header': 'Status', 'width': 30, 'field': 'status', 'align': 'C'},
            {'header': 'Prop.', 'width': 25, 'field': 'proprietario_nome', 'align': 'L'},  # ✅ Reduzido
            {'header': 'Usuário', 'width': 40, 'field': 'usuario_nome', 'align': 'L'},     # ✅ Novo
            {'header': 'Local', 'width': 25, 'field': 'local_nome', 'align': 'L'},
        ]

        # Cabeçalho da tabela
        self._imprimir_cabecalho_tabela(colunas)

        # Dados
        self.set_font('Helvetica', '', 7)  # ✅ Fonte menor para caber mais texto
        linha_alt = False

        for ativo in ativos:
            # Verifica se precisa de nova página
            if self.get_y() > 270:
                self.add_page()
                self._imprimir_cabecalho_tabela(colunas)
                self.set_font('Helvetica', '', 7)
                linha_alt = False

            # Cor alternada para melhor leitura
            if linha_alt:
                self.set_fill_color(245, 248, 250)
            else:
                self.set_fill_color(255, 255, 255)

            altura_linha = 7

            for col in colunas:
                valor = ativo.get(col['field']) or '-'
                # Trunca texto longo para caber na célula (fator ajustado para fonte 7)
                max_chars = int(col['width'] / 1.6)
                if len(str(valor)) > max_chars:
                    valor = str(valor)[:max_chars - 2] + '...'

                self.cell(col['width'], altura_linha, str(valor), border=1, fill=True, align=col['align'])

            self.ln()
            linha_alt = not linha_alt

        # Rodapé com total
        self.ln(5)
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(0, 0, 0)
        self.cell(0, 8, f'Total de ativos: {len(ativos)}', new_x="LMARGIN", new_y="NEXT")


def gerar_pdf_ativos(ativos, filtros_aplicados=None):
    """
    Gera o PDF e retorna os bytes para download.

    Args:
        ativos: Lista de dicionários com dados dos ativos
        filtros_aplicados: Dict com filtros para exibir no cabeçalho

    Returns:
        bytes do PDF
    """
    pdf = RelatorioAtivosPDF(filtros_aplicados)
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.adicionar_tabela(ativos)

    # ✅ CORREÇÃO CRÍTICA: Força a saída como bytes (latin-1) para o Flask
    pdf_bytes = pdf.output(dest='S')
    if isinstance(pdf_bytes, str):
        return pdf_bytes.encode('latin-1')

    return pdf_bytes