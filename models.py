from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    senha = Column(String)
    is_admin = Column(Boolean, default=False)
    
    # Relacionamentos para facilitar a busca de dados do dono
    materiais = relationship("MaterialBase", back_populates="dono")
    orcamentos = relationship("HistoricoOrcamento", back_populates="dono")
    perfil = relationship("PerfilEmpresa", back_populates="dono", uselist=False)

class MaterialBase(Base):
    __tablename__ = "materiais_base"
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    slug = Column(String) # Identificador interno (ex: haste_cerca)
    nome = Column(String)
    preco = Column(Float)
    dono = relationship("Usuario", back_populates="materiais")

class HistoricoOrcamento(Base):
    __tablename__ = "historico_orcamentos"
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    nome_cliente = Column(String)
    categoria_servico = Column(String)
    valor_total = Column(Float)
    data_cadastro = Column(String)
    status = Column(String, default="Pendente")
    dono = relationship("Usuario", back_populates="orcamentos")

class PerfilEmpresa(Base):
    __tablename__ = "perfil_empresa"
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), unique=True)
    nome_fantasia = Column(String)
    telefone = Column(String)
    instagram = Column(String)
    dono = relationship("Usuario", back_populates="perfil")
