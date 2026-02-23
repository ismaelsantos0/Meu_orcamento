import streamlit as st
import io
import pandas as pd
from datetime import datetime
from core.db import get_conn
from core.materials import build_materials_list
import services.registry as registry

# --- SEGURANCA ---
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.stop()

st.set_page_config(page_title="Vero | Gerador", layout="wide", initial_sidebar_state="collapsed")
user_id = st.session_state.user_id

# --- ESTILO VERO PREMIUM ---
st.markdown("""
<style>
    header {visibility: hidden;} footer {visibility: hidden;}
    [data-testid="stSidebar"] { display: none; }
    .stApp { background: radial-gradient(circle at 50% 50%, #101a26 0%, #080d12 100%); color: white; font-family: 'Poppins', sans-serif; }
    
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(255,255,255,0.03) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 20px !important;
    }
    
    .stButton > button {
        background-color: #ffffff !important;
        color: #080d12 !important;
        border-radius: 50px !important;
        font-weight: 800 !important;
        border: none !important;
        transition: 0.3s;
    }
    .stButton > button:hover {
        transform: scale(1.02);
        background-color: #3b82f6 !important;
        color: white !important;
    }
    .stDownloadButton > button {
        background-color: #3b82f6 !important;
        color: white !important;
        border-radius: 50px !important;
    }
</style>
""", unsafe_allow_html=True)

# --- NAVEGACAO ---
if st.button("VOLTAR AO PAINEL"):
    st.switch_page("app.py")

# --- BUSCA CONFIGURACOES E LOGO ---
def get_user_config(uid):
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT nome_empresa, whatsapp, logo, pagamento_padrao, garantia_padrao, validade_dias 
            FROM config_empresa WHERE usuario_id = %s
        """, (uid,))
        return cur.fetchone()

config_data = get_user_config(user_id) or ("Vero", "", None, "A combinar", "90 dias", 7)

st.title("Gerador de Orcamentos")

# --- FORMULARIO CLIENTE ---
with st.container(border=True):
    col_c1, col_c2 = st.columns(2)
    nome_cliente = col_c1.text_input("Cliente", placeholder="Nome do cliente")
    zap_cliente = col_c2.text_input("Contato", placeholder="WhatsApp")

# --- SELECAO DE SERVICO ---
plugins = registry.get_plugins()
servico_label = st.selectbox("Tipo de Servico", list(p.label for p in plugins.values()))
plugin = next(p for p in plugins.values() if p.label == servico_label)

with st.container(border=True):
    st.subheader(f"Configuracao de {servico_label}")
    inputs = plugin.render_fields()

# --- ITENS EXTRAS DA TABELA PRIVADA ---
with st.container(border=True):
    st.subheader("Itens Adicionais")
    conn = get_conn()
    df_precos = pd.read_sql("SELECT chave, nome, valor FROM precos WHERE usuario_id = %s", conn, params=(user_id,))
    
    opcoes = {f"{r['nome']} (R$ {r['valor']:.2f})": r for _, r in df_precos.iterrows()}
    selecionados = st.multiselect("Adicionar pecas avulsas", list(opcoes.keys()))
    
    extras_selecionados = []
    if selecionados:
        cols = st.columns(3)
        for i, sel in enumerate(selecionados):
            with cols[i % 3]:
                qtd = st.number_input(f"Qtd: {opcoes[sel]['nome']}", min_value=1, value=1, key=f"ex_{i}")
                extras_selecionados.append({"info": opcoes[sel], "qtd": qtd})

# --- PROCESSAMENTO E GERACAO ---
if st.button("FINALIZAR E GERAR PROPOSTA", use_container_width=True):
    # 1. Calculo base do plugin
    resultado = plugin.compute(conn, inputs)
    
    # 2. Soma itens extras
    for ex in extras_selecionados:
        sub_ex = ex['qtd'] * ex['info']['valor']
        resultado['items'].append({
            'desc': f"Adicional: {ex['info']['nome']}",
            'qty': ex['qtd'],
            'unit': ex['info']['valor'],
            'sub': sub_ex
        })
        resultado['subtotal'] += sub_ex

    # 3. Busca Texto de Entrega Personalizado
    with conn.cursor() as cur:
        cur.execute("SELECT texto_detalhado FROM modelos_texto WHERE usuario_id = %s AND servico_tipo = %s", 
                    (user_id, servico_label))
        modelo = cur.fetchone()
        texto_entrega = modelo[0] if modelo else "Instalacao realizada com materiais de alta qualidade."

    st.success(f"Orcamento calculado: R$ {resultado['subtotal']:.2f}")
    
    # --- RESULTADOS ---
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
            "servicos": [resultado],
            "total": resultado['subtotal'],
            "pagamento": config_data[3],
            "garantia": config_data[4],
            "validade_dias": config_data[5],
            "detalhamento_entrega": texto_entrega # Campo novo para o PDF
        }
        render_summary_pdf(pdf_io, pdf_payload)
        
        st.download_button(
            label="Baixar Proposta em PDF",
            data=pdf_io.getvalue(),
            file_name=f"Orcamento_{nome_cliente}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
        
        # Resumo WhatsApp
        resumo_zap = f"Ola {nome_cliente}! Segue a proposta para {servico_label}.\nValor total: R$ {resultado['subtotal']:.2f}"
        st.text_area("Texto para copiar e enviar no WhatsApp", resumo_zap, height=100)

    with aba_mat:
        materiais = build_materials_list(resultado)
        st.table(pd.DataFrame(materiais))
