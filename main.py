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
from passlib.context import CryptContext

# --- SEGURANÇA ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- CONEXÃO BANCO ---
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- MODELOS ---
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

app = FastAPI(title="VERO Smart Systems")

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

# --- ROTA DE SETUP (UPDATE DIRETO) ---
@app.get("/api/setup-admin")
def setup_admin(db: Session = Depends(get_db)):
    try:
        email_alvo = "ismaelifrr@gmail.com"
        novo_hash = pwd_context.hash("Admin@123")
        resultado = db.query(Usuario).filter(Usuario.email == email_alvo).update({"senha": novo_hash})
        if resultado == 0:
            return {"error": "Usuário não encontrado."}
        db.commit()
        return {"status": "Sucesso! Senha atualizada."}
    except Exception as e:
        db.rollback()
        return {"error": str(e)}

# --- ROTA DE LOGIN ---
@app.post("/api/login")
def login(dados: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(Usuario).filter(Usuario.email == dados.email.strip().lower()).first()
    if not user or not pwd_context.verify(dados.senha.strip(), user.senha):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    return {"access_token": "vero_auth_2026", "user": {"nome": user.nome, "email": user.email}}

# --- DADOS DINÂMICOS ---
@app.get("/api/servicos")
def listar_servicos(db: Session = Depends(get_db)):
    return db.query(Servico).all()

@app.get("/api/perfil")
def obter_perfil(db: Session = Depends(get_db)):
    perfil = db.query(PerfilEmpresa).first()
    if not perfil:
        raise HTTPException(status_code=404, detail="Perfil não configurado no banco.")
    return perfil

# --- GERAÇÃO DE PDF (100% DINÂMICO) ---
@app.post("/api/gerar-orcamento")
async def gerar_orcamento(pedido: RequisicaoOrcamento, db: Session = Depends(get_db)):
    # Puxa os dados da empresa diretamente da tabela perfil_empresa
    empresa = db.query(PerfilEmpresa).first()
    
    if not empresa:
        raise HTTPException(status_code=400, detail="Erro: Dados da empresa não encontrados no banco.")

    total_geral = sum(i.quantidade * i.preco_unitario for i in pedido.itens) + pedido.valor_mao_de_obra
    
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    
    # Cabeçalho usando APENAS as variáveis do banco
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, 800, empresa.nome_fantasia.upper())
    p.setFont("Helvetica", 10)
    p.drawString(50, 785, f"Contato: {empresa.telefone} | Instagram: {empresa.instagram}")
    p.line(50, 775, 550, 775)
    
    # Corpo do Orçamento
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, 750, f"CLIENTE: {pedido.nome_cliente}")
    p.drawString(50, 735, f"CATEGORIA: {pedido.categoria_servico}")
    
    y = 690
    p.drawString(50, y, "ITEM")
    p.drawRightString(540, y, "SUBTOTAL")
    p.line(50, y-5, 550, y-5)
    y -= 25
    
    for item in pedido.itens:
        p.setFont("Helvetica", 11)
        p.drawString(50, y, f"{item.quantidade}x {item.nome}")
        p.drawRightString(540, y, f"R$ {item.quantidade * item.preco_unitario:.2f}")
        y -= 20
        
    p.line(50, y, 550, y)
    y -= 30
    p.setFont("Helvetica-Bold", 14)
    p.drawString(300, y, f"TOTAL GERAL: R$ {total_geral:.2f}")
    
    p.showPage()
    p.save()
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/pdf")
