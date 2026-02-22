import textwrap
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from core.money import brl
from core.pdf.base import draw_header

def render_summary_pdf(out_path, quote: dict):
    c = canvas.Canvas(out_path, pagesize=A4)
    w, h = A4

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
        texto_beneficios = s.get("summary_client", s.get("summary_full", "Serviço de instalação."))
        
        # Lê cada linha do texto e quebra automaticamente se for muito longa
        for paragraph in texto_beneficios.split("\n"):
            # O width=80 garante que o texto não ultrapassa a margem da folha
            wrapped_lines = textwrap.wrap(paragraph, width=80) 
            
            if not wrapped_lines: # Se for uma linha vazia, dá só um espacinho
                y -= 8
                continue
                
            for line in wrapped_lines:
                # Se for o título dos benefícios, coloca em Negrito
                if line.startswith("O que está incluso") or line.startswith("Principais Vantagens"):
                    c.setFont("Helvetica-Bold", 11)
                else:
                    c.setFont("Helvetica", 11)
                    
                c.drawString(55, y, line)
                y -= 16
                
                # Se o texto chegar muito perto do fim da folha, cria uma nova página!
                if y < 100:
                    c.showPage()
                    draw_header(c, quote, "Proposta Comercial (Continuação)")
                    y = h - 180
                    
        y -= 15 # Espaço extra antes de um próximo serviço

    y -= 10
    c.line(40, y, 550, y)
    y -= 40

    # Verifica se há espaço para o valor total, se não, joga para a próxima página
    if y < 180:
        c.showPage()
        draw_header(c, quote, "Proposta Comercial (Valores)")
        y = h - 180

    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, "Investimento Total")
    y -= 35
    c.setFont("Helvetica-Bold", 34)
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
    c.drawString(40, y, f"Para aprovar o orçamento, chame no WhatsApp: {quote.get('whatsapp','')}")

    c.save()
