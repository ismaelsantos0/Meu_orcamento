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

    # 3. Tabela Base de Preços (Para o cálculo da cerca)
    if not db.query(MaterialBase).first():
        precos_iniciais = [
            ("haste_cerca", "Haste de Cerca 1m", 19.00),
            ("haste_canto", "Haste de Canto", 50.00),
            ("fio_aco", "Fio de Aço (Rolo 200m)", 80.00),
            ("concertina_30cm", "Rolo Concertina 30cm (10m)", 90.00),
            ("concertina_linear", "Rolo Concertina Linear (20m - 6 fios)", 53.00),
            ("central_sh1800", "Central SH1800", 310.00),
            ("bateria", "Bateria 7A", 83.00),
            ("sirene", "Sirene", 2.00),
            ("kit_aterramento", "Kit Aterramento", 45.00),
            ("arame_galvanizado", "Rolo Arame Galvanizado", 80.00),
            ("fio_alta_tensao", "Rolo Fio de Alta Tensão (50m)", 90.00),
            ("fio_paralelo", "Fio Paralelo (Metro)", 2.50),
            ("fio_sirene", "Fio para Sirene (Metro)", 4.00),
            ("fio_aterramento", "Fio para Aterramento (Metro)", 3.00)
        ]
        for slug, nome, preco in precos_iniciais:
            if not db.query(MaterialBase).filter(MaterialBase.slug == slug).first():
                db.add(MaterialBase(slug=slug, nome=nome, preco=preco))

    # 4. Catálogo Visível (Para os botões Manuais e de Manutenção no App)
    if not db.query(Servico).first():
        catalogo_inicial = [
            # MATERIAIS DE CERCA
            ("CER01", "Haste de Cerca 1m", 19.00, "Cerca"),
            ("CER02", "Haste de Canto", 50.00, "Cerca"),
            ("CER03", "Fio de Aço (Rolo 200m)", 80.00, "Cerca"),
            ("CER04", "Central SH1800", 310.00, "Segurança"),
            ("CER05", "Bateria 7A", 83.00, "Segurança"),
            ("CER06", "Sirene", 2.00, "Segurança"),
            ("CER07", "Rolo Concertina 30cm (10m)", 90.00, "Cerca"),
            ("CER08", "Rolo Concertina Linear (20m)", 53.00, "Cerca"),
            ("CER09", "Kit Aterramento", 45.00, "Segurança"),
            ("CER10", "Rolo Arame Galvanizado", 80.00, "Cerca"),
            ("CER11", "Rolo Fio de Alta Tensão (50m)", 90.00, "Cerca"),
            
            # PACOTES DE MANUTENÇÃO (BOTÕES RÁPIDOS)
            ("MAN01", "Visita Técnica / Deslocamento", 50.00, "Manutenção"),
            ("MAN02", "Manutenção Preventiva (Ajustes e Limpeza)", 150.00, "Manutenção"),
            ("MAN03", "Reparo de Fio Rompido (Por Lance)", 120.00, "Manutenção"),
            ("MAN04", "Mão de Obra - Troca de Bateria", 80.00, "Manutenção"),
            ("MAN05", "Mão de Obra - Troca de Placa/Central", 150.00, "Manutenção"),
            ("MAN06", "Mão de Obra - Troca de Haste/Isolador (Unidade)", 30.00, "Manutenção")
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
    return {"status": "online", "message": "VERO API - Manutenção e Matemática Ativas"}
