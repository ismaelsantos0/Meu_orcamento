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

# Cria conexão apenas se a URL existir
engine = create_engine(DATABASE_URL, pool_pre_ping=True) if DATABASE_URL else None
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) if engine else None
Base = declarative_base()

class HistoricoOrcamento(Base):
    __tablename__ = "historico_orcamentos"
    id = Column(Integer, primary_key=True, index=True)
    nome_cliente = Column(String)
    categoria_servico = Column(String)
    valor_total = Column(Float)
    data_criacao = Column(String)

# Tenta criar a tabela de forma direta
if engine:
    Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    if not SessionLocal:
        raise HTTPException(status_code=500, detail="Banco não configurado")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# SCHEMAS PARA NÃO DAR ERRO DE VALIDAÇÃO
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
def home():
    return {"status": "online"}

@app.get("/api/dashboard")
def dashboard(db: Session = Depends(get_db)):
    try:
        orcamentos = db.query(HistoricoOrcamento).all()
        faturamento = sum(o.valor_total for o in orcamentos)
        return {
            "faturamento_mes": faturamento,
            "total_orcamentos": len(orcamentos),
            "ticket_medio": faturamento / len(orcamentos) if len(orcamentos) > 0 else 0,
            "recentes": orcamentos[-5:] if orcamentos else []
        }
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/gerar-orcamento")
async def gerar(pedido: Requisicao, db: Session = Depends(get_db)):
    try:
        total = sum(i.quantidade * i.preco_unitario for i in pedido.itens) + pedido.valor_mao_de_obra
        novo = HistoricoOrcamento(
            nome_cliente=pedido.nome_cliente,
            categoria_servico=pedido.categoria_servico,
            valor_total=total,
            data_criacao=datetime.now().strftime("%d/%m/%Y %H:%M")
        )
        db.add(novo)
        db.commit()
        return {"status": "sucesso", "valor": total}
    except Exception as e:
        return {"error": str(e)}
