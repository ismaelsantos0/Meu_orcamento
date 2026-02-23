import streamlit as st
from core.db import get_conn

# 1. Configuração da página - Mantendo o menu lateral fechado
st.set_page_config(
    page_title="Vero | Inteligência em Orçamentos", 
    page_icon="🛡️", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# 2. CSS Avançado para Estilo "Vero Premium" e Remoção da Barra Superior
st.markdown("""
<style>
    /* REMOVER BARRA SUPERIOR E FOOTER */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    
    /* Importando fontes modernas */
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;800&display=swap');

    /* Fundo Dark Gradiente Deep */
    .stApp {
        background: radial-gradient(circle at 50% 50%, #101a26 0%, #080d12 100%);
        font-family: 'Poppins', sans-serif;
    }

    /* Esconder Sidebar no Login */
    [data-testid="stSidebar"] { display: none; }

    /* Container do Login centralizado */
    .login-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        margin-top: 8%; /* Ajustado para compensar a falta da barra */
    }

    /* Título Vero */
    .brand-title {
        color: #ffffff;
        font-size: 64px;
        font-weight: 800;
        letter-spacing: -2px;
        margin-bottom: 0px;
        text-shadow: 0px 10px 30px rgba(0,0,0,0.5);
    }
    
    .brand-subtitle {
        color: #3b82f6;
        font-size: 14px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 5px;
        margin-bottom: 50px;
    }

    /* Inputs Estilo Cápsula (Conforme sua imagem de referência) */
    .stTextInput > div > div {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 50px !important;
        padding: 8px 25px !important;
        color: white !important;
    }

    /* Botão de Login Estilo Cápsula Branca */
    .stButton > button {
        background-color: #ffffff !important;
        color: #080d12 !important;
        border-radius: 50px !important;
        font-weight: 800 !important;
        font-size: 16px !important;
        padding: 12px 0px !important;
        width: 100%;
        border: none !important;
        transition: all 0.3s ease !important;
        margin-top: 30px;
    }

    .stButton > button:hover {
        transform: scale(1.03) !important;
        background-color: #3b82f6 !important;
        color: white !important;
    }

    /* Ajuste para remover bordas do formulário */
    [data-testid="stForm"] {
        border: none !important;
        padding: 0 !important;
    }
</style>
""", unsafe_allow_html=True)

# 3. Lógica de Autenticação
def validar_login(email, senha):
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute("SELECT id, email FROM usuarios WHERE email = %s AND senha = %s", (email, senha))
            return cur.fetchone()
    except:
        return None

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- TELA DE LOGIN VERO ---
if not st.session_state.logged_in:
    _, col_login, _ = st.columns([1, 1, 1])
    
    with col_login:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        st.markdown('<h1 class="brand-title">VERO</h1>', unsafe_allow_html=True)
        st.markdown('<p class="brand-subtitle">Smart Systems</p>', unsafe_allow_html=True)
        
        with st.form("login_form"):
            email_i = st.text_input("Username", placeholder="E-mail de acesso", label_visibility="collapsed")
            senha_i = st.text_input("Password", type="password", placeholder="Senha", label_visibility="collapsed")
            
            if st.form_submit_button("LOGIN"):
                user = validar_login(email_i, senha_i)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.user_id = user[0]
                    st.session_state.user_email = user[1]
                    st.rerun()
                else:
                    st.error("Credenciais inválidas.")
        
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- ÁREA LOGADA ---
# Reativar cabeçalho se desejar na área interna, ou manter oculto para design personalizado
st.markdown("<style>[data-testid='stSidebar'] { display: block !important; }</style>", unsafe_allow_html=True)

st.title(f"Bem-vindo ao Vero")
st.write("Acesso autorizado. Utilize o menu lateral.")
