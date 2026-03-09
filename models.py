from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey
from database import Base

class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)
    senha = Column(String)
    is_admin = Column(Boolean, default=False)

class MaterialBase(Base):
    __tablename__ = "materiais_base"
    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    slug = Column(String)
    nome = Column(String)
    preco = Column(Float)

class HistoricoOrcamento(Base):
    __tablename__ = "historico_orcamentos"
    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    nome_cliente = Column(String)
    categoria_servico = Column(String)
    valor_total = Column(Float)
    data_cadastro = Column(String)
    status = Column(String, default="Pendente")

class PerfilEmpresa(Base):
    __tablename__ = "perfil_empresa"
    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), unique=True)
    nome_fantasia = Column(String)
    telefone = Column(String)
    instagram = Column(String)
