from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from core.money import brl
from core.pdf.base import draw_header


def render_complete_pdf(out_path: str, quote: dict):
    c = canvas.Canvas(out_path, pagesize=A4)
    w, h = A4

    draw_header(c, quote, "Orçamento (Completo)")
    y = h - 210

    # Resumo dos serviços
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y, "Resumo dos serviços")
    y -= 14

    c.setFont("Helvetica-Bold", 9)
    c.drawString(40, y, "Serviço")
    c.drawRightString(550, y, "Subtotal")
    y -= 8
    c.line(40, y, 550, y)
    y -= 14

    c.setFont("Helvetica", 9)
    for s in quote["servicos"]:
        if y < 130:
            c.showPage()
            draw_header(c, quote, "Orçamento (Completo)")
            y = h - 210

            c.setFont("Helvetica-Bold", 11)
            c.drawString(40, y, "Resumo dos serviços (continuação)")
            y -= 14
            c.setFont("Helvetica-Bold", 9)
            c.drawString(40, y, "Serviço")
            c.drawRightString(550, y, "Subtotal")
            y -= 8
            c.line(40, y, 550, y)
            y -= 14
            c.setFont("Helvetica", 9)

        c.drawString(40, y, s["service_name"][:65])
        c.drawRightString(550, y, brl(float(s["subtotal"])))
        y -= 14

    y -= 6
    c.line(40, y, 550, y)
    y -= 18

    c.setFont("Helvetica-Bold", 10)
    c.drawRightString(550, y, f"Subtotal: {brl(float(quote['subtotal']))}")
    y -= 14
    if quote["desconto_valor"] > 0:
        c.drawRightString(550, y, f"Desconto ({quote['desconto_label']}): - {brl(float(quote['desconto_valor']))}")
        y -= 14

    c.setFont("Helvetica-Bold", 12)
    c.drawRightString(550, y, f"TOTAL: {brl(float(quote['total']))}")

    # Condições
    y -= 28
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y, "Condições")
    y -= 16
    c.setFont("Helvetica", 10)
    c.drawString(40, y, f"Pagamento: {quote.get('pagamento','')}")
    y -= 14
    c.drawString(40, y, f"Garantia: {quote.get('garantia','')}")
    y -= 14
    c.drawString(40, y, f"Validade do orçamento: {quote.get('validade_dias', 7)} dias")

    # Detalhamento por serviço
    for idx, s in enumerate(quote["servicos"], start=1):
        c.showPage()
        draw_header(c, quote, f"Detalhamento — Serviço {idx}")

        y = h - 210
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y, s["service_name"])
        y -= 18

        c.setFont("Helvetica-Bold", 11)
        c.drawString(40, y, "O que será entregue")
        y -= 16

        c.setFont("Helvetica", 10)
        for line in s["summary_full"].split("\n"):
            line = line.strip()
            if not line:
                continue
            c.drawString(40, y, line[:110])
            y -= 14

        y -= 8
        c.setFont("Helvetica-Bold", 11)
        c.drawString(40, y, "Composição (materiais / serviços)")
        y -= 14

        c.setFont("Helvetica-Bold", 9)
        c.drawString(40, y, "Descrição")
        c.drawString(300, y, "Qtd")
        c.drawString(350, y, "Unit")
        c.drawString(430, y, "Subtotal")
        y -= 10
        c.line(40, y, 550, y)
        y -= 14

        c.setFont("Helvetica", 9)
        for item in s["items"]:
            desc, qtd, unit, sub = item["desc"], item["qty"], item["unit"], item["sub"]
            if y < 120:
                c.showPage()
                draw_header(c, quote, f"Detalhamento — Serviço {idx} (continuação)")
                y = h - 210

                c.setFont("Helvetica-Bold", 12)
                c.drawString(40, y, s["service_name"])
                y -= 20

                c.setFont("Helvetica-Bold", 9)
                c.drawString(40, y, "Descrição")
                c.drawString(300, y, "Qtd")
                c.drawString(350, y, "Unit")
                c.drawString(430, y, "Subtotal")
                y -= 10
                c.line(40, y, 550, y)
                y -= 14

                c.setFont("Helvetica", 9)

            c.drawString(40, y, str(desc)[:45])
            c.drawRightString(330, y, f"{qtd}")
            c.drawRightString(410, y, brl(float(unit)).replace("R$ ", ""))
            c.drawRightString(550, y, brl(float(sub)).replace("R$ ", ""))
            y -= 14

        y -= 6
        c.line(40, y, 550, y)
        y -= 18
        c.setFont("Helvetica-Bold", 10)
        c.drawRightString(550, y, f"Subtotal do serviço: {brl(float(s['subtotal']))}")

    c.save()
