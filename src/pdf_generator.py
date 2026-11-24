# src/pdf_generator.py
from fpdf import FPDF
from datetime import datetime


class RelatorioAtivosPDF(FPDF):
    """Gerador de relatório PDF para lista de ativos (6 colunas)"""

    def __init__(self, filtros_aplicados=None):
        super().__init__(orientation='P', unit='mm', format='A4')  # Retrato
        self.filtros_aplicados = filtros_aplicados or {}
        self.set_auto_page_break(auto=True, margin=20)

    def header(self):
        self.set_font('Helvetica', 'B', 16)
        self.cell(0, 10, 'Relatório de Ativos - CTC INFRA', 0, 1, 'C')

        self.set_font('Helvetica', '', 10)
        data_hora = datetime.now().strftime('%d/%m/%Y %H:%M')
        self.cell(0, 6, f'Gerado em: {data_hora}', 0, 1, 'C')

        if self.filtros_aplicados:
            self.ln(2)
            self.set_font('Helvetica', 'I', 9)
            filtros_texto = ' | '.join([f'{k}: {v}' for k, v in self.filtros_aplicados.items() if v])
            if filtros_texto:
                self.cell(0, 5, f'Filtros: {filtros_texto}', 0, 1, 'C')

        self.ln(3)
        self.set_draw_color(0, 0, 0)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(3)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Página {self.page_no()}/{{nb}}', 0, 0, 'C')

    def _imprimir_cabecalho_tabela(self, colunas):
        self.set_font('Helvetica', 'B', 8)  # Fonte 8 para caber os títulos
        self.set_fill_color(41, 128, 185)   # Azul corporativo
        self.set_text_color(255, 255, 255)

        for col in colunas:
            self.cell(col['width'], 8, col['header'], 1, 0, 'C', 1)
        self.ln()
        self.set_text_color(0, 0, 0)

    def adicionar_tabela(self, ativos):
        if not ativos:
            self.set_font('Helvetica', 'I', 12)
            self.cell(0, 10, 'Nenhum ativo encontrado com os filtros aplicados.', 0, 1, 'C')
            return

        # ✅ 6 Colunas Otimizadas (Total: 180mm)
        colunas = [
            {'header': 'Código', 'width': 25, 'field': 'codigo_ativo', 'align': 'L'},
            {'header': 'Patrimônio', 'width': 25, 'field': 'patrimonio', 'align': 'L'},
            {'header': 'Nº Série', 'width': 30, 'field': 'numero_serie', 'align': 'L'},
            {'header': 'Proprietário', 'width': 35, 'field': 'proprietario_nome', 'align': 'L'},
            {'header': 'Usuário', 'width': 50, 'field': 'usuario_nome', 'align': 'L'},
        ]

        self._imprimir_cabecalho_tabela(colunas)

        self.set_font('Helvetica', '', 7)  # Fonte 7 para o conteúdo
        linha_alt = False

        for ativo in ativos:
            if self.get_y() > 270:
                self.add_page()
                self._imprimir_cabecalho_tabela(colunas)
                self.set_font('Helvetica', '', 7)
                linha_alt = False

            if linha_alt:
                self.set_fill_color(245, 248, 250)
            else:
                self.set_fill_color(255, 255, 255)

            altura_linha = 7

            for col in colunas:
                valor = ativo.get(col['field']) or '-'
                # Trunca texto longo para caber na célula
                max_chars = int(col['width'] / 1.5)
                if len(str(valor)) > max_chars:
                    valor = str(valor)[:max_chars - 2] + '...'

                self.cell(col['width'], altura_linha, str(valor), 1, 0, col['align'], 1)

            self.ln()
            linha_alt = not linha_alt

        # Rodapé com total
        self.ln(5)
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(0, 0, 0)
        self.cell(0, 8, f'Total de ativos: {len(ativos)}', 0, 1, 'L')


def gerar_pdf_ativos(ativos, filtros_aplicados=None):
    pdf = RelatorioAtivosPDF(filtros_aplicados)
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.adicionar_tabela(ativos)

    # Garante saída em bytes para o Flask
    pdf_bytes = pdf.output(dest='S')
    if isinstance(pdf_bytes, str):
        return pdf_bytes.encode('latin-1')

    return pdf_bytes