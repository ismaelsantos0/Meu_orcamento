import io
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from fastapi.responses import StreamingResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from database import get_db
from models import HistoricoOrcamento
from schemas import Requisicao

router = APIRouter()

@router.post("/api/gerar-orcamento")
async def gerar(pedido: Requisicao, db: Session = Depends(get_db)):
    total_materiais = sum(i.quantidade * i.preco_unitario for i in pedido.itens)
    total_geral = total_materiais + pedido.valor_mao_de_obra
    
    # Salva no banco
    novo = HistoricoOrcamento(
        nome_cliente=pedido.nome_cliente,
        categoria_servico=pedido.categoria_servico,
        valor_total=total_geral,
        data_cadastro=datetime.now().strftime("%d/%m/%Y %H:%M")
    )
    db.add(novo)
    db.commit()

    # Gera PDF
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    p.drawString(100, 800, f"VERO - Orcamento: {pedido.nome_cliente}")
    p.drawString(100, 780, f"Contato: +55 95 8418-7832")
    p.drawString(100, 760, f"Total: R$ {total_geral:.2f}")
    p.showPage()
    p.save()
    buffer.seek(0)
    
    return StreamingResponse(buffer, media_type="application/pdf")
