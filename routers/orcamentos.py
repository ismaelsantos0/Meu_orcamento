import io
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from fastapi.responses import StreamingResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from database import get_db
from models import HistoricoOrcamento, PerfilEmpresa, MaterialBase
from schemas import Requisicao, RequisicaoCerca, AtualizarStatusRequest
from services.fence import calcular_cerca_completa

router = APIRouter()

# Função para extrair o usuário do Header (Authorization) enviado pelo Lovable
def get_user_id(authorization: str = Header(None)):
    if not authorization: raise HTTPException(status_code=401)
    return int(authorization.replace("Bearer user_", ""))

@router.get("/api/dashboard")
def get_dashboard(db: Session = Depends(get_db), user_id: int = Depends(get_user_id)):
    dados = db.query(HistoricoOrcamento).filter(HistoricoOrcamento.usuario_id == user_id).all()
    # ... lógica de cálculo de faturamento apenas desses dados ...
    return {"total": len(dados), "orcamentos": dados}

@router.post("/api/gerar-orcamento")
async def gerar(pedido: Requisicao, db: Session = Depends(get_db), user_id: int = Depends(get_user_id)):
    subtotal = sum(i.quantidade * i.preco_unitario for i in pedido.itens)
    valor_desconto = subtotal * (pedido.desconto_percentual / 100) if pedido.desconto_percentual else 0
    total_final = subtotal - valor_desconto
    
    # Salva vinculado ao usuário logado
    novo = HistoricoOrcamento(
        usuario_id=user_id,
        nome_cliente=pedido.nome_cliente,
        categoria_servico=pedido.categoria_servico,
        valor_total=total_final,
        data_cadastro=datetime.now().strftime("%d/%m/%Y %H:%M")
    )
    db.add(novo)
    db.commit()
    
    # ... lógica de geração de PDF ...
    return {"message": "PDF Gerado e vinculado ao seu perfil"}

@router.delete("/api/orcamentos/{orcamento_id}")
def deletar_orcamento(orcamento_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_user_id)):
    # Garante que o usuário só pode deletar o que é DELE
    orcamento = db.query(HistoricoOrcamento).filter(
        HistoricoOrcamento.id == orcamento_id, 
        HistoricoOrcamento.usuario_id == user_id
    ).first()
    
    if not orcamento:
        raise HTTPException(status_code=404, detail="Orçamento não encontrado ou acesso negado")
    
    db.delete(orcamento)
    db.commit()
    return {"message": "Removido"}
