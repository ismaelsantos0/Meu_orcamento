from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from database import get_db
from models import PerfilEmpresa
from pydantic import BaseModel

router = APIRouter()

# Schema para validação dos dados
class PerfilUpdate(BaseModel):
    nome_fantasia: str
    telefone: str
    instagram: str

# Função para pegar o ID do usuário pelo Token
def get_user_id(authorization: str = Header(None)):
    if not authorization: raise HTTPException(status_code=401)
    try:
        token = authorization.replace("Bearer ", "")
        return int(token.replace("user_", ""))
    except:
        raise HTTPException(status_code=401)

# ROTA PARA BUSCAR O PERFIL ATUAL
@router.get("/api/perfil")
def buscar_perfil(db: Session = Depends(get_db), user_id: int = Depends(get_user_id)):
    perfil = db.query(PerfilEmpresa).filter(PerfilEmpresa.usuario_id == user_id).first()
    if not perfil:
        return {"nome_fantasia": "", "telefone": "", "instagram": ""}
    return perfil

# ROTA PARA SALVAR OU ATUALIZAR O PERFIL
@router.post("/api/perfil")
def salvar_perfil(dados: PerfilUpdate, db: Session = Depends(get_db), user_id: int = Depends(get_user_id)):
    perfil = db.query(PerfilEmpresa).filter(PerfilEmpresa.usuario_id == user_id).first()
    
    if perfil:
        # Atualiza o existente
        perfil.nome_fantasia = dados.nome_fantasia
        perfil.telefone = dados.telefone
        perfil.instagram = dados.instagram
    else:
        # Cria um novo para este usuário
        novo_perfil = PerfilEmpresa(
            usuario_id=user_id,
            nome_fantasia=dados.nome_fantasia,
            telefone=dados.telefone,
            instagram=dados.instagram
        )
        db.add(novo_perfil)
    
    db.commit()
    return {"message": "Perfil atualizado com sucesso!"}
