import streamlit as st
import pandas as pd
from core.db import get_conn

if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.stop()

st.set_page_config(page_title="Vero | Preços", layout="wide", initial_sidebar_state="collapsed")
user_id = st.session_state.user_id
conn = get_conn()

st.markdown("<style>header {visibility: hidden;} footer {visibility: hidden;} [data-testid='stSidebar'] { display: none; } .stApp { background: radial-gradient(circle at 50% 50%, #101a26 0%, #080d12 100%); color: white; }</style>", unsafe_allow_html=True)

if st.button("VOLTAR", key="b_tp"): st.switch_page("app.py")

st.title("Tabela de Preços")

with st.container(border=True):
    with st.form("add_p", clear_on_submit=True):
        c1, c2, c3, c4 = st.columns([2, 2, 1, 1.5])
        ch = c1.text_input("Chave única")
        nm = c2.text_input("Produto")
        vl = c3.number_input("Preço R$", min_value=0.0)
        ct = c4.selectbox("Categoria", ["CFTV", "Cerca/Concertina", "Motor de Portão", "Geral"])
        if st.form_submit_button("CADASTRAR"):
            with conn.cursor() as cur:
                cur.execute("INSERT INTO precos (chave, nome, valor, usuario_id, categoria) VALUES (%s,%s,%s,%s,%s)", (ch,nm,vl,user_id,ct))
            conn.commit()
            st.rerun()

abas = st.tabs(["Todos", "CFTV", "Cerca/Concertina", "Motor de Portão", "Geral"])
cat_list = [None, "CFTV", "Cerca/Concertina", "Motor de Portão", "Geral"]

for i, aba_nome in enumerate(abas):
    with aba_nome:
        q = "SELECT chave, nome, valor, categoria FROM precos WHERE usuario_id = %s"
        p = [user_id]
        if cat_list[i]:
            q += " AND categoria = %s"
            p.append(cat_list[i])
        df = pd.read_sql(q, conn, params=p)
        st.data_editor(df, use_container_width=True, key=f"ed_{cat_list[i] or 'all'}")
