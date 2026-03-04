import os
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from fastapi.middleware.cors import CORSMiddleware
from passlib.context import CryptContext

# --- CONFIGURAÇÃO DE SEGURANÇA ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- CONFIGURAÇÃO DO BANCO (AJUSTE DE DIALETO) ---
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# O engine agora tem um 'pool_pre_ping' para evitar quedas de conexão
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- MODELO DE USUÁRIO ---
class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    senha = Column(String, nullable=False)
    nome = Column(String, nullable=False)

# Tenta criar as tabelas
Base.metadata.create_all(bind=engine)

app = FastAPI()

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

# --- ROTA DE SETUP (EXECUTE ISSO PRIMEIRO) ---
@app.get("/api/setup-admin")
def setup_admin(db: Session = Depends(get_db)):
    try:
        email_admin = "ismaelifrr@gmail.com"
        # Limpa o usuário antigo para evitar conflito de hash manual
        db.query(Usuario).filter(Usuario.email == email_admin).delete()
        
        # Gera o hash perfeito via código
        hash_seguro = pwd_context.hash("Admin@123")
        
        novo_user = Usuario(email=email_admin, senha=hash_seguro, nome="Ismael")
        db.add(novo_user)
        db.commit()
        return {"status": "Usuário Ismael configurado com sucesso!"}
    except Exception as e:
        return {"error": str(e)}

# --- ROTA DE LOGIN ---
class LoginRequest(BaseModel):
    email: str
    senha: str

@app.post("/api/login")
def login(dados: LoginRequest, db: Session = Depends(get_db)):
    try:
        email_limpo = dados.email.strip().lower()
        senha_digitada = dados.senha.strip()
        
        user = db.query(Usuario).filter(Usuario.email == email_limpo).first()
        
        if not user or not pwd_context.verify(senha_digitada, user.senha):
            raise HTTPException(status_code=401, detail="Credenciais inválidas")
            
        return {
            "access_token": "vero_2026_auth",
            "user": {"nome": user.nome, "email": user.email}
        }
    except Exception as e:
        # Se der 'Internal Server Error', o erro real aparecerá aqui
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")
