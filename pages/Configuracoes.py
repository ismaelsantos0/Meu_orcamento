import streamlit as st
from core.db import get_conn

if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.stop()

st.set_page_config(page_title="Vero | Ajustes", layout="wide", initial_sidebar_state="collapsed")
user_id = st.session_state.user_id

st.markdown("<style>header {visibility: hidden;} footer {visibility: hidden;} [data-testid='stSidebar'] { display: none; } .stApp { background: radial-gradient(circle at 50% 50%, #101a26 0%, #080d12 100%); color: white; } .stButton > button { background-color: #ffffff !important; border-radius: 50px !important; }</style>", unsafe_allow_html=True)

if st.button("VOLTAR"):
    st.switch_page("app.py")

st.title("Configuracoes")

with st.form("config"):
    nome = st.text_input("Nome da Empresa")
    if st.form_submit_button("SALVAR"):
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute("UPDATE config_empresa SET nome_empresa=%s WHERE usuario_id=%s", (nome, user_id))
        conn.commit()
        st.success("Salvo")
