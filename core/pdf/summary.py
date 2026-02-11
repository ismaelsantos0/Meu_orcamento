from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from core.money import brl


def render_summary_pdf(out_path: str, quote: dict):
    c = canvas.Canvas(out_path, pagesize=A4)
    w, h = A4

    # Header simples
    from core.pdf.base import draw_header
    draw_header(c, quote, "Orçamento (Resumo)")

    y = h - 210
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y, "Serviços incluídos")
    y -= 16

    c.setFont("Helvetica", 10)
    for s in quote["servicos"]:
        c.drawString(40, y, f"• {s['service_name']}")
        y -= 14

    y -= 18
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "Valor final")
    y -= 34
    c.setFont("Helvetica-Bold", 34)
    c.drawString(40, y, brl(float(quote["total"])))

    y -= 50
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y, "Condições")
    y -= 16
    c.setFont("Helvetica", 10)
    c.drawString(40, y, f"Pagamento: {quote.get('pagamento','')}")
    y -= 14
    c.drawString(40, y, f"Garantia: {quote.get('garantia','')} | Validade: {quote.get('validade_dias', 7)} dias")

    y -= 26
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y, "Fechamento")
    y -= 16
    c.setFont("Helvetica", 10)
    c.drawString(40, y, f"Para confirmar e agendar, me chame no WhatsApp: {quote.get('whatsapp','')}")

    c.save()
