# core/pdf/summary.py
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from core.money import brl
from core.pdf.base import draw_header

def render_summary_pdf(out_path, quote: dict):
    c = canvas.Canvas(out_path, pagesize=A4)
    w, h = A4

    # Muda o título do cabeçalho
    draw_header(c, quote, "Proposta Comercial")

    y = h - 210
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, "O que será entregue (Serviços e Benefícios)")
    y -= 25

    for s in quote["servicos"]:
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y, f"• {s['service_name']}")
        y -= 16

        c.setFont("Helvetica", 11)
        # Pega a descrição focada no cliente (ou a completa se não tiver)
        texto_beneficios = s.get("summary_client", s.get("summary_full", "Serviço de instalação padrão."))
        
        # Quebra as linhas direitinho no PDF
        for line in texto_beneficios.split("\n"):
            c.drawString(55, y, line.strip())
            y -= 16
        y -= 10 # Espaço extra antes do próximo serviço

    y -= 10
    c.line(40, y, 550, y)
    y -= 35

    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, "Investimento Total")
    y -= 30
    c.setFont("Helvetica-Bold", 32)
    # Mostra apenas o totalzão final
    c.drawString(40, y, brl(float(quote["total"])))

    y -= 60
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y, "Condições")
    y -= 16
    c.setFont("Helvetica", 10)
    c.drawString(40, y, f"Pagamento: {quote.get('pagamento','')}")
    y -= 14
    c.drawString(40, y, f"Garantia: {quote.get('garantia','')}   |   Validade: {quote.get('validade_dias', 7)} dias")

    y -= 26
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y, "Dúvidas e Fechamento")
    y -= 16
    c.setFont("Helvetica", 10)
    c.drawString(40, y, f"Para aprovar o orçamento ou tirar dúvidas, me chame no WhatsApp: {quote.get('whatsapp','')}")

    c.save()
