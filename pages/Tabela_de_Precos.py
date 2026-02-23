import streamlit as st
import pandas as pd
from core.db import get_conn
from core.style import apply_vero_style

st.set_page_config(page_title="Vero | Preços", layout="wide")
apply_vero_style()
user_id = st.session_state.user_id
conn = get_conn()

if st.button("← VOLTAR"): st.switch_page("app.py")

st.title("Tabela de Preços")

with st.container(border=True):
    with st.form("add_item", clear_on_submit=True):
        c1, c2, c3, c4 = st.columns([1, 2, 1, 1])
        ch = c1.text_input("Chave")
        nm = c2.text_input("Produto")
        vl = c3.number_input("Valor R$", min_value=0.0)
        ct = c4.selectbox("Categoria", ["CFTV", "Cerca/Concertina", "Motor de Portão", "Geral"])
        if st.form_submit_button("CADASTRAR ITEM"):
            with conn.cursor() as cur:
                cur.execute("INSERT INTO precos (chave, nome, valor, usuario_id, categoria) VALUES (%s,%s,%s,%s,%s)", (ch,nm,vl,user_id,ct))
            conn.commit()
            st.rerun()

tabs = st.tabs(["Todos", "CFTV", "Cerca/Concertina", "Motor de Portão", "Geral"])
cats = [None, "CFTV", "Cerca/Concertina", "Motor de Portão", "Geral"]

for i, tab in enumerate(tabs):
    with tab:
        q = "SELECT chave, nome, valor, categoria FROM precos WHERE usuario_id = %s"
        p = [user_id]
        if cats[i]:
            q += " AND categoria = %s"
            p.append(cats[i])
        df = pd.read_sql(q, conn, params=p)
        st.data_editor(df, use_container_width=True, key=f"edit_{cats[i] or 'all'}")
