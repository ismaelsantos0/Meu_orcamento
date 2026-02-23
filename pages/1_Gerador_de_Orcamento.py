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

# --- ESTILO VERO (SEM EMOJIS) ---
st.markdown("""
<style>
    header {visibility: hidden;} footer {visibility: hidden;}
    [data-testid="stSidebar"] { display: none; }
    .stApp { background: radial-gradient(circle at 50% 50%, #101a26 0%, #080d12 100%); color: white; font-family: 'Poppins', sans-serif; }
    [data-testid="stVerticalBlockBorderWrapper"] { background: rgba(255,255,255,0.03) !important; border: 1px solid rgba(255,255,255,0.1) !important; border-radius: 20px !important; }
    .stButton > button { background-color: #ffffff !important; color: #080d12 !important; border-radius: 50px !important; font-weight: 800 !important; }
</style>
""", unsafe_allow_html=True)

if st.button("VOLTAR", key="back_gen"): 
    st.switch_page("app.py")

# Busca configurações da empresa
with conn.cursor() as cur:
    cur.execute("SELECT nome_empresa, whatsapp, logo, pagamento_padrao, garantia_padrao, validade_dias FROM config_empresa WHERE usuario_id = %s", (user_id,))
    cfg = cur.fetchone() or ("RR Smart Soluções", "", None, "A combinar", "90 dias", 7)

st.title("Gerador de Orcamentos")

# --- DADOS DO CLIENTE ---
with st.container(border=True):
    col1, col2 = st.columns(2)
    cliente = col1.text_input("Cliente")
    contato = col2.text_input("Contato")

# --- PLUGIN DE SERVIÇO ---
plugins = registry.get_plugins()
servico_label = st.selectbox("Tipo de Servico", list(p.label for p in plugins.values()))
plugin = next(p for p in plugins.values() if p.label == servico_label)

with st.container(border=True):
    inputs = plugin.render_fields()

# --- MAPEAMENTO DE CATEGORIAS (SINCRONIZADO COM SUA TABELA) ---
# O sistema identifica qual categoria buscar no banco baseado no plugin escolhido
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

# --- ITENS ADICIONAIS FILTRADOS ---
extras_selecionados = []

with st.container(border=True):
    st.subheader(f"Itens Adicionais para {categoria_atual}")
    
    # Busca apenas itens que pertencem ao serviço selecionado ou são de uso 'Geral'
    df_p = pd.read_sql("""
        SELECT chave, nome, valor FROM precos 
        WHERE usuario_id = %s AND (categoria = %s OR categoria = 'Geral')
    """, conn, params=(user_id, categoria_atual))
    
    if not df_p.empty:
        opcoes = {f"{r['nome']} (R$ {r['valor']:.2f})": r for _, r in df_p.iterrows()}
        selecionados = st.multiselect("Adicionar pecas e acessorios", list(opcoes.keys()))
        
        if selecionados:
            cols = st.columns(3)
            for i, sel in enumerate(selecionados):
                with cols[i % 3]:
                    qtd = st.number_input(f"Qtd: {opcoes[sel]['nome']}", min_value=1, value=1, key=f"ex_{i}")
                    extras_selecionados.append({"info": opcoes[sel], "qtd": qtd})
    else:
        st.info(f"Nenhum item adicional cadastrado na categoria {categoria_atual}.")

# --- FINALIZAÇÃO E PDF ---
if st.button("FINALIZAR", use_container_width=True, key="f_btn"):
    res = plugin.compute(conn, inputs)
    
    # Adiciona os itens extras selecionados ao cálculo
    for ex in extras_selecionados:
        sub = ex['qtd'] * ex['info']['valor']
        res['items'].append({'desc': ex['info']['nome'], 'qty': ex['qtd'], 'unit': ex['info']['valor'], 'sub': sub})
        res['subtotal'] += sub
    
    # Busca o texto detalhado para o PDF
    with conn.cursor() as cur:
        cur.execute("SELECT texto_detalhado FROM modelos_texto WHERE usuario_id = %s AND servico_tipo = %s", (user_id, categoria_atual))
        txt = cur.fetchone()
        res['entrega_detalhada'] = txt[0] if txt else "Instalacao padrao realizada pela equipe RR Smart Solucoes."

    st.success(f"Orcamento finalizado: R$ {res['subtotal']:.2f}")
    
    st.divider()
    aba_pdf, aba_mat = st.tabs(["Proposta PDF", "Lista Tecnica"])
    
    with aba_pdf:
        from core.pdf.summary import render_summary_pdf
        pdf_io = io.BytesIO()
        render_summary_pdf(pdf_io, {
            "logo_bytes": cfg[2], "empresa": cfg[0], "whatsapp": cfg[1], 
            "cliente": cliente, "servicos": [res], "total": res['subtotal'], 
            "pagamento": cfg[3], "garantia": cfg[4], "validade_dias": cfg[5],
            "detalhamento_entrega": res['entrega_detalhada']
        })
        st.download_button("Baixar Proposta PDF", pdf_io.getvalue(), f"Orcamento_{cliente}.pdf", "application/pdf")
    
    with aba_mat:
        # Exibe a lista de materiais para conferência de estoque da RR Smart Soluções
        st.table(pd.DataFrame(build_materials_list(res)))
