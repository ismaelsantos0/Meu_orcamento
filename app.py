import streamlit as st
from core.style import apply_vero_style
from core.db import get_conn

# Configurações Iniciais
st.set_page_config(page_title="Vero | RR Smart Soluções", layout="wide", initial_sidebar_state="collapsed")
apply_vero_style() # Aplica o estilo arredondado e a Navbar azul

# Inicializa variáveis de sessão
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- 1. TELA DE LOGIN (Aparece se não estiver logado) ---
if not st.session_state.logged_in:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    _, col_login, _ = st.columns([1, 1.2, 1])
    
    with col_login:
        st.markdown("<div style='text-align:center;'><h1>VERO</h1><p style='color:#3b82f6; letter-spacing:5px;'>SMART SYSTEMS</p></div>", unsafe_allow_html=True)
        with st.container(border=True):
            with st.form("login_form", border=False):
                st.markdown("<p style='text-align:center; opacity:0.7;'>Acesso Administrativo RR Smart</p>", unsafe_allow_html=True)
                email = st.text_input("USUÁRIO")
                senha = st.text_input("SENHA", type="password")
                
                if st.form_submit_button("ENTRAR NO SISTEMA", use_container_width=True):
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
    st.stop() # Bloqueia o restante do código até o login ser feito

# --- 2. MENU SUPERIOR (Aparece após o Login) ---
# Estilo idêntico ao da imagem que você enviou (Início azul e fundo dark)
tab_inicio, tab_gerador, tab_precos, tab_textos, tab_config = st.tabs([
    "🏠 Início", 
    "📑 Gerador", 
    "💰 Tabela de Preços", 
    "✍️ Modelos", 
    "⚙️ Configurações"
])

# --- CONTEÚDO DE CADA ABA ---

with tab_inicio:
    st.markdown("<h1 style='text-align:center; padding: 40px;'>PAINEL ADMINISTRATIVO</h1>", unsafe_allow_html=True)
    st.markdown("""
        <div style='text-align:center; padding: 20px;'>
            <h3>Bem-vindo à RR Smart Soluções</h3>
            <p>Utilize o menu acima para navegar entre as ferramentas do sistema.</p>
        </div>
    """, unsafe_allow_html=True)

with tab_gerador:
    # Insira aqui a lógica de pages/1_Gerador_de_Orcamento.py
    st.header("Gerador de Orçamentos")
    with st.container(border=True):
        st.write("Formulário de orçamentos aqui...")

with tab_precos:
    # Insira aqui a lógica de pages/Tabela_de_Precos.py
    st.header("Gestão de Preços")
    with st.container(border=True):
        st.write("Tabela de materiais aqui...")

with tab_textos:
    # Insira aqui a lógica de pages/Modelos_de_Texto.py
    st.header("Modelos de Proposta")
    with st.container(border=True):
        st.write("Área de textos aqui...")

with tab_config:
    st.header("Configurações")
    if st.button("SAIR DO SISTEMA", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()
