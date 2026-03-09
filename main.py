import hashlib
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from database import engine, Base, SessionLocal
from models import Usuario, PerfilEmpresa, MaterialBase, Servico
from routers import auth, servicos, dashboard, orcamentos

# Tenta criar as tabelas novas (como a de Usuários se não existir)
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
    
    # --- BLOCO DE MIGRAÇÃO MANUAL (FORÇANDO AS COLUNAS NO RAILWAY) ---
    # Isso resolve o erro 'column does not exist' adicionando-as via SQL Puro
    migrations = [
        "ALTER TABLE historico_orcamentos ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'Pendente';",
        "ALTER TABLE historico_orcamentos ADD COLUMN IF NOT EXISTS usuario_id INTEGER REFERENCES usuarios(id);",
        "ALTER TABLE servicos ADD COLUMN IF NOT EXISTS usuario_id INTEGER REFERENCES usuarios(id);",
        "ALTER TABLE materiais_base ADD COLUMN IF NOT EXISTS usuario_id INTEGER REFERENCES usuarios(id);",
        "ALTER TABLE perfil_empresa ADD COLUMN IF NOT EXISTS usuario_id INTEGER REFERENCES usuarios(id);"
    ]
    
    for query in migrations:
        try:
            db.execute(text(query))
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"Aviso de Migração: {e}") # Geralmente significa que a coluna já existe

    # --- INJEÇÃO DE DADOS INICIAIS ---
    
    # 1. Usuário Admin Padrão
    admin_email = "admin@vero.com"
    if not db.query(Usuario).filter(Usuario.email == admin_email).first():
        db.add(Usuario(
            email=admin_email, 
            senha=hashlib.sha256("Admin@123".encode()).hexdigest(), 
            is_admin=True
        ))
        db.commit()

    # Pega o ID do admin para vincular os dados iniciais
    admin_user = db.query(Usuario).filter(Usuario.email == admin_email).first()

    # 2. Perfil de Empresa (Vinculado ao Admin)
    if not db.query(PerfilEmpresa).filter(PerfilEmpresa.usuario_id == admin_user.id).first():
        db.add(PerfilEmpresa(
            usuario_id=admin_user.id,
            nome_fantasia="RR Smart Soluções", #
            telefone="+55 95 8418-7832", 
            instagram="@rr_smart_solucoes"
        ))

    # 3. Materiais de Cálculo (Vinculados ao Admin)
    if not db.query(MaterialBase).filter(MaterialBase.usuario_id == admin_user.id).first():
        precos = [
            ("haste_cerca", "Haste de Cerca 1m", 19.00),
            ("fio_aco", "Fio de Aço (Rolo 200m)", 80.00),
            ("concertina_30cm", "Rolo Concertina 30cm (10m)", 90.00),
            ("concertina_linear", "Rolo Concertina Linear (20m)", 53.00),
            ("central_sh1800", "Central Eletrificadora", 310.00),
            ("bateria", "Bateria 7A", 83.00),
            ("sirene", "Sirene", 2.00),
            ("kit_aterramento", "Kit Aterramento", 45.00),
            ("arame_galvanizado", "Arame Galvanizado", 80.00),
            ("fio_alta_tensao", "Cabo Alta Tensão (50m)", 90.00),
            ("fio_paralelo", "Fio Paralelo (m)", 2.50),
            ("fio_sirene", "Fio Sirene (m)", 4.00),
            ("fio_aterramento", "Fio Aterramento (m)", 3.00)
        ]
        for s, n, p in precos:
            db.add(MaterialBase(usuario_id=admin_user.id, slug=s, nome=n, preco=p))

    db.commit()
    db.close()

app.include_router(auth.router)
app.include_router(servicos.router)
app.include_router(dashboard.router)
app.include_router(orcamentos.router)

@app.get("/")
def health_check():
    return {"status": "online", "message": "VERO SaaS - Migrações de Banco Aplicadas"}
