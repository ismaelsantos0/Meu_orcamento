import streamlit as st
from core.db import get_conn

if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.stop()

st.set_page_config(page_title="Vero | Textos", layout="wide", initial_sidebar_state="collapsed")
user_id = st.session_state.user_id

st.markdown("<style>header {visibility: hidden;} footer {visibility: hidden;} [data-testid='stSidebar'] { display: none; } .stApp { background: radial-gradient(circle at 50% 50%, #101a26 0%, #080d12 100%); color: white; }</style>", unsafe_allow_html=True)

if st.button("VOLTAR", key="back_textos"):
    st.switch_page("app.py")

st.title("Modelos de Proposta PDF")

# NOMES PADRONIZADOS COM A TABELA DE PREÇOS
servicos = ["CFTV", "Cerca/Concertina", "Motor de Portão"]
servico_sel = st.selectbox("Escolha o servico", servicos)

conn = get_conn()
with conn.cursor() as cur:
    cur.execute("SELECT texto_detalhado FROM modelos_texto WHERE usuario_id = %s AND servico_tipo = %s", (user_id, servico_sel))
    res = cur.fetchone()
    texto_atual = res[0] if res else ""

with st.form("f_text"):
    novo = st.text_area("Descricao detalhada (O que sera entregue)", value=texto_atual, height=300)
    if st.form_submit_button("SALVAR MODELO"):
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO modelos_texto (usuario_id, servico_tipo, texto_detalhado) 
                VALUES (%s, %s, %s) 
                ON CONFLICT (usuario_id, servico_tipo) 
                DO UPDATE SET texto_detalhado = EXCLUDED.texto_detalhado
            """, (user_id, servico_sel, novo))
        conn.commit()
        st.success(f"Modelo para {servico_sel} atualizado!")
