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

# Função para identificar o usuário logado via Token
def get_user_id(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Token ausente")
    try:
        # Formato: "Bearer user_1"
        return int(authorization.replace("Bearer user_", "").replace("Bearer ", ""))
    except:
        raise HTTPException(status_code=401, detail="Token inválido")

# --- ROTA DE CÁLCULO (Onde estava dando erro) ---
@router.post("/api/previa-cerca")
async def previa_cerca(pedido: RequisicaoCerca, db: Session = Depends(get_db), user_id: int = Depends(get_user_id)):
    # Busca materiais específicos do usuário logado
    materiais_db = db.query(MaterialBase).filter(MaterialBase.usuario_id == user_id).all()
    
    # Converte para dicionário que o service/fence.py entende
    dicionario_materiais = {m.slug: {"nome": m.nome, "preco": m.preco} for m in materiais_db}

    # Executa a matemática
    calculo = calcular_cerca_completa(
        metros=pedido.metros, 
        distancia_haste=pedido.distancia_haste, 
        tipo=pedido.tipo, 
        tem_central=pedido.tem_central,
        materiais_db=dicionario_materiais
    )
    return {"itens": calculo["itens"]}

# --- GERAÇÃO DE PDF ---
@router.post("/api/gerar-orcamento")
async def gerar(pedido: Requisicao, db: Session = Depends(get_db), user_id: int = Depends(get_user_id)):
    subtotal = sum(i.quantidade * i.preco_unitario for i in pedido.itens)
    desc = pedido.desconto_percentual if pedido.desconto_percentual else 0
    total_final = subtotal - (subtotal * (desc / 100))
    
    return gerar_pdf_e_salvar(pedido.nome_cliente, pedido.categoria_servico, pedido.itens, subtotal, total_final, db, user_id)

# --- GERENCIAMENTO ---
@router.delete("/api/orcamentos/{orcamento_id}")
def deletar_orcamento(orcamento_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_user_id)):
    orc = db.query(HistoricoOrcamento).filter(HistoricoOrcamento.id == orcamento_id, HistoricoOrcamento.usuario_id == user_id).first()
    if not orc: raise HTTPException(status_code=404)
    db.delete(orc)
    db.commit()
    return {"status": "sucesso"}

@router.patch("/api/orcamentos/{orcamento_id}/status")
def atualizar_status(orcamento_id: int, dados: AtualizarStatusRequest, db: Session = Depends(get_db), user_id: int = Depends(get_user_id)):
    orc = db.query(HistoricoOrcamento).filter(HistoricoOrcamento.id == orcamento_id, HistoricoOrcamento.usuario_id == user_id).first()
    if not orc: raise HTTPException(status_code=404)
    orc.status = dados.status
    db.commit()
    return {"status": "atualizado"}

def gerar_pdf_e_salvar(nome_cliente, categoria, itens, subtotal, total_final, db, user_id):
    perfil = db.query(PerfilEmpresa).filter(PerfilEmpresa.usuario_id == user_id).first()
    empresa = perfil.nome_fantasia if perfil else "VERO SaaS"

    novo = HistoricoOrcamento(
        usuario_id=user_id,
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
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, 800, "VERO - PROPOSTA COMERCIAL")
    p.setFont("Helvetica", 10)
    p.drawString(50, 785, f"Prestador: {empresa}")
    p.line(50, 775, 550, 775)
    # ... (Restante da lógica do PDF se mantém)
    p.showPage()
    p.save()
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/pdf")
