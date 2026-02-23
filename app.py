import streamlit as st
import io
from datetime import datetime
from core.db import get_conn
import services.registry as registry

st.set_page_config(page_title="Portal SaaS", page_icon="🛡️", layout="wide")

# --- ESTILO ---
st.markdown("""
<style>
    [data-testid="stVerticalBlockBorderWrapper"] { background-color: #262933 !important; border-radius: 12px !important; padding: 1.5rem !important; }
    .stButton > button { border-radius: 8px !important; }
</style>
""", unsafe_allow_html=True)

# --- LOGIN ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        with st.container(border=True):
            st.title("🛡️ Login")
            email = st.text_input("E-mail")
            senha = st.text_input("Senha", type="password")
            if st.button("Aceder Sistema", use_container_width=True, type="primary"):
                conn = get_conn()
                with conn.cursor() as cur:
                    cur.execute("SELECT id, email FROM usuarios WHERE email = %s AND senha = %s", (email, senha))
                    user = cur.fetchone()
                if user:
                    st.session_state.logged_in = True
                    st.session_state.user_id = user[0]
                    st.rerun()
                else:
                    st.error("Credenciais inválidas.")
    st.stop()

# --- SISTEMA LOGADO ---
user_id = st.session_state.user_id
conn = get_conn()

# Busca Configuração do Usuário
with conn.cursor() as cur:
    cur.execute("SELECT nome_empresa, whatsapp, logo FROM config_empresa WHERE usuario_id = %s", (user_id,))
    config = cur.fetchone()

nome_empresa = config[0] if config else "Minha Empresa"
whatsapp_emp = config[1] if config else ""

with st.sidebar:
    st.title(f"🏢 {nome_empresa}")
    if st.button("Sair"):
        st.session_state.logged_in = False
        st.rerun()

st.title(f"🚀 Orçamentos Inteligentes")

# Aqui você continua com a lógica de Plugins e Geração de PDF 
# que já tínhamos, sempre passando o user_id nas consultas de PRECOS.
st.info(f"Bem-vindo de volta! Seu ID de assinante é: {user_id}")
