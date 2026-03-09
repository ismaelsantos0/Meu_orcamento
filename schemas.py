from pydantic import BaseModel
from typing import List, Optional

class LoginRequest(BaseModel):
    email: str
    senha: str

class Item(BaseModel):
    nome: str
    quantidade: int
    preco_unitario: float

class Requisicao(BaseModel):
    nome_cliente: str
    categoria_servico: str
    itens: List[Item]
    valor_mao_de_obra: float
    desconto_percentual: Optional[float] = 0.0

class RequisicaoCerca(BaseModel):
    nome_cliente: str
    metros: float
    distancia_haste: float
    tipo: str
    tem_central: bool
    valor_mao_de_obra: float

class AtualizarStatusRequest(BaseModel):
    status: str

# NOVO: Schema para o Catálogo de Materiais
class MaterialCreate(BaseModel):
    nome: str
    slug: str
    preco: float
