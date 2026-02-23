import streamlit as st
import pandas as pd
from core.db import get_conn
from core.style import apply_vero_style
import services.registry as registry

# Configuração essencial
st.set_page_config(page_title="Vero | RR Smart", layout="wide")
apply_vero_style()

# Controle de Sessão
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- TELA DE LOGIN ---
if not st.session_state.logged_in:
    _, col_login, _ = st.columns([1, 1.5, 1])
    with col_login:
        st.markdown("<h1 style='text-align:center;'>VERO LOGIN</h1>", unsafe_allow_html=True)
        with st.container(border=True):
            with st.form("login_form"):
                u = st.text_input("Usuário (E-mail)")
                p = st.text_input("Senha", type="password")
                if st.form_submit_button("ENTRAR NO SISTEMA", use_container_width=True):
                    conn = get_conn()
                    with conn.cursor() as cur:
                        cur.execute("SELECT id FROM usuarios WHERE email=%s AND senha=%s", (u, p))
                        user = cur.fetchone()
                    if user:
                        st.session_state.logged_in = True
                        st.session_state.user_id = user[0]
                        st.rerun()
                    else:
                        st.error("Acesso negado.")
    st.stop()

# --- ÁREA ADMINISTRATIVA ---
user_id = st.session_state.user_id
conn = get_conn()

# Carregar Dados da RR Smart Soluções
with conn.cursor() as cur:
    cur.execute("SELECT nome_empresa, whatsapp, pagamento_padrao, garantia_padrao FROM config_empresa WHERE usuario_id = %s", (user_id,))
    cfg = cur.fetchone() or ("RR Smart Soluções", "95984187832", "A combinar", "90 dias")

# Menu Superior (Abas)
tab_gerador, tab_precos, tab_modelos, tab_config = st.tabs([
    "📑 Gerador de Orçamento", "💰 Tabela de Preços", "✍️ Modelos de Texto", "⚙️ Configurações"
])

# FUNCIONALIDADE: GERADOR
with tab_gerador:
    st.header("Gerador de Orçamentos")
    with st.container(border=True):
        c1, c2 = st.columns(2)
        cliente = c1.text_input("Nome do Cliente")
        zap_cli = c2.text_input("WhatsApp do Cliente")
        
        plugins = registry.get_plugins()
        servico = st.selectbox("Selecione o Serviço", list(plugins.keys()))
        plugin = plugins[servico]
        inputs = plugin.render_fields()
        
        if st.button("CALCULAR E FINALIZAR"):
            st.success(f"Orçamento para {cliente} gerado com sucesso!")

# FUNCIONALIDADE: TABELA DE PREÇOS
with tab_precos:
    st.header("Gestão de Preços")
    with st.container(border=True):
        st.subheader("Cadastrar Novo Item")
        with st.form("add_item"):
            col_a, col_b, col_c = st.columns([2, 1, 1])
            nome_p = col_a.text_input("Produto/Serviço")
            valor_p = col_b.number_input("Valor R$", min_value=0.0)
            cat_p = col_c.selectbox("Categoria", ["CFTV", "Cerca/Concertina", "Motor de Portão"])
            if st.form_submit_button("SALVAR"):
                with conn.cursor() as cur:
                    cur.execute("INSERT INTO precos (nome, valor, categoria, usuario_id) VALUES (%s,%s,%s,%s)", (nome_p, valor_p, cat_p, user_id))
                conn.commit()
                st.rerun()
    
    st.subheader("Itens Cadastrados")
    df = pd.read_sql("SELECT id, nome, valor, categoria FROM precos WHERE usuario_id = %s", conn, params=(user_id,))
    st.data_editor(df, use_container_width=True)

# FUNCIONALIDADE: CONFIGURAÇÕES
with tab_config:
    st.header("Configurações da Empresa")
    with st.container(border=True):
        with st.form("cfg_form"):
            n_emp = st.text_input("Nome da Empresa", value=cfg[0])
            w_emp = st.text_input("WhatsApp Comercial", value=cfg[1])
            if st.form_submit_button("ATUALIZAR DADOS"):
                with conn.cursor() as cur:
                    cur.execute("UPDATE config_empresa SET nome_empresa=%s, whatsapp=%s WHERE usuario_id=%s", (n_emp, w_emp, user_id))
                conn.commit()
                st.success("Dados da RR Smart Soluções atualizados.")
    
    if st.button("SAIR DO SISTEMA"):
        st.session_state.logged_in = False
        st.rerun()
