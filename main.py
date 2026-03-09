import hashlib
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base, SessionLocal
from models import Usuario, PerfilEmpresa, MaterialBase, Servico
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

    # 3. Cria Tabela Base de Preços Oculta com os Slugs Fidedignos
    if not db.query(MaterialBase).first():
        precos_iniciais = [
            ("haste_cerca", "Haste de Cerca 1m", 19.00),
            ("haste_canto", "Haste de Canto", 50.00),
            ("fio_aco", "Fio de Aço (Rolo)", 80.00),
            ("central_sh1800", "Central SH1800", 310.00),
            ("bateria", "Bateria 7A", 83.00),
            ("sirene", "Sirene", 2.00),
            ("concertina_30cm", "Rolo Concertina 30cm (10m)", 90.00),
            ("concertina_linear", "Rolo Concertina Linear (20m - 6 fios)", 53.00),
            ("kit_aterramento", "Kit Aterramento", 45.00)
        ]
        for slug, nome, preco in precos_iniciais:
            if not db.query(MaterialBase).filter(MaterialBase.slug == slug).first():
                db.add(MaterialBase(slug=slug, nome=nome, preco=preco))

    # 4. Injeta os produtos no Catálogo Visível
    if not db.query(Servico).first():
        catalogo_inicial = [
            ("CER01", "Haste de Cerca 1m", 19.00, "Cerca"),
            ("CER02", "Haste de Canto", 50.00, "Cerca"),
            ("CER03", "Fio de Aço (Rolo)", 80.00, "Cerca"),
            ("CER04", "Central SH1800", 310.00, "Segurança"),
            ("CER05", "Bateria 7A", 83.00, "Segurança"),
            ("CER06", "Sirene", 2.00, "Segurança"),
            ("CER07", "Rolo Concertina 30cm (10m)", 90.00, "Cerca"),
            ("CER08", "Rolo Concertina Linear (20m)", 53.00, "Cerca"),
            ("CER09", "Kit Aterramento", 45.00, "Segurança")
        ]
        for codigo, nome, preco, categoria in catalogo_inicial:
             if not db.query(Servico).filter(Servico.codigo == codigo).first():
                db.add(Servico(codigo=codigo, nome=nome, preco_base=preco, categoria=categoria))

    db.commit()
    db.close()

app.include_router(auth.router)
app.include_router(servicos.router)
app.include_router(dashboard.router)
app.include_router(orcamentos.router)

@app.get("/")
def health_check():
    return {"status": "online", "message": "VERO API - Arquitetura de IDs robusta aplicada!"}
