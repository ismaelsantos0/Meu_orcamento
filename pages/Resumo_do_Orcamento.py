import streamlit as st
import io
import urllib.parse
from datetime import datetime

# --- SEGURANÇA ---
if 'dados_orcamento' not in st.session_state:
    st.switch_page("pages/1_Gerador_de_Orcamento.py")

d = st.session_state.dados_orcamento
cfg = d['config_empresa']

st.set_page_config(page_title="Vero | Resumo", layout="wide", initial_sidebar_state="collapsed")

# --- CSS PREMIUM ---
st.markdown("""
<style>
    header {visibility: hidden;} footer {visibility: hidden;}
    [data-testid="stSidebar"] { display: none; }
    .stApp { background: #080d12; color: white; font-family: 'Poppins', sans-serif; }
    .card {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 24px;
        padding: 30px;
        height: 100%;
        transition: 0.3s;
    }
    .card:hover { border-color: #3b82f6; background: rgba(59, 130, 246, 0.02); }
    .stat-val { font-size: 36px; font-weight: 800; color: #3b82f6; margin-bottom: 20px; }
    .stButton > button { border-radius: 50px !important; font-weight: 700 !important; height: 45px; }
</style>
""", unsafe_allow_html=True)

if st.button("← NOVO ORÇAMENTO", key="btn_new"):
    st.switch_page("pages/1_Gerador_de_Orcamento.py")

st.markdown(f"# Resumo da Proposta")
st.markdown(f"### Cliente: **{d['cliente']}**")

col1, col2, col3 = st.columns(3)

# --- CARD 1: PDF PARA O CLIENTE ---
with col1:
    st.markdown("<div class='card'><h3>📄 Proposta PDF</h3>", unsafe_allow_html=True)
    st.markdown(f"<p class='stat-val'>R$ {d['total']:.2f}</p>", unsafe_allow_html=True)
    
    from core.pdf.summary import render_summary_pdf
    pdf_io = io.BytesIO()
    render_summary_pdf(pdf_io, d['payload_pdf'])
    
    st.download_button(
        label="📥 BAIXAR PDF PROFISSIONAL",
        data=pdf_io.getvalue(),
        file_name=f"Orcamento_{d['cliente']}.pdf",
        mime="application/pdf",
        use_container_width=True
    )
    st.markdown("</div>", unsafe_allow_html=True)

# --- CARD 2: WHATSAPP DO CLIENTE ---
with col2:
    st.markdown("<div class='card'><h3>📱 Enviar p/ WhatsApp</h3>", unsafe_allow_html=True)
    
    msg_cliente = f"*PROPOSTA: {cfg[0]}*\n\n"
    msg_cliente += f"Olá {d['cliente']}! Segue a proposta para o serviço de *{d['servico']}*:\n\n"
    msg_cliente += f"{d['texto_beneficios']}\n\n"
    msg_cliente += f"*Valor Total: R$ {d['total']:.2f}*\n"
    msg_cliente += f"Pagamento: {cfg[3]}\n"
    msg_cliente += f"Garantia: {cfg[4]}\n\n"
    msg_cliente += "Qualquer dúvida, estou à disposição!"

    st.text_area("Prévia da mensagem:", msg_cliente, height=180, label_visibility="collapsed")
    
    # Botão de Link Direto
    whatsapp_url = f"https://wa.me/{d['whatsapp_cliente']}?text={urllib.parse.quote(msg_cliente)}"
    st.markdown(f'<a href="{whatsapp_url}" target="_blank"><button style="width:100%; height:45px; border-radius:50px; background:#25D366; color:white; border:none; font-weight:700; cursor:pointer;">ABRIR NO WHATSAPP</button></a>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# --- CARD 3: FORNECEDOR / LOGÍSTICA ---
with col3:
    st.markdown("<div class='card'><h3>📦 Lista de Materiais</h3>", unsafe_allow_html=True)
    
    msg_forn = f"*PEDIDO - {cfg[0]}*\n"
    msg_forn += f"Data: {datetime.now().strftime('%d/%m')}\n"
    msg_forn += "----------------------------\n"
    for m in d['materiais']:
        msg_forn += f"• {m['qty']}x {m['desc']}\n"
    
    st.text_area("Lista técnica:", msg_forn, height=180, label_visibility="collapsed")
    st.download_button("💾 SALVAR LISTA TXT", msg_forn, f"Materiais_{d['cliente']}.txt", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# --- TABELA DETALHADA ---
st.markdown("<br>", unsafe_allow_html=True)
with st.expander("DETALHAMENTO TÉCNICO DE CUSTOS"):
    st.table(d['materiais'])
