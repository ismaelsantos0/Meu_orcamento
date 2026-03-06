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

# --- BANCO DE DADOS ---
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class HistoricoOrcamento(Base):
    __tablename__ = "historico_orcamentos"
    id = Column(Integer, primary_key=True)
    nome_cliente = Column(String)
    categoria_servico = Column(String)
    valor_total = Column(Float)
    data_criacao = Column(String)

# Cria a tabela
Base.metadata.create_all(bind=engine)

# ATIVAÇÃO DO DOCS E REDOC
app = FastAPI(
    title="VERO API",
    docs_url="/docs",
    redoc_url="/redoc"
)

# LIBERAÇÃO TOTAL PARA O LOVABLE
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

@app.get("/")
def home():
    return {"message": "VERO API Online", "docs": "/docs"}

@app.get("/api/dashboard")
def dashboard(db: Session = Depends(get_db)):
    orcamentos = db.query(HistoricoOrcamento).all()
    total = len(orcamentos)
    faturamento = sum(o.valor_total for o in orcamentos)
    recentes = db.query(HistoricoOrcamento).order_by(desc(HistoricoOrcamento.id)).limit(5).all()
    
    return {
        "faturamento_mes": faturamento,
        "total_orcamentos": total,
        "ticket_medio": faturamento / total if total > 0 else 0,
        "recentes": [
            {
                "id": o.id,
                "nome_cliente": o.nome_cliente,
                "categoria_servico": o.categoria_servico,
                "valor_total": o.valor_total,
                "data_criacao": o.data_criacao
            } for o in recentes
        ]
    }

@app.post("/api/gerar-orcamento")
async def gerar(pedido: Requisicao, db: Session = Depends(get_db)):
    total_geral = sum(i.quantidade * i.preco_unitario for i in pedido.itens) + pedido.valor_mao_de_obra
    
    novo = HistoricoOrcamento(
        nome_cliente=pedido.nome_cliente,
        categoria_servico=pedido.categoria_servico,
        valor_total=total_geral,
        data_criacao=datetime.now().strftime("%d/%m/%Y %H:%M")
    )
    db.add(novo)
    db.commit()

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    p.drawString(100, 800, f"Orcamento: {pedido.nome_cliente}")
    p.drawString(100, 780, f"Total: R$ {total_geral:.2f}")
    p.showPage()
    p.save()
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/pdf")
