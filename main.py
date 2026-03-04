import os
import io
import hashlib
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# --- FUNÇÃO DE HASH BLINDADA (SHA-256) ---
def gerar_hash(senha: str):
    return hashlib.sha256(senha.encode()).hexdigest()

# --- CONEXÃO BANCO DE DADOS ---
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- MODELOS (Fiéis ao seu banco de dados) ---
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

app = FastAPI(title="VERO Smart Systems")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

# --- ROTA DE REPARAÇÃO (ALVO: vssdamassa) ---
@app.get("/api/setup-admin")
def setup_admin():
    with engine.begin() as conn:
        try:
            # Gera o hash limpo para Admin@123
            novo_hash = gerar_hash("Admin@123")
            
            # Atualiza direto no banco apenas o usuário vssdamassa
            query = text("UPDATE usuarios SET senha = :h WHERE email = 'vssdamassa@gmail.com'")
            resultado = conn.execute(query, {"h": novo_hash})
            
            if resultado.rowcount == 0:
                return {"error": "Usuário vssdamassa@gmail.com não encontrado no banco."}
                
            return {"status": "FEITO! Senha do vssdamassa resetada para Admin@123 com sucesso."}
        except Exception as e:
            return {"error": f"Erro fatal: {str(e)}"}

# --- LOGIN ---
class LoginRequest(BaseModel):
    email: str
    senha: str

@app.post("/api/login")
def login(dados: LoginRequest, db: Session = Depends(get_db)):
    email_limpo = dados.email.strip().lower()
    user = db.query(Usuario).filter(Usuario.email == email_limpo).first()
    
    if not user:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")
        
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
    if not empresa: 
        raise HTTPException(status_code=400, detail="Perfil da empresa ausente no banco.")
    
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    # Puxa o nome da empresa dinamicamente
    p.drawString(50, 800, str(empresa.nome_fantasia).upper())
    p.drawString(50, 785, f"Contato: {empresa.telefone} | Instagram: {empresa.instagram}")
    p.showPage()
    p.save()
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/pdf")
