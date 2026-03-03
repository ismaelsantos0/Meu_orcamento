from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(title="VERO Smart Systems API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ItemOrcamento(BaseModel):
    id_produto: int
    nome: str
    quantidade: int
    preco_unitario: float

class PedidoOrcamento(BaseModel):
    nome_cliente: str
    whatsapp_cliente: str
    categoria_servico: str
    itens: list[ItemOrcamento]
    valor_mao_de_obra: float

@app.get("/")
def home():
    return {"status": "VERO API Online e Operante no Railway!"}

@app.post("/api/gerar-orcamento")
async def gerar_orcamento(pedido: PedidoOrcamento):
    total_materiais = sum(item.quantidade * item.preco_unitario for item in pedido.itens)
    total_geral = total_materiais + pedido.valor_mao_de_obra
    
    return {
        "mensagem": "Orçamento recebido com sucesso!",
        "cliente": pedido.nome_cliente,
        "total_calculado": total_geral,
        "pdf_url": "link_falso_por_enquanto.pdf"
    }
