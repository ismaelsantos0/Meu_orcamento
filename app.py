import streamlit as st
from core.style import apply_vero_style
from core.scripts import apply_vero_js
from core.db import get_conn

st.set_page_config(page_title="Vero | RR Smart Soluções", layout="wide", initial_sidebar_state="collapsed")
apply_vero_style()
apply_vero_js()

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- TELA DE LOGIN ---
if not st.session_state.logged_in:
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, col_login, _ = st.columns([1, 1.2, 1])
    with col_login:
        st.markdown("<div style='text-align:center;'><h1>VERO</h1><p style='color:#3b82f6; letter-spacing:4px;'>SMART SYSTEMS</p></div>", unsafe_allow_html=True)
        with st.container(border=True):
            with st.form("login_form", border=False):
                email = st.text_input("USUÁRIO", placeholder="seu@email.com")
                senha = st.text_input("SENHA", type="password", placeholder="••••••")
                if st.form_submit_button("INICIAR SESSÃO", use_container_width=True):
                    conn = get_conn()
                    with conn.cursor() as cur:
                        cur.execute("SELECT id FROM usuarios WHERE email=%s AND senha=%s", (email, senha))
                        user = cur.fetchone()
                    if user:
                        st.session_state.logged_in = True
                        st.session_state.user_id = user[0]
                        st.rerun()
                    else:
                        st.error("Credenciais inválidas")
    st.stop()

# --- PAINEL PRINCIPAL ---
st.markdown("<h1 style='text-align:center; padding: 40px;'>PAINEL ADMINISTRATIVO</h1>", unsafe_allow_html=True)

col1, col2 = st.columns(2, gap="large")
col3, col4 = st.columns(2, gap="large")

with col1:
    with st.container(border=True):
        st.subheader("📋 Orçamentos")
        if st.button("ABRIR GERADOR", key="nav1", use_container_width=True): st.switch_page("pages/1_Gerador_de_Orcamento.py")

with col2:
    with st.container(border=True):
        st.subheader("💰 Tabela de Preços")
        if st.button("VER MATERIAIS", key="nav2", use_container_width=True): st.switch_page("pages/Tabela_de_Precos.py")

with col3:
    with st.container(border=True):
        st.subheader("✍️ Modelos de Texto")
        if st.button("EDITAR BENEFÍCIOS", key="nav3", use_container_width=True): st.switch_page("pages/Modelos_de_Texto.py")

with col4:
    with st.container(border=True):
        st.subheader("⚙️ Configurações")
        if st.button("AJUSTES GERAIS", key="nav4", use_container_width=True): st.switch_page("pages/Configuracoes.py")

if st.button("SAIR DO SISTEMA", use_container_width=True):
    st.session_state.logged_in = False
    st.rerun()
