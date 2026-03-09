import hashlib
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Usuario
from schemas import LoginRequest

router = APIRouter()

def gerar_hash(senha: str):
    return hashlib.sha256(senha.encode()).hexdigest()

@router.post("/api/login")
def login(dados: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(Usuario).filter(Usuario.email == dados.email.strip().lower()).first()
    if not user or gerar_hash(dados.senha.strip()) != user.senha:
        raise HTTPException(status_code=401, detail="Credenciais incorretas")
    return {"access_token": "vero_2026", "user": {"email": user.email, "is_admin": user.is_admin}}
