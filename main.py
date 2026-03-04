import os
import io
import hashlib # A SOLUÇÃO NATIVA E BLINDADA
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# --- FUNÇÃO DE HASH INQUEBRÁVEL (SEM LIMITE DE 72 BYTES) ---
def gerar_hash(senha: str):
    # Transforma qualquer senha em um código seguro SHA-256
    return hashlib.sha256(senha.encode()).hexdigest()

# --- CONEXÃO BANCO ---
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- MODELO EXATAMENTE IGUAL À SUA FOTO ---
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

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

# --- ROTA DE REPARAÇÃO ---
@app.get("/api/setup-admin")
def setup_admin():
    with engine.begin() as conn:
        try:
            # Gera o hash SHA-256 (Impossível dar o erro de 72 bytes aqui)
            novo_hash = gerar_hash("Admin@123")
            
            # Grava direto no banco
            query = text("UPDATE usuarios SET senha = :h WHERE email = 'ismaelifrr@gmail.com'")
            conn.execute(query, {"h": novo_hash})
            
            return {"status": "AMÉM! Bcrypt removido. Senha atualizada com SHA-256."}
        except Exception as e:
            return {"error": f"Erro: {str(e)}"}

# --- LOGIN ---
class LoginRequest(BaseModel):
    email: str
    senha: str

@app.post("/api/login")
def login(dados: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(Usuario).filter(Usuario.email == dados.email.strip().lower()).first()
    
    if not user:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")
        
    # Criptografa o que o usuário digitou e compara com o banco
    hash_tentativa = gerar_hash(dados.senha.strip())
    
    if hash_tentativa != user.senha:
        raise HTTPException(status_code=401, detail="Senha incorreta")
        
    return {
        "access_token": "vero_2026", 
        "user": {
            "email": user.email, 
            "telefone": user.telefone, 
            "is_admin": user.is_admin
        }
    }

# --- PDF E DADOS DINÂMICOS ---
@app.get("/api/servicos")
def listar(db: Session = Depends(get_db)):
    return db.query(Servico).all()

@app.get("/api/perfil")
def perfil(db: Session = Depends(get_db)):
    return db.query(PerfilEmpresa).first()

@app.post("/api/gerar-orcamento")
async def gerar(pedido: dict, db: Session = Depends(get_db)):
    empresa = db.query(PerfilEmpresa).first()
    if not empresa: raise HTTPException(status_code=400, detail="Perfil ausente no banco")
    
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    p.drawString(50, 800, str(empresa.nome_fantasia).upper())
    p.showPage()
    p.save()
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/pdf")
