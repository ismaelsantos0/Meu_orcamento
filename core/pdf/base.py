import os
from reportlab.lib.pagesizes import A4


def draw_header(c, quote: dict, title: str):
    w, h = A4
    logo_path = quote.get("logo_path")

    if logo_path and os.path.exists(logo_path):
        c.drawImage(logo_path, 40, h - 120, width=80, height=80, mask="auto")

    c.setFont("Helvetica-Bold", 16)
    c.drawString(140, h - 70, quote.get("empresa", ""))

    c.setFont("Helvetica", 10)
    c.drawString(140, h - 88, f"WhatsApp: {quote.get('whatsapp', '')}")
    c.drawString(140, h - 104, f"Data: {quote.get('data_str', '')}")

    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, h - 150, title)

    c.setFont("Helvetica", 11)
    c.drawString(40, h - 170, f"Cliente: {quote.get('cliente', '')}")
