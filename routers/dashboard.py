from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc
from database import get_db
from models import HistoricoOrcamento

router = APIRouter()

@router.get("/api/dashboard")
def get_dashboard(db: Session = Depends(get_db)):
    try:
        dados = db.query(HistoricoOrcamento).all()
        faturamento = sum(d.valor_total for d in dados)
        recentes = db.query(HistoricoOrcamento).order_by(desc(HistoricoOrcamento.id)).limit(5).all()
        return {
            "faturamento_mes": faturamento,
            "total_orcamentos": len(dados),
            "ticket_medio": faturamento / len(dados) if len(dados) > 0 else 0,
            "recentes": recentes
        }
    except Exception as e:
        return {"error": str(e)}
