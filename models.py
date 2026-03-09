from sqlalchemy import Column, Integer, String, Float, Boolean
from database import Base

class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)
    senha = Column(String)
    is_admin = Column(Boolean, default=True)

class Servico(Base):
    __tablename__ = "servicos"
    id = Column(Integer, primary_key=True)
    codigo = Column(String)
    nome = Column(String)
    preco_base = Column(Float)
    categoria = Column(String)

class HistoricoOrcamento(Base):
    __tablename__ = "historico_orcamentos"
    id = Column(Integer, primary_key=True)
    nome_cliente = Column(String)
    categoria_servico = Column(String)
    valor_total = Column(Float)
    data_cadastro = Column(String)

class PerfilEmpresa(Base):
    __tablename__ = "perfil_empresa"
    id = Column(Integer, primary_key=True)
    nome_fantasia = Column(String)
    telefone = Column(String)
    instagram = Column(String)

class MaterialBase(Base):
    __tablename__ = "materiais_base"
    id = Column(Integer, primary_key=True)
    slug = Column(String, unique=True)
    nome = Column(String)
    preco = Column(Float)
