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
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- CONFIGURAÇÃO DO BANCO DE DADOS ---
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- MODELOS DO BANCO (REAIS E SEM DEFAULTS) ---

class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    senha = Column(String, nullable=False) # Armazena o HASH aqui
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

# --- INICIALIZAÇÃO APP ---

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

# --- ROTAS ---

@app.get("/")
def health_check():
    return {"status": "Online", "mode": "Enterprise (Hash Enabled)"}

@app.post("/api/login")
def login(dados: LoginRequest, db: Session = Depends(get_db)):
    email_limpo = dados.email.strip().lower()
    senha_digitada = dados.senha.strip()
    
    print(f"DEBUG: Tentativa de login para {email_limpo}")
    
    usuario = db.query(Usuario).filter(Usuario.email == email_limpo).first()
    
    if not usuario:
        print(f"DEBUG: Usuário {email_limpo} não encontrado no banco.")
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    
    # VERIFICAÇÃO DO HASH
    try:
        # A passlib verifica se a 'senha_digitada' gera o mesmo hash que está no 'usuario.senha'
        senha_valida = pwd_context.verify(senha_digitada, usuario.senha)
    except Exception as e:
        print(f"DEBUG: Erro na verificação do hash: {e}")
        senha_valida = False

    if not senha_valida:
        print(f"DEBUG: Senha incorreta para {email_limpo}")
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    
    print(f"DEBUG: Sucesso! {usuario.nome} logou com hash verificado.")
    return {
        "access_token": "vero_auth_2026_active",
        "user": {"nome": usuario.nome, "email": usuario.email}
    }

@app.get("/api/servicos")
def listar_servicos(db: Session = Depends(get_db)):
    return db.query(Servico).all()

@app.get("/api/perfil")
def obter_perfil(db: Session = Depends(get_db)):
    perfil = db.query(PerfilEmpresa).first()
    if not perfil:
        raise HTTPException(status_code=404, detail="Perfil não configurado no banco")
    return perfil

@app.post("/api/gerar-orcamento")
async def gerar_orcamento(pedido: RequisicaoOrcamento, db: Session = Depends(get_db)):
    empresa = db.query(PerfilEmpresa).first()
    if not empresa:
        raise HTTPException(status_code=400, detail="Perfil da empresa ausente.")

    total_materiais = sum(i.quantidade * i.preco_unitario for i in pedido.itens)
    total_geral = total_materiais + pedido.valor_mao_de_obra
    
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    
    # Layout RR Smart Soluções
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, 800, empresa.nome_fantasia.upper())
    p.setFont("Helvetica", 10)
    p.drawString(50, 785, f"WhatsApp: {empresa.telefone} | Insta: {empresa.instagram}")
    p.line(50, 775, 550, 775)
    
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, 750, f"CLIENTE: {pedido.nome_cliente}")
    p.drawString(50, 735, f"SERVIÇO: {pedido.categoria_servico}")
    
    y = 700
    p.drawString(50, y, "ITEM")
    p.drawRightString(540, y, "VALOR")
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
