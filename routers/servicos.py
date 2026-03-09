from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import Servico

router = APIRouter()

@router.get("/api/servicos")
def listar_servicos(db: Session = Depends(get_db)):
    return db.query(Servico).all()
