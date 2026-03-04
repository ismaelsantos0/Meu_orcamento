from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

app = FastAPI(title="VERO Smart Systems API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ItemOrcamento(BaseModel):
    id_produto: str
    nome: str
    quantidade: int
    preco_unitario: float

class PedidoOrcamento(BaseModel):
    nome_cliente: str
    whatsapp_cliente: str
    categoria_servico: str
    itens: list[ItemOrcamento]
    valor_mao_de_obra: float

@app.get("/")
def home():
    return {"status": "VERO API Online e Operante!"}

@app.post("/api/gerar-orcamento")
async def gerar_orcamento(pedido: PedidoOrcamento):
    total_materiais = sum(item.quantidade * item.preco_unitario for item in pedido.itens)
    total_geral = total_materiais + pedido.valor_mao_de_obra
    
    # 1. Prepara a memória do servidor para criar o arquivo (sem salvar no HD)
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    pdf.setTitle(f"Orcamento_{pedido.nome_cliente}.pdf")

    # 2. Desenhando o Cabeçalho da Empresa
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(50, 800, "ORÇAMENTO DE SERVIÇOS")
    pdf.setFont("Helvetica", 10)
    pdf.drawString(50, 785, "RR Smart Soluções - Tecnologia e Automação")
    pdf.drawString(50, 770, "WhatsApp: +55 95 8418-7832")
    
    pdf.line(50, 755, 545, 755) # Linha divisória

    # 3. Dados do Cliente
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, 730, f"Cliente: {pedido.nome_cliente}")
    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, 710, f"Contato: {pedido.whatsapp_cliente}")
    pdf.drawString(50, 690, f"Referência: Instalação de {pedido.categoria_servico}")

    # 4. Tabela de Itens
    pdf.drawString(50, 650, "Qtd   |   Descrição do Equipamento   |   Valor Unit.   |   Subtotal")
    pdf.line(50, 640, 545, 640)
    
    y = 620
    for item in pedido.itens:
        sub = item.quantidade * item.preco_unitario
        linha = f"{item.quantidade:02d}    |   {item.nome[:30]:<30}   |   R$ {item.preco_unitario:.2f}   |   R$ {sub:.2f}"
        pdf.drawString(50, y, linha)
        y -= 25

    # 5. Totais
    pdf.line(50, y, 545, y)
    y -= 20
    pdf.drawString(300, y, f"Subtotal Materiais: R$ {total_materiais:.2f}")
    y -= 20
    pdf.drawString(300, y, f"Mão de Obra: R$ {pedido.valor_mao_de_obra:.2f}")
    y -= 25
    
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(300, y, f"TOTAL GERAL: R$ {total_geral:.2f}")

    # 6. Finaliza e empacota o PDF
    pdf.showPage()
    pdf.save()
    buffer.seek(0) # Volta o cursor para o início do arquivo

    # 7. Dispara o arquivo direto para o navegador do cliente!
    return StreamingResponse(
        buffer, 
        media_type="application/pdf", 
        headers={"Content-Disposition": f"attachment; filename=Orcamento_{pedido.nome_cliente.replace(' ', '_')}.pdf"}
    )
