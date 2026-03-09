import os
import io
import hashlib
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, desc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# Se você já tiver a função de cálculo pronta, importe aqui:
# from services.fence import calcular_cerca_completa 

# --- BANCO DE DADOS ---
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- SEGURANÇA ---
def gerar_hash(senha: str):
    return hashlib.sha256(senha.encode()).hexdigest()

# --- MODELOS ---
class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)
    senha = Column(String)
    is_admin = Column(Boolean, default=True)

class HistoricoOrcamento(Base):
    __tablename__ = "historico_orcamentos"
    id = Column(Integer, primary_key=True)
    nome_cliente = Column(String)
    categoria_servico = Column(String)
    valor_total = Column(Float)
    data_cadastro = Column(String)

# A TABELA DO CATÁLOGO QUE HAVIA FALTADO
class Servico(Base):
    __tablename__ = "servicos"
    id = Column(Integer, primary_key=True)
    codigo = Column(String)
    nome = Column(String)
    preco_base = Column(Float)
    categoria = Column(String)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="VERO API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

# --- CRIAÇÃO AUTOMÁTICA DO ADMIN ---
@app.on_event("startup")
def startup_db():
    db = SessionLocal()
    admin_existente = db.query(Usuario).filter(Usuario.email == "admin@vero.com").first()
    if not admin_existente:
        novo_admin = Usuario(
            email="admin@vero.com",
            senha=gerar_hash("Admin@123"),
            is_admin=True
        )
        db.add(novo_admin)
        db.commit()
    db.close()

# --- SCHEMAS ---
class LoginRequest(BaseModel):
    email: str
    senha: str

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

@app.post("/api/login")
def login(dados: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(Usuario).filter(Usuario.email == dados.email.strip().lower()).first()
    if not user or gerar_hash(dados.senha.strip()) != user.senha:
        raise HTTPException(status_code=401, detail="Credenciais incorretas")
    return {"access_token": "vero_2026", "user": {"email": user.email, "is_admin": user.is_admin}}

# A ROTA DO CATÁLOGO QUE HAVIA FALTADO
@app.get("/api/servicos")
def listar_servicos(db: Session = Depends(get_db)):
    return db.query(Servico).all()

@app.get("/api/dashboard")
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

@app.post("/api/gerar-orcamento")
async def gerar(pedido: Requisicao, db: Session = Depends(get_db)):
    total_materiais = sum(i.quantidade * i.preco_unitario for i in pedido.itens)
    total_geral = total_materiais + pedido.valor_mao_de_obra
    
    novo = HistoricoOrcamento(
        nome_cliente=pedido.nome_cliente,
        categoria_servico=pedido.categoria_servico,
        valor_total=total_geral,
        data_cadastro=datetime.now().strftime("%d/%m/%Y %H:%M")
    )
    db.add(novo)
    db.commit()

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    p.drawString(100, 800, f"VERO - Orcamento: {pedido.nome_cliente}")
    p.drawString(100, 780, f"Contato: (95) 98418-7832")
    p.drawString(100, 760, f"Total: R$ {total_geral:.2f}")
    p.showPage()
    p.save()
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/pdf")
