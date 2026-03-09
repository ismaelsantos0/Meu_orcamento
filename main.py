import hashlib
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base, SessionLocal
from models import Usuario
from routers import auth, servicos, dashboard, orcamentos

# Cria as tabelas
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

# Cria o admin no momento em que o servidor liga
@app.on_event("startup")
def startup_db():
    if not engine: return
    db = SessionLocal()
    admin_existente = db.query(Usuario).filter(Usuario.email == "admin@vero.com").first()
    if not admin_existente:
        novo_admin = Usuario(
            email="admin@vero.com",
            senha=hashlib.sha256("Admin@123".encode()).hexdigest(),
            is_admin=True
        )
        db.add(novo_admin)
        db.commit()
    db.close()

# Conecta todas as rotas que criamos nas outras pastas
app.include_router(auth.router)
app.include_router(servicos.router)
app.include_router(dashboard.router)
app.include_router(orcamentos.router)

@app.get("/")
def health_check():
    return {"status": "online", "message": "VERO API Organizada"}
