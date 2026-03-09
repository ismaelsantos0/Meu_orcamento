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

@router.post("/api/gerar-orcamento")
async def gerar(pedido: Requisicao, db: Session = Depends(get_db)):
    total_materiais = sum(i.quantidade * i.preco_unitario for i in pedido.itens)
    return gerar_pdf_e_salvar(pedido.nome_cliente, pedido.categoria_servico, pedido.itens, total_materiais, pedido.valor_mao_de_obra, db)

@router.post("/api/gerar-orcamento-cerca")
async def gerar_cerca(pedido: RequisicaoCerca, db: Session = Depends(get_db)):
    # Busca os preços dinâmicos no banco
    materiais_db = db.query(MaterialBase).all()
    dicionario_precos = {m.slug: m.preco for m in materiais_db}

    calculo = calcular_cerca_completa(
        metros=pedido.metros, 
        distancia_haste=pedido.distancia_haste, 
        tipo=pedido.tipo, 
        tem_central=pedido.tem_central,
        precos_db=dicionario_precos
    )
    
    categoria = f"Cerca - {pedido.tipo.replace('_', ' ').title()}"
    return gerar_pdf_e_salvar(pedido.nome_cliente, categoria, calculo["itens"], calculo["total_materiais"], pedido.valor_mao_de_obra, db)

def gerar_pdf_e_salvar(nome_cliente, categoria, itens, total_materiais, mao_de_obra, db):
    total_geral = total_materiais + mao_de_obra
    
    # Busca o Perfil da Empresa
    perfil = db.query(PerfilEmpresa).first()
    nome_empresa = perfil.nome_fantasia if perfil else "EMPRESA NÃO CADASTRADA"
    contato_empresa = perfil.telefone if perfil else "Sem Contato"
    insta_empresa = perfil.instagram if perfil else ""

    novo = HistoricoOrcamento(
        nome_cliente=nome_cliente,
        categoria_servico=categoria,
        valor_total=total_geral,
        data_cadastro=datetime.now().strftime("%d/%m/%Y %H:%M")
    )
    db.add(novo)
    db.commit()

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    largura, altura = A4

    p.setFont("Helvetica-Bold", 18)
    p.drawString(50, altura - 50, nome_empresa.upper())
    p.setFont("Helvetica", 10)
    texto_contato = f"Contato: {contato_empresa}"
    if insta_empresa:
        texto_contato += f" | Instagram: {insta_empresa}"
    p.drawString(50, altura - 65, texto_contato)
    p.line(50, altura - 85, largura - 50, altura - 85)

    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, altura - 110, f"CLIENTE: {nome_cliente.upper()}")
    p.drawString(50, altura - 125, f"SERVIÇO: {categoria.upper()}")
    
    y = altura - 160
    p.setFont("Helvetica-Bold", 10)
    p.drawString(50, y, "DESCRIÇÃO")
    p.drawString(350, y, "QTD")
    p.drawString(420, y, "UNIT.")
    p.drawString(500, y, "TOTAL")
    p.line(50, y - 5, largura - 50, y - 5)
    
    y -= 25
    p.setFont("Helvetica", 10)
    for item in itens:
        nome = item["nome"] if isinstance(item, dict) else item.nome
        qtd = item["quantidade"] if isinstance(item, dict) else item.quantidade
        preco = item["preco_unitario"] if isinstance(item, dict) else item.preco_unitario
        
        subtotal = qtd * preco
        p.drawString(50, y, nome[:45])
        p.drawString(350, y, str(qtd))
        p.drawString(420, y, f"R$ {preco:.2f}")
        p.drawString(500, y, f"R$ {subtotal:.2f}")
        y -= 20
        
        if y < 100:
            p.showPage()
            y = altura - 50

    y -= 20
    p.line(350, y + 10, largura - 50, y + 10)
    p.drawString(350, y, "Total Materiais:")
    p.drawRightString(largura - 50, y, f"R$ {total_materiais:.2f}")
    y -= 15
    p.drawString(350, y, "Mão de Obra:")
    p.drawRightString(largura - 50, y, f"R$ {mao_de_obra:.2f}")
    
    y -= 25
    p.setFont("Helvetica-Bold", 12)
    p.drawString(350, y, "TOTAL GERAL:")
    p.drawRightString(largura - 50, y, f"R$ {total_geral:.2f}")

    p.showPage()
    p.save()
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/pdf")
