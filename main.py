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

# Conexão direta e simples
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class HistoricoOrcamento(Base):
    __tablename__ = "historico_orcamentos"
    id = Column(Integer, primary_key=True)
    nome_cliente = Column(String)
    categoria_servico = Column(String)
    valor_total = Column(Float)
    data_cadastro = Column(String)

# Cria as tabelas assim que o script carrega
Base.metadata.create_all(bind=engine)

app = FastAPI(title="VERO API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# SCHEMAS
class Item(BaseModel):
    nome: str
    quantidade: int
    preco_unitario: float

class Requisicao(BaseModel):
    nome_cliente: str
    categoria_servico: str
    itens: list[Item]
    valor_mao_de_obra: float

# --- ROTAS ---

@app.get("/")
def health():
    return {"status": "online", "docs": "/docs"}

@app.get("/api/dashboard")
def get_dashboard(db: Session = Depends(get_db)):
    try:
        dados = db.query(HistoricoOrcamento).all()
        faturamento = sum(d.valor_total for d in dados)
        # Retorna os últimos 5
        recentes = db.query(HistoricoOrcamento).order_by(desc(HistoricoOrcamento.id)).limit(5).all()
        
        return {
            "faturamento_mes": faturamento,
            "total_orcamentos": len(dados),
            "ticket_medio": faturamento / len(dados) if len(dados) > 0 else 0,
            "recentes": recentes
        }
    except Exception as e:
        return {"error": str(e)}

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

    # Gera PDF básico
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    p.drawString(100, 800, f"Orcamento: {pedido.nome_cliente}")
    p.drawString(100, 780, f"Total: R$ {total_geral:.2f}")
    p.showPage()
    p.save()
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/pdf")
