import streamlit as st
import io
import pandas as pd
from pathlib import Path
from datetime import datetime
from core.db import get_conn
from core.materials import build_materials_list, materials_text_for_whatsapp
import services.registry as registry

# =========================
# 1. TRAVA DE SEGURANÇA (LACRANDO A PÁGINA)
# =========================
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.error("❌ Acesso negado! Por favor, faça login na página inicial.")
    st.stop()

# =========================
# 2. CONFIGURAÇÃO E ESTILO
# =========================
st.set_page_config(page_title="Gerar Orçamento", page_icon="🧾", layout="wide")

user_id = st.session_state.user_id # ID do inquilino logado

st.markdown("""
<style>
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #262933 !important;
        border-radius: 12px !important;
        border: 1px solid #333845 !important;
        padding: 1.5rem !important;
    }
    .stButton > button { border-radius: 8px !important; font-weight: 600 !important; }
</style>
""", unsafe_allow_html=True)

# =========================
# 3. FUNÇÕES AUXILIARES E BANCO
# =========================
def buscar_dados_empresa(conn, uid):
    with conn.cursor() as cur:
        cur.execute("SELECT nome_empresa, whatsapp, pagamento_padrao, garantia_padrao, validade_dias, logo FROM config_empresa WHERE usuario_id = %s", (uid,))
        linha = cur.fetchone()
        if linha:
            return {"nome": linha[0], "whatsapp": linha[1], "pagamento": linha[2], "garantia": linha[3], "validade": linha[4], "logo": linha[5]}
    return {"nome": "Empresa", "whatsapp": "00", "pagamento": "A combinar", "garantia": "90 dias", "validade": 7, "logo": None}

def brl(v: float) -> str:
    return "R$ " + f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def generate_pdf_bytes(quote, config_emp):
    buffer = io.BytesIO()
    quote_for_pdf = {
        "logo_bytes": config_emp["logo"],
        "empresa": config_emp["nome"], 
        "whatsapp": config_emp["whatsapp"], 
        "data_str": datetime.now().strftime("%d/%m/%Y"),
        "cliente": quote.get("client_name") or "Cliente",
        "servicos": [quote], 
        "total": quote.get("subtotal", 0.0),
        "pagamento": config_emp["pagamento"], 
        "garantia": config_emp["garantia"],
        "validade_dias": config_emp["validade"]
    }
    from core.pdf.summary import render_summary_pdf
    render_summary_pdf(buffer, quote_for_pdf)
    return buffer.getvalue()

# =========================
# 4. CARREGAMENTO DE DADOS
# =========================
conn = get_conn()
config = buscar_dados_empresa(conn, user_id)

st.title(f"🚀 Novo Orçamento | {config['nome']}")

# Sidebar para dados do cliente
with st.sidebar:
    st.subheader("👤 Dados do Cliente")
    c_nome = st.text_input("Nome do Cliente")
    c_tel = st.text_input("WhatsApp")
    st.divider()
    if st.button("⬅️ Sair do Sistema"):
        st.session_state.logged_in = False
        st.rerun()

# Carregar Plugins dinamicamente
plugins = list(registry.get_plugins().values())
plugin_by_label = {p.label: p for p in plugins}

# =========================
# 5. PASSO 1: SELEÇÃO DE SERVIÇO
# =========================
with st.container(border=True):
    st.subheader("📁 Escolha o Serviço")
    service_label = st.selectbox("Selecione o tipo de instalação:", list(plugin_by_label.keys()))
    plugin = plugin_by_label[service_label]
    inputs = plugin.render_fields()

# =========================
# 6. PASSO 2: ITENS EXTRAS (SAAS FILTER)
# =========================
with st.container(border=True):
    st.subheader("➕ Itens Adicionais")
    with conn.cursor() as cur:
        # Filtramos os preços para aparecerem apenas os deste usuário
        cur.execute("SELECT chave, nome, valor FROM precos WHERE usuario_id = %s ORDER BY nome", (user_id,))
        db_items = cur.fetchall()
    
    items_dict = {f"{r[1]} ({brl(float(r[2]))})": {"chave": r[0], "nome": r[1], "valor": float(r[2])} for r in db_items}
    sel_extras = st.multiselect("Adicionar peças avulsas:", options=list(items_dict.keys()))
    
    extras_to_add = []
    if sel_extras:
        cols = st.columns(4)
        for i, label in enumerate(sel_extras):
            with cols[i % 4]:
                q = st.number_input(f"Qtd: {items_dict[label]['nome']}", min_value=1, value=1, key=f"ex_{i}")
                extras_to_add.append({"item": items_dict[label], "qty": q})

# =========================
# 7. CÁLCULO E RESULTADO
# =========================
if st.button("🚀 CALCULAR E GERAR PROPOSTA", type="primary", use_container_width=True):
    # Cálculo via Plugin (Câmeras, Motores, etc)
    quote = plugin.compute(conn, inputs)
    
    # Soma dos Extras
    for ex in extras_to_add:
        v_sub = ex["qty"] * ex["item"]["valor"]
        quote["items"].append({"desc": f"[EXTRA] {ex['item']['nome']}", "qty": ex["qty"], "unit": ex["item"]["valor"], "sub": v_sub})
        quote["subtotal"] += v_sub
    
    quote["client_name"] = c_nome
    quote["client_phone"] = c_tel
    total = quote["subtotal"]

    st.divider()
    aba_p, aba_m = st.tabs(["📄 Proposta Cliente", "🛒 Lista de Materiais"])

    with aba_p:
        pdf_bytes = generate_pdf_bytes(quote, config)
        st.download_button("📥 Baixar Proposta em PDF", data=pdf_bytes, file_name=f"Orcamento_{c_nome}.pdf", mime="application/pdf", type="primary")
        
        # Texto WhatsApp
        wpp = f"🛡️ *{config['nome']}*\nOlá {c_nome}!\nSegue proposta para *{service_label}*.\nTotal: *{brl(total)}*\nPagamento: {config['pagamento']}"
        st.text_area("Copiar para WhatsApp", wpp, height=100)

    with aba_m:
        materiais = build_materials_list(quote)
        st.dataframe(pd.DataFrame(materiais), use_container_width=True)
