import streamlit as st
import pandas as pd
from core.db import get_conn

if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.stop()

st.set_page_config(page_title="Vero | Precos", layout="wide", initial_sidebar_state="collapsed")
user_id = st.session_state.user_id
conn = get_conn()

# Garante que a coluna categoria existe no banco
with conn.cursor() as cur:
    cur.execute("ALTER TABLE precos ADD COLUMN IF NOT EXISTS categoria VARCHAR(50) DEFAULT 'Geral';")
conn.commit()

st.markdown("<style>header {visibility: hidden;} footer {visibility: hidden;} [data-testid='stSidebar'] { display: none; } .stApp { background: radial-gradient(circle at 50% 50%, #101a26 0%, #080d12 100%); color: white; }</style>", unsafe_allow_html=True)

if st.button("VOLTAR", key="b_tp"): st.switch_page("app.py")

st.title("Tabela de Precos por Servico")

with st.container(border=True):
    with st.form("add_p"):
        c1, c2, c3, c4 = st.columns([2, 2, 1, 1])
        ch = c1.text_input("Chave")
        nm = c2.text_input("Produto")
        vl = c3.number_input("Preco", min_value=0.0)
        ct = c4.selectbox("Servico", ["Cameras", "Cercas", "Motores", "Concertinas", "Geral"])
        if st.form_submit_button("CADASTRAR"):
            with conn.cursor() as cur:
                cur.execute("INSERT INTO precos (chave, nome, valor, usuario_id, categoria) VALUES (%s,%s,%s,%s,%s)", (ch,nm,vl,user_id,ct))
            conn.commit()
            st.rerun()

abas = st.tabs(["Todos", "Cameras", "Cercas", "Motores", "Concertinas", "Geral"])
cat_list = [None, "Cameras", "Cercas", "Motores", "Concertinas", "Geral"]

for i, aba_nome in enumerate(["Todos", "Cameras", "Cercas", "Motores", "Concertinas", "Geral"]):
    with abas[i]:
        q = "SELECT chave, nome, valor, categoria FROM precos WHERE usuario_id = %s"
        p = [user_id]
        if cat_list[i]:
            q += " AND categoria = %s"
            p.append(cat_list[i])
        df = pd.read_sql(q, conn, params=p)
        st.data_editor(df, use_container_width=True, key=f"ed_{aba_nome}")
