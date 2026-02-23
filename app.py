import streamlit as st
from core.db import get_conn

# 1. Configuração da página - Lacrando o menu lateral para deslogados
st.set_page_config(
    page_title="Vero | Inteligência em Orçamentos", 
    page_icon="", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# 2. CSS Avançado para Estilo "Vero Premium"
st.markdown("""
<style>
    /* Importando fontes modernas */
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;800&display=swap');

    /* Fundo Dark Gradiente Deep */
    .stApp {
        background: radial-gradient(circle at 50% 50%, #101a26 0%, #080d12 100%);
        font-family: 'Poppins', sans-serif;
    }

    /* Esconder Sidebar no Login */
    [data-testid="stSidebar"] { display: none; }

    /* Container do Card de Login */
    .login-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        margin-top: 5%;
    }

    /* Título Vero */
    .brand-title {
        color: #ffffff;
        font-size: 56px;
        font-weight: 800;
        letter-spacing: -2px;
        margin-bottom: 5px;
        text-shadow: 0px 10px 20px rgba(0,0,0,0.5);
    }
    
    .brand-subtitle {
        color: #3b82f6;
        font-size: 14px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 4px;
        margin-bottom: 40px;
    }

    /* Estilização dos Inputs Estilo a Imagem Enviada */
    .stTextInput > div > div {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 50px !important; /* Totalmente arredondado */
        padding: 5px 20px !important;
        color: white !important;
    }

    /* Botão de Login Estilo Cápsula */
    .stButton > button {
        background-color: #ffffff !important;
        color: #080d12 !important;
        border-radius: 50px !important;
        font-weight: 800 !important;
        font-size: 18px !important;
        padding: 15px 0px !important;
        width: 100%;
        border: none !important;
        box-shadow: 0 10px 30px rgba(255,255,255,0.1) !important;
        transition: all 0.3s ease !important;
        margin-top: 20px;
    }

    .stButton > button:hover {
        transform: scale(1.02) !important;
        background-color: #3b82f6 !important;
        color: white !important;
    }

    /* Remove bordas extras do Streamlit */
    [data-testid="stForm"] {
        border: none !important;
        padding: 0 !important;
    }
</style>
""", unsafe_allow_html=True)

# 3. Lógica de Login
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
    # Centralização com colunas
    _, col_login, _ = st.columns([1, 1, 1])
    
    with col_login:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        st.markdown('<h1 class="brand-title">VERO</h1>', unsafe_allow_html=True)
        st.markdown('<p class="brand-subtitle">Smart Systems</p>', unsafe_allow_html=True)
        
        with st.form("login_form"):
            # Usando label_visibility para um visual mais limpo
            email_i = st.text_input("Username", placeholder="E-mail de acesso", label_visibility="collapsed")
            senha_i = st.text_input("Password", type="password", placeholder="Senha", label_visibility="collapsed")
            
            st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)
            
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

# --- ÁREA LOGADA (Apenas aparece após o login) ---
st.markdown("<style>[data-testid='stSidebar'] { display: block !important; }</style>", unsafe_allow_html=True)

# Busca nome da empresa para as boas-vindas
conn = get_conn()
with conn.cursor() as cur:
    cur.execute("SELECT nome_empresa FROM config_empresa WHERE usuario_id = %s", (st.session_state.user_id,))
    res = cur.fetchone()
    nome_emp = res[0] if res else "Parceiro"

st.title(f"Bem-vindo ao Vero, {nome_emp}!")
st.info("Utilize o menu lateral para acessar as ferramentas de orçamento e tabelas de preços.")
