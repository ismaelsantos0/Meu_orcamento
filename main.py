import hashlib
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from database import engine, Base, SessionLocal
from models import Usuario, PerfilEmpresa, MaterialBase
from routers import auth, servicos, dashboard, orcamentos

if engine:
    Base.metadata.create_all(bind=engine)

app = FastAPI(title="VERO SaaS")

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
    
    # 1. Migração Forçada de Colunas
    queries = [
        "ALTER TABLE historico_orcamentos ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'Pendente';",
        "ALTER TABLE historico_orcamentos ADD COLUMN IF NOT EXISTS usuario_id INTEGER;",
        "ALTER TABLE servicos ADD COLUMN IF NOT EXISTS usuario_id INTEGER;",
        "ALTER TABLE materiais_base ADD COLUMN IF NOT EXISTS usuario_id INTEGER;",
        "ALTER TABLE perfil_empresa ADD COLUMN IF NOT EXISTS usuario_id INTEGER;"
    ]
    for q in queries:
        try:
            db.execute(text(q))
            db.commit()
        except:
            db.rollback()

    # 2. Garante o SEU usuário (ismaelifrr@gmail.com)
    meu_email = "ismaelifrr@gmail.com"
    user = db.query(Usuario).filter(Usuario.email == meu_email).first()
    if not user:
        user = Usuario(email=meu_email, senha=hashlib.sha256("Admin@123".encode()).hexdigest(), is_admin=True)
        db.add(user)
        db.commit()
        db.refresh(user)

    # 3. Dá dono aos dados órfãos
    db.execute(text(f"UPDATE historico_orcamentos SET usuario_id = {user.id} WHERE usuario_id IS NULL"))
    db.execute(text(f"UPDATE materiais_base SET usuario_id = {user.id} WHERE usuario_id IS NULL"))
    db.commit()

    # 4. Injeta Preços se estiverem vazios para o seu ID
    if not db.query(MaterialBase).filter(MaterialBase.usuario_id == user.id).first():
        precos = [
            ("haste_cerca", "Haste de Cerca 1m", 19.00),
            ("fio_aco", "Fio de Aço (Rolo 200m)", 80.00),
            ("concertina_30cm", "Rolo Concertina 30cm (10m)", 90.00),
            ("concertina_linear", "Rolo Concertina Linear (20m)", 53.00),
            ("central_sh1800", "Central Eletrificadora", 310.00),
            ("bateria", "Bateria 7A", 83.00),
            ("sirene", "Sirene", 2.00),
            ("kit_aterramento", "Kit Aterramento", 45.00),
            ("fio_alta_tensao", "Cabo Alta Tensão (50m)", 90.00)
        ]
        for s, n, p in precos:
            db.add(MaterialBase(usuario_id=user.id, slug=s, nome=n, preco=p))
        db.commit()

    db.close()

app.include_router(auth.router)
app.include_router(servicos.router)
app.include_router(dashboard.router)
app.include_router(orcamentos.router)

@app.get("/")
def health_check():
    return {"status": "online", "message": "VERO SaaS Ativo"}
