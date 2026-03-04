import os
import io
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from passlib.context import CryptContext

# --- CONFIGURAÇÃO DE SEGURANÇA ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- CONEXÃO COM O BANCO ---
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- MODELOS (MANTENDO A ESTRUTURA QUE VOCÊ JÁ TEM) ---
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

# --- APP ---
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

# --- ROTA DE SETUP (SÓ PARA AJUSTAR A SENHA SEM APAGAR NADA) ---
@app.get("/api/setup-admin")
def setup_admin(db: Session = Depends(get_db)):
    try:
        email_alvo = "ismaelifrr@gmail.com"
        usuario = db.query(Usuario).filter(Usuario.email == email_alvo).first()
        
        if not usuario:
            return {"error": "Usuário não encontrado no banco de dados."}

        # Gera o hash correto para Admin@123
        usuario.senha = pwd_context.hash("Admin@123")
        db.commit()
        
        return {"status": "Sucesso! Senha do Ismael atualizada. Nenhum dado foi apagado."}
    except Exception as e:
        db.rollback()
        return {"error": str(e)}

# --- ROTA DE LOGIN ---
@app.post("/api/login")
def login(dados: LoginRequest, db: Session = Depends(get_db)):
    email_limpo = dados.email.strip().lower()
    user = db.query(Usuario).filter(Usuario.email == email_limpo).first()
    
    if not user or not pwd_context.verify(dados.senha.strip(), user.senha):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
        
    return {
        "access_token": "vero_auth_2026",
        "user": {"nome": user.nome, "email": user.email}
    }

# --- OUTRAS ROTAS ---
@app.get("/api/servicos")
def listar_servicos(db: Session = Depends(get_db)):
    return db.query(Servico).all()

@app.get("/api/perfil")
def obter_perfil(db: Session = Depends(get_db)):
    return db.query(PerfilEmpresa).first()

@app.post("/api/gerar-orcamento")
async def gerar_orcamento(pedido: RequisicaoOrcamento, db: Session = Depends(get_db)):
    # Sua lógica de PDF aqui (mantida igual)
    # ... (omitido para brevidade, mas você já tem no seu arquivo)
    return {"message": "PDF Gerado com sucesso"} # Exemplo
