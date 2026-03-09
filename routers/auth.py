import hashlib
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Usuario, MaterialBase
from pydantic import BaseModel

router = APIRouter()

class UserAuth(BaseModel):
    email: str
    senha: str

@router.post("/api/register")
def register(dados: UserAuth, db: Session = Depends(get_db)):
    email_limpo = dados.email.lower().strip()
    if db.query(Usuario).filter(Usuario.email == email_limpo).first():
        raise HTTPException(status_code=400, detail="E-mail já cadastrado.")

    hash_senha = hashlib.sha256(dados.senha.encode()).hexdigest()
    novo_user = Usuario(email=email_limpo, senha=hash_senha)
    db.add(novo_user)
    db.commit()
    db.refresh(novo_user)

    # ONBOARDING: Injeta materiais padrão para o novo usuário
    materiais_padrao = [
        ("haste_cerca", "Haste de Cerca 1m", 19.00),
        ("fio_aco", "Fio de Aço (Rolo 200m)", 80.00),
        ("concertina_30cm", "Concertina 30cm (10m)", 90.00),
        ("central_sh1800", "Central SH1800", 310.00),
        ("bateria", "Bateria 7A", 83.00),
        ("sirene", "Sirene", 20.00),
        ("kit_aterramento", "Kit Aterramento", 45.00)
    ]
    for slug, nome, preco in materiais_padrao:
        db.add(MaterialBase(usuario_id=novo_user.id, slug=slug, nome=nome, preco=preco))
    
    db.commit()
    return {"message": "Conta criada! Catálogo inicial configurado."}

@router.post("/api/login")
def login(dados: UserAuth, db: Session = Depends(get_db)):
    hash_senha = hashlib.sha256(dados.senha.encode()).hexdigest()
    user = db.query(Usuario).filter(Usuario.email == dados.email.lower().strip(), Usuario.senha == hash_senha).first()
    if not user:
        raise HTTPException(status_code=401, detail="E-mail ou senha incorretos.")
    return {"access_token": f"user_{user.id}", "user": {"email": user.email}}
