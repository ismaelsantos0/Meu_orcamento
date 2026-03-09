from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from database import get_db
from models import MaterialBase
from schemas import MaterialCreate

router = APIRouter()

# Função para identificar o usuário pelo Token
def get_user_id(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Token ausente")
    try:
        token = authorization.replace("Bearer ", "")
        return int(token.replace("user_", ""))
    except:
        raise HTTPException(status_code=401, detail="Token inválido")

# LISTAR MATERIAIS DO USUÁRIO
@router.get("/api/materiais")
def listar_materiais(db: Session = Depends(get_db), user_id: int = Depends(get_user_id)):
    return db.query(MaterialBase).filter(MaterialBase.usuario_id == user_id).all()

# ADICIONAR NOVO MATERIAL AO CATÁLOGO
@router.post("/api/materiais")
def adicionar_material(novo_material: MaterialCreate, db: Session = Depends(get_db), user_id: int = Depends(get_user_id)):
    # Verifica se já existe um material com esse 'slug' (ID interno) para esse usuário
    existente = db.query(MaterialBase).filter(
        MaterialBase.slug == novo_material.slug, 
        MaterialBase.usuario_id == user_id
    ).first()
    
    if existente:
        # Se já existe, apenas atualiza o preço e o nome
        existente.nome = novo_material.nome
        existente.preco = novo_material.preco
    else:
        # Se não existe, cria um novo
        material = MaterialBase(
            usuario_id=user_id,
            nome=novo_material.nome,
            slug=novo_material.slug,
            preco=novo_material.preco
        )
        db.add(material)
    
    db.commit()
    return {"message": "Material salvo com sucesso no seu catálogo VERO"}

# EXCLUIR MATERIAL DO CATÁLOGO
@router.delete("/api/materiais/{material_id}")
def deletar_material(material_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_user_id)):
    item = db.query(MaterialBase).filter(MaterialBase.id == material_id, MaterialBase.usuario_id == user_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Material não encontrado")
    db.delete(item)
    db.commit()
    return {"message": "Material removido"}
