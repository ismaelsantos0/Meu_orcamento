import streamlit as st
from core.db import get_conn

st.set_page_config(page_title="Vero | Smart Systems", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    header {visibility: hidden;} footer {visibility: hidden;}
    [data-testid="stSidebar"] { display: none; }
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;800&display=swap');
    .stApp {
        background: radial-gradient(circle at 50% 50%, #101a26 0%, #080d12 100%);
        font-family: 'Poppins', sans-serif;
        color: white;
    }
    .stTextInput > div > div > input {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 50px !important;
        color: white !important;
        padding: 10px 20px !important;
    }
    .stButton > button {
        background-color: #ffffff !important;
        color: #080d12 !important;
        border-radius: 50px !important;
        font-weight: 800 !important;
        border: none !important;
        height: 50px;
    }
    .option-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 20px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    _, col_login, _ = st.columns([1, 1, 1])
    with col_login:
        st.markdown("<div style='text-align:center; margin-top:15vh;'><h1 style='font-size:64px; font-weight:800; margin-bottom:0;'>VERO</h1><p style='letter-spacing:5px; color:#3b82f6;'>SMART SYSTEMS</p></div>", unsafe_allow_html=True)
        with st.form("login"):
            e = st.text_input("User", placeholder="E-mail", label_visibility="collapsed")
            s = st.text_input("Pass", type="password", placeholder="Senha", label_visibility="collapsed")
            if st.form_submit_button("LOGIN", use_container_width=True):
                conn = get_conn()
                with conn.cursor() as cur:
                    cur.execute("SELECT id, email FROM usuarios WHERE email = %s AND senha = %s", (e, s))
                    user = cur.fetchone()
                if user:
                    st.session_state.logged_in = True
                    st.session_state.user_id = user[0]
                    st.rerun()
                else:
                    st.error("Credenciais invalidas")
    st.stop()

# Painel Principal
st.markdown("<div style='text-align:center; margin-top:5vh;'><h1 style='font-size:40px; font-weight:800;'>PAINEL VERO</h1></div>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("<div class='option-card'><h3>Orcamentos</h3></div>", unsafe_allow_html=True)
    if st.button("ABRIR GERADOR", use_container_width=True):
        st.switch_page("pages/1_Gerador_de_Orcamento.py")

with col2:
    st.markdown("<div class='option-card'><h3>Precos</h3></div>", unsafe_allow_html=True)
    if st.button("TABELA PRIVADA", use_container_width=True):
        st.switch_page("pages/Tabela_de_Precos.py")

with col3:
    st.markdown("<div class='option-card'><h3>Ajustes</h3></div>", unsafe_allow_html=True)
    if st.button("CONFIGURACOES", use_container_width=True):
        st.switch_page("pages/Configuracoes.py")

if st.button("LOGOUT", use_container_width=True):
    st.session_state.logged_in = False
    st.rerun()
# ... (mantenha o código de login e CSS anterior)

# PAINEL HOME (LOGADO)
st.markdown("<div style='text-align:center; margin-top:5vh;'><h1 style='font-size:40px; font-weight:800;'>PAINEL VERO</h1></div>", unsafe_allow_html=True)

col1, col2 = st.columns(2)
col3, col4 = st.columns(2)

with col1:
    if st.button("GERAR ORCAMENTO", use_container_width=True):
        st.switch_page("pages/1_Gerador_de_Orcamento.py")

with col2:
    if st.button("TABELA DE PRECOS", use_container_width=True):
        st.switch_page("pages/Tabela_de_Precos.py")

with col3:
    if st.button("TEXTOS DO PDF", use_container_width=True):
        st.switch_page("pages/Modelos_de_Texto.py")

with col4:
    if st.button("CONFIGURACOES", use_container_width=True):
        st.switch_page("pages/Configuracoes.py")

if st.button("LOGOUT", use_container_width=True):
    st.session_state.logged_in = False
    st.rerun()
