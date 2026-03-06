import os
import io
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float, desc, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# --- BANCO DE DADOS ---
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Se não houver banco, o app não crasha, ele avisa
engine = None
if DATABASE_URL:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
else:
    print("ERRO: DATABASE_URL não configurada!")

Base = declarative_base()

class HistoricoOrcamento(Base):
    __tablename__ = "historico_orcamentos"
    id = Column(Integer, primary_key=True)
    nome_cliente = Column(String)
    categoria_servico = Column(String)
    valor_total = Column(Float)
    data_criacao = Column(String)

app = FastAPI(title="VERO API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Tenta criar a tabela toda vez que o servidor liga, mas sem travar o app
@app.on_event("startup")
def startup():
    if engine:
        try:
            Base.metadata.create_all(bind=engine)
            print("Tabelas verificadas/criadas com sucesso!")
        except Exception as e:
            print(f"Erro ao criar tabelas: {e}")

def get_db():
    if not engine:
        raise HTTPException(status_code=500, detail="Banco não configurado")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- ROTAS ---

@app.get("/api/dashboard")
def dashboard(db: Session = Depends(get_db)):
    try:
        # Teste de conexão simples
        db.execute(text("SELECT 1"))
        
        orcamentos = db.query(HistoricoOrcamento).all()
        faturamento = sum(o.valor_total for o in orcamentos)
        
        return {
            "faturamento_mes": faturamento,
            "total_orcamentos": len(orcamentos),
            "ticket_medio": faturamento / len(orcamentos) if len(orcamentos) > 0 else 0,
            "recentes": orcamentos[-5:] if orcamentos else []
        }
    except Exception as e:
        print(f"ERRO DASHBOARD: {e}")
        return {"error": str(e), "status": "500_internal_db_error"}

@app.post("/api/gerar-orcamento")
async def gerar(pedido: dict, db: Session = Depends(get_db)):
    # Rota ultra simplificada para teste de gravação
    try:
        total = sum(i['quantidade'] * i['preco_unitario'] for i in pedido['itens']) + pedido['valor_mao_de_obra']
        novo = HistoricoOrcamento(
            nome_cliente=pedido['nome_cliente'],
            categoria_servico=pedido['categoria_servico'],
            valor_total=total,
            data_criacao=datetime.now().strftime("%d/%m/%Y %H:%M")
        )
        db.add(novo)
        db.commit()
        return {"status": "sucesso", "valor": total}
    except Exception as e:
        return {"status": "erro", "detalhe": str(e)}
