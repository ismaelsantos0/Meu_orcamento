import streamlit as st
import pandas as pd
from core.db import get_conn

if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.stop()

st.set_page_config(page_title="Vero | Precos", layout="wide", initial_sidebar_state="collapsed")
user_id = st.session_state.user_id

st.markdown("""
<style>
    header {visibility: hidden;} footer {visibility: hidden;}
    [data-testid="stSidebar"] { display: none; }
    .stApp { background: radial-gradient(circle at 50% 50%, #101a26 0%, #080d12 100%); color: white; font-family: 'Poppins', sans-serif; }
    .stButton > button { background-color: #ffffff !important; color: #080d12 !important; border-radius: 50px !important; font-weight: 800 !important; }
    .stDataEditor { background-color: rgba(255,255,255,0.05) !important; border-radius: 15px; }
</style>
""", unsafe_allow_html=True)

if st.button("VOLTAR"):
    st.switch_page("app.py")

st.title("Tabela de Precos")

conn = get_conn()

with st.container():
    with st.form("add_item"):
        c1, c2, c3 = st.columns(3)
        chave = c1.text_input("Chave")
        nome = c2.text_input("Produto")
        valor = c3.number_input("Preco", min_value=0.0)
        if st.form_submit_button("CADASTRAR"):
            with conn.cursor() as cur:
                cur.execute("INSERT INTO precos (chave, nome, valor, usuario_id) VALUES (%s, %s, %s, %s)", (chave, nome, valor, user_id))
            conn.commit()
            st.rerun()

df = pd.read_sql("SELECT chave, nome, valor FROM precos WHERE usuario_id = %s", conn, params=(user_id,))
st.data_editor(df, use_container_width=True)
