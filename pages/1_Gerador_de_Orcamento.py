import streamlit as st
import pandas as pd
from core.db import get_conn
from core.style import apply_vero_style
from core.materials import build_materials_list
import services.registry as registry

st.set_page_config(page_title="Vero | Gerador", layout="wide")
apply_vero_style()
user_id = st.session_state.user_id
conn = get_conn()

if st.button("← CANCELAR"): st.switch_page("app.py")

st.title("Novo Orçamento")

with st.container(border=True):
    col1, col2 = st.columns(2)
    cliente = col1.text_input("Nome do Cliente")
    contato = col2.text_input("WhatsApp (ex: 95984...)")

plugins = registry.get_plugins()
servico_label = st.selectbox("Serviço Principal", list(p.label for p in plugins.values()))
plugin = next(p for p in plugins.values() if p.label == servico_label)

with st.container(border=True):
    inputs = plugin.render_fields()

# Mapeamento para buscar texto e materiais
mapeamento = {"Camera": "CFTV", "Motor": "Motor de Portão", "Cerca": "Cerca/Concertina", "Concertina": "Cerca/Concertina"}
categoria_atual = next((v for k, v in mapeamento.items() if k in servico_label), "Geral")

if st.button("GERAR APRESENTAÇÃO PROFISSIONAL", use_container_width=True):
    res = plugin.compute(conn, inputs)
    
    with conn.cursor() as cur:
        cur.execute("SELECT texto_detalhado FROM modelos_texto WHERE usuario_id = %s AND servico_tipo = %s", (user_id, categoria_atual))
        txt = cur.fetchone()
        texto_final = txt[0] if (txt and txt[0]) else "Instalação padrão RR Smart Soluções."
        res['summary_client'] = texto_final

    # Configurações da empresa para o PDF
    with conn.cursor() as cur:
        cur.execute("SELECT nome_empresa, whatsapp, logo, pagamento_padrao, garantia_padrao, validade_dias FROM config_empresa WHERE usuario_id = %s", (user_id,))
        cfg = cur.fetchone() or ("RR Smart Soluções", "", None, "A combinar", "90 dias", 7)

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
