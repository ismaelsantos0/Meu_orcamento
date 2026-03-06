import os
import io
import hashlib
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, desc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# --- SEGURANÇA ---
def gerar_hash(senha: str):
    return hashlib.sha256(senha.encode()).hexdigest()

# --- CONEXÃO BANCO DE DADOS ---
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- MODELOS ---
class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True)
    email = Column(String)
    senha = Column(String)
    is_admin = Column(Boolean)

class PerfilEmpresa(Base):
    __tablename__ = "perfil_empresa"
    id = Column(Integer, primary_key=True)
    nome_fantasia = Column(String)
    telefone = Column(String)
    instagram = Column(String)

# TABELA DO DASHBOARD
class HistoricoOrcamento(Base):
    __tablename__ = "historico_orcamentos"
    id = Column(Integer, primary_key=True)
    nome_cliente = Column(String)
    categoria_servico = Column(String)
    valor_total = Column(Float)
    status = Column(String, default="Pendente")
    data_criacao = Column(String)

# Criação de tabelas simplificada
Base.metadata.create_all(bind=engine)

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

# --- SCHEMAS ---
class ItemPedido(BaseModel):
    nome: str
    quantidade: int
    preco_unitario: float

class RequisicaoOrcamento(BaseModel):
    nome_cliente: str
    categoria_servico: str
    itens: list[ItemPedido]
    valor_mao_de_obra: float

# --- ROTAS ---

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
        "taxa_aprovacao": "100%",
        "recentes": recentes
    }

@app.post("/api/gerar-orcamento")
async def gerar_orcamento(pedido: RequisicaoOrcamento, db: Session = Depends(get_db)):
    total_materiais = sum(i.quantidade * i.preco_unitario for i in pedido.itens)
    total_geral = total_materiais + pedido.valor_mao_de_obra

    # SALVA NO BANCO
    novo = HistoricoOrcamento(
        nome_cliente=pedido.nome_cliente,
        categoria_servico=pedido.categoria_servico,
        valor_total=total_geral,
        data_criacao=datetime.now().strftime("%d/%m/%Y %H:%M")
    )
    db.add(novo)
    db.commit()

    # GERA PDF
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    p.drawString(100, 800, f"VERO - ORCAMENTO: {pedido.nome_cliente}")
    p.drawString(100, 780, f"Total: R$ {total_geral:.2f}")
    p.showPage()
    p.save()
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/pdf")
