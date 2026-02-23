import streamlit as st
import io
import urllib.parse
from core.style import apply_vero_style
from core.scripts import apply_vero_js

if 'dados_orcamento' not in st.session_state:
    st.switch_page("pages/1_Gerador_de_Orcamento.py")

st.set_page_config(page_title="Vero | Resumo", layout="wide")
apply_vero_style()
apply_vero_js()

d = st.session_state.dados_orcamento
cfg = d['config_empresa']

st.markdown(f"## Proposta para {d['cliente']}")

c1, c2, c3 = st.columns(3, gap="large")

with c1:
    with st.container(border=True):
        st.markdown("### 📄 PDF Profissional")
        st.markdown(f"<h2 style='color:#3b82f6;'>R$ {d['total']:.2f}</h2>", unsafe_allow_html=True)
        from core.pdf.summary import render_summary_pdf
        pdf_io = io.BytesIO()
        render_summary_pdf(pdf_io, d['payload_pdf'])
        st.download_button("📥 BAIXAR PROPOSTA", pdf_io.getvalue(), f"Orcamento_{d['cliente']}.pdf", use_container_width=True)

with c2:
    with st.container(border=True):
        st.markdown("### 📱 WhatsApp Cliente")
        msg = f"*PROPOSTA: {cfg[0]}*\n\n{d['texto_beneficios']}\n\n*Total: R$ {d['total']:.2f}*"
        st.text_area("Mensagem:", msg, height=150, label_visibility="collapsed")
        wp_url = f"https://wa.me/{d['whatsapp_cliente']}?text={urllib.parse.quote(msg)}"
        st.markdown(f'<a href="{wp_url}" target="_blank"><button style="width:100%; height:50px; border-radius:20px; background:#25d366; color:white; border:none; font-weight:800; cursor:pointer;">ENVIAR AGORA</button></a>', unsafe_allow_html=True)

with c3:
    with st.container(border=True):
        st.markdown("### 📦 Fornecedor")
        lista = "\n".join([f"• {m['qty']}x {m['desc']}" for m in d['materiais']])
        st.text_area("Lista técnica:", lista, height=150, label_visibility="collapsed")
        st.download_button("💾 SALVAR LISTA TXT", lista, "materiais.txt", use_container_width=True)
