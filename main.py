from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(title="VERO Smart Systems API", version="1.0")

# Libera a comunicação entre o seu frontend (Lovable/Vercel) e este backend (Railway)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MODELOS DE DADOS ---

class ItemOrcamento(BaseModel):
    id_produto: str  # <--- A CORREÇÃO: Agora aceita textos como "cerca-001" ou "CFTV-INTELBRAS"
    nome: str
    quantidade: int
    preco_unitario: float

class PedidoOrcamento(BaseModel):
    nome_cliente: str
    whatsapp_cliente: str
    categoria_servico: str
    itens: list[ItemOrcamento]
    valor_mao_de_obra: float

# --- ROTAS DA API ---

@app.get("/")
def home():
    return {"status": "VERO API Online e Operante no Railway!"}

@app.post("/api/gerar-orcamento")
async def gerar_orcamento(pedido: PedidoOrcamento):
    # 1. Faz o cálculo matemático dos materiais
    total_materiais = sum(item.quantidade * item.preco_unitario for item in pedido.itens)
    
    # 2. Soma a mão de obra ao total
    total_geral = total_materiais + pedido.valor_mao_de_obra
    
    print(f"Pedido processado com sucesso para: {pedido.nome_cliente}")
    
    # 3. Devolve a resposta mastigada para o React mostrar na tela
    return {
        "mensagem": "Orçamento recebido e processado pelo Cérebro!",
        "cliente": pedido.nome_cliente,
        "total_calculado": total_geral,
        "pdf_url": "link_falso_por_enquanto.pdf"
    }
