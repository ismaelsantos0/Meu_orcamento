import io
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.responses import StreamingResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from database import get_db
from models import HistoricoOrcamento, PerfilEmpresa, MaterialBase
from schemas import Requisicao, RequisicaoCerca, AtualizarStatusRequest
from services.fence import calcular_cerca_completa

router = APIRouter()

# --- GERENCIAMENTO DE ORÇAMENTOS ---

@router.delete("/api/orcamentos/{orcamento_id}")
def deletar_orcamento(orcamento_id: int, db: Session = Depends(get_db)):
    orcamento = db.query(HistoricoOrcamento).filter(HistoricoOrcamento.id == orcamento_id).first()
    if not orcamento:
        raise HTTPException(status_code=404, detail="Orçamento não encontrado")
    db.delete(orcamento)
    db.commit()
    return {"message": "Orçamento removido com sucesso"}

@router.patch("/api/orcamentos/{orcamento_id}/status")
def atualizar_status(orcamento_id: int, dados: AtualizarStatusRequest, db: Session = Depends(get_db)):
    orcamento = db.query(HistoricoOrcamento).filter(HistoricoOrcamento.id == orcamento_id).first()
    if not orcamento:
        raise HTTPException(status_code=404, detail="Orçamento não encontrado")
    orcamento.status = dados.status
    db.commit()
    return {"message": f"Status atualizado para {dados.status}"}

# --- CÁLCULOS E PDF ---

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
    valor_desconto = subtotal * (pedido.desconto_percentual / 100) if pedido.desconto_percentual else 0
    total_final = subtotal - valor_desconto
    
    return gerar_pdf_e_salvar(pedido.nome_cliente, pedido.categoria_servico, pedido.itens, subtotal, valor_desconto, total_final, db)

def gerar_pdf_e_salvar(nome_cliente, categoria, itens, subtotal, valor_desconto, total_final, db):
    perfil = db.query(PerfilEmpresa).first()
    empresa_nome = perfil.nome_fantasia if perfil else "VERO"

    novo = HistoricoOrcamento(
        nome_cliente=nome_cliente,
        categoria_servico=categoria,
        valor_total=total_final,
        data_cadastro=datetime.now().strftime("%d/%m/%Y %H:%M"),
        status="Pendente"
    )
    db.add(novo)
    db.commit()

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    p.setFont("Helvetica-Bold", 20)
    p.drawString(50, 800, "VERO")
    p.setFont("Helvetica", 12)
    p.drawString(50, 780, f"Empresa: {empresa_nome}")
    p.line(50, 770, 550, 770)
    p.drawString(50, 750, f"Cliente: {nome_cliente}")
    p.drawString(50, 730, f"Total: R$ {total_final:.2f}")
    p.showPage()
    p.save()
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/pdf")
