import os
import io
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float, text
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

# --- MODELO SIMPLIFICADO (Para evitar erros de colunas extras) ---
class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True)
    email = Column(String)
    senha = Column(String)
    nome = Column(String)

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

# --- ROTA DE REPARAÇÃO (SQL PURO - RESOLVE OS 72 BYTES) ---
@app.get("/api/setup-admin")
def setup_admin(db: Session = Depends(get_db)):
    try:
        # Geramos o hash correto para Admin@123
        novo_hash = pwd_context.hash("Admin@123")
        
        # Usamos SQL puro para não dar erro com as colunas 'is_admin' ou 'data_cadastro'
        query = text("UPDATE usuarios SET senha = :h WHERE email = :e")
        db.execute(query, {"h": novo_hash, "e": "ismaelifrr@gmail.com"})
        db.commit()
        
        return {"status": "SUCESSO! Senha atualizada no banco. Agora você pode logar."}
    except Exception as e:
        db.rollback()
        return {"error": f"Erro: {str(e)}"}

# --- LOGIN ---
class LoginRequest(BaseModel):
    email: str
    senha: str

@app.post("/api/login")
def login(dados: LoginRequest, db: Session = Depends(get_db)):
    # Busca apenas os campos que precisamos
    user = db.query(Usuario).filter(Usuario.email == dados.email.strip().lower()).first()
    
    if not user or not pwd_context.verify(dados.senha.strip(), user.senha):
        raise HTTPException(status_code=401, detail="Credenciais incorretas")
        
    return {"access_token": "vero_2026", "user": {"nome": user.nome}}

# --- PDF E DADOS (100% DINÂMICOS) ---
@app.get("/api/servicos")
def listar(db: Session = Depends(get_db)):
    return db.query(Servico).all()

@app.get("/api/perfil")
def perfil(db: Session = Depends(get_db)):
    return db.query(PerfilEmpresa).first()

@app.post("/api/gerar-orcamento")
async def gerar(pedido: dict, db: Session = Depends(get_db)):
    empresa = db.query(PerfilEmpresa).first()
    if not empresa: raise HTTPException(status_code=400, detail="Perfil ausente")
    
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    p.drawString(50, 800, empresa.nome_fantasia.upper())
    p.drawString(50, 785, f"Tel: {empresa.telefone}")
    p.showPage()
    p.save()
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/pdf")
