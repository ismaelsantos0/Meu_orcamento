import streamlit as st
import pandas as pd
from core.db import get_conn
from core.style import apply_vero_style
from core.materials import build_materials_list
import services.registry as registry

st.set_page_config(page_title="Vero | Gerador", layout="wide")
apply_vero_style()

# --- TRAVA DE SEGURANÇA (CORREÇÃO DO ERRO) ---
if 'user_id' not in st.session_state:
    st.warning("Sessão expirada. Por favor, faça login novamente.")
    if st.button("IR PARA LOGIN"):
        st.switch_page("app.py")
    st.stop()

user_id = st.session_state.user_id
conn = get_conn()

if st.button("← VOLTAR"): 
    st.switch_page("app.py")

st.markdown("# Novo Orçamento")

with st.container(border=True):
    col1, col2 = st.columns(2, gap="medium")
    cliente = col1.text_input("Nome do Cliente", placeholder="Ex: João Silva")
    contato = col2.text_input("WhatsApp Cliente", placeholder="95984...")

plugins = registry.get_plugins()
servico_label = st.selectbox("Tipo de Serviço", list(p.label for p in plugins.values()))
plugin = next(p for p in plugins.values() if p.label == servico_label)

with st.container(border=True):
    inputs = plugin.render_fields()

# Identificação da Categoria
mapeamento = {"Camera": "CFTV", "Motor": "Motor de Portão", "Cerca": "Cerca/Concertina", "Concertina": "Cerca/Concertina"}
categoria_atual = next((v for k, v in mapeamento.items() if k in servico_label), "Geral")

# Itens Adicionais (Tabela da RR Smart Soluções)
df_p = pd.read_sql("SELECT chave, nome, valor FROM precos WHERE usuario_id = %s AND (categoria = %s OR categoria = 'Geral')", conn, params=(user_id, categoria_atual))
extras_list = []
if not df_p.empty:
    with st.container(border=True):
        st.subheader(f"Adicionais: {categoria_atual}")
        opcoes = {f"{r['nome']} (R$ {r['valor']:.2f})": r for _, r in df_p.iterrows()}
        selecionados = st.multiselect("Selecione itens extras", list(opcoes.keys()))
        if selecionados:
            cols = st.columns(3)
            for i, sel in enumerate(selecionados):
                with cols[i % 3]:
                    q = st.number_input(f"Qtd: {opcoes[sel]['nome']}", min_value=1, key=f"q_{i}")
                    extras_list.append({"info": opcoes[sel], "qtd": q})

if st.button("GERAR APRESENTAÇÃO PROFISSIONAL", use_container_width=True):
    res = plugin.compute(conn, inputs)
    for ex in extras_list:
        sub = ex['qtd'] * ex['info']['valor']
        res['items'].append({'desc': ex['info']['nome'], 'qty': ex['qtd'], 'unit': ex['info']['valor'], 'sub': sub})
        res['subtotal'] += sub
    
    with conn.cursor() as cur:
        cur.execute("SELECT texto_detalhado FROM modelos_texto WHERE usuario_id = %s AND servico_tipo = %s", (user_id, categoria_atual))
        txt = cur.fetchone()
        texto_final = txt[0] if (txt and txt[0]) else "Serviço de alta qualidade realizado pela RR Smart Soluções."
        res['summary_client'] = texto_final

    with conn.cursor() as cur:
        cur.execute("SELECT nome_empresa, whatsapp, logo, pagamento_padrao, garantia_padrao, validade_dias FROM config_empresa WHERE usuario_id = %s", (user_id,))
        cfg = cur.fetchone() or ("RR Smart Soluções", "95984187832", None, "A combinar", "90 dias", 7)

    st.session_state.dados_orcamento = {
        "cliente": cliente,
        "whatsapp_cliente": contato,
        "servico": servico_label,
        "total": res['subtotal'],
        "materiais": build_materials_list(res),
        "texto_beneficios": texto_final,
        "config_empresa": cfg,
        "payload_pdf": {
            "logo_bytes": cfg[2], "empresa": cfg[0], "whatsapp": cfg[1], "cliente": cliente, 
            "servicos": [res], "total": res['subtotal'], "pagamento": cfg[3], "garantia": cfg[4], "validade_dias": cfg[5]
        }
    }
    st.switch_page("pages/Resumo_do_Orcamento.py")
