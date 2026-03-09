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

# Função robusta para pegar o usuário logado
def get_user_id(authorization: str = Header(None)):
    if not authorization:
        # Se não houver token, tentamos pegar o primeiro usuário apenas para não travar no desenvolvimento
        return 1 
    try:
        # Formato esperado: "Bearer user_1"
        return int(authorization.replace("Bearer user_", "").replace("Bearer ", ""))
    except:
        return 1

@router.delete("/api/orcamentos/{orcamento_id}")
def deletar_orcamento(orcamento_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_user_id)):
    orcamento = db.query(HistoricoOrcamento).filter(
        HistoricoOrcamento.id == orcamento_id,
        HistoricoOrcamento.usuario_id == user_id
    ).first()
    
    if not orcamento:
        raise HTTPException(status_code=404, detail="Orçamento não encontrado ou você não tem permissão")
    
    db.delete(orcamento)
    db.commit()
    return {"message": "Removido com sucesso"}

@router.post("/api/gerar-orcamento")
async def gerar(pedido: Requisicao, db: Session = Depends(get_db), user_id: int = Depends(get_user_id)):
    subtotal = sum(i.quantidade * i.preco_unitario for i in pedido.itens)
    desc = pedido.desconto_percentual if pedido.desconto_percentual else 0
    total = subtotal - (subtotal * (desc / 100))
    
    # Salva vinculado ao usuário
    novo = HistoricoOrcamento(
        usuario_id=user_id,
        nome_cliente=pedido.nome_cliente,
        categoria_servico=pedido.categoria_servico,
        valor_total=total,
        data_cadastro=datetime.now().strftime("%d/%m/%Y %H:%M"),
        status="Pendente"
    )
    db.add(novo)
    db.commit()
    
    # ... Lógica simplificada de retorno para o Lovable não travar ...
    return {"message": "Sucesso", "id": novo.id}
