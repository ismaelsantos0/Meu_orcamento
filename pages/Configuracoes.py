import streamlit as st
from core.db import get_conn

# --- TRAVA DE SEGURANÇA ---
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.error("Acesso negado.")
    st.stop()

st.set_page_config(page_title="Vero | Ajustes", layout="wide", initial_sidebar_state="collapsed")
user_id = st.session_state.user_id

# --- ESTILO VERO ---
st.markdown("""
<style>
    header {visibility: hidden;} footer {visibility: hidden;}
    [data-testid="stSidebar"] { display: none; }
    .stApp { background: radial-gradient(circle at 50% 50%, #101a26 0%, #080d12 100%); color: white; }
    .stButton > button { background-color: #ffffff !important; color: #080d12 !important; border-radius: 50px !important; font-weight: 800 !important; }
</style>
""", unsafe_allow_html=True)

if st.button("← VOLTAR"):
    st.switch_page("app.py")

st.title("⚙️ Configurações")

def buscar_dados():
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("SELECT nome_empresa, whatsapp, pagamento_padrao, garantia_padrao, validade_dias, logo FROM config_empresa WHERE usuario_id = %s", (user_id,))
        return cur.fetchone()

dados = buscar_dados() or ("", "", "À vista", "90 dias", 7, None)

with st.container(border=True):
    with st.form("config"):
        nome = st.text_input("Nome da Empresa", value=dados[0])
        wpp = st.text_input("WhatsApp", value=dados[1])
        logo = st.file_uploader("Alterar Logo", type=['png', 'jpg'])
        if st.form_submit_button("Atualizar Perfil"):
            logo_bytes = logo.read() if logo else None
            conn = get_conn()
            with conn.cursor() as cur:
                if buscar_dados():
                    cur.execute("UPDATE config_empresa SET nome_empresa=%s, whatsapp=%s, logo=COALESCE(%s, logo) WHERE usuario_id=%s", (nome, wpp, logo_bytes, user_id))
                else:
                    cur.execute("INSERT INTO config_empresa (usuario_id, nome_empresa, whatsapp, logo) VALUES (%s, %s, %s, %s)", (user_id, nome, wpp, logo_bytes))
            conn.commit()
            st.success("Configurações salvas!")
