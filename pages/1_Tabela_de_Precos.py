# pages/Tabela_de_Precos.py
import streamlit as st
import pandas as pd
from core.db import get_conn

# Proteção de Login
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("Por favor, faça login na página principal.")
    st.stop()

user_id = st.session_state.user_id
conn = get_conn()

st.title("💰 Minha Tabela de Preços")

# FORMULÁRIO DE ADIÇÃO (SALVA COM O SEU ID)
with st.container(border=True):
    with st.form("novo_item"):
        c1, c2, c3 = st.columns([2, 3, 1])
        chave = c1.text_input("Chave única")
        nome = c2.text_input("Nome comercial")
        valor = c3.number_input("Preço R$", min_value=0.0)
        if st.form_submit_button("Adicionar"):
            with conn.cursor() as cur:
                cur.execute("INSERT INTO precos (chave, nome, valor, usuario_id) VALUES (%s, %s, %s, %s)", 
                            (chave, nome, valor, user_id))
            conn.commit()
            st.success("Item salvo!")
            st.rerun()

# TABELA DE EDIÇÃO (MOSTRA APENAS OS SEUS)
st.subheader("Meus Itens Cadastrados")
df = pd.read_sql("SELECT chave, nome, valor FROM precos WHERE usuario_id = %s", conn, params=(user_id,))
if not df.empty:
    edited = st.data_editor(df, use_container_width=True)
    if st.button("Salvar Alterações"):
        with conn.cursor() as cur:
            for i, row in edited.iterrows():
                cur.execute("UPDATE precos SET nome=%s, valor=%s WHERE chave=%s AND usuario_id=%s", 
                            (row['nome'], row['valor'], row['chave'], user_id))
        conn.commit()
        st.success("Tabela atualizada!")
