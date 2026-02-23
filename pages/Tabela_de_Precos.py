import streamlit as st
import pandas as pd
from core.db import get_conn

if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.stop()

st.set_page_config(page_title="Vero | Precos", layout="wide", initial_sidebar_state="collapsed")
user_id = st.session_state.user_id

# Auto-correcao do banco
conn = get_conn()
with conn.cursor() as cur:
    cur.execute("ALTER TABLE precos ADD COLUMN IF NOT EXISTS categoria VARCHAR(50) DEFAULT 'Geral';")
conn.commit()

st.markdown("<style>header {visibility: hidden;} footer {visibility: hidden;} [data-testid='stSidebar'] { display: none; } .stApp { background: radial-gradient(circle at 50% 50%, #101a26 0%, #080d12 100%); color: white; }</style>", unsafe_allow_html=True)

if st.button("VOLTAR", key="back_tabela"):
    st.switch_page("app.py")

st.title("Tabela de Precos por Servico")

with st.container(border=True):
    with st.form("add_item"):
        c1, c2, c3, c4 = st.columns([2, 2, 1, 1])
        chave = c1.text_input("Chave")
        nome = c2.text_input("Produto")
        valor = c3.number_input("Preco", min_value=0.0)
        cat = c4.selectbox("Servico", ["Cameras", "Cercas", "Motores", "Concertinas", "Geral"])
        if st.form_submit_button("CADASTRAR"):
            with conn.cursor() as cur:
                cur.execute("INSERT INTO precos (chave, nome, valor, usuario_id, categoria) VALUES (%s, %s, %s, %s, %s)", (chave, nome, valor, user_id, cat))
            conn.commit()
            st.rerun()

tabs = st.tabs(["Todos", "Cameras", "Cercas", "Motores", "Concertinas", "Geral"])
for i, cat_name in enumerate(["Todos", "Cameras", "Cercas", "Motores", "Concertinas", "Geral"]):
    with tabs[i]:
        query = "SELECT chave, nome, valor, categoria FROM precos WHERE usuario_id = %s"
        params = [user_id]
        if cat_name != "Todos":
            query += " AND categoria = %s"
            params.append(cat_name)
        df = pd.read_sql(query, conn, params=params)
        st.data_editor(df, use_container_width=True, key=f"edit_{cat_name}")
