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
        raise HTTPException(status_code=401, detail="Não autorizado: Token ausente")
    try:
        # Suporta "Bearer user_1" ou apenas "user_1"
        token = authorization.replace("Bearer ", "")
        return int(token.replace("user_", ""))
    except Exception:
        raise HTTPException(status_code=401, detail="Não autorizado: Token inválido")

# --- ROTA DE CÁLCULO ---
@router.post("/api/previa-cerca")
async def previa_cerca(pedido: RequisicaoCerca, db: Session = Depends(get_db), user_id: int = Depends(get_user_id)):
    materiais_db = db.query(MaterialBase).filter(MaterialBase.usuario_id == user_id).all()
    dicionario_materiais = {m.slug: {"nome": m.nome, "preco": m.preco} for m in materiais_db}

    calculo = calcular_cerca_completa(
        metros=pedido.metros, 
        distancia_haste=pedido.distancia_haste, 
        tipo=pedido.tipo, 
        tem_central=pedido.tem_central,
        materiais_db=dicionario_materiais
    )
    return {"itens": calculo["itens"]}

# --- ROTA DE GERAÇÃO DE PDF ---
@router.post("/api/gerar-orcamento")
async def gerar(pedido: Requisicao, db: Session = Depends(get_db), user_id: int = Depends(get_user_id)):
    try:
        subtotal = sum(float(i.quantidade) * float(i.preco_unitario) for i in pedido.itens)
        desc = float(pedido.desconto_percentual) if pedido.desconto_percentual else 0
        valor_desconto = subtotal * (desc / 100)
        total_final = subtotal - valor_desconto
        
        return gerar_pdf_e_salvar(
            pedido.nome_cliente, 
            pedido.categoria_servico, 
            pedido.itens, 
            subtotal, 
            valor_desconto, 
            total_final, 
            db, 
            user_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno ao processar orçamento: {str(e)}")

# --- GERENCIAMENTO ---
@router.delete("/api/orcamentos/{orcamento_id}")
def deletar_orcamento(orcamento_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_user_id)):
    orc = db.query(HistoricoOrcamento).filter(
        HistoricoOrcamento.id == orcamento_id, 
        HistoricoOrcamento.usuario_id == user_id
    ).first()
    if not orc:
        raise HTTPException(status_code=404, detail="Orçamento não encontrado")
    db.delete(orc)
    db.commit()
    return {"message": "Sucesso"}

@router.patch("/api/orcamentos/{orcamento_id}/status")
def atualizar_status(orcamento_id: int, dados: AtualizarStatusRequest, db: Session = Depends(get_db), user_id: int = Depends(get_user_id)):
    orc = db.query(HistoricoOrcamento).filter(
        HistoricoOrcamento.id == orcamento_id, 
        HistoricoOrcamento.usuario_id == user_id
    ).first()
    if not orc:
        raise HTTPException(status_code=404, detail="Orçamento não encontrado")
    orc.status = dados.status
    db.commit()
    return {"message": "Status atualizado"}

# --- MOTOR DO PDF ---
def gerar_pdf_e_salvar(nome_cliente, categoria, itens, subtotal, valor_desconto, total_final, db, user_id):
    # Busca o perfil do usuário logado
    perfil = db.query(PerfilEmpresa).filter(PerfilEmpresa.usuario_id == user_id).first()
    empresa_nome = perfil.nome_fantasia if perfil else "VERO - SISTEMA DE ORÇAMENTOS"
    empresa_fone = perfil.telefone if perfil else ""

    # Salva no histórico vinculado ao usuário
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
    largura, altura = A4

    # Cabeçalho
    p.setFont("Helvetica-Bold", 20)
    p.drawString(50, altura - 50, "VERO") 
    p.setFont("Helvetica", 10)
    p.drawString(50, altura - 65, empresa_nome.upper())
    if empresa_fone:
        p.drawRightString(largura - 50, altura - 65, f"Contato: {empresa_fone}")
    
    p.line(50, altura - 75, largura - 50, altura - 75)

    # Info do Cliente
    p.setFont("Helvetica-Bold", 11)
    p.drawString(50, altura - 100, f"CLIENTE: {nome_cliente.upper()}")
    p.drawString(50, altura - 115, f"PROPOSTA: {categoria.upper()}")
    p.drawRightString(largura - 50, altura - 100, f"DATA: {datetime.now().strftime('%d/%m/%Y')}")

    # Tabela de Itens
    y = altura - 150
    p.setFont("Helvetica-Bold", 10)
    p.drawString(50, y, "DESCRIÇÃO")
    p.drawString(350, y, "QTD")
    p.drawString(420, y, "UNIT.")
    p.drawString(500, y, "TOTAL")
    p.line(50, y - 5, largura - 50, y - 5)
    
    y -= 25
    p.setFont("Helvetica", 9)
    for item in itens:
        nome = item.nome if hasattr(item, 'nome') else item["nome"]
        qtd = float(item.quantidade) if hasattr(item, 'quantidade') else float(item["quantidade"])
        preco = float(item.preco_unitario) if hasattr(item, 'preco_unitario') else float(item["preco_unitario"])
        item_total = qtd * preco
        
        p.drawString(50, y, str(nome)[:50])
        p.drawString(350, y, str(int(qtd)))
        p.drawString(420, y, f"R$ {preco:.2f}")
        p.drawString(500, y, f"R$ {item_total:.2f}")
        y -= 20
        if y < 120:
            p.showPage()
            y = altura - 50

    # Resumo Financeiro
    y -= 20
    p.line(350, y + 10, largura - 50, y + 10)
    p.setFont("Helvetica", 10)
    p.drawString(350, y, "Subtotal:")
    p.drawRightString(largura - 50, y, f"R$ {subtotal:.2f}")
    
    if valor_desconto > 0:
        y -= 15
        p.setFillColorRGB(0.7, 0, 0) # Vermelho
        p.drawString(350, y, "Desconto:")
        p.drawRightString(largura - 50, y, f"- R$ {valor_desconto:.2f}")
        p.setFillColorRGB(0, 0, 0)

    y -= 30
    p.setFont("Helvetica-Bold", 14)
    p.drawRightString(largura - 50, y, f"TOTAL FINAL: R$ {total_final:.2f}")
    
    p.setFont("Helvetica-Oblique", 8)
    p.drawString(50, 40, "Orçamento gerado pelo VERO SaaS. Válido por 7 dias.")

    p.showPage()
    p.save()
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/pdf")
