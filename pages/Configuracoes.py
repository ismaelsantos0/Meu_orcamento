import streamlit as st
from core.db import get_conn

# =========================
# TRAVA DE SEGURANÇA (A PORTARIA)
# =========================
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.error("❌ Acesso negado! Por favor, faça login na página principal.")
    st.stop()

user_id = st.session_state.user_id

st.set_page_config(page_title="Configurações", page_icon="⚙️", layout="wide")

st.markdown("""
<style>
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #262933 !important;
        border-radius: 12px !important;
        border: 1px solid #333845 !important;
        padding: 1.5rem !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("⚙️ Configurações da Empresa")

# Funções de Banco de Dados com Filtro de Usuário
def buscar_dados():
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT nome_empresa, whatsapp, pagamento_padrao, garantia_padrao, validade_dias, logo 
                FROM config_empresa WHERE usuario_id = %s
            """, (user_id,))
            return cur.fetchone()
    except:
        return None

dados_atuais = buscar_dados()
if not dados_atuais:
    dados_atuais = ("", "", "À vista", "90 dias", 7, None)

with st.container(border=True):
    with st.form("form_config"):
        col1, col2 = st.columns(2)
        with col1:
            nome_empresa = st.text_input("Nome da Empresa", value=dados_atuais[0])
            whatsapp = st.text_input("WhatsApp", value=dados_atuais[1])
            st.markdown("**Logo (PNG/JPG - Máx 2MB)**")
            uploaded_logo = st.file_uploader("Upload", type=['png', 'jpg', 'jpeg'], label_visibility="collapsed")
        
        with col2:
            garantia = st.text_input("Garantia", value=dados_atuais[3])
            validade = st.number_input("Validade (Dias)", value=dados_atuais[4], min_value=1)
            pagamento = st.text_input("Pagamento", value=dados_atuais[2])
        
        if st.form_submit_button("💾 Salvar Configurações", type="primary", use_container_width=True):
            logo_bytes = uploaded_logo.read() if uploaded_logo else None
            conn = get_conn()
            with conn.cursor() as cur:
                if buscar_dados():
                    cur.execute("""
                        UPDATE config_empresa SET nome_empresa=%s, whatsapp=%s, pagamento_padrao=%s, 
                        garantia_padrao=%s, validade_dias=%s, logo=COALESCE(%s, logo)
                        WHERE usuario_id = %s
                    """, (nome_empresa, whatsapp, pagamento, garantia, validade, logo_bytes, user_id))
                else:
                    cur.execute("""
                        INSERT INTO config_empresa (usuario_id, nome_empresa, whatsapp, pagamento_padrao, garantia_padrao, validade_dias, logo)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (user_id, nome_empresa, whatsapp, pagamento, garantia, validade, logo_bytes))
            conn.commit()
            st.success("Dados atualizados!")
            st.rerun()
