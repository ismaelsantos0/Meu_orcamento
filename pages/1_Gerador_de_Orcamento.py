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

st.markdown("<style>header {visibility: hidden;} footer {visibility: hidden;} [data-testid='stSidebar'] { display: none; } .stApp { background: radial-gradient(circle at 50% 50%, #101a26 0%, #080d12 100%); color: white; }</style>", unsafe_allow_html=True)

if st.button("VOLTAR", key="back_gen"): st.switch_page("app.py")

# Busca configurações da empresa RR Smart Soluções
with conn.cursor() as cur:
    cur.execute("SELECT nome_empresa, whatsapp, logo, pagamento_padrao, garantia_padrao, validade_dias FROM config_empresa WHERE usuario_id = %s", (user_id,))
    cfg = cur.fetchone() or ("RR Smart Soluções", "", None, "A combinar", "90 dias", 7)

st.title("Gerador de Orcamentos")

# ... (Blocos de Cliente e Plugin)
plugins = registry.get_plugins()
servico_label = st.selectbox("Tipo de Servico", list(p.label for p in plugins.values()))
plugin = next(p for p in plugins.values() if p.label == servico_label)

with st.container(border=True):
    inputs = plugin.render_fields()

# MAPEAMENTO PARA SINCRONIZAR COM AS CATEGORIAS DO BANCO
mapeamento = {
    "Camera": "CFTV",
    "Motor": "Motor de Portão",
    "Cerca": "Cerca/Concertina",
    "Concertina": "Cerca/Concertina"
}
categoria_atual = "Geral"
for termo, cat_banco in mapeamento.items():
    if termo in servico_label:
        categoria_atual = cat_banco
        break

# ... (Bloco de Itens Adicionais filtrados por categoria_atual)

if st.button("FINALIZAR E GERAR PDF", use_container_width=True, key="btn_pdf_final"):
    res = plugin.compute(conn, inputs)
    
    # BUSCA O TEXTO DETALHADO SALVO NA PÁGINA 'MODELOS'
    with conn.cursor() as cur:
        cur.execute("SELECT texto_detalhado FROM modelos_texto WHERE usuario_id = %s AND servico_tipo = %s", (user_id, categoria_atual))
        txt_modelo = cur.fetchone()
        # Se houver texto no banco, ele substitui a descrição curta
        res['entrega_detalhada'] = txt_modelo[0] if txt_modelo else "Instalacao padrao realizada."

    from core.pdf.summary import render_summary_pdf
    pdf_io = io.BytesIO()
    
    # PAYLOAD ENVIADO PARA O PDF
    payload = {
        "logo_bytes": cfg[2], "empresa": cfg[0], "whatsapp": cfg[1], 
        "cliente": st.session_state.get('cliente_nome', 'Cliente'), 
        "data_str": datetime.now().strftime("%d/%m/%Y"),
        "servicos": [res], "total": res['subtotal'], 
        "pagamento": cfg[3], "garantia": cfg[4], "validade_dias": cfg[5],
        "detalhamento_entrega": res['entrega_detalhada'] # ENVIA O TEXTO LONGO AQUI
    }
    
    render_summary_pdf(pdf_io, payload)
    st.download_button("📥 BAIXAR PROPOSTA PDF", pdf_io.getvalue(), "Orcamento_Vero.pdf", "application/pdf")
