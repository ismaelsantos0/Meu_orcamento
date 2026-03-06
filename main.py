import os
import io
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float, desc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors

# --- BANCO DE DADOS ---
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Servico(Base):
    __tablename__ = "servicos"
    id = Column(Integer, primary_key=True)
    codigo = Column(String)
    nome = Column(String)
    preco_base = Column(Float)
    categoria = Column(String)

class HistoricoOrcamento(Base):
    __tablename__ = "historico_orcamentos"
    id = Column(Integer, primary_key=True)
    nome_cliente = Column(String)
    categoria_servico = Column(String)
    valor_total = Column(Float)
    data_cadastro = Column(String)

Base.metadata.create_all(bind=engine)

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

class Item(BaseModel):
    nome: str
    quantidade: int
    preco_unitario: float

class Requisicao(BaseModel):
    nome_cliente: str
    categoria_servico: str
    itens: list[Item]
    valor_mao_de_obra: float

@app.get("/api/servicos")
def listar_servicos(db: Session = Depends(get_db)):
    return db.query(Servico).all()

@app.get("/api/dashboard")
def get_dashboard(db: Session = Depends(get_db)):
    dados = db.query(HistoricoOrcamento).all()
    faturamento = sum(d.valor_total for d in dados)
    recentes = db.query(HistoricoOrcamento).order_by(desc(HistoricoOrcamento.id)).limit(5).all()
    return {
        "faturamento_mes": faturamento,
        "total_orcamentos": len(dados),
        "ticket_medio": faturamento / len(dados) if len(dados) > 0 else 0,
        "recentes": recentes
    }

@app.post("/api/gerar-orcamento")
async def gerar(pedido: Requisicao, db: Session = Depends(get_db)):
    total_materiais = sum(i.quantidade * i.preco_unitario for i in pedido.itens)
    total_geral = total_materiais + pedido.valor_mao_de_obra
    
    # Salva no histórico
    novo = HistoricoOrcamento(
        nome_cliente=pedido.nome_cliente,
        categoria_servico=pedido.categoria_servico,
        valor_total=total_geral,
        data_cadastro=datetime.now().strftime("%d/%m/%Y %H:%M")
    )
    db.add(novo)
    db.commit()

    # --- GERAÇÃO DO PDF PROFISSIONAL ---
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    largura, altura = A4

    # Cabeçalho
    p.setFont("Helvetica-Bold", 18)
    p.drawString(50, altura - 50, "RR SMART SOLUÇÕES")
    p.setFont("Helvetica", 10)
    p.drawString(50, altura - 65, "Segurança Eletrônica e Automação Residencial")
    p.drawString(50, altura - 77, "Contato: (95) 98418-7832 | Instagram: @rr_smart_solucoes")
    p.line(50, altura - 85, largura - 50, altura - 85)

    # Dados do Cliente
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, altura - 110, f"CLIENTE: {pedido.nome_cliente.upper()}")
    p.drawString(50, altura - 125, f"SERVIÇO: {pedido.categoria_servico.upper()}")
    p.setFont("Helvetica", 10)
    p.drawString(largura - 150, altura - 110, f"Data: {datetime.now().strftime('%d/%m/%Y')}")

    # Tabela de Itens
    y = altura - 160
    p.setFont("Helvetica-Bold", 10)
    p.drawString(50, y, "DESCRIÇÃO")
    p.drawString(350, y, "QTD")
    p.drawString(420, y, "UNIT.")
    p.drawString(500, y, "TOTAL")
    p.line(50, y - 5, largura - 50, y - 5)
    
    y -= 25
    p.setFont("Helvetica", 10)
    for item in pedido.itens:
        subtotal = item.quantidade * item.preco_unitario
        p.drawString(50, y, item.nome[:45])
        p.drawString(350, y, str(item.quantidade))
        p.drawString(420, y, f"R$ {item.preco_unitario:.2f}")
        p.drawString(500, y, f"R$ {subtotal:.2f}")
        y -= 20
        if y < 100: # Nova página se necessário
            p.showPage()
            y = altura - 50

    # Resumo Financeiro
    y -= 20
    p.line(350, y + 10, largura - 50, y + 10)
    p.drawString(350, y, "Total Materiais:")
    p.drawRightString(largura - 50, y, f"R$ {total_materiais:.2f}")
    y -= 15
    p.drawString(350, y, "Mão de Obra:")
    p.drawRightString(largura - 50, y, f"R$ {pedido.valor_mao_de_obra:.2f}")
    y -= 25
    
    p.setFont("Helvetica-Bold", 14)
    p.setFillColor(colors.black)
    p.rect(345, y - 10, 200, 30, fill=0)
    p.drawString(350, y, "TOTAL GERAL:")
    p.drawRightString(largura - 55, y, f"R$ {total_geral:.2f}")

    # Rodapé
    p.setFont("Helvetica-Oblique", 8)
    p.drawCentredString(largura / 2, 30, "VERO SaaS - RR Smart Soluções © 2026")

    p.showPage()
    p.save()
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/pdf")
