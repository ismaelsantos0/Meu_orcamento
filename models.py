from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

# 1. TABELA DE USUÁRIOS (A base de tudo)
class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    senha = Column(String)
    is_admin = Column(Boolean, default=False)
    
    # Relacionamentos (Opcional, mas ajuda o SQLAlchemy a organizar os dados)
    materiais = relationship("MaterialBase", back_populates="dono")
    orcamentos = relationship("HistoricoOrcamento", back_populates="dono")
    perfil = relationship("PerfilEmpresa", back_populates="dono", uselist=False)

# 2. TABELA DE MATERIAIS (Catálogo customizado por usuário)
class MaterialBase(Base):
    __tablename__ = "materiais_base"
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id")) # FK para o dono
    slug = Column(String) # Ex: 'haste_cerca', 'fio_aco'
    nome = Column(String)
    preco = Column(Float)

    dono = relationship("Usuario", back_populates="materiais")

# 3. TABELA DE ORÇAMENTOS (Histórico privado)
class HistoricoOrcamento(Base):
    __tablename__ = "historico_orcamentos"
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id")) # FK para o dono
    nome_cliente = Column(String)
    categoria_servico = Column(String)
    valor_total = Column(Float)
    data_cadastro = Column(String)
    status = Column(String, default="Pendente") # Pendente ou Aprovado

    dono = relationship("Usuario", back_populates="orcamentos")

# 4. TABELA DE PERFIL (Dados da empresa do usuário)
class PerfilEmpresa(Base):
    __tablename__ = "perfil_empresa"
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), unique=True)
    nome_fantasia = Column(String)
    telefone = Column(String)
    instagram = Column(String)

    dono = relationship("Usuario", back_populates="perfil")

# 5. TABELA DE SERVIÇOS AVULSOS (Para o catálogo de botões manuais)
class Servico(Base):
    __tablename__ = "servicos"
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    codigo = Column(String) # Ex: 'MAN01'
    nome = Column(String)
    preco_base = Column(Float)
    categoria = Column(String)
