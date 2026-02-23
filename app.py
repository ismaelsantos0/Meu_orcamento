# app.py
from __future__ import annotations

import io
from pathlib import Path
from datetime import datetime

import pandas as pd
import streamlit as st

from core.materials import build_materials_list, materials_text_for_whatsapp
from core.db import get_conn

# =========================
# Registry de serviços (plugins)
# =========================
import services.registry as registry

def load_plugins():
    if hasattr(registry, "get_plugins") and callable(getattr(registry, "get_plugins")):
        plugins = registry.get_plugins()
    elif hasattr(registry, "REGISTRY"):
        plugins = registry.REGISTRY
    elif hasattr(registry, "PLUGINS"):
        plugins = registry.PLUGINS
    elif hasattr(registry, "plugins"):
        plugins = registry.plugins
    else:
        raise RuntimeError("Não encontrei plugins no services/registry.py")

    if isinstance(plugins, dict):
        return list(plugins.values())
    return list(plugins)


# =========================
# PDF - Wrapper Atualizado
# =========================
def generate_pdf_bytes(single_quote: dict, tipo: str = "summary", logo_path: str | None = None) -> bytes:
    if "summary_full" not in single_quote:
        desc = single_quote.get("service_description", {})
        if isinstance(desc, dict):
            texto_base = desc.get("description", "Serviço de instalação.")
            inclusos = desc.get("includes", [])
            vantagens = desc.get("advantages", [])
            
            texto_formatado = texto_base
            if inclusos:
                texto_formatado += "\n\nO que está incluso:\n• " + "\n• ".join(inclusos)
            if vantagens:
                texto_formatado += "\n\nPrincipais Vantagens:\n• " + "\n• ".join(vantagens)
                
            single_quote["summary_full"] = texto_formatado
            single_quote["summary_client"] = texto_formatado
        else:
            single_quote["summary_full"] = str(desc) if desc else "Serviço de instalação."
            single_quote["summary_client"] = str(desc) if desc else "Serviço de instalação."

    quote_for_pdf = {
        "logo_path": logo_path,
        "empresa": "RR Smart Soluções", 
        "whatsapp": single_quote.get("client_phone") or "(95) 98418-7832", 
        "data_str": datetime.now().strftime("%d/%m/%Y"),
        "cliente": single_quote.get("client_name") or "Cliente não informado",
        "servicos": [single_quote], 
        "subtotal": single_quote.get("subtotal", 0.0),
        "desconto_valor": 0.0,
        "desconto_label": "",
        "total": single_quote.get("subtotal", 0.0),
        "pagamento": "À vista ou 50% entrada / 50% na entrega", 
        "garantia": "Garantia de 90 dias",
        "validade_dias": 7
    }

    buffer = io.BytesIO()
    
    from core.pdf.summary import render_summary_pdf
    render_summary_pdf(buffer, quote_for_pdf)

    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


# =========================
# Helpers
# =========================
def brl(v: float) -> str:
    s = f"{v:,.2f}"
    return "R$ " + s.replace(",", "X").replace(".", ",").replace("X", ".")


# =========================
# Configuração da Página e CSS Mágico
# =========================
st.set_page_config(page_title="Gerador de Orçamentos", page_icon="🧾", layout="wide")

st.markdown("""
<style>
    /* Estilizando os Cards modernos do Bootstrap */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #262933 !important;
        border-radius: 12px !important;
        border: 1px solid #333845 !important;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2) !important;
        padding: 1rem !important;
        transition: all 0.3s ease-in-out !important;
    }
    
    [data-testid="stVerticalBlockBorderWrapper"]:hover {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 15px rgba(59, 130, 246, 0.15) !important;
    }

    /* Estilizando os botões principais de Ação */
    .stButton > button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.3s !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3) !important;
    }
    
    /* MÁGICA DOS BOTÕES DE SELEÇÃO DE SERVIÇO (Radio to Pills) */
    div[data-testid="stRadio"] > div[role="radiogroup"] {
        gap: 15px; 
    }
    div[data-testid="stRadio"] > div[role="radiogroup"] > label {
        background-color: #1a1c23 !important;
        border: 1px solid #333845 !important;
        padding: 12px 24px !important;
        border-radius: 10px !important;
        cursor: pointer;
        transition: all 0.3s ease !important;
        display: flex;
        justify-content: center;
        align-items: center;
    }
    div[data-testid="stRadio"] > div[role="radiogroup"] > label span[data-baseweb="radio"] {
        display: none !important; /* Esconde a bolinha */
    }
    div[data-testid="stRadio"] > div[role="radiogroup"] > label div[dir="auto"] {
        margin-left: 0px !important; 
    }
    div[data-testid="stRadio"] > div[role="radiogroup"] > label:hover {
        border-color: #3b82f6 !important;
        transform: translateY(-2px);
    }
    div[data-testid="stRadio"] > div[role="radiogroup"] > label[data-checked="true"] {
        background-color: rgba(59, 130, 246, 0.15) !important;
        border-color: #3b82f6 !important;
        box-shadow: 0 0 15px rgba(59, 130, 246, 0.4) !important;
    }
    div[data-testid="stRadio"] > div[role="radiogroup"] > label p {
        font-weight: 600 !important;
        color: #e2e8f0 !important;
        margin: 0 !important;
        font-size: 15px !important;
    }
</style>
""", unsafe_allow_html=True)


ASSETS_DIR = Path(__file__).parent / "assets"
DEFAULT_LOGO = ASSETS_DIR / "logo.png"

st.title("🛡️ RR Smart Soluções | Orçamentos")
st.write("Crie propostas comerciais profissionais em segundos.")

# =========================
# Barra Lateral (Menu)
# =========================
with st.sidebar:
    st.header("⚙️ Configurações")
    usar_logo = st.checkbox("Usar logo no PDF", value=DEFAULT_LOGO.exists())
    logo_path = str(DEFAULT_LOGO) if usar_logo and DEFAULT_LOGO.exists() else None

    st.divider()
    st.subheader("👤 Dados do Cliente")
    cliente_nome = st.text_input("Nome do cliente", value="", placeholder="Ex: João Silva")
    cliente_tel = st.text_input("WhatsApp do cliente", value="", placeholder="(00) 00000-0000")
    obs_geral = st.text_area("Observações (Internas)", value="", height=90)

try:
    plugins = load_plugins()
except Exception as e:
    st.error(f"Erro carregando plugins: {e}")
    st.stop()

if not plugins:
    st.error("Nenhum serviço (plugin) encontrado.")
    st.stop()

plugin_by_label = {p.label: p for p in plugins}

try:
    conn = get_conn()
except Exception as e:
    st.error(f"Falha ao conectar no banco de dados: {e}")
    st.stop()


# =========================
# CARD 1: Seleção Dinâmica do Serviço (Botões Pílula)
# =========================
with st.container(border=True):
    st.subheader("🛠️ Qual serviço será realizado?")

    # Agrupa os serviços inteligentemente
    todos_servicos = list(plugin_by_label.keys())
    cat_cameras = []
    cat_cercas = []
    cat_motores = []
    cat_outros = []
    
    for s in todos_servicos:
        sl = s.lower()
        if "câmera" in sl or "camera" in sl or "cftv" in sl:
            cat_cameras.append(s)
        elif "cerca" in sl or "concertina" in sl or "linear" in sl:
            cat_cercas.append(s)
        elif "motor" in sl or "portão" in sl or "portao" in sl:
            cat_motores.append(s)
        else:
            cat_outros.append(s)

    categorias = {}
    if cat_cameras: categorias["📷 Câmeras de Segurança"] = cat_cameras
    if cat_cercas: categorias["⚡ Cercas e Concertinas"] = cat_cercas
    if cat_motores: categorias["🚪 Motores de Portão"] = cat_motores
    if cat_outros: categorias["🔧 Outros Serviços"] = cat_outros

    # Escolha da Categoria Principal
    cat_escolhida = st.radio("Selecione a Categoria:", list(categorias.keys()), horizontal=True, label_visibility="collapsed")

    # Escolha do Serviço Específico
    opcoes_servico = categorias[cat_escolhida]
    
    st.write("") # Espaçinho
    if len(opcoes_servico) > 1:
        st.write("**Selecione a variação:**")
        service_label = st.radio("Selecione a variação:", opcoes_servico, horizontal=True, label_visibility="collapsed")
    else:
        service_label = opcoes_servico[0]
        st.info(f"Serviço selecionado: **{service_label}**")

    plugin = plugin_by_label[service_label]
    
    st.markdown("---")
    # Campos dinâmicos do serviço escolhido
    inputs = plugin.render_fields()


# =========================
# CARD 2: Itens Extras e Adicionais
# =========================
with st.container(border=True):
    st.subheader("➕ Itens Adicionais (Extras)")
    st.write("Selecione sensores, cabos extras, ou peças avulsas para somar neste orçamento.")

    extras_to_add = []
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT chave, nome, valor FROM precos ORDER BY nome")
            db_items = cur.fetchall()
            
        items_dict = {}
        for row in db_items:
            chave = row[0]
            nome = row[1] if row[1] else chave.replace("_", " ").title()
            valor = float(row[2])
            label = f"{nome} (R$ {valor:.2f})"
            items_dict[label] = {"chave": chave, "nome": nome, "valor": valor}
            
        selected_extra_labels = st.multiselect("Selecione os itens extras", options=list(items_dict.keys()), placeholder="Clique para buscar...")
        
        if selected_extra_labels:
            cols = st.columns(min(len(selected_extra_labels), 4))
            for i, label in enumerate(selected_extra_labels):
                with cols[i % 4]:
                    qty = st.number_input(f"Qtd: {items_dict[label]['nome']}", min_value=1, value=1, step=1, key=f"extra_qty_{items_dict[label]['chave']}")
                    extras_to_add.append({"item": items_dict[label], "qty": qty})

    except Exception as e:
        st.error(f"Erro ao carregar itens extras: {e}")


# =========================
# AÇÃO: Gerar Orçamento
# =========================
st.write("") 
colA, colB, colC = st.columns([1, 2, 1])
with colB:
    gerar = st.button("🚀 GERAR ORÇAMENTO COMPLETO", use_container_width=True, type="primary")

if not gerar:
    st.stop()

# ----- Processamento dos Cálculos -----
try:
    quote = plugin.compute(conn, inputs)
except Exception as e:
    st.error(f"Erro ao calcular itens do orçamento: {e}")
    st.stop()

if extras_to_add:
    for extra in extras_to_add:
        item_data = extra["item"]
        qty = extra["qty"]
        sub = qty * item_data["valor"]
        
        quote["items"].append({"desc": f"[EXTRA] {item_data['nome']}", "qty": qty, "unit": item_data["valor"], "sub": sub})
        quote["subtotal"] += sub
        
    qtd_extras = len(extras_to_add)
    if "summary_client" in quote:
        quote["summary_client"] += f"\n\nItens Adicionais Selecionados:\n• {qtd_extras} tipo(s) de item(ns) extra(s) incluso(s)."

quote["client_name"] = cliente_nome
quote["client_phone"] = cliente_tel
quote["notes"] = obs_geral
subtotal = float(quote.get("subtotal", 0.0))

st.divider()


# =========================
# CARD 3: Resultados (Proposta Cliente)
# =========================
with st.container(border=True):
    st.subheader("🧑‍💼 Proposta Comercial (Para o Cliente)")
    st.write("Baixe o PDF com as vantagens ou copie o texto estruturado para enviar no WhatsApp.")
    
    col_pdf, col_wpp = st.columns([1, 2])

    with col_pdf:
        try:
            pdf_cliente = generate_pdf_bytes(quote, tipo="summary", logo_path=logo_path)
            st.download_button(
                label="📄 Baixar PDF da Proposta",
                help="Gera o PDF com serviços, vantagens e valor total.",
                data=pdf_cliente,
                file_name=f"Proposta_RR_Smart_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                use_container_width=True,
                type="primary" 
            )
        except Exception as e:
            st.error(f"Erro ao gerar PDF do Cliente: {e}")

    with col_wpp:
        wpp_texto = f"🛡️ *RR Smart Soluções*\n\n"
        if cliente_nome:
            wpp_texto += f"Olá, *{cliente_nome}*! Segue a nossa proposta comercial:\n\n"
        else:
            wpp_texto += "Olá! Segue a nossa proposta comercial:\n\n"

        wpp_texto += f"🛠️ *Serviço:* {quote.get('service_name', '')}\n"
        desc_wpp = quote.get("summary_client", quote.get("summary_full", ""))
        if desc_wpp:
            wpp_texto += f"{desc_wpp}\n\n"

        wpp_texto += f"💰 *Investimento Total: {brl(subtotal)}*\n\n"
        wpp_texto += f"💳 *Condições de Pagamento:*\nÀ vista ou 50% entrada / 50% na entrega\n\n"
        wpp_texto += f"⚙️ *Garantia:* 90 dias\n"
        wpp_texto += f"⏳ *Validade:* 7 dias\n\n"
        wpp_texto += "Qualquer dúvida, estou à disposição para fecharmos o serviço! 🤝"
        
        st.text_area("💬 Copiar para WhatsApp", wpp_texto, height=200)


# =========================
# CARD 4: Controle Interno
# =========================
with st.container(border=True):
    st.subheader("🔒 Seu Controle Interno (Custos e Peças)")
    st.markdown(f"**Total Calculado: {brl(subtotal)}**")
    
    items_df = pd.DataFrame(quote.get("items", []))
    if not items_df.empty:
        st.dataframe(items_df, use_container_width=True)
    else:
        st.warning("Nenhum item retornado pelo serviço.")

# =========================
# CARD 5: Lista de Compras
# =========================
with st.container(border=True):
    st.subheader("🛒 Lista de Materiais (Para Compra)")
    only_materials = st.checkbox("Gerar somente materiais (ignorar mão de obra)", value=True)

    materials = build_materials_list(
        quote,
        exclude_keywords=None if only_materials else [],
        group_same_desc=True,
    )

    if materials:
        mats_df = pd.DataFrame(materials)
        st.dataframe(mats_df, use_container_width=True)

        text_materiais = materials_text_for_whatsapp(
            materials,
            header_lines=[
                f"Serviço: {quote.get('service_name', '')}",
                f"Data: {datetime.now().strftime('%d/%m/%Y')}",
            ],
        )

        with st.expander("Copiar lista em texto"):
            st.text_area("Lista de Peças", text_materiais, height=150)

        csv = mats_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Baixar CSV",
            data=csv,
            file_name=f"compras_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
