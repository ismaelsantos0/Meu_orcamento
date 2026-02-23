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
# CONFIGURAÇÃO E ESTILO
# =========================
st.set_page_config(page_title="Gerador de Orçamentos SaaS", page_icon="🛡️", layout="wide")

st.markdown("""
<style>
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #262933 !important;
        border-radius: 12px !important;
        border: 1px solid #333845 !important;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2) !important;
        padding: 1.5rem !important;
    }
    div[data-testid="stRadio"] > div[role="radiogroup"] {
        flex-direction: row; gap: 4px; border-bottom: 3px solid #3b82f6; 
    }
    div[data-testid="stRadio"] > div[role="radiogroup"] > label {
        background-color: #1a1c23 !important; border: 1px solid #333845 !important;
        border-bottom: none !important; border-radius: 12px 12px 0 0 !important; 
        padding: 10px 20px !important; opacity: 0.6; cursor: pointer;
    }
    div[data-testid="stRadio"] > div[role="radiogroup"] > label[data-checked="true"] {
        background-color: #3b82f6 !important; border-color: #3b82f6 !important; opacity: 1;
    }
    div[data-testid="stRadio"] > div[role="radiogroup"] > label span[data-baseweb="radio"] { display: none !important; }
    .stButton > button { border-radius: 8px !important; font-weight: 600 !important; }
</style>
""", unsafe_allow_html=True)

# =========================
# FUNÇÕES DE AUTENTICAÇÃO
# =========================
def validar_login(email, senha):
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("SELECT id, email FROM usuarios WHERE email = %s AND senha = %s", (email, senha))
        return cur.fetchone()

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_id = None

if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.container(border=True):
            st.title("🛡️ Acesso ao Sistema")
            email_i = st.text_input("E-mail")
            senha_i = st.text_input("Senha", type="password")
            if st.button("Entrar", use_container_width=True, type="primary"):
                user = validar_login(email_i, senha_i)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.user_id = user[0]
                    st.rerun()
                else:
                    st.error("Dados incorretos.")
    st.stop()

# =========================
# CARREGAMENTO DE DADOS DO USUÁRIO
# =========================
def buscar_dados_empresa(conn, user_id):
    with conn.cursor() as cur:
        cur.execute("SELECT nome_empresa, whatsapp, pagamento_padrao, garantia_padrao, validade_dias, logo FROM config_empresa WHERE usuario_id = %s", (user_id,))
        row = cur.fetchone()
        if row:
            return {"nome": row[0], "whatsapp": row[1], "pagamento": row[2], "garantia": row[3], "validade": row[4], "logo": row[5]}
    return {"nome": "Nova Empresa", "whatsapp": "00", "pagamento": "À combinar", "garantia": "90 dias", "validade": 7, "logo": None}

conn = get_conn()
config = buscar_dados_empresa(conn, st.session_state.user_id)

# =========================
# PDF DInâmico
# =========================
def generate_pdf_bytes(single_quote: dict, config: dict, logo_bytes: bytes | None = None) -> bytes:
    # Prepara os dados para o renderizador de PDF usando o dicionário config
    quote_for_pdf = {
        "logo_bytes": logo_bytes, # Passamos os bytes da logo do banco
        "empresa": config["nome"], 
        "whatsapp": config["whatsapp"], 
        "data_str": datetime.now().strftime("%d/%m/%Y"),
        "cliente": single_quote.get("client_name", "Cliente"),
        "servicos": [single_quote], 
        "total": single_quote.get("subtotal", 0.0),
        "pagamento": config["pagamento"], 
        "garantia": config["garantia"],
        "validade_dias": config["validade"]
    }
    buffer = io.BytesIO()
    from core.pdf.summary import render_summary_pdf
    render_summary_pdf(buffer, quote_for_pdf)
    return buffer.getvalue()

# =========================
# INTERFACE PRINCIPAL
# =========================
with st.sidebar:
    st.header(f"🏢 {config['nome']}")
    if st.button("Sair"):
        st.session_state.logged_in = False
        st.rerun()
    st.divider()
    cliente_nome = st.text_input("Nome do cliente")
    cliente_tel = st.text_input("WhatsApp do cliente")

st.title(f"🛠️ Orçamentos | {config['nome']}")

import services.registry as registry
plugins = list(registry.get_plugins().values())
plugin_by_label = {p.label: p for p in plugins}

# CARD 1: SERVIÇOS
with st.container(border=True):
    st.subheader("📁 Categorias de Serviço")
    todos = list(plugin_by_label.keys())
    # ... (lógica de categorias que já temos)
    cat_escolhida = st.radio("Categoria", ["📷 Câmeras", "⚡ Cercas", "🚪 Motores"], horizontal=True, label_visibility="collapsed")
    # Simplificado para o exemplo, use sua lógica de filtros aqui
    service_label = st.selectbox("Variação:", [s for s in todos if cat_escolhida[2:] in s] or todos)
    plugin = plugin_by_label[service_label]
    inputs = plugin.render_fields()

# CARD 2: EXTRAS (FILTRADOS POR USUÁRIO)
with st.container(border=True):
    st.subheader("➕ Itens Adicionais")
    with conn.cursor() as cur:
        # AQUI ESTÁ O FILTRO SAAS:
        cur.execute("SELECT chave, nome, valor FROM precos WHERE usuario_id = %s ORDER BY nome", (st.session_state.user_id,))
        db_items = cur.fetchall()
    
    items_dict = {f"{r[1]} (R$ {r[2]:.2f})": {"chave": r[0], "nome": r[1], "valor": float(r[2])} for r in db_items}
    sel_extras = st.multiselect("Buscar itens:", options=list(items_dict.keys()))
    extras_to_add = []
    if sel_extras:
        cols = st.columns(4)
        for i, label in enumerate(sel_extras):
            with cols[i % 4]:
                qty = st.number_input(f"Qtd: {items_dict[label]['nome']}", min_value=1, value=1, key=f"ex_{i}")
                extras_to_add.append({"item": items_dict[label], "qty": qty})

if st.button("🚀 GERAR ORÇAMENTO", type="primary", use_container_width=True):
    quote = plugin.compute(conn, inputs)
    for ex in extras_to_add:
        sub = ex["qty"] * ex["item"]["valor"]
        quote["items"].append({"desc": ex["item"]["nome"], "qty": ex["qty"], "unit": ex["item"]["valor"], "sub": sub})
        quote["subtotal"] += sub
    
    st.divider()
    aba_p, aba_i = st.tabs(["Proposta", "Controle"])
    with aba_p:
        pdf = generate_pdf_bytes(quote, config, config['logo'])
        st.download_button("📄 Baixar PDF", data=pdf, file_name="proposta.pdf", mime="application/pdf")
        # ... (texto do WhatsApp dinâmico aqui)
