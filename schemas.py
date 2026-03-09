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
