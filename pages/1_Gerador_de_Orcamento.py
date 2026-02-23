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
conn = get_conn()

st.markdown("<style>header {visibility: hidden;} footer {visibility: hidden;} [data-testid='stSidebar'] { display: none; } .stApp { background: radial-gradient(circle at 50% 50%, #101a26 0%, #080d12 100%); color: white; } .stButton > button { background-color: #ffffff !important; color: #080d12 !important; border-radius: 50px !important; font-weight: 800 !important; }</style>", unsafe_allow_html=True)

if st.button("VOLTAR", key="back_gen"):
    st.switch_page("app.py")

st.title("Gerador de Orcamentos")

with st.container(border=True):
    col1, col2 = st.columns(2)
    cliente = col1.text_input("Cliente")
    contato = col2.text_input("Contato")

plugins = registry.get_plugins()
servico_label = st.selectbox("Tipo de Servico", list(p.label for p in plugins.values()))
plugin = next(p for p in plugins.values() if p.label == servico_label)

with st.container(border=True):
    inputs = plugin.render_fields()

# Filtro de materiais por categoria
cat_map = {"Concertina": "Concertinas", "Cerca": "Cercas", "Camera": "Cameras", "Motor": "Motores"}
cat_filtro = next((v for k, v in cat_map.items() if k in servico_label), "Geral")

df_precos = pd.read_sql("SELECT chave, nome, valor FROM precos WHERE usuario_id = %s AND (categoria = %s OR categoria = 'Geral')", conn, params=(user_id, cat_filtro))
opcoes = {f"{r['nome']} (R$ {r['valor']:.2f})": r for _, r in df_precos.iterrows()}
selecionados = st.multiselect("Itens Adicionais", list(opcoes.keys()))

extras = []
if selecionados:
    cols = st.columns(3)
    for i, sel in enumerate(selecionados):
        with cols[i % 3]:
            qtd = st.number_input(f"Qtd: {opcoes[sel]['nome']}", min_value=1, key=f"q_{i}")
            extras.append({"info": opcoes[sel], "qtd": qtd})

if st.button("FINALIZAR", use_container_width=True, key="btn_fin"):
    res = plugin.compute(conn, inputs)
    for ex in extras:
        sub = ex['qtd'] * ex['info']['valor']
        res['items'].append({'desc': ex['info']['nome'], 'qty': ex['qtd'], 'unit': ex['info']['valor'], 'sub': sub})
        res['subtotal'] += sub
    
    # Busca texto customizado
    with conn.cursor() as cur:
        cur.execute("SELECT texto_detalhado FROM modelos_texto WHERE usuario_id = %s AND servico_tipo = %s", (user_id, cat_filtro))
        txt = cur.fetchone()
        res['entrega_detalhada'] = txt[0] if txt else "Instalacao padrao."

    st.success(f"Total: R$ {res['subtotal']:.2f}")
    
    from core.pdf.summary import render_summary_pdf
    pdf_io = io.BytesIO()
    # Payload simplificado para exemplo
    render_summary_pdf(pdf_io, {"empresa": "Vero", "cliente": cliente, "servicos": [res], "total": res['subtotal']})
    st.download_button("Baixar PDF", pdf_io.getvalue(), "orcamento.pdf", "application/pdf", key="dl_pdf")
