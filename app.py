import streamlit as st
from core.style import apply_vero_style

st.set_page_config(page_title="Vero | RR Smart", layout="wide")
apply_vero_style()

st.markdown("<h1 style='text-align:center; padding: 40px;'>PAINEL VERO</h1>", unsafe_allow_html=True)

# Usando gap="large" para separar os cards
col1, col2 = st.columns(2, gap="large")
col3, col4 = st.columns(2, gap="large")

with col1:
    with st.container(border=True):
        st.subheader("Orçamentos")
        st.write("Gerar novas propostas em PDF.")
        if st.button("ABRIR GERADOR", key="h1"): st.switch_page("pages/1_Gerador_de_Orcamento.py")

with col2:
    with st.container(border=True):
        st.subheader("Preços")
        st.write("Lista de materiais e serviços.")
        if st.button("VER MATERIAIS", key="h2"): st.switch_page("pages/Tabela_de_Precos.py")

with col3:
    with st.container(border=True):
        st.subheader("Textos")
        st.write("Modelos de benefícios para o PDF.")
        if st.button("EDITAR MODELOS", key="h3"): st.switch_page("pages/Modelos_de_Texto.py")

with col4:
    with st.container(border=True):
        st.subheader("Ajustes")
        st.write("Configurações da empresa e logo.")
        if st.button("CONFIGURAÇÕES", key="h4"): st.switch_page("pages/Configuracoes.py")

st.markdown("<br><br>", unsafe_allow_html=True)
if st.button("SAIR DO SISTEMA", key="logout"):
    st.session_state.logged_in = False
    st.rerun()
