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

if st.button("VOLTAR", key="b_gen"): st.switch_page("app.py")

# Configurações da Empresa
with conn.cursor() as cur:
    cur.execute("SELECT nome_empresa, whatsapp, logo, pagamento_padrao, garantia_padrao, validade_dias FROM config_empresa WHERE usuario_id = %s", (user_id,))
    cfg = cur.fetchone() or ("RR Smart Soluções", "", None, "A combinar", "90 dias", 7)

st.title("Gerador de Orçamentos")

with st.container(border=True):
    col1, col2 = st.columns(2)
    cliente = col1.text_input("Cliente")
    contato = col2.text_input("WhatsApp Cliente")

plugins = registry.get_plugins()
servico_label = st.selectbox("Tipo de Serviço", list(p.label for p in plugins.values()))
plugin = next(p for p in plugins.values() if p.label == servico_label)

with st.container(border=True):
    inputs = plugin.render_fields()

# Identificação da Categoria para Filtro e Texto
mapeamento = {"Camera": "CFTV", "Motor": "Motor de Portão", "Cerca": "Cerca/Concertina", "Concertina": "Cerca/Concertina"}
categoria_atual = next((v for k, v in mapeamento.items() if k in servico_label), "Geral")

# Itens Adicionais
df_p = pd.read_sql("SELECT chave, nome, valor FROM precos WHERE usuario_id = %s AND (categoria = %s OR categoria = 'Geral')", conn, params=(user_id, categoria_atual))
extras_list = []
if not df_p.empty:
    with st.container(border=True):
        st.subheader(f"Adicionais: {categoria_atual}")
        opcoes = {f"{r['nome']} (R$ {r['valor']:.2f})": r for _, r in df_p.iterrows()}
        selecionados = st.multiselect("Adicionar itens", list(opcoes.keys()))
        if selecionados:
            cols = st.columns(3)
            for i, sel in enumerate(selecionados):
                with cols[i % 3]:
                    q = st.number_input(f"Qtd: {opcoes[sel]['nome']}", min_value=1, key=f"q_{i}")
                    extras_list.append({"info": opcoes[sel], "qtd": q})

if st.button("FINALIZAR E GERAR PDF", use_container_width=True, key="f_pdf"):
    res = plugin.compute(conn, inputs)
    for ex in extras_list:
        sub = ex['qtd'] * ex['info']['valor']
        res['items'].append({'desc': ex['info']['nome'], 'qty': ex['qtd'], 'unit': ex['info']['valor'], 'sub': sub})
        res['subtotal'] += sub
    
    # BUSCA TEXTO PERSONALIZADO PARA O PDF (CHAVE summary_client)
    with conn.cursor() as cur:
        cur.execute("SELECT texto_detalhado FROM modelos_texto WHERE usuario_id = %s AND servico_tipo = %s", (user_id, categoria_atual))
        txt = cur.fetchone()
        # Injeção direta para o core/pdf ler
        res['summary_client'] = txt[0] if (txt and txt[0]) else "Instalação profissional padrão."

    from core.pdf.summary import render_summary_pdf
    pdf_io = io.BytesIO()
    payload = {
        "logo_bytes": cfg[2], "empresa": cfg[0], "whatsapp": cfg[1], "cliente": cliente, 
        "data_str": datetime.now().strftime("%d/%m/%Y"), "servicos": [res], 
        "total": res['subtotal'], "pagamento": cfg[3], "garantia": cfg[4], "validade_dias": cfg[5]
    }
    render_summary_pdf(pdf_io, payload)
    
    st.success(f"Total: R$ {res['subtotal']:.2f}")
    st.download_button("📥 BAIXAR PROPOSTA", pdf_io.getvalue(), f"Orcamento_{cliente}.pdf", "application/pdf")
