import streamlit as st
from core.style import apply_vero_style
from core.db import get_conn

st.set_page_config(page_title="Vero | RR Smart", layout="wide", initial_sidebar_state="collapsed")
apply_vero_style()

if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    # Lógica de login simplificada
    _, col_login, _ = st.columns([1, 1.2, 1])
    with col_login:
        st.markdown("<h1 style='text-align:center;'>VERO</h1>", unsafe_allow_html=True)
        with st.form("login"):
            u = st.text_input("Usuário")
            p = st.text_input("Senha", type="password")
            if st.form_submit_button("ENTRAR", use_container_width=True):
                conn = get_conn()
                with conn.cursor() as cur:
                    cur.execute("SELECT id FROM usuarios WHERE email=%s AND senha=%s", (u, p))
                    user = cur.fetchone()
                if user:
                    st.session_state.logged_in = True
                    st.session_state.user_id = user[0]
                    st.rerun()
    st.stop()

st.markdown("<h1 style='text-align:center;'>PAINEL VERO</h1>", unsafe_allow_html=True)

col1, col2 = st.columns(2, gap="large")
col3, col4 = st.columns(2, gap="large")

with col1:
    with st.container(border=True):
        st.subheader("Orçamentos")
        if st.button("ABRIR GERADOR", use_container_width=True, key="h1"): st.switch_page("pages/1_Gerador_de_Orcamento.py")
with col2:
    with st.container(border=True):
        st.subheader("Tabela de Preços")
        if st.button("VER MATERIAIS", use_container_width=True, key="h2"): st.switch_page("pages/Tabela_de_Precos.py")
with col3:
    with st.container(border=True):
        st.subheader("Modelos de Texto")
        if st.button("EDITAR BENEFÍCIOS", use_container_width=True, key="h3"): st.switch_page("pages/Modelos_de_Texto.py")
with col4:
    with st.container(border=True):
        st.subheader("Configurações")
        if st.button("AJUSTES GERAIS", use_container_width=True, key="h4"): st.switch_page("pages/Configuracoes.py")

if st.button("SAIR DO SISTEMA", use_container_width=True):
    st.session_state.logged_in = False
    st.rerun()
