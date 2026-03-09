from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from database import engine, Base, SessionLocal
from routers import auth, servicos, dashboard, orcamentos

if engine:
    Base.metadata.create_all(bind=engine)

app = FastAPI(title="VERO SaaS")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_db():
    db = SessionLocal()
    # Migração segura para o Railway
    queries = [
        "ALTER TABLE historico_orcamentos ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'Pendente';",
        "ALTER TABLE historico_orcamentos ADD COLUMN IF NOT EXISTS usuario_id INTEGER;",
        "ALTER TABLE materiais_base ADD COLUMN IF NOT EXISTS usuario_id INTEGER;",
        "ALTER TABLE perfil_empresa ADD COLUMN IF NOT EXISTS usuario_id INTEGER;"
    ]
    for q in queries:
        try:
            db.execute(text(q))
            db.commit()
        except:
            db.rollback()
    db.close()

app.include_router(auth.router)
app.include_router(orcamentos.router)
# Inclua os outros conforme necessário
