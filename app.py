import streamlit as st
import pandas as pd
import io
import urllib.parse
from core.db import get_conn
from core.style import apply_vero_style
from core.materials import build_materials_list
import services.registry as registry

# Configuração Base
st.set_page_config(page_title="Vero | RR Smart", layout="wide")
apply_vero_style()

if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# CONTROLE DE VISUALIZAÇÃO DO ORÇAMENTO
if 'orcamento_pronto' not in st.session_state:
    st.session_state.orcamento_pronto = False

# --- LOGIN ---
if not st.session_state.logged_in:
    # ... (Seu código de login funcional)
    st.stop()

# --- DADOS ---
user_id = st.session_state.user_id
conn = get_conn()
with conn.cursor() as cur:
    cur.execute("SELECT nome_empresa, whatsapp, logo, pagamento_padrao, garantia_padrao, validade_dias FROM config_empresa WHERE usuario_id = %s", (user_id,))
    cfg = cur.fetchone() or ("RR Smart Soluções", "95984187832", None, "A combinar", "90 dias", 7)

# --- MENU SUPERIOR (TABS) ---
tab_gerador, tab_precos, tab_modelos, tab_config = st.tabs([
    "📄 Gerador de Orçamento", "💰 Tabela de Preços", "✍️ Modelos de Texto", "⚙️ Configurações"
])

# --- FUNCIONALIDADE: GERADOR ---
with tab_gerador:
    # SE O ORÇAMENTO JÁ FOI GERADO, MOSTRA A TELA DE RESULTADO
    if st.session_state.orcamento_pronto:
        d = st.session_state.dados_finais
        st.markdown(f"## ✅ Orçamento Gerado para {d['cliente']}")
        
        if st.button("⬅️ CRIAR NOVO ORÇAMENTO"):
            st.session_state.orcamento_pronto = False
            st.rerun()

        col_res1, col_res2, col_res3 = st.columns(3)

        with col_res1:
            with st.container(border=True):
                st.subheader("📄 Proposta PDF")
                st.write(f"Valor Total: **R$ {d['total']:.2f}**")
                from core.pdf.summary import render_summary_pdf
                pdf_io = io.BytesIO()
                render_summary_pdf(pdf_io, d['payload_pdf'])
                st.download_button("📥 BAIXAR PDF", pdf_io.getvalue(), f"Orcamento_{d['cliente']}.pdf", use_container_width=True)

        with col_res2:
            with st.container(border=True):
                st.subheader("📱 WhatsApp")
                msg_zap = f"*PROPOSTA: {cfg[0]}*\n\n{d['texto_beneficios']}\n\n*Total: R$ {d['total']:.2f}*"
                st.text_area("Mensagem:", msg_zap, height=150)
                url_zap = f"https://wa.me/{d['whatsapp_cliente']}?text={urllib.parse.quote(msg_zap)}"
                st.markdown(f'<a href="{url_zap}" target="_blank"><button style="width:100%; height:45px; border-radius:10px; background:#25d366; color:white; border:none; font-weight:700;">ENVIAR WHATSAPP</button></a>', unsafe_allow_html=True)

        with col_res3:
            with st.container(border=True):
                st.subheader("📦 Materiais")
                txt_materiais = "\n".join([f"• {m['qty']}x {m['desc']}" for m in d['materiais']])
                st.text_area("Lista técnica:", txt_materiais, height=150)

    else:
        # TELA DE EDIÇÃO (FORMULÁRIO)
        st.header("Gerador de Orçamentos")
        with st.container(border=True):
            c1, c2 = st.columns(2)
            cliente = c1.text_input("Nome do Cliente")
            zap_cli = c2.text_input("WhatsApp do Cliente")
            
            plugins = registry.get_plugins()
            servico = st.selectbox("Selecione o Serviço", list(plugins.keys()))
            plugin = plugins[servico]
            inputs = plugin.render_fields()
            
            if st.button("CALCULAR E FINALIZAR", use_container_width=True):
                # 1. Realiza os cálculos
                res = plugin.compute(conn, inputs)
                
                # 2. Busca texto de benefícios para RR Smart Soluções
                with conn.cursor() as cur:
                    cur.execute("SELECT texto_detalhado FROM modelos_texto WHERE usuario_id = %s", (user_id,))
                    t_row = cur.fetchone()
                
                # 3. Salva os dados na sessão
                st.session_state.dados_finais = {
                    "cliente": cliente, "whatsapp_cliente": zap_cli, "total": res['subtotal'],
                    "materiais": build_materials_list(res), "texto_beneficios": t_row[0] if t_row else "",
                    "payload_pdf": {
                        "logo_bytes": cfg[2], "empresa": cfg[0], "whatsapp": cfg[1], "cliente": cliente,
                        "servicos": [res], "total": res['subtotal'], "pagamento": cfg[3], "garantia": cfg[4], "validade_dias": cfg[5]
                    }
                }
                st.session_state.orcamento_pronto = True
                st.rerun()

# --- DEMAIS ABAS (PREÇOS / CONFIG) ---
# ... (Mantenha o código que já funciona para elas)
