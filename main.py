import hashlib
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base, SessionLocal
from models import Usuario, PerfilEmpresa, MaterialBase
from routers import auth, servicos, dashboard, orcamentos

if engine:
    Base.metadata.create_all(bind=engine)

app = FastAPI(title="VERO API")

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
    
    # 1. Cria Admin
    admin_existente = db.query(Usuario).filter(Usuario.email == "admin@vero.com").first()
    if not admin_existente:
        novo_admin = Usuario(email="admin@vero.com", senha=hashlib.sha256("Admin@123".encode()).hexdigest(), is_admin=True)
        db.add(novo_admin)

    # 2. Cria Perfil da Empresa
    perfil = db.query(PerfilEmpresa).first()
    if not perfil:
        novo_perfil = PerfilEmpresa(
            nome_fantasia="RR Smart Soluções", 
            telefone="+55 95 8418-7832", 
            instagram="@rr_smart_solucoes"
        )
        db.add(novo_perfil)

    # 3. Cria Tabela Base de Preços
    if not db.query(MaterialBase).first():
        precos_iniciais = [
            ("haste_cerca", "Haste de Cerca", 19.00),
            ("haste_canto", "Haste de Canto", 50.00),
            ("fio_aco", "Fio de Aço", 80.00),
            ("central_sh1800", "Central SH1800", 310.00),
            ("bateria", "Bateria", 83.00),
            ("sirene", "Sirene", 2.00),
            ("concertina_30cm", "Concertina 30cm", 90.00),
            ("concertina_linear", "Concertina Linear", 53.00)
        ]
        for slug, nome, preco in precos_iniciais:
            db.add(MaterialBase(slug=slug, nome=nome, preco=preco))

    db.commit()
    db.close()

app.include_router(auth.router)
app.include_router(servicos.router)
app.include_router(dashboard.router)
app.include_router(orcamentos.router)

@app.get("/")
def health_check():
    return {"status": "online", "message": "VERO API Organizada"}
