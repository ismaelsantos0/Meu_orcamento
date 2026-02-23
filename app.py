import streamlit as st
import pandas as pd
import io
import urllib.parse
from datetime import datetime
from core.db import get_conn
from core.style import apply_vero_style
from core.materials import build_materials_list
import services.registry as registry

# Configurações de Design e Identidade RR Smart Soluções
st.set_page_config(page_title="Vero | RR Smart Soluções", layout="wide", initial_sidebar_state="collapsed")
apply_vero_style()

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# Estado para controlar se estamos editando ou vendo o resultado
if 'view_mode' not in st.session_state:
    st.session_state.view_mode = "edit"

# --- 1. TELA DE LOGIN ---
if not st.session_state.logged_in:
    # ... (Mantenha seu código de login aqui)
    st.stop()

# --- 2. DADOS DO USUÁRIO ---
user_id = st.session_state.user_id
conn = get_conn()

with conn.cursor() as cur:
    cur.execute("SELECT nome_empresa, whatsapp, logo, pagamento_padrao, garantia_padrao, validade_dias FROM config_empresa WHERE usuario_id = %s", (user_id,))
    cfg = cur.fetchone() or ("RR Smart Soluções", "95984187832", None, "A combinar", "90 dias", 7)

# --- 3. MENU SUPERIOR ---
tab_inicio, tab_gerador, tab_precos, tab_modelos, tab_config = st.tabs([
    "🏠 Início", "📑 Gerador", "💰 Tabela de Preços", "✍️ Modelos", "⚙️ Configurações"
])

# --- ABA: GERADOR (AQUI ESTÁ A CORREÇÃO) ---
with tab_gerador:
    # Se estivermos no modo de resultado, mostra os Cards de entrega
    if st.session_state.view_mode == "result" and 'dados_orcamento' in st.session_state:
        d = st.session_state.dados_orcamento
        
        st.markdown(f"## ✅ Orçamento Pronto: {d['cliente']}")
        
        if st.button("⬅️ CRIAR NOVO ORÇAMENTO"):
            st.session_state.view_mode = "edit"
            st.rerun()

        col1, col2, col3 = st.columns(3, gap="large")

        with col1:
            with st.container(border=True):
                st.markdown("### 📄 Proposta PDF")
                st.markdown(f"<h2 style='color:#3b82f6;'>R$ {d['total']:.2f}</h2>", unsafe_allow_html=True)
                from core.pdf.summary import render_summary_pdf
                pdf_io = io.BytesIO()
                render_summary_pdf(pdf_io, d['payload_pdf'])
                st.download_button("📥 BAIXAR PDF", pdf_io.getvalue(), f"Orcamento_{d['cliente']}.pdf", use_container_width=True)

        with col2:
            with st.container(border=True):
                st.markdown("### 📱 WhatsApp")
                msg = f"*PROPOSTA: {cfg[0]}*\n\n{d['texto_beneficios']}\n\n*Total: R$ {d['total']:.2f}*"
                st.text_area("Copiar mensagem:", msg, height=150)
                wp_url = f"https://wa.me/{d['whatsapp_cliente']}?text={urllib.parse.quote(msg)}"
                st.markdown(f'<a href="{wp_url}" target="_blank"><button style="width:100%; height:50px; border-radius:18px; background:#25d366; color:white; border:none; font-weight:700;">ENVIAR WHATSAPP</button></a>', unsafe_allow_html=True)

        with col3:
            with st.container(border=True):
                st.markdown("### 📦 Materiais")
                lista = "\n".join([f"• {m['qty']}x {m['desc']}" for m in d['materiais']])
                st.text_area("Lista técnica:", lista, height=150)
                st.download_button("💾 SALVAR LISTA .TXT", lista, "pedido.txt", use_container_width=True)

    else:
        # MODO DE EDIÇÃO (O que você vê agora nas imagens)
        st.header("Gerador de Orçamentos")
        with st.container(border=True):
            # ... (Mantenha os campos de Cliente, WhatsApp, etc)
            
            # AO CLICAR NO BOTÃO:
            if st.button("FINALIZAR E GERAR", use_container_width=True):
                # 1. Faz os cálculos (como você já tem no código)
                res = plugin.compute(conn, inputs)
                # ... (Lógica de somar os extras e buscar o texto de benefícios)
                
                # 2. Salva o Payload
                st.session_state.dados_orcamento = {
                    "cliente": cliente, "whatsapp_cliente": whatsapp_cli,
                    "total": res['subtotal'], "materiais": build_materials_list(res),
                    "texto_beneficios": texto_final,
                    "payload_pdf": {
                         "logo_bytes": cfg[2], "empresa": cfg[0], "whatsapp": cfg[1], "cliente": cliente,
                         "servicos": [res], "total": res['subtotal'], "pagamento": cfg[3], "garantia": cfg[4], "validade_dias": cfg[5]
                    }
                }
                # 3. MUDA O MODO DE VISÃO
                st.session_state.view_mode = "result"
                st.rerun()

# --- ABA: PREÇOS, MODELOS E CONFIG (Mantenha como estão) ---
