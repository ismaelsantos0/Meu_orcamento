import streamlit as st
from core.db import get_conn

if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.stop()

st.set_page_config(page_title="Vero | Ajustes", layout="wide", initial_sidebar_state="collapsed")
user_id = st.session_state.user_id

st.markdown("""
<style>
    header {visibility: hidden;} footer {visibility: hidden;}
    [data-testid="stSidebar"] { display: none; }
    .stApp { background: radial-gradient(circle at 50% 50%, #101a26 0%, #080d12 100%); color: white; font-family: 'Poppins', sans-serif; }
    .stButton > button { background-color: #ffffff !important; color: #080d12 !important; border-radius: 50px !important; font-weight: 800 !important; }
    [data-testid="stVerticalBlockBorderWrapper"] { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1); border-radius: 20px; }
</style>
""", unsafe_allow_html=True)

if st.button("← VOLTAR"):
    st.switch_page("app.py")

st.title("⚙️ Configurações Vero")

def buscar_config():
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("SELECT nome_empresa, whatsapp, pagamento_padrao, garantia_padrao, validade_dias, logo FROM config_empresa WHERE usuario_id = %s", (user_id,))
        return cur.fetchone()

dados = buscar_config() or ("Empresa", "", "À vista", "90 dias", 7, None)

with st.container(border=True):
    with st.form("config"):
        c1, c2 = st.columns(2)
        with c1:
            n = st.text_input("Nome da Empresa", value=dados[0])
            w = st.text_input("WhatsApp", value=dados[1])
            l = st.file_uploader("Trocar Logo", type=['png', 'jpg'])
        with c2:
            p = st.text_input("Pagamento", value=dados[2])
            g = st.text_input("Garantia", value=dados[3])
            v = st.number_input("Validade (Dias)", value=dados[4])
        
        if st.form_submit_button("ATUALIZAR DADOS"):
            lb = l.read() if l else None
            conn = get_conn()
            with conn.cursor() as cur:
                if buscar_config():
                    cur.execute("UPDATE config_empresa SET nome_empresa=%s, whatsapp=%s, pagamento_padrao=%s, garantia_padrao=%s, validade_dias=%s, logo=COALESCE(%s, logo) WHERE usuario_id=%s", (n, w, p, g, v, lb, user_id))
                else:
                    cur.execute("INSERT INTO config_empresa (usuario_id, nome_empresa, whatsapp, pagamento_padrao, garantia_padrao, validade_dias, logo) VALUES (%s, %s, %s, %s, %s, %s, %s)", (user_id, n, w, p, g, v, lb))
            conn.commit()
            st.success("Perfil atualizado!")
