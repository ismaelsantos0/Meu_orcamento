import streamlit as st
import pandas as pd
from core.db import get_conn

# =========================
# TRAVA DE SEGURANÇA
# =========================
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.error("❌ Acesso negado! Por favor, faça login na página principal.")
    st.stop()

user_id = st.session_state.user_id
st.set_page_config(page_title="Preços", page_icon="💰", layout="wide")

st.title("💰 Minha Tabela de Preços")

conn = get_conn()

# Formulário de Adição
with st.container(border=True):
    st.subheader("➕ Novo Item")
    with st.form("add_item", clear_on_submit=True):
        c1, c2, c3 = st.columns([2, 3, 1])
        n_chave = c1.text_input("Chave (ex: cabo_cat5)")
        n_nome = c2.text_input("Nome do Produto")
        n_valor = c3.number_input("Valor R$", min_value=0.0)
        
        if st.form_submit_button("Salvar Item"):
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO precos (chave, nome, valor, usuario_id) 
                    VALUES (%s, %s, %s, %s)
                """, (n_chave, n_nome, n_valor, user_id))
            conn.commit()
            st.success("Item adicionado!")
            st.rerun()

# Edição de Itens Existentes
st.divider()
st.subheader("📋 Meus Itens")
df = pd.read_sql("SELECT chave, nome, valor FROM precos WHERE usuario_id = %s ORDER BY nome", conn, params=(user_id,))

if not df.empty:
    edited_df = st.data_editor(df, use_container_width=True, num_rows="dynamic", key="editor_precos")
    
    if st.button("💾 Salvar Alterações na Tabela", type="primary"):
        with conn.cursor() as cur:
            # Primeiro remove o que foi deletado no editor (opcional, mas recomendado)
            cur.execute("DELETE FROM precos WHERE usuario_id = %s", (user_id,))
            for _, row in edited_df.iterrows():
                cur.execute("""
                    INSERT INTO precos (chave, nome, valor, usuario_id) 
                    VALUES (%s, %s, %s, %s)
                """, (row['chave'], row['nome'], row['valor'], user_id))
        conn.commit()
        st.success("Alterações salvas com sucesso!")
else:
    st.info("Sua tabela está vazia. Adicione itens acima.")
