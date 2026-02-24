import streamlit as st

# 1. CONFIGURAÇÃO OBRIGATÓRIA
st.set_page_config(page_title="Vero | RR Smart Soluções", layout="wide", initial_sidebar_state="collapsed")

from core.db import get_conn
from core.style import apply_vero_style

# 2. IMPORTAÇÃO DAS ABAS MODULARIZADAS
from tabs.historico import render_historico
from tabs.gerador import render_gerador
from tabs.precos import render_precos
from tabs.modelos import render_modelos
from tabs.configuracoes import render_configuracoes

# 3. APLICA ESTILO E ESTADOS
apply_vero_style()

if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'orcamento_pronto' not in st.session_state: st.session_state.orcamento_pronto = False

# 4. TELA DE LOGIN
if not st.session_state.logged_in:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    _, col_login, _ = st.columns([1, 1.2, 1])
    with col_login:
        st.markdown("<div style='text-align:center;'><h1>VERO</h1><p style='color:#3b82f6; letter-spacing:5px;'>SMART SYSTEMS</p></div>", unsafe_allow_html=True)
        with st.container(border=True):
            with st.form("login_form"):
                email = st.text_input("Usuário", placeholder="E-mail administrador")
                senha = st.text_input("Senha", type="password")
                
                if st.form_submit_button("ENTRAR NO SISTEMA", use_container_width=True):
                    conn = get_conn()
                    with conn.cursor() as cur:
                        cur.execute("SELECT id FROM usuarios WHERE email=%s AND senha=%s", (email, senha))
                        user = cur.fetchone()
                    if user:
                        st.session_state.logged_in = True
                        st.session_state.user_id = user[0]
                        st.rerun()
                    else:
                        st.error("Credenciais inválidas")
    st.stop()

# 5. CARREGAMENTO DE DADOS PRINCIPAIS
user_id = st.session_state.user_id
conn = get_conn()

with conn.cursor() as cur:
    cur.execute("SELECT nome_empresa, whatsapp, logo, pagamento_padrao, garantia_padrao, validade_dias FROM config_empresa WHERE usuario_id = %s", (user_id,))
    cfg = cur.fetchone() or ("RR Smart Soluções", "95984187832", None, "A combinar", "90 dias", 7)

# 6. MENU SUPERIOR E CHAMADA DAS FUNÇÕES
tab_historico, tab_gerador, tab_precos, tab_modelos, tab_config = st.tabs([
    "📊 Histórico & Funil", "📑 Gerador de Orçamento", "💰 Tabela de Preços", "✍️ Modelos de Texto", "⚙️ Configurações"
])

with tab_historico:
    render_historico(conn, user_id)

with tab_gerador:
    render_gerador(conn, user_id, cfg)

with tab_precos:
    render_precos(conn, user_id)

with tab_modelos:
    render_modelos(conn, user_id)

with tab_config:
    render_configuracoes(conn, user_id, cfg)
