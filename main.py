import os
import io
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from fastapi.middleware.cors import CORSMiddleware
from passlib.context import CryptContext

# --- CONFIGURAÇÃO ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
DATABASE_URL = os.getenv("DATABASE_URL").replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    senha = Column(String)
    nome = Column(String)

Base.metadata.create_all(bind=engine)

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

# --- A ROTA QUE VAI RESOLVER O SEU PROBLEMA ---
@app.get("/api/setup-admin")
def setup_admin(db: Session = Depends(get_db)):
    email = "ismaelifrr@gmail.com"
    # Deleta se já existir para não dar erro de duplicado
    db.query(Usuario).filter(Usuario.email == email).delete()
    
    # GERA O HASH DO JEITO QUE O PYTHON GOSTA
    hash_seguro = pwd_context.hash("Admin@123")
    
    novo_user = Usuario(email=email, senha=hash_seguro, nome="Ismael")
    db.add(novo_user)
    db.commit()
    return {"status": "Usuário Ismael atualizado com sucesso!", "hash_gerado": hash_seguro}

# --- ROTA DE LOGIN (IGUAL À ANTERIOR) ---
class LoginRequest(BaseModel):
    email: str
    senha: str

@app.post("/api/login")
def login(dados: LoginRequest, db: Session = Depends(get_db)):
    u = db.query(Usuario).filter(Usuario.email == dados.email.strip().lower()).first()
    if not u or not pwd_context.verify(dados.senha.strip(), u.senha):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    return {"access_token": "vero_2026", "user": {"nome": u.nome}}
