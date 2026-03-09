import hashlib
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base, SessionLocal
from models import Usuario, PerfilEmpresa, MaterialBase, Servico
from routers import auth, servicos, dashboard, orcamentos

if engine:
    Base.metadata.create_all(bind=engine)

app = FastAPI(title="VERO SaaS API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_db():
    if not engine: return
    db = SessionLocal()
    
    # 1. Usuário Admin do Sistema
    if not db.query(Usuario).first():
        db.add(Usuario(
            email="admin@vero.com", 
            senha=hashlib.sha256("Admin@123".encode()).hexdigest(), 
            is_admin=True
        ))

    # 2. Perfil de Empresa Padrão (Editável pelo usuário depois)
    if not db.query(PerfilEmpresa).first():
        db.add(PerfilEmpresa(
            nome_fantasia="Minha Empresa VERO", 
            telefone="+55 00 0000-0000", 
            instagram="@vero.sistema"
        ))

    # 3. Base de Materiais e Preços para o Motor de Cálculo
    if not db.query(MaterialBase).first():
        precos = [
            ("haste_cerca", "Haste de Cerca 1m", 19.00),
            ("fio_aco", "Fio de Aço (Rolo 200m)", 80.00),
            ("concertina_30cm", "Concertina 30cm (10m)", 90.00),
            ("concertina_linear", "Concertina Linear (20m)", 53.00),
            ("central_sh1800", "Central Eletrificadora", 310.00),
            ("bateria", "Bateria 7A", 83.00),
            ("sirene", "Sirene", 2.00),
            ("kit_aterramento", "Kit Aterramento", 45.00),
            ("arame_galvanizado", "Arame Galvanizado (Sustentação)", 80.00),
            ("fio_alta_tensao", "Cabo de Alta Tensão (50m)", 90.00),
            ("fio_paralelo", "Fio Paralelo (Metro)", 2.50),
            ("fio_sirene", "Fio para Sirene (Metro)", 4.00),
            ("fio_aterramento", "Fio para Aterramento (Metro)", 3.00)
        ]
        for s, n, p in precos:
            db.add(MaterialBase(slug=s, nome=n, preco=p))

    # 4. Serviços de Manutenção Iniciais do VERO
    if not db.query(Servico).first():
        manutencao = [
            ("MAN01", "Visita Técnica / Deslocamento", 50.00, "Manutenção"),
            ("MAN02", "Manutenção Preventiva", 150.00, "Manutenção"),
            ("MAN03", "Reparo de Fio Rompido", 120.00, "Manutenção"),
            ("MAN04", "Troca de Bateria (Mão de Obra)", 80.00, "Manutenção")
        ]
        for c, n, p, cat in manutencao:
            db.add(Servico(codigo=c, nome=n, preco_base=p, categoria=cat))

    db.commit()
    db.close()

app.include_router(auth.router)
app.include_router(servicos.router)
app.include_router(dashboard.router)
app.include_router(orcamentos.router)

@app.get("/")
def health_check():
    return {"status": "online", "message": "VERO SaaS Engine - Ativo"}
