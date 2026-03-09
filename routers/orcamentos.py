import io
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from fastapi.responses import StreamingResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from database import get_db
from models import HistoricoOrcamento, PerfilEmpresa, MaterialBase
from schemas import Requisicao, RequisicaoCerca
from services.fence import calcular_cerca_completa

router = APIRouter()

@router.post("/api/previa-cerca")
async def previa_cerca(pedido: RequisicaoCerca, db: Session = Depends(get_db)):
    materiais_db = db.query(MaterialBase).all()
    dicionario_materiais = {m.slug: {"nome": m.nome, "preco": m.preco} for m in materiais_db}

    calculo = calcular_cerca_completa(
        metros=pedido.metros, 
        distancia_haste=pedido.distancia_haste, 
        tipo=pedido.tipo, 
        tem_central=pedido.tem_central,
        materiais_db=dicionario_materiais
    )
    return {"itens": calculo["itens"]}

@router.post("/api/gerar-orcamento")
async def gerar(pedido: Requisicao, db: Session = Depends(get_db)):
    subtotal = sum(i.quantidade * i.preco_unitario for i in pedido.itens)
    
    # Cálculo do Desconto
    valor_desconto = 0
    if pedido.desconto_percentual and pedido.desconto_percentual > 0:
        valor_desconto = subtotal * (pedido.desconto_percentual / 100)
    
    total_final = subtotal - valor_desconto
    
    return gerar_pdf_e_salvar(
        pedido.nome_cliente, 
        pedido.categoria_servico, 
        pedido.itens, 
        subtotal, 
        valor_desconto, 
        total_final, 
        db
    )

def gerar_pdf_e_salvar(nome_cliente, categoria, itens, subtotal, valor_desconto, total_final, db):
    perfil = db.query(PerfilEmpresa).first()
    empresa_nome = perfil.nome_fantasia if perfil else "VERO - Sistema de Orçamentos"
    empresa_contato = perfil.telefone if perfil else ""

    novo = HistoricoOrcamento(
        nome_cliente=nome_cliente,
        categoria_servico=categoria,
        valor_total=total_final,
        data_cadastro=datetime.now().strftime("%d/%m/%Y %H:%M")
    )
    db.add(novo)
    db.commit()

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    largura, altura = A4

    # Cabeçalho VERO
    p.setFont("Helvetica-Bold", 20)
    p.drawString(50, altura - 50, "VERO") 
    p.setFont("Helvetica", 10)
    p.drawString(50, altura - 65, empresa_nome)
    if empresa_contato:
        p.drawRightString(largura - 50, altura - 65, f"Contato: {empresa_contato}")
    
    p.line(50, altura - 75, largura - 50, altura - 75)

    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, altura - 100, f"CLIENTE: {nome_cliente.upper()}")
    p.drawString(50, altura - 115, f"PROPOSTA: {categoria.upper()}")
    p.drawRightString(largura - 50, altura - 100, f"DATA: {datetime.now().strftime('%d/%m/%Y')}")

    # Tabela
    y = altura - 150
    p.setFont("Helvetica-Bold", 10)
    p.drawString(50, y, "DESCRIÇÃO")
    p.drawString(350, y, "QTD")
    p.drawString(420, y, "UNIT.")
    p.drawString(500, y, "TOTAL")
    p.line(50, y - 5, largura - 50, y - 5)
    
    y -= 25
    p.setFont("Helvetica", 10)
    for item in itens:
        nome = item.nome if hasattr(item, 'nome') else item["nome"]
        qtd = item.quantidade if hasattr(item, 'quantidade') else item["quantidade"]
        preco = item.preco_unitario if hasattr(item, 'preco_unitario') else item["preco_unitario"]
        item_total = float(qtd) * float(preco)
        
        p.drawString(50, y, str(nome)[:45])
        p.drawString(350, y, str(qtd))
        p.drawString(420, y, f"R$ {preco:.2f}")
        p.drawString(500, y, f"R$ {item_total:.2f}")
        y -= 20
        if y < 150:
            p.showPage()
            y = altura - 50

    # Resumo de Valores no Final
    y -= 20
    p.line(350, y + 10, largura - 50, y + 10)
    p.setFont("Helvetica", 10)
    p.drawString(350, y, "Subtotal:")
    p.drawRightString(largura - 50, y, f"R$ {subtotal:.2f}")
    
    if valor_desconto > 0:
        y -= 15
        p.setFont("Helvetica-Bold", 10)
        p.setFillColorRGB(0.8, 0, 0) # Vermelho para o desconto
        p.drawString(350, y, f"Desconto Applied:")
        p.drawRightString(largura - 50, y, f"- R$ {valor_desconto:.2f}")
        p.setFillColorRGB(0, 0, 0) # Volta para preto

    y -= 30
    p.setFont("Helvetica-Bold", 14)
    p.drawRightString(largura - 50, y, f"TOTAL FINAL: R$ {total_final:.2f}")
    
    p.setFont("Helvetica-Oblique", 8)
    p.drawString(50, 30, "Gerado pelo Sistema VERO.")

    p.showPage()
    p.save()
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/pdf")
