from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from database import get_db
from models import MaterialBase
from schemas import MaterialCreate

router = APIRouter()

# Função segura para pegar o Usuário
def get_user_id(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Sessão expirada. Faça login novamente.")
    try:
        # Aceita "Bearer user_1" ou "user_1"
        token = authorization.replace("Bearer ", "")
        return int(token.replace("user_", ""))
    except Exception:
        raise HTTPException(status_code=401, detail="Token de acesso inválido.")

# LISTAR MATERIAIS (Onde o erro costuma acontecer)
@router.get("/api/materiais")
def listar_materiais(db: Session = Depends(get_db), user_id: int = Depends(get_user_id)):
    materiais = db.query(MaterialBase).filter(MaterialBase.usuario_id == user_id).all()
    # Retorna lista vazia [] se não encontrar nada, evitando erro 404 ou 500
    return materiais if materiais else []

# ADICIONAR MATERIAL
@router.post("/api/materiais")
def adicionar_material(novo: MaterialCreate, db: Session = Depends(get_db), user_id: int = Depends(get_user_id)):
    # Verifica se já existe um material com o mesmo ID Interno (Slug)
    item_existente = db.query(MaterialBase).filter(
        MaterialBase.slug == novo.slug, 
        MaterialBase.usuario_id == user_id
    ).first()
    
    if item_existente:
        item_existente.nome = novo.nome
        item_existente.preco = novo.preco
    else:
        item = MaterialBase(
            usuario_id=user_id,
            nome=novo.nome,
            slug=novo.slug,
            preco=novo.preco
        )
        db.add(item)
    
    db.commit()
    return {"status": "sucesso"}

# DELETAR MATERIAL
@router.delete("/api/materiais/{material_id}")
def deletar_material(material_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_user_id)):
    item = db.query(MaterialBase).filter(
        MaterialBase.id == material_id, 
        MaterialBase.usuario_id == user_id
    ).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Material não encontrado")
    
    db.delete(item)
    db.commit()
    return {"status": "removido"}
