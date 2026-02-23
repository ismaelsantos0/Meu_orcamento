import streamlit as st
import io
import urllib.parse
from core.style import apply_vero_style

if 'dados_orcamento' not in st.session_state: st.switch_page("pages/1_Gerador_de_Orcamento.py")

st.set_page_config(page_title="Vero | Resumo", layout="wide")
apply_vero_style()
d = st.session_state.dados_orcamento
cfg = d['config_empresa']

st.markdown(f"# Orçamento: {d['cliente']}")

c1, c2, c3 = st.columns(3, gap="large")

with c1:
    with st.container(border=True):
        st.write("📄 PROPOSTA PDF")
        st.markdown(f"## R$ {d['total']:.2f}")
        from core.pdf.summary import render_summary_pdf
        pdf_io = io.BytesIO()
        render_summary_pdf(pdf_io, d['payload_pdf'])
        st.download_button("BAIXAR PDF", pdf_io.getvalue(), f"Orcamento_{d['cliente']}.pdf", use_container_width=True)

with c2:
    with st.container(border=True):
        st.write("📱 WHATSAPP")
        msg = f"*PROPOSTA: {cfg[0]}*\n\n{d['texto_beneficios']}\n\n*Total: R$ {d['total']:.2f}*"
        st.text_area("Mensagem:", msg, height=150, label_visibility="collapsed")
        wp_url = f"https://wa.me/{d['whatsapp_cliente']}?text={urllib.parse.quote(msg)}"
        st.markdown(f'<a href="{wp_url}" target="_blank"><button style="width:100%; height:50px; border-radius:18px; background:#25d366; color:white; border:none; font-weight:700;">ENVIAR WHATSAPP</button></a>', unsafe_allow_html=True)

with c3:
    with st.container(border=True):
        st.write("📦 FORNECEDOR")
        lista = "\n".join([f"• {m['qty']}x {m['desc']}" for m in d['materiais']])
        st.text_area("Materiais:", lista, height=150, label_visibility="collapsed")
        st.download_button("SALVAR LISTA .TXT", lista, "pedido.txt", use_container_width=True)
