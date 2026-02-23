import streamlit as st
from core.style import apply_vero_style
from core.db import get_conn

# Configuração da página e Estilo Arredondado
st.set_page_config(page_title="Vero | Login", layout="wide", initial_sidebar_state="collapsed")
apply_vero_style() #

# Inicializa o estado de login se não existir
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- TELA DE LOGIN ---
if not st.session_state.logged_in:
    _, col_login, _ = st.columns([1, 1.2, 1])
    
    with col_login:
        st.markdown("<div style='text-align:center; margin-top:10vh;'><h1 style='font-size:60px;'>VERO</h1><p style='color:#3b82f6; letter-spacing:3px;'>SMART SYSTEMS</p></div>", unsafe_allow_html=True)
        
        with st.container(border=True):
            st.markdown("### Acesso ao Sistema")
            with st.form("form_login", clear_on_submit=True):
                email = st.text_input("E-mail", placeholder="seu@email.com")
                senha = st.text_input("Senha", type="password", placeholder="******")
                
                if st.form_submit_button("ENTRAR NO PAINEL", use_container_width=True):
                    conn = get_conn()
                    with conn.cursor() as cur:
                        # Busca o usuário no banco de dados da RR Smart Soluções
                        cur.execute("SELECT id, email FROM usuarios WHERE email = %s AND senha = %s", (email, senha))
                        user = cur.fetchone()
                    
                    if user:
                        st.session_state.logged_in = True
                        st.session_state.user_id = user[0]
                        st.session_state.user_email = user[1]
                        st.rerun()
                    else:
                        st.error("E-mail ou senha incorretos.")
    st.stop() # Interrompe o script aqui se não estiver logado

# --- PAINEL PRINCIPAL (SÓ APARECE SE LOGADO) ---
st.markdown("<h1 style='text-align:center; padding: 30px;'>PAINEL VERO</h1>", unsafe_allow_html=True)

col1, col2 = st.columns(2, gap="large")
col3, col4 = st.columns(2, gap="large")

with col1:
    with st.container(border=True):
        st.subheader("Orçamentos")
        st.write("Gerar novas propostas PDF.")
        if st.button("ABRIR GERADOR", key="btn_h1", use_container_width=True): 
            st.switch_page("pages/1_Gerador_de_Orcamento.py")

with col2:
    with st.container(border=True):
        st.subheader("Tabela de Preços")
        st.write("Materiais e Mão de Obra.")
        if st.button("VER MATERIAIS", key="btn_h2", use_container_width=True): 
            st.switch_page("pages/Tabela_de_Precos.py")

with col3:
    with st.container(border=True):
        st.subheader("Textos PDF")
        st.write("Modelos de benefícios.")
        if st.button("EDITAR MODELOS", key="btn_h3", use_container_width=True): 
            st.switch_page("pages/Modelos_de_Texto.py")

with col4:
    with st.container(border=True):
        st.subheader("Configurações")
        st.write("Dados da empresa e logo.")
        if st.button("AJUSTES GERAIS", key="btn_h4", use_container_width=True): 
            st.switch_page("pages/Configuracoes.py")

st.markdown("<br>", unsafe_allow_html=True)
if st.button("SAIR DO SISTEMA", use_container_width=True, key="logout_main"):
    st.session_state.logged_in = False
    st.rerun()
