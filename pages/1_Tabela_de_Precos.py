import streamlit as st
import pandas as pd
from core.db import get_conn

if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.stop()

st.set_page_config(page_title="Vero | Preços", layout="wide", initial_sidebar_state="collapsed")
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

st.title("💰 Minha Tabela de Preços")

conn = get_conn()

with st.container(border=True):
    with st.form("add_item", clear_on_submit=True):
        c1, c2, c3 = st.columns([2, 3, 1])
        chave = c1.text_input("Chave única (ex: motor_jet)")
        nome = c2.text_input("Descrição do Produto")
        valor = c3.number_input("Preço R$", min_value=0.0)
        if st.form_submit_button("CADASTRAR"):
            with conn.cursor() as cur:
                cur.execute("INSERT INTO precos (chave, nome, valor, usuario_id) VALUES (%s, %s, %s, %s)", (chave, nome, valor, user_id))
            conn.commit()
            st.success("Item salvo!")
            st.rerun()

st.subheader("📋 Itens em Linha")
df = pd.read_sql("SELECT chave, nome, valor FROM precos WHERE usuario_id = %s ORDER BY nome", conn, params=(user_id,))
st.data_editor(df, use_container_width=True, disabled=["chave"])
