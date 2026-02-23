import streamlit as st
from core.db import get_conn

# 1. Configuração da página - Escondendo a sidebar por padrão
st.set_page_config(page_title="Vero | Smart Systems", page_icon="🛡️", layout="wide", initial_sidebar_state="collapsed")

# 2. CSS Universal (Login e Home)
st.markdown("""
<style>
    header {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stSidebar"] { display: none; }
    
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;800&display=swap');

    .stApp {
        background: radial-gradient(circle at 50% 50%, #101a26 0%, #080d12 100%);
        font-family: 'Poppins', sans-serif;
        color: white;
    }

    /* Estilo dos Inputs Cápsula */
    .stTextInput > div > div {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 50px !important;
        padding: 8px 25px !important;
        color: white !important;
    }

    /* Botão Principal Branco */
    .stButton > button {
        background-color: #ffffff !important;
        color: #080d12 !important;
        border-radius: 50px !important;
        font-weight: 800 !important;
        border: none !important;
        transition: all 0.3s ease !important;
    }
    .stButton > button:hover {
        transform: scale(1.05) !important;
        background-color: #3b82f6 !important;
        color: white !important;
    }

    /* Card de Opções na Home */
    .option-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 30px;
        text-align: center;
        transition: 0.3s;
    }
</style>
""", unsafe_allow_html=True)

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- LÓGICA DE LOGIN ---
if not st.session_state.logged_in:
    _, col_login, _ = st.columns([1, 1, 1])
    with col_login:
        st.markdown("<div style='text-align:center; margin-top:15vh;'><h1 style='font-size:64px; font-weight:800; margin-bottom:0;'>VERO</h1><p style='letter-spacing:5px; color:#3b82f6;'>SMART SYSTEMS</p></div>", unsafe_allow_html=True)
        with st.form("login"):
            e = st.text_input("Username", placeholder="E-mail", label_visibility="collapsed")
            s = st.text_input("Password", type="password", placeholder="Senha", label_visibility="collapsed")
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
                    st.error("Erro de acesso.")
    st.stop()

# --- HOME LOGADA (MENU DE BOTÕES) ---
st.markdown("<div style='text-align:center; margin-top:5vh;'><h1 style='font-size:40px; font-weight:800;'>PAINEL VERO</h1><p style='color:#64748b;'>Selecione uma ferramenta abaixo</p></div>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("<div class='option-card'><h3>📝 Orçamentos</h3></div>", unsafe_allow_html=True)
    if st.button("ABRIR GERADOR", use_container_width=True, key="btn_orc"):
        st.switch_page("pages/1_Gerador_de_Orcamento.py")

with col2:
    st.markdown("<div class='option-card'><h3>💰 Preços</h3></div>", unsafe_allow_html=True)
    if st.button("EDITAR TABELA", use_container_width=True, key="btn_pre"):
        st.switch_page("pages/Tabela_de_Precos.py")

with col3:
    st.markdown("<div class='option-card'><h3>⚙️ Ajustes</h3></div>", unsafe_allow_html=True)
    if st.button("CONFIGURAÇÕES", use_container_width=True, key="btn_conf"):
        st.switch_page("pages/Configuracoes.py")

st.markdown("<br><br>", unsafe_allow_html=True)
_, col_out, _ = st.columns([1, 0.5, 1])
with col_out:
    if st.button("DESLOGAR", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()
