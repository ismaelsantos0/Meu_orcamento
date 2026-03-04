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

# --- CONFIGURAÇÃO DE SEGURANÇA (BCRYPT) ---
# Usamos o pwd_context para transformar texto puro em hash seguro
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- CONEXÃO COM O BANCO DE DADOS ---
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- MODELOS (MANTENDO SUA ESTRUTURA EXISTENTE) ---

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

# Cria as tabelas se não existirem (sem apagar dados)
Base.metadata.create_all(bind=engine)

# --- SCHEMAS DE VALIDAÇÃO ---

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

# --- INICIALIZAÇÃO DO APP ---

app = FastAPI(title="VERO Smart Systems API")

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

# --- ROTA DE REPARAÇÃO (SETUP) ---
# Use esta rota para garantir que o hash da sua senha esteja correto no banco
@app.get("/api/setup-admin")
def setup_admin(db: Session = Depends(get_db)):
    try:
        email_alvo = "ismaelifrr@gmail.com"
        usuario = db.query(Usuario).filter(Usuario.email == email_alvo).first()
        
        if not usuario:
            return {"error": "Usuário não encontrado. Verifique o e-mail no banco."}

        # Transformamos o texto puro "Admin@123" em hash bcrypt
        # Isso evita o erro de 72 bytes porque o hash é gerado do zero
        usuario.senha = pwd_context.hash("Admin@123")
        db.commit()
        
        return {"status": "Sucesso! Senha do Ismael atualizada para Admin@123."}
    except Exception as e:
        db.rollback()
        return {"error": f"Erro ao processar: {str(e)}"}

# --- ROTA DE LOGIN ---

@app.post("/api/login")
def login(dados: LoginRequest, db: Session = Depends(get_db)):
    email_limpo = dados.email.strip().lower()
    senha_digitada = dados.senha.strip()
    
    usuario = db.query(Usuario).filter(Usuario.email == email_limpo).first()
    
    # O verify compara a senha digitada com o hash salvo no banco
    if not usuario or not pwd_context.verify(senha_digitada, usuario.senha):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="E-mail ou senha incorretos."
        )
    
    return {
        "access_token": "vero_token_2026",
        "user": {"nome": usuario.nome, "email": usuario.email}
    }

# --- ROTAS DE DADOS ---

@app.get("/api/servicos")
def listar_servicos(db: Session = Depends(get_db)):
    return db.query(Servico).all()

@app.get("/api/perfil")
def obter_perfil(db: Session = Depends(get_db)):
    return db.query(PerfilEmpresa).first()

# --- GERAÇÃO DE PDF ---

@app.post("/api/gerar-orcamento")
async def gerar_orcamento(pedido: RequisicaoOrcamento, db: Session = Depends(get_db)):
    empresa = db.query(PerfilEmpresa).first()
    total_geral = sum(i.quantidade * i.preco_unitario for i in pedido.itens) + pedido.valor_mao_de_obra
    
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    
    # Cabeçalho RR Smart
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, 800, empresa.nome_fantasia.upper() if empresa else "RR SMART SOLUÇÕES")
    p.setFont("Helvetica", 10)
    p.drawString(50, 785, f"WhatsApp: {empresa.telefone if empresa else ''}")
    p.line(50, 775, 550, 775)
    
    # Conteúdo do orçamento...
    p.drawString(50, 750, f"CLIENTE: {pedido.nome_cliente}")
    p.drawString(300, 700, f"TOTAL: R$ {total_geral:.2f}")
    
    p.showPage()
    p.save()
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/pdf")
