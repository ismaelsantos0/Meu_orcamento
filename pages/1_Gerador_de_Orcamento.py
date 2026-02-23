import streamlit as st
import io
import pandas as pd
from datetime import datetime
from core.db import get_conn
from core.materials import build_materials_list
import services.registry as registry

if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.stop()

st.set_page_config(page_title="Vero | Gerador", layout="wide", initial_sidebar_state="collapsed")
user_id = st.session_state.user_id

st.markdown("""
<style>
    header {visibility: hidden;} footer {visibility: hidden;}
    [data-testid="stSidebar"] { display: none; }
    .stApp { background: radial-gradient(circle at 50% 50%, #101a26 0%, #080d12 100%); color: white; font-family: 'Poppins', sans-serif; }
    [data-testid="stVerticalBlockBorderWrapper"] { background: rgba(255,255,255,0.03) !important; border: 1px solid rgba(255,255,255,0.1) !important; border-radius: 20px !important; }
    .stButton > button { background-color: #ffffff !important; color: #080d12 !important; border-radius: 50px !important; font-weight: 800 !important; }
</style>
""", unsafe_allow_html=True)

if st.button("VOLTAR"):
    st.switch_page("app.py")

st.title("Gerador de Orcamentos")

conn = get_conn()
plugins = registry.get_plugins()

with st.container(border=True):
    col1, col2 = st.columns(2)
    cliente = col1.text_input("Cliente")
    contato = col2.text_input("Contato")

servico_label = st.selectbox("Tipo de Servico", list(p.label for p in plugins.values()))
plugin = next(p for p in plugins.values() if p.label == servico_label)

with st.container(border=True):
    inputs = plugin.render_fields()

if st.button("FINALIZAR", use_container_width=True):
    res = plugin.compute(conn, inputs)
    st.success(f"Orcamento finalizado: R$ {res['subtotal']:.2f}")
    # Logica de PDF omitida aqui para brevidade, mas deve seguir o padrao anterior
