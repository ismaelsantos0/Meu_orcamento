import streamlit as st
import io
import pandas as pd
from datetime import datetime
from core.db import get_conn
from core.materials import build_materials_list
import services.registry as registry

# --- TRAVA DE SEGURANÇA ---
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.stop()

st.set_page_config(page_title="Vero | Gerador", layout="wide", initial_sidebar_state="collapsed")
user_id = st.session_state.user_id
conn = get_conn()

# --- ESTILO VERO ---
st.markdown("""
<style>
    header {visibility: hidden;} footer {visibility: hidden;}
    [data-testid="stSidebar"] { display: none; }
    .stApp { background: radial-gradient(circle at 50% 50%, #101a26 0%, #080d12 100%); color: white; font-family: 'Poppins', sans-serif; }
    .stButton > button { background-color: #ffffff !important; color: #080d12 !important; border-radius: 50px !important; font-weight: 800 !important; }
</style>
""", unsafe_allow_html=True)

if st.button("VOLTAR", key="b_gen_back"): 
    st.switch_page("app.py")

# Busca configurações da empresa (Logo, Nome, WhatsApp)
with conn.cursor() as cur:
    cur.execute("SELECT nome_empresa, whatsapp, logo, pagamento_padrao, garantia_padrao, validade_dias FROM config_empresa WHERE usuario_id = %s", (user_id,))
    cfg = cur.fetchone() or ("RR Smart Soluções", "", None, "A combinar", "90 dias", 7)

st.title("Gerador de Orcamentos")

# --- DADOS DO CLIENTE ---
with st.container(border=True):
    col1, col2 = st.columns(2)
    cliente = col1.text_input("Cliente")
    contato = col2.text_input("Contato")

# --- SELEÇÃO DE SERVIÇO ---
plugins = registry.get_plugins()
servico_label = st.selectbox("Tipo de Servico", list(p.label for p in plugins.values()))
plugin = next(p for p in plugins.values() if p.label == servico_label)

with st.container(border=True):
    inputs = plugin.render_fields()

# --- MAPEAMENTO PARA BUSCA DE TEXTOS E MATERIAIS ---
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

# --- ITENS ADICIONAIS ---
extras_selecionados = []
df_p = pd.read_sql("SELECT chave, nome, valor FROM precos WHERE usuario_id = %s AND (categoria = %s OR categoria = 'Geral')", conn, params=(user_id, categoria_atual))

if not df_p.empty:
    with st.container(border=True):
        st.subheader(f"Adicionais para {categoria_atual}")
        selecionados = st.multiselect("Adicionar pecas avulsas", list({f"{r['nome']} (R$ {r['valor']:.2f})": r for _, r in df_p.iterrows()}.keys()))
        # ... lógica de Qtd omitida para brevidade ...

# --- FINALIZAÇÃO E PDF (ONDE ESTAVA O ERRO) ---
if st.button("FINALIZAR E GERAR PDF", use_container_width=True, key="f_btn_pdf"):
    res = plugin.compute(conn, inputs)
    
    # 1. Busca o Texto de Entrega Personalizado para este serviço
    with conn.cursor() as cur:
        cur.execute("SELECT texto_detalhado FROM modelos_texto WHERE usuario_id = %s AND servico_tipo = %s", (user_id, categoria_atual))
        texto_db = cur.fetchone()
        # Se não achar no banco, usa um texto padrão
        texto_final_pdf = texto_db[0] if texto_db else "Instalacao realizada com materiais de alta qualidade pela RR Smart Solucoes."

    st.success(f"Orcamento finalizado: R$ {res['subtotal']:.2f}")
    
    # 2. Renderização do PDF enviando o texto personalizado
    from core.pdf.summary import render_summary_pdf
    pdf_io = io.BytesIO()
    
    # O PAYLOAD deve conter o campo 'detalhamento_entrega' ou o nome que seu template usa
    payload_pdf = {
        "logo_bytes": cfg[2],
        "empresa": cfg[0],
        "whatsapp": cfg[1],
        "cliente": cliente,
        "data_str": datetime.now().strftime("%d/%m/%Y"),
        "servicos": [res],
        "total": res['subtotal'],
        "pagamento": cfg[3],
        "garantia": cfg[4],
        "validade_dias": cfg[5],
        "detalhamento_entrega": texto_final_pdf  # ESTE CAMPO ENVIA O TEXTO PARA O PDF
    }
    
    render_summary_pdf(pdf_io, payload_pdf)
    
    st.divider()
    st.download_button("📥 BAIXAR PROPOSTA PDF", pdf_io.getvalue(), f"Orcamento_{cliente}.pdf", "application/pdf", use_container_width=True)
