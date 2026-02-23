import streamlit as st
import io
import pandas as pd
from datetime import datetime
from core.db import get_conn
from core.materials import build_materials_list
import services.registry as registry

# ==========================================
# 1. TRAVA DE SEGURANÇA E CONFIGURAÇÃO
# ==========================================
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.error("❌ Acesso negado! Por favor, faça login na página inicial.")
    st.stop()

st.set_page_config(page_title="Vero | Gerar Orçamento", layout="wide", initial_sidebar_state="collapsed")

user_id = st.session_state.user_id

# ==========================================
# 2. ESTILO VERO (CLEAN & DARK)
# ==========================================
st.markdown("""
<style>
    header {visibility: hidden;} footer {visibility: hidden;}
    [data-testid="stSidebar"] { display: none; }
    
    .stApp {
        background: radial-gradient(circle at 50% 50%, #101a26 0%, #080d12 100%);
        font-family: 'Poppins', sans-serif;
        color: white;
    }
    
    /* Estilização de containers e inputs para o tema escuro */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 20px !important;
    }
    
    .stButton > button {
        background-color: #ffffff !important;
        color: #080d12 !important;
        border-radius: 50px !important;
        font-weight: 800 !important;
        transition: 0.3s;
    }
    
    .stButton > button:hover {
        transform: scale(1.02) !important;
        background-color: #3b82f6 !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. FUNÇÕES DE APOIO
# ==========================================
def buscar_config(uid):
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("SELECT nome_empresa, whatsapp, pagamento_padrao, garantia_padrao, validade_dias, logo FROM config_empresa WHERE usuario_id = %s", (uid,))
        return cur.fetchone()

def brl(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# Busca dados do usuário logado
dados_user = buscar_config(user_id)
config = {
    "nome": dados_user[0] if dados_user else "Empresa",
    "whatsapp": dados_user[1] if dados_user else "",
    "pagamento": dados_user[2] if dados_user else "A combinar",
    "garantia": dados_user[3] if dados_user else "90 dias",
    "validade": dados_user[4] if dados_user else 7,
    "logo": dados_user[5] if dados_user else None
}

# Cabeçalho da Página
col_back, col_title = st.columns([1, 4])
with col_back:
    if st.button("← VOLTAR"):
        st.switch_page("app.py")
with col_title:
    st.markdown(f"## 📝 Orçamentos | {config['nome']}")

# ==========================================
# 4. FORMULÁRIO DE ORÇAMENTO
# ==========================================
with st.container(border=True):
    c1, c2 = st.columns(2)
    cliente = c1.text_input("Nome do Cliente", placeholder="Ex: João Silva")
    contato = c2.text_input("WhatsApp do Cliente", placeholder="(95) 9...")

# SELEÇÃO DE PLUGIN (Câmeras, Cercas, Motores)
plugins = list(registry.get_plugins().values())
labels = [p.label for p in plugins]

with st.container(border=True):
    st.subheader("🛠️ Serviço Principal")
    servico_sel = st.selectbox("O que vamos instalar?", labels)
    plugin = registry.get_plugins()[list(registry.get_plugins().keys())[labels.index(servico_sel)]]
    
    # Renderiza os campos específicos do plugin (ex: qtd câmeras, metros de cerca)
    inputs = plugin.render_fields()

# ITENS EXTRAS DO BANCO (FILTRADO POR USUÁRIO)
with st.container(border=True):
    st.subheader("➕ Itens Adicionais")
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("SELECT chave, nome, valor FROM precos WHERE usuario_id = %s ORDER BY nome", (user_id,))
        itens_db = cur.fetchall()
    
    opcoes_extras = {f"{r[1]} ({brl(float(r[2]))})": {"chave": r[0], "nome": r[1], "valor": float(r[2])} for r in itens_db}
    selecionados = st.multiselect("Adicionar ao orçamento:", list(opcoes_extras.keys()))
    
    extras = []
    if selecionados:
        cols = st.columns(3)
        for i, item_label in enumerate(selecionados):
            with cols[i % 3]:
                qtd = st.number_input(f"Qtd: {opcoes_extras[item_label]['nome']}", min_value=1, value=1, key=f"extra_{i}")
                extras.append({"info": opcoes_extras[item_label], "qtd": qtd})

# ==========================================
# 5. CÁLCULO FINAL E GERAÇÃO
# ==========================================
if st.button("🚀 GERAR PROPOSTA FINAL", use_container_width=True):
    # 1. Calcula base do plugin
    proposta = plugin.compute(conn, inputs)
    
    # 2. Soma os extras
    for ex in extras:
        sub = ex["qtd"] * ex["info"]["valor"]
        proposta["items"].append({"desc": f"[ADICIONAL] {ex['info']['nome']}", "qty": ex["qtd"], "unit": ex["info"]["valor"], "sub": sub})
        proposta["subtotal"] += sub
    
    st.success(f"Orçamento calculado: {brl(proposta['subtotal'])}")
    
    # 3. Preparação do PDF
    from core.pdf.summary import render_summary_pdf
    pdf_buffer = io.BytesIO()
    dados_pdf = {
        "logo_bytes": config["logo"],
        "empresa": config["nome"],
        "whatsapp": config["whatsapp"],
        "cliente": cliente or "Cliente",
        "data_str": datetime.now().strftime("%d/%m/%Y"),
        "servicos": [proposta],
        "total": proposta["subtotal"],
        "pagamento": config["pagamento"],
        "garantia": config["garantia"],
        "validade_dias": config["validade"]
    }
    render_summary_pdf(pdf_buffer, dados_pdf)
    
    st.divider()
    col_pdf, col_wpp = st.columns(2)
    
    with col_pdf:
        st.download_button("📥 BAIXAR PDF", data=pdf_buffer.getvalue(), file_name=f"Orcamento_{cliente}.pdf", mime="application/pdf", use_container_width=True)
        
    with col_wpp:
        msg = f"🛡️ *{config['nome']}*\nOlá {cliente}!\nSegue o orçamento para *{servico_sel}*.\nTotal: *{brl(proposta['subtotal'])}*"
        st.text_area("Texto para WhatsApp:", msg, height=100)
