import os
import io
from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# --- DATABASE ENGINE ---
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- MODELS REAIS (SEM VALORES DEFAULT) ---

class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    senha = Column(String, nullable=False) 
    nome = Column(String, nullable=False)

class PerfilEmpresa(Base):
    __tablename__ = "perfil_empresa"
    id = Column(Integer, primary_key=True, index=True)
    nome_fantasia = Column(String, nullable=False)
    telefone = Column(String, nullable=False)
    instagram = Column(String, nullable=False)
    cnpj = Column(String, nullable=True) # Adicionado para mais profissionalismo

class Servico(Base):
    __tablename__ = "servicos"
    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, unique=True, index=True, nullable=False)
    nome = Column(String, nullable=False)
    preco_base = Column(Float, nullable=False)
    categoria = Column(String, nullable=False)

Base.metadata.create_all(bind=engine)

# --- SCHEMAS ---
class LoginRequest(BaseModel):
    email: str
    senha: str

class ItemPedido(BaseModel):
    codigo: str
    nome: str
    quantidade: int
    preco_unitario: float

class RequisicaoOrcamento(BaseModel):
    nome_cliente: str
    whatsapp_cliente: str
    categoria_servico: str
    itens: list[ItemPedido]
    valor_mao_de_obra: float

app = FastAPI(title="VERO Custom API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- ROTAS PERSONALIZADAS ---

@app.post("/api/login")
def login(dados: LoginRequest, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.email == dados.email).first()
    # Comparação direta conforme solicitado para teste
    if not usuario or usuario.senha != dados.senha:
        raise HTTPException(status_code=401, detail="Acesso Negado: Credenciais Inválidas")
    
    return {
        "token": "VERO_AUTH_TOKEN_ACTIVE",
        "user": {"nome": usuario.nome, "email": usuario.email}
    }

@app.get("/api/perfil")
def obter_perfil(db: Session = Depends(get_db)):
    perfil = db.query(PerfilEmpresa).first()
    if not perfil:
        raise HTTPException(status_code=404, detail="Perfil da Empresa não configurado no Banco")
    return perfil

@app.post("/api/gerar-orcamento")
async def gerar_orcamento(pedido: RequisicaoOrcamento, db: Session = Depends(get_db)):
    empresa = db.query(PerfilEmpresa).first()
    if not empresa:
        raise HTTPException(status_code=400, detail="Configure o Perfil da Empresa antes de gerar orçamentos")

    total_geral = sum(i.quantidade * i.preco_unitario for i in pedido.itens) + pedido.valor_mao_de_obra
    
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    
    # PDF Customizado com dados REAIS do banco
    p.setFont("Helvetica-Bold", 18)
    p.drawString(50, 800, empresa.nome_fantasia.upper())
    p.setFont("Helvetica", 10)
    p.drawString(50, 785, f"Contato: {empresa.telefone} | Insta: {empresa.instagram}")
    p.line(50, 775, 550, 775)
    
    # ... resto da lógica do PDF ...
    p.showPage()
    p.save()
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/pdf")
