import os
import io
import hashlib
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# ==========================================
# IMPORTANDO SEUS SCRIPTS DA PASTA SERVICES
# (O main.py precisa conhecer suas funções)
# ==========================================
# Descomente e ajuste os nomes das funções conforme os seus arquivos reais:
# from services.cftv_install import calcular_cftv
# from services.gate_motor_install import calcular_motor
# from services.fence_concertina import calcular_concertina
# ==========================================

# --- SEGURANÇA ---
def gerar_hash(senha: str):
    return hashlib.sha256(senha.encode()).hexdigest()

# --- CONEXÃO BANCO ---
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- MODELOS ---
class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True)
    email = Column(String)
    telefone = Column(String)
    senha = Column(String)
    is_admin = Column(Boolean)
    data_cadastro = Column(String)

class PerfilEmpresa(Base):
    __tablename__ = "perfil_empresa"
    id = Column(Integer, primary_key=True)
    nome_fantasia = Column(String)
    telefone = Column(String)
    instagram = Column(String)

class Servico(Base):
    __tablename__ = "servicos"
    id = Column(Integer, primary_key=True)
    codigo = Column(String)
    nome = Column(String)
    preco_base = Column(Float)
    categoria = Column(String)

app = FastAPI(title="VERO Smart Systems")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

# --- SCHEMAS ---
class LoginRequest(BaseModel):
    email: str
    senha: str

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

# --- LOGIN ---
@app.post("/api/login")
def login(dados: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(Usuario).filter(Usuario.email == dados.email.strip().lower()).first()
    if not user or gerar_hash(dados.senha.strip()) != user.senha:
        raise HTTPException(status_code=401, detail="Credenciais incorretas")
    return {
        "access_token": "vero_2026", 
        "user": {"email": user.email, "telefone": user.telefone, "is_admin": user.is_admin}
    }

# --- DADOS ---
@app.get("/api/servicos")
def listar(db: Session = Depends(get_db)):
    return db.query(Servico).all()

@app.get("/api/perfil")
def perfil(db: Session = Depends(get_db)):
    return db.query(PerfilEmpresa).first()

# --- ROTEADOR E GERAÇÃO DE PDF ---
@app.post("/api/gerar-orcamento")
async def gerar_orcamento(pedido: RequisicaoOrcamento, db: Session = Depends(get_db)):
    empresa = db.query(PerfilEmpresa).first()
    if not empresa: 
        raise HTTPException(status_code=400, detail="Perfil da empresa ausente.")
    
    categoria = pedido.categoria_servico.lower()
    
    # 1. DELEGAÇÃO: Manda os dados para o arquivo certo na pasta services
    try:
        # EXEMPLO DE ROTEAMENTO (Você vai plugar suas funções reais aqui):
        # if "cftv" in categoria:
        #     resultado_calculo = calcular_cftv(pedido.itens, db)
        # elif "concertina" in categoria:
        #     resultado_calculo = calcular_concertina(pedido.itens, db)
        # else:
        
        # Como as importações ainda estão comentadas, faremos um cálculo padrão genérico por enquanto:
        resultado_calculo = {
            "itens_processados": [{"nome": i.nome, "quantidade": i.quantidade, "subtotal": i.quantidade * i.preco_unitario} for i in pedido.itens],
            "total_materiais": sum(i.quantidade * i.preco_unitario for i in pedido.itens),
            "mao_de_obra": pedido.valor_mao_de_obra
        }
    except Exception as e:
         raise HTTPException(status_code=500, detail=f"Erro no cálculo: {str(e)}")

    total_geral = resultado_calculo["total_materiais"] + resultado_calculo["mao_de_obra"]

    # 2. DESENHO DO PDF
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, 800, str(empresa.nome_fantasia).upper())
    p.setFont("Helvetica", 10)
    p.drawString(50, 785, f"Contato: {empresa.telefone} | Instagram: {empresa.instagram}")
    p.line(50, 775, 550, 775)
    
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, 750, f"CLIENTE: {pedido.nome_cliente}")
    p.drawString(50, 735, f"SERVIÇO: {pedido.categoria_servico}")
    
    y = 700
    p.drawString(50, y, "ITEM")
    p.drawRightString(540, y, "VALOR")
    p.line(50, y-5, 550, y-5)
    y -= 25
    
    p.setFont("Helvetica", 11)
    for item in resultado_calculo["itens_processados"]:
        p.drawString(50, y, f"{item['quantidade']}x {item['nome']}")
        p.drawRightString(540, y, f"R$ {item['subtotal']:.2f}")
        y -= 20
        
    p.line(50, y, 550, y)
    y -= 30
    
    p.drawString(50, y, "Mão de Obra:")
    p.drawRightString(540, y, f"R$ {resultado_calculo['mao_de_obra']:.2f}")
    y -= 25
    
    p.setFont("Helvetica-Bold", 14)
    p.drawString(300, y, f"TOTAL GERAL: R$ {total_geral:.2f}")
    
    p.showPage()
    p.save()
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/pdf")
