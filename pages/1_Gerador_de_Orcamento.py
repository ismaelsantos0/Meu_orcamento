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

# --- ESTILO VERO PREMIUM (SEM EMOJIS) ---
st.markdown("""
<style>
    header {visibility: hidden;} footer {visibility: hidden;}
    [data-testid="stSidebar"] { display: none; }
    .stApp { background: radial-gradient(circle at 50% 50%, #101a26 0%, #080d12 100%); color: white; font-family: 'Poppins', sans-serif; }
    [data-testid="stVerticalBlockBorderWrapper"] { background: rgba(255,255,255,0.03) !important; border: 1px solid rgba(255,255,255,0.1) !important; border-radius: 20px !important; }
    .stButton > button { background-color: #ffffff !important; color: #080d12 !important; border-radius: 50px !important; font-weight: 800 !important; border: none !important; }
    .stButton > button:hover { background-color: #3b82f6 !important; color: white !important; }
    .stDownloadButton > button { background-color: #3b82f6 !important; color: white !important; border-radius: 50px !important; width: 100%; }
</style>
""", unsafe_allow_html=True)

# --- NAVEGAÇÃO ---
if st.button("VOLTAR"):
    st.switch_page("app.py")

# --- BUSCA CONFIGURAÇÕES DO USUÁRIO ---
def get_user_config(uid):
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("SELECT nome_empresa, whatsapp, logo, pagamento_padrao, garantia_padrao, validade_dias FROM config_empresa WHERE usuario_id = %s", (uid,))
        return cur.fetchone()

config_data = get_user_config(user_id) or ("Vero", "", None, "A combinar", "90 dias", 7)

st.title("Gerador de Orcamentos")

# --- FORMULÁRIO DE CLIENTE ---
with st.container(border=True):
    col_c1, col_c2 = st.columns(2)
    nome_cliente = col_c1.text_input("Cliente", placeholder="Nome do cliente")
    zap_cliente = col_c2.text_input("Contato", placeholder="WhatsApp")

# --- SELEÇÃO DE SERVIÇO (PLUGINS) ---
plugins = registry.get_plugins()
servico_label = st.selectbox("Tipo de Servico", list(p.label for p in plugins.values()))
plugin = next(p for p in plugins.values() if p.label == servico_label)

with st.container(border=True):
    inputs = plugin.render_fields()

# --- ITENS EXTRAS DA TABELA DE PREÇOS ---
with st.container(border=True):
    st.subheader("Itens Adicionais")
    conn = get_conn()
    df_precos = pd.read_sql("SELECT chave, nome, valor FROM precos WHERE usuario_id = %s", conn, params=(user_id,))
    
    opcoes = {f"{r['nome']} (R$ {r['valor']:.2f})": r for _, r in df_precos.iterrows()}
    selecionados = st.multiselect("Adicionar pecas da sua tabela", list(opcoes.keys()))
    
    itens_extras = []
    if selecionados:
        cols = st.columns(3)
        for i, sel in enumerate(selecionados):
            with cols[i % 3]:
                qtd = st.number_input(f"Qtd: {opcoes[sel]['nome']}", min_value=1, value=1, key=f"extra_{i}")
                itens_extras.append({"info": opcoes[sel], "qtd": qtd})

# --- PROCESSAMENTO FINAL ---
if st.button("FINALIZAR ORCAMENTO", use_container_width=True):
    # 1. Calcula base do plugin (Câmeras, Cercas, etc)
    res = plugin.compute(conn, inputs)
    
    # 2. Soma itens extras
    for ex in itens_extras:
        subtotal_ex = ex['qtd'] * ex['info']['valor']
        res['items'].append({
            'desc': f"[ADICIONAL] {ex['info']['nome']}",
            'qty': ex['qtd'],
            'unit': ex['info']['valor'],
            'sub': subtotal_ex
        })
        res['subtotal'] += subtotal_ex

    st.success(f"Orcamento finalizado: R$ {res['subtotal']:.2f}")
    
    # --- RESULTADOS: PDF E MATERIAIS ---
    st.divider()
    aba_pdf, aba_mat = st.tabs(["Proposta em PDF", "Lista de Materiais"])

    with aba_pdf:
        from core.pdf.summary import render_summary_pdf
        pdf_io = io.BytesIO()
        pdf_payload = {
            "logo_bytes": config_data[2],
            "empresa": config_data[0],
            "whatsapp": config_data[1],
            "cliente": nome_cliente or "Cliente",
            "data_str": datetime.now().strftime("%d/%m/%Y"),
            "servicos": [res],
            "total": res['subtotal'],
            "pagamento": config_data[3],
            "garantia": config_data[4],
            "validade_dias": config_data[5]
        }
        render_summary_pdf(pdf_io, pdf_payload)
        
        st.download_button(
            label="Baixar Proposta em PDF",
            data=pdf_io.getvalue(),
            file_name=f"Orcamento_{nome_cliente}.pdf",
            mime="application/pdf"
        )
        
        # Resumo para WhatsApp
        texto_wpp = f"Olá {nome_cliente}! Segue a proposta de {servico_label}.\nTotal: R$ {res['subtotal']:.2f}"
        st.text_area("Texto para WhatsApp", texto_wpp)

    with aba_mat:
        lista_materiais = build_materials_list(res)
        st.table(pd.DataFrame(lista_materiais))
