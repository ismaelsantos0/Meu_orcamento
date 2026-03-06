import os
import io
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float, desc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# --- CONFIGURAÇÃO DO BANCO DE DADOS ---
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- MODELO DE DADOS ---
class HistoricoOrcamento(Base):
    __tablename__ = "historico_orcamentos"
    id = Column(Integer, primary_key=True)
    nome_cliente = Column(String)
    categoria_servico = Column(String)
    valor_total = Column(Float)
    data_criacao = Column(String)

# Cria as tabelas no banco de dados se não existirem
Base.metadata.create_all(bind=engine)

# --- INICIALIZAÇÃO DO APP ---
app = FastAPI(
    title="VERO API - Dashboard Edition",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configuração de Permissões (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependência do Banco
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- SCHEMAS (Formatos de Dados) ---
class Item(BaseModel):
    nome: str
    quantidade: int
    preco_unitario: float

class Requisicao(BaseModel):
    nome_cliente: str
    categoria_servico: str
    itens: list[Item]
    valor_mao_de_obra: float

# --- ROTAS ---

@app.get("/")
def home():
    return {"status": "online", "message": "VERO API está rodando perfeitamente", "docs": "/docs"}

@app.get("/api/dashboard")
def dashboard(db: Session = Depends(get_db)):
    try:
        orcamentos = db.query(HistoricoOrcamento).all()
        total = len(orcamentos)
        faturamento = sum(o.valor_total for o in orcamentos)
        
        # Pega os 5 orçamentos mais recentes
        recentes_query = db.query(HistoricoOrcamento).order_by(desc(HistoricoOrcamento.id)).limit(5).all()
        
        return {
            "faturamento_mes": faturamento,
            "total_orcamentos": total,
            "ticket_medio": faturamento / total if total > 0 else 0,
            "recentes": [
                {
                    "id": o.id,
                    "nome_cliente": o.nome_cliente,
                    "categoria_servico": o.categoria_servico,
                    "valor_total": o.valor_total,
                    "data_criacao": o.data_criacao
                } for o in recentes_query
            ]
        }
    except Exception as e:
        # Se der erro, o servidor não crasha, ele te avisa o porquê
        print(f"DEBUG DASHBOARD: {str(e)}")
        return {
            "faturamento_mes": 0,
            "total_orcamentos": 0,
            "ticket_medio": 0,
            "recentes": [],
            "error_detail": str(e)
        }

@app.post("/api/gerar-orcamento")
async def gerar(pedido: Requisicao, db: Session = Depends(get_db)):
    try:
        total_materiais = sum(i.quantidade * i.preco_unitario for i in pedido.itens)
        total_geral = total_materiais + pedido.valor_mao_de_obra
        
        # 1. Salva no banco de dados primeiro
        novo_registro = HistoricoOrcamento(
            nome_cliente=pedido.nome_cliente,
            categoria_servico=pedido.categoria_servico,
            valor_total=total_geral,
            data_criacao=datetime.now().strftime("%d/%m/%Y %H:%M")
        )
        db.add(novo_registro)
        db.commit()

        # 2. Gera o PDF para o usuário
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        p.setFont("Helvetica-Bold", 16)
        p.drawString(100, 800, f"VERO - ORÇAMENTO")
        p.setFont("Helvetica", 12)
        p.drawString(100, 770, f"Cliente: {pedido.nome_cliente}")
        p.drawString(100, 750, f"Serviço: {pedido.categoria_servico}")
        p.drawString(100, 730, f"Total: R$ {total_geral:.2f}")
        p.showPage()
        p.save()
        buffer.seek(0)
        
        return StreamingResponse(buffer, media_type="application/pdf")
    except Exception as e:
        print(f"DEBUG ORÇAMENTO: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
