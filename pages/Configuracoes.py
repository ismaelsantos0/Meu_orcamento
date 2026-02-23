import streamlit as st
from core.db import get_conn

if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.stop()

st.set_page_config(page_title="Vero | Ajustes", layout="wide", initial_sidebar_state="collapsed")
user_id = st.session_state.user_id

st.markdown("<style>header {visibility: hidden;} footer {visibility: hidden;} [data-testid='stSidebar'] { display: none; } .stApp { background: radial-gradient(circle at 50% 50%, #101a26 0%, #080d12 100%); color: white; } .stButton > button { background-color: #ffffff !important; border-radius: 50px !important; color: black !important; font-weight: 800; }</style>", unsafe_allow_html=True)

if st.button("VOLTAR"):
    st.switch_page("app.py")

st.title("Configuracoes")

def buscar_c():
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("SELECT nome_empresa, whatsapp FROM config_empresa WHERE usuario_id = %s", (user_id,))
        return cur.fetchone()

atual = buscar_c() or ("Empresa", "")

with st.form("conf"):
    novo_nome = st.text_input("Nome da Empresa", value=atual[0])
    novo_wpp = st.text_input("WhatsApp", value=atual[1])
    if st.form_submit_button("SALVAR"):
        conn = get_conn()
        with conn.cursor() as cur:
            if buscar_c():
                cur.execute("UPDATE config_empresa SET nome_empresa=%s, whatsapp=%s WHERE usuario_id=%s", (novo_nome, novo_wpp, user_id))
            else:
                cur.execute("INSERT INTO config_empresa (usuario_id, nome_empresa, whatsapp) VALUES (%s, %s, %s)", (user_id, novo_nome, novo_wpp))
        conn.commit()
        st.success("Configuracoes salvas")
