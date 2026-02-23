import streamlit as st
from core.db import get_conn

# 1. Configuração da página (DEVE ser a primeira linha)
st.set_page_config(page_title="Login | RR Smart Pro", page_icon="🛡️", layout="wide", initial_sidebar_state="collapsed")

# 2. CSS para "Limpar" a tela e criar o efeito visual Premium
st.markdown("""
<style>
    /* Esconde o menu lateral na tela de login */
    [data-testid="stSidebar"] { display: none; }
    
    .stApp {
        background: radial-gradient(circle at top right, #1e293b, #0f172a);
    }

    .login-card {
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(15px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 28px;
        padding: 50px;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.6);
        margin-top: 10% !important;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        padding: 14px !important;
        text-transform: uppercase;
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

# --- TELA DE LOGIN ---
if not st.session_state.logged_in:
    e1, col_login, e2 = st.columns([1, 1.2, 1])
    with col_login:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.markdown("<h1 style='text-align: center; color: white;'>🛡️ RR Smart Pro</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #94a3b8;'>Acesse sua plataforma de orçamentos</p>", unsafe_allow_html=True)
        
        with st.form("login_form"):
            email_input = st.text_input("E-mail")
            senha_input = st.text_input("Senha", type="password")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.form_submit_button("ENTRAR NO SISTEMA", use_container_width=True):
                user = validar_login(email_input, senha_input)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.user_id = user[0]
                    st.session_state.user_email = user[1]
                    st.rerun()
                else:
                    st.error("Credenciais inválidas.")
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- REDIRECIONAMENTO APÓS LOGIN ---
# Se o usuário logar, mostramos uma tela de boas-vindas simples ou instruções
st.markdown("""<style>[data-testid="stSidebar"] { display: block !important; }</style>""", unsafe_allow_html=True)
st.title(f"Seja bem-vindo, {st.session_state.user_email}!")
st.info("👈 Use o menu ao lado para acessar as ferramentas do sistema.")
