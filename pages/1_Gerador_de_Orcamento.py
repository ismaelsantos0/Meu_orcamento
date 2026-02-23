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

# --- ESTILO VERO ---
st.markdown("""
<style>
    header {visibility: hidden;} footer {visibility: hidden;}
    [data-testid="stSidebar"] { display: none; }
    .stApp { background: radial-gradient(circle at 50% 50%, #101a26 0%, #080d12 100%); color: white; font-family: 'Poppins', sans-serif; }
    [data-testid="stVerticalBlockBorderWrapper"] { background: rgba(255,255,255,0.03) !important; border: 1px solid rgba(255,255,255,0.1) !important; border-radius: 20px !important; }
    .stButton > button { background-color: #ffffff !important; color: #080d12 !important; border-radius: 50px !important; font-weight: 800 !important; }
</style>
""", unsafe_allow_html=True)

if st.button("VOLTAR", key="b_gen"): 
    st.switch_page("app.py")

# Busca configurações da empresa
with conn.cursor() as cur:
    cur.execute("SELECT nome_empresa, whatsapp, logo, pagamento_padrao, garantia_padrao, validade_dias FROM config_empresa WHERE usuario_id = %s", (user_id,))
    cfg = cur.fetchone() or ("Vero", "", None, "A combinar", "90 dias", 7)

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

# --- FILTRO DE CATEGORIA ---
mapeamento = {"Concertina": "Concertinas", "Cerca": "Cercas", "Camera": "Cameras", "Motor": "Motores"}
categoria_atual = next((v for k, v in mapeamento.items() if k in servico_label), "Geral")

# --- ITENS ADICIONAIS (CORREÇÃO DO NAMEERROR) ---
extras_selecionados = [] # Inicializa a variável para evitar o NameError

with st.container(border=True):
    st.subheader(f"Itens Adicionais ({categoria_atual})")
    df_p = pd.read_sql("""
        SELECT chave, nome, valor FROM precos 
        WHERE usuario_id = %s AND (categoria = %s OR categoria = 'Geral')
    """, conn, params=(user_id, categoria_atual))
    
    if not df_p.empty:
        opcoes = {f"{r['nome']} (R$ {r['valor']:.2f})": r for _, r in df_p.iterrows()}
        selecionados = st.multiselect("Adicionar pecas avulsas", list(opcoes.keys()))
        
        if selecionados:
            cols = st.columns(3)
            for i, sel in enumerate(selecionados):
                with cols[i % 3]:
                    qtd = st.number_input(f"Qtd: {opcoes[sel]['nome']}", min_value=1, value=1, key=f"ex_{i}")
                    extras_selecionados.append({"info": opcoes[sel], "qtd": qtd})
    else:
        st.info("Nenhum item adicional nesta categoria.")

# --- FINALIZAÇÃO ---
if st.button("FINALIZAR", use_container_width=True, key="f_btn"):
    # 1. Calculo do Plugin
    res = plugin.compute(conn, inputs)
    
    # 2. Soma dos Extras (Agora a variável sempre existe)
    for ex in extras_selecionados:
        sub = ex['qtd'] * ex['info']['valor']
        res['items'].append({'desc': ex['info']['nome'], 'qty': ex['qtd'], 'unit': ex['info']['valor'], 'sub': sub})
        res['subtotal'] += sub
    
    # 3. Texto do PDF
    with conn.cursor() as cur:
        cur.execute("SELECT texto_detalhado FROM modelos_texto WHERE usuario_id = %s AND servico_tipo = %s", (user_id, categoria_atual))
        txt = cur.fetchone()
        res['entrega_detalhada'] = txt[0] if txt else "Instalacao padrao realizada pela equipe RR Smart Solucoes."

    st.success(f"Orcamento finalizado: R$ {res['subtotal']:.2f}")
    
    st.divider()
    aba_pdf, aba_mat = st.tabs(["PDF", "Materiais"])
    
    with aba_pdf:
        from core.pdf.summary import render_summary_pdf
        pdf_io = io.BytesIO()
        render_summary_pdf(pdf_io, {
            "logo_bytes": cfg[2], "empresa": cfg[0], "whatsapp": cfg[1], 
            "cliente": cliente, "servicos": [res], "total": res['subtotal'], 
            "pagamento": cfg[3], "garantia": cfg[4], "validade_dias": cfg[5],
            "detalhamento_entrega": res['entrega_detalhada']
        })
        st.download_button("Baixar Proposta", pdf_io.getvalue(), f"Orcamento_{cliente}.pdf", "application/pdf")
    
    with aba_mat:
        st.table(pd.DataFrame(build_materials_list(res)))
