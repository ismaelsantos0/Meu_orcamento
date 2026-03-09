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
    
    # Em um SaaS real, aqui retornamos um JWT. Para o VERO, enviaremos o ID para o Lovable gerenciar
    return {
        "access_token": f"user_{user.id}", 
        "user": {"id": user.id, "email": user.email}
    }

# Função auxiliar para as outras rotas saberem quem é o usuário
def get_current_user_id(token: str):
    try:
        return int(token.replace("user_", ""))
    except:
        raise HTTPException(status_code=401, detail="Usuário não autenticado")
