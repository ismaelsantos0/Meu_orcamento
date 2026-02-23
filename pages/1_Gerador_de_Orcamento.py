import streamlit as st
import io
import pandas as pd
from datetime import datetime
from core.db import get_conn
from core.materials import build_materials_list
import services.registry as registry

# --- SEGURANÇA ---
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.stop()

st.set_page_config(page_title="Vero | Gerador", layout="wide", initial_sidebar_state="collapsed")
user_id = st.session_state.user_id
conn = get_conn()

# --- ESTILO ---
st.markdown("<style>header {visibility: hidden;} footer {visibility: hidden;} [data-testid='stSidebar'] { display: none; } .stApp { background: radial-gradient(circle at 50% 50%, #101a26 0%, #080d12 100%); color: white; }</style>", unsafe_allow_html=True)

if st.button("VOLTAR", key="back_gen"): st.switch_page("app.py")

# Busca configurações da RR Smart Soluções
with conn.cursor() as cur:
    cur.execute("SELECT nome_empresa, whatsapp, logo, pagamento_padrao, garantia_padrao, validade_dias FROM config_empresa WHERE usuario_id = %s", (user_id,))
    cfg = cur.fetchone() or ("RR Smart Soluções", "", None, "A combinar", "90 dias", 7)

st.title("Gerador de Orcamentos")

with st.container(border=True):
    col1, col2 = st.columns(2)
    cliente = col1.text_input("Cliente")
    contato = col2.text_input("Contato")

# Plugin de Serviço
plugins = registry.get_plugins()
servico_label = st.selectbox("Tipo de Servico", list(p.label for p in plugins.values()))
plugin = next(p for p in plugins.values() if p.label == servico_label)

with st.container(border=True):
    inputs = plugin.render_fields()

# Mapeamento para buscar o Modelo de Texto correto
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

# --- FINALIZAÇÃO ---
if st.button("FINALIZAR E GERAR PDF", use_container_width=True):
    # 1. Gera o cálculo base
    res = plugin.compute(conn, inputs)
    
    # 2. Busca o Texto Personalizado (Modelos de Texto)
    with conn.cursor() as cur:
        cur.execute("SELECT texto_detalhado FROM modelos_texto WHERE usuario_id = %s AND servico_tipo = %s", (user_id, categoria_atual))
        txt_modelo = cur.fetchone()
        
    # IMPORTANTE: Substituímos a descrição padrão pelo seu texto detalhado
    if txt_modelo and txt_modelo[0]:
        # Esta linha garante que o 'core/pdf' leia o seu texto longo
        res['entrega_detalhada'] = txt_modelo[0] 
        # Algumas versões do core pedem dentro de 'description' ou 'detalhes'
        res['description'] = txt_modelo[0]
    
    # 3. Chamar o renderizador do core/pdf
    from core.pdf.summary import render_summary_pdf
    pdf_io = io.BytesIO()
    
    payload = {
        "logo_bytes": cfg[2],
        "empresa": cfg[0],
        "whatsapp": cfg[1],
        "cliente": cliente,
        "data_str": datetime.now().strftime("%d/%m/%Y"),
        "servicos": [res], # O texto longo agora está dentro do objeto 'res'
        "total": res['subtotal'],
        "pagamento": cfg[3],
        "garantia": cfg[4],
        "validade_dias": cfg[5],
        "detalhamento_entrega": res.get('entrega_detalhada', "") # Enviamos também como campo solto por segurança
    }
    
    render_summary_pdf(pdf_io, payload)
    
    st.success(f"Orcamento pronto: R$ {res['subtotal']:.2f}")
    st.download_button("📥 BAIXAR PROPOSTA PDF", pdf_io.getvalue(), f"Orcamento_{cliente}.pdf", "application/pdf", use_container_width=True)
