import hashlib
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from database import engine, Base, SessionLocal
from models import Usuario, MaterialBase
from routers import auth, servicos, dashboard, orcamentos

if engine:
    Base.metadata.create_all(bind=engine)

app = FastAPI(title="VERO SaaS API")

# 1. Configuração de CORS (Essencial para o Lovable não ser bloqueado)
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
    
    # 2. MIGRAÇÕES: Força a criação das colunas no Railway
    migrations = [
        "ALTER TABLE historico_orcamentos ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'Pendente';",
        "ALTER TABLE historico_orcamentos ADD COLUMN IF NOT EXISTS usuario_id INTEGER;",
        "ALTER TABLE materiais_base ADD COLUMN IF NOT EXISTS usuario_id INTEGER;",
        "ALTER TABLE perfil_empresa ADD COLUMN IF NOT EXISTS usuario_id INTEGER;",
        "ALTER TABLE servicos ADD COLUMN IF NOT EXISTS usuario_id INTEGER;"
    ]
    for q in migrations:
        try:
            db.execute(text(q))
            db.commit()
        except:
            db.rollback()

    # 3. RECUPERAÇÃO DE DADOS: Vincula tudo ao seu e-mail
    # IMPORTANTE: Verifique se este é o e-mail que você usa para logar!
    meu_email = "ismaelifrr@gmail.com" 
    user = db.query(Usuario).filter(Usuario.email == meu_email).first()
    
    if user:
        # Vincula materiais e orçamentos que ficaram sem dono
        res_mat = db.execute(text(f"UPDATE materiais_base SET usuario_id = {user.id} WHERE usuario_id IS NULL"))
        res_orc = db.execute(text(f"UPDATE historico_orcamentos SET usuario_id = {user.id} WHERE usuario_id IS NULL"))
        db.commit()
        print(f"✅ VERO: {res_mat.rowcount} materiais e {res_orc.rowcount} orçamentos vinculados ao usuário {user.id}")
    else:
        print(f"⚠️ VERO: Usuário {meu_email} não encontrado para vincular dados antigos.")

    db.close()

app.include_router(auth.router)
app.include_router(servicos.router)
app.include_router(dashboard.router)
app.include_router(orcamentos.router)
