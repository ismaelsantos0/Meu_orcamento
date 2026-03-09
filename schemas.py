from pydantic import BaseModel
from typing import List

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

# NOVO: Molde para o cálculo automático de cerca
class RequisicaoCerca(BaseModel):
    nome_cliente: str
    metros: float
    distancia_haste: float
    tipo: str  # "simples", "com_concertina" ou "concertina_linear"
    tem_central: bool
    valor_mao_de_obra: float
