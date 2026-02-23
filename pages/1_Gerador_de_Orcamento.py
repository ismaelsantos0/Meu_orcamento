import streamlit as st
import io
import pandas as pd
from datetime import datetime
from core.db import get_conn
from core.materials import build_materials_list
import services.registry as registry

# --- SEGURANÇA (TRAVA DE ACESSO) ---
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.error("Acesso negado! Por favor, faça login na página inicial.")
    st.stop()

st.set_page_config(page_title="Vero | Gerador", layout="wide", initial_sidebar_state="collapsed")
user_id = st.session_state.user_id
conn = get_conn()

# --- ESTILO VERO PREMIUM (SEM EMOJIS) ---
st.markdown("""
<style>
    header {visibility: hidden;} footer {visibility: hidden;}
    [data-testid="stSidebar"] { display: none; }
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;800&display=swap');
    
    .stApp {
        background: radial-gradient(circle at 50% 50%, #101a26 0%, #080d12 100%);
        font-family: 'Poppins', sans-serif;
        color: white;
    }
    
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

# --- NAVEGAÇÃO ---
if st.button("VOLTAR AO PAINEL", key="back_gen"):
    st.switch_page("app.py")

# --- BUSCA CONFIGURAÇÕES DA EMPRESA (RR SMART SOLUÇÕES) ---
with conn.cursor() as cur:
    cur.execute("""
        SELECT nome_empresa, whatsapp, logo, pagamento_padrao, garantia_padrao, validade_dias 
        FROM config_empresa WHERE usuario_id = %s
    """, (user_id,))
    cfg = cur.fetchone() or ("Vero", "", None, "A combinar", "90 dias", 7)

st.title("Gerador de Orcamentos")

# --- FORMULÁRIO DO CLIENTE ---
with st.container(border=True):
    col_c1, col_c2 = st.columns(2)
    nome_cliente = col_c1.text_input("Cliente", placeholder="Nome do cliente")
    zap_cliente = col_c2.text_input("Contato", placeholder="WhatsApp")

# --- SELEÇÃO DE SERVIÇO PRINCIPAL ---
plugins = registry.get_plugins()
servico_label = st.selectbox("Tipo de Servico", list(p.label for p in plugins.values()))
plugin = next(p for p in plugins.values() if p.label == servico_label)

with st.container(border=True):
    st.subheader(f"Configuracao de {servico_label}")
    inputs = plugin.render_fields()

# --- FILTRO INTELIGENTE DE MATERIAIS ADICIONAIS ---
# Mapeia o serviço selecionado para a categoria da tabela de preços
mapeamento = {
    "Concertina": "Concertinas",
    "Cerca": "Cercas",
    "Camera": "Cameras",
    "Motor": "Motores"
}
categoria_atual = "Geral"
for chave_map, valor_map in mapeamento.items():
    if chave_map in servico_label:
        categoria_atual = valor_map
        break

with st.container(border=True):
    st.subheader(f"Itens Adicionais para {categoria_atual}")
    
    # Busca itens da categoria específica OU itens Gerais da RR Smart Soluções
    df_precos = pd.read_sql("""
        SELECT chave, nome, valor FROM precos 
        WHERE usuario_id = %s AND (categoria = %s OR categoria = 'Geral')
    """, conn, params=(user_id, categoria_atual))
    
    if not df_precos.empty:
        opcoes = {f"{r['nome']} (R$ {r['valor']:.2f})": r for _, r in df_precos.iterrows()}
        selecionados = st.multiselect("Selecione pecas avulsas", list(opcoes.keys()))
        
        extras_selecionados = []
        if selecionados:
            cols = st.columns(3)
            for i, sel in enumerate(selecionados):
                with cols[i % 3]:
                    qtd = st.number_input(f"Qtd: {opcoes[sel]['nome']}", min_value=1, value=1, key=f"ex_{i}")
                    extras_selecionados.append({"info": opcoes[sel], "qtd": qtd})
    else:
        st.info(f"Nenhum item adicional cadastrado para {categoria_atual}.")

# --- PROCESSAMENTO FINAL ---
if st.button("FINALIZAR E GERAR PROPOSTA", use_container_width=True, key="btn_finalizar"):
    # 1. Cálculo base via Plugin
    resultado = plugin.compute(conn, inputs)
    
    # 2. Soma itens extras selecionados
    for ex in extras_selecionados:
        sub_ex = ex['qtd'] * ex['info']['valor']
        resultado['items'].append({
            'desc': f"Adicional: {ex['info']['nome']}",
            'qty': ex['qtd'],
            'unit': ex['info']['valor'],
            'sub': sub_ex
        })
        resultado['subtotal'] += sub_ex

    # 3. Busca Texto de Entrega Personalizado (Modelos de Texto)
    with conn.cursor() as cur:
        cur.execute("""
            SELECT texto_detalhado FROM modelos_texto 
            WHERE usuario_id = %s AND servico_tipo = %s
        """, (user_id, categoria_atual))
        modelo_texto = cur.fetchone()
        texto_entrega = modelo_texto[0] if modelo_texto else "Instalacao realizada com materiais de alta qualidade."

    st.success(f"Orcamento calculado: R$ {resultado['subtotal']:.2f}")
    
    # --- RESULTADOS: PDF E MATERIAIS ---
    st.divider()
    aba_pdf, aba_mat = st.tabs(["Proposta em PDF", "Lista de Materiais"])

    with aba_pdf:
        from core.pdf.summary import render_summary_pdf
        pdf_io = io.BytesIO()
        pdf_payload = {
            "logo_bytes": cfg[2],
            "empresa": cfg[0],
            "whatsapp": cfg[1],
            "cliente": nome_cliente or "Cliente",
            "data_str": datetime.now().strftime("%d/%m/%Y"),
            "servicos": [resultado],
            "total": resultado['subtotal'],
            "pagamento": cfg[3],
            "garantia": cfg[4],
            "validade_dias": cfg[5],
            "detalhamento_entrega": texto_entrega
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
        # Exibe a lista técnica para a equipe da RR Smart Soluções
        lista_materiais = build_materials_list(resultado)
        st.table(pd.DataFrame(lista_materiais))
