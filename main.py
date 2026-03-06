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

# Se não houver DATABASE_URL, ele não vai quebrar o deploy, vai avisar no log
if not DATABASE_URL:
    print("AVISO: DATABASE_URL não encontrada. O sistema pode falhar em rotas de banco.")

engine = create_engine(DATABASE_URL, pool_pre_ping=True) if DATABASE_URL else None
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) if engine else None
Base = declarative_base()

# --- MODELOS ---
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

app = FastAPI(title="VERO Smart Systems")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cria as tabelas na inicialização (forma simples e direta)
@app.on_event("startup")
def startup_db():
    if engine:
        Base.metadata.create_all(bind=engine)

def get_db():
    if not SessionLocal:
        raise HTTPException(status_code=500, detail="Banco de dados não configurado.")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- SCHEMAS ---
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
@app.get("/")
def health_check():
    return {"status": "online", "projeto": "VERO"}

@app.post("/api/login")
def login(dados: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(Usuario).filter(Usuario.email == dados.email.strip().lower()).first()
    if not user or gerar_hash(dados.senha.strip()) != user.senha:
        raise HTTPException(status_code=401, detail="Credenciais incorretas")
    return {"access_token": "vero_2026", "user": {"email": user.email, "is_admin": user.is_admin}}

@app.get("/api/dashboard")
def obter_dados_dashboard(db: Session = Depends(get_db)):
    orcamentos = db.query(HistoricoOrcamento).all()
    total = len(orcamentos)
    faturamento = sum(o.valor_total for o in orcamentos)
    ticket = faturamento / total if total > 0 else 0
    recentes = db.query(HistoricoOrcamento).order_by(desc(HistoricoOrcamento.id)).limit(5).all()
    return {
        "faturamento_mes": faturamento,
        "total_orcamentos": total,
        "ticket_medio": ticket,
        "taxa_aprovacao": "100%",
        "recentes": recentes
    }

@app.post("/api/gerar-orcamento")
async def gerar_orcamento(pedido: RequisicaoOrcamento, db: Session = Depends(get_db)):
    total_materiais = sum(i.quantidade * i.preco_unitario for i in pedido.itens)
    total_geral = total_materiais + pedido.valor_mao_de_obra

    # Salva no histórico
    novo = HistoricoOrcamento(
        nome_cliente=pedido.nome_cliente,
        categoria_servico=pedido.categoria_servico,
        valor_total=total_geral,
        data_criacao=datetime.now().strftime("%d/%m/%Y %H:%M")
    )
    db.add(novo)
    db.commit()

    # Gera PDF simplificado para teste
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    p.drawString(100, 800, f"ORCAMENTO - {pedido.nome_cliente}")
    p.drawString(100, 780, f"Total: R$ {total_geral:.2f}")
    p.showPage()
    p.save()
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/pdf")
