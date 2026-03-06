import os
import io
import hashlib
from datetime import datetime
from contextlib import asynccontextmanager
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

# --- CONEXÃO BANCO DE DADOS (Com blindagem anti-crash) ---
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./banco_sobrevivencia.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Ajuste necessário caso o Railway falhe e ele use o banco de sobrevivência (SQLite)
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- MODELOS (Tabelas do Banco) ---
class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True)
    email = Column(String)
    telefone = Column(String)
    senha = Column(String)
    is_admin = Column(Boolean)
    data_cadastro = Column(String)

class PerfilEmpresa(Base):
    __tablename__ = "perfil_empresa"
    id = Column(Integer, primary_key=True)
    nome_fantasia = Column(String)
    telefone = Column(String)
    instagram = Column(String)

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
    status = Column(String, default="Pendente") 
    data_criacao = Column(String)

# --- O AJUSTE DEFINITIVO: O motor liga antes de acessar o banco ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Roda exatamente no momento em que o servidor fica online
    Base.metadata.create_all(bind=engine)
    yield
    # Roda quando o servidor é desligado

app = FastAPI(title="VERO Smart Systems", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

# --- SCHEMAS (Entrada de Dados) ---
class LoginRequest(BaseModel):
    email: str
    senha: str

class PerfilRequest(BaseModel):
    nome_fantasia: str
    telefone: str
    instagram: str

class ItemPedido(BaseModel):
    codigo: str = "000"     
    id_produto: str = "0"   
    nome: str
    quantidade: int
    preco_unitario: float

class RequisicaoOrcamento(BaseModel):
    nome_cliente: str
    whatsapp_cliente: str
    categoria_servico: str
    itens: list[ItemPedido]
    valor_mao_de_obra: float

# --- ROTAS ---
@app.post("/api/login")
def login(dados: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(Usuario).filter(Usuario.email == dados.email.strip().lower()).first()
    if not user or gerar_hash(dados.senha.strip()) != user.senha:
        raise HTTPException(status_code=401, detail="Credenciais incorretas")
    return {"access_token": "vero_2026", "user": {"email": user.email, "telefone": user.telefone, "is_admin": user.is_admin}}

@app.get("/api/dashboard")
def obter_dados_dashboard(db: Session = Depends(get_db)):
    orcamentos = db.query(HistoricoOrcamento).all()
    total_orcamentos = len(orcamentos)
    faturamento = sum(o.valor_total for o in orcamentos)
    ticket_medio = faturamento / total_orcamentos if total_orcamentos > 0 else 0
    recentes = db.query(HistoricoOrcamento).order_by(desc(HistoricoOrcamento.id)).limit(5).all()
    
    return {
        "faturamento_mes": faturamento,
        "total_orcamentos": total_orcamentos,
        "ticket_medio": ticket_medio,
        "taxa_aprovacao": "100%", 
        "recentes": recentes
    }

@app.get("/api/servicos")
def
