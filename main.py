import os
import io
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, ForeignKey
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

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- MODELOS DO BANCO DE DADOS (REGRAS DE PERFIL E PRODUTOS) ---

class PerfilEmpresa(Base):
    __tablename__ = "perfil_empresa"
    id = Column(Integer, primary_key=True, index=True)
    nome_fantasia = Column(String, default="RR Smart Soluções")
    telefone = Column(String, default="+55 95 8418-7832")
    instagram = Column(String, default="@rr_smart_solucoes")
    logotipo_url = Column(String, nullable=True)

class Servico(Base):
    __tablename__ = "servicos"
    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, unique=True, index=True)
    nome = Column(String)
    descricao = Column(Text)
    preco_base = Column(Float)
    categoria = Column(String) # Ex: CFTV, Alarme, Automação

# Cria as tabelas no Railway
Base.metadata.create_all(bind=engine)

# --- SCHEMAS PARA O FASTAPI (PYDANTIC) ---

class ItemPedido(BaseModel):
    codigo: str
    nome: str
    quantidade: int
    preco_unitario: float

class RequisicaoOrcamento(BaseModel):
    nome_cliente: str
    whatsapp_cliente: str
    categoria_servico: str
    itens: list[ItemPedido]
    valor_mao_de_obra: float

# --- INICIALIZAÇÃO APP ---

app = FastAPI(title="VERO Smart Systems API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependência para o Banco
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- ROTAS ---

@app.get("/")
def health_check():
    return {"status": "Vero API Online", "database": "Conectado"}

@app.get("/api/perfil")
def obter_perfil(db: Session = Depends(get_db)):
    perfil = db.query(PerfilEmpresa).first()
    if not perfil:
        # Cria um perfil padrão se o banco estiver vazio
        novo_perfil = PerfilEmpresa()
        db.add(novo_perfil)
        db.commit()
        return novo_perfil
    return perfil

@app.get("/api/servicos")
def listar_servicos(db: Session = Depends(get_db)):
    return db.query(Servico).all()

@app.post("/api/gerar-orcamento")
async def gerar_orcamento(pedido: RequisicaoOrcamento, db: Session = Depends(get_db)):
    # Busca dados da RR Smart Soluções no Banco
    empresa = db.query(PerfilEmpresa).first()
    
    total_materiais = sum(item.quantidade * item.preco_unitario for item in pedido.itens)
    total_geral = total_materiais + pedido.valor_mao_de_obra
    
    # Geração do PDF via ReportLab
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    
    # Cabeçalho dinâmico vindo do Banco
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, 800, "ORÇAMENTO PROFISSIONAL")
    p.setFont("Helvetica", 10)
    p.drawString(50, 785, f"{empresa.nome_fantasia if empresa else 'RR Smart Soluções'}")
    p.drawString(50, 770, f"WhatsApp: {empresa.telefone if empresa else '95 98418-7832'}")
    
    p.line(50, 755, 550, 755)
    
    # Dados do Cliente
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, 730, f"Cliente: {pedido.nome_cliente}")
    p.setFont("Helvetica", 11)
    p.drawString(50, 715, f"Contato: {pedido.whatsapp_cliente}")
    
    # Itens
    y = 670
    p.drawString(50, 690, "Descrição dos Serviços/Produtos")
    p.line(50, 685, 550, 685)
    
    for item in pedido.itens:
        p.drawString(50, y, f"{item.quantidade}x {item.nome}")
        p.drawRightString(540, y, f"R$ {item.quantidade * item.preco_unitario:.2f}")
        y -= 20
        
    p.line(50, y, 550, y)
    y -= 30
    p.setFont("Helvetica-Bold", 14)
    p.drawString(300, y, f"TOTAL GERAL: R$ {total_geral:.2f}")
    
    p.showPage()
    p.save()
    buffer.seek(0)
    
    return StreamingResponse(buffer, media_type="application/pdf")
