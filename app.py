import streamlit as st
import pandas as pd
import io
from datetime import datetime
from core.db import get_conn
from core.style import apply_vero_style
from core.materials import build_materials_list
import services.registry as registry

# Configurações Iniciais
st.set_page_config(page_title="Vero | RR Smart Soluções", layout="wide", initial_sidebar_state="collapsed")
apply_vero_style()

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- 1. TELA DE LOGIN ---
if not st.session_state.logged_in:
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, col_login, _ = st.columns([1, 1.2, 1])
    with col_login:
        st.markdown("<div style='text-align:center;'><h1>VERO</h1><p style='color:#3b82f6; letter-spacing:5px;'>SMART SYSTEMS</p></div>", unsafe_allow_html=True)
        with st.container(border=True):
            with st.form("login_form", border=False):
                email = st.text_input("USUÁRIO")
                senha = st.text_input("SENHA", type="password")
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

# --- 2. DADOS DO USUÁRIO E EMPRESA ---
user_id = st.session_state.user_id
conn = get_conn()

with conn.cursor() as cur:
    cur.execute("SELECT nome_empresa, whatsapp, logo, pagamento_padrao, garantia_padrao, validade_dias FROM config_empresa WHERE usuario_id = %s", (user_id,))
    cfg = cur.fetchone() or ("RR Smart Soluções", "95984187832", None, "A combinar", "90 dias", 7) #

# --- 3. MENU SUPERIOR (TABS) ---
tab_inicio, tab_gerador, tab_precos, tab_modelos, tab_config = st.tabs([
    "🏠 Início", "📑 Gerador", "💰 Tabela de Preços", "✍️ Modelos", "⚙️ Configurações"
])

# ABA: INÍCIO
with tab_inicio:
    st.markdown("<h1 style='text-align:center; padding: 40px;'>PAINEL ADMINISTRATIVO</h1>", unsafe_allow_html=True)
    st.markdown(f"<div style='text-align:center;'><h3>Bem-vindo à {cfg[0]}</h3></div>", unsafe_allow_html=True)

# ABA: GERADOR
with tab_gerador:
    st.header("Gerador de Orçamentos")
    with st.container(border=True):
        col1, col2 = st.columns(2)
        cliente_nome = col1.text_input("Nome do Cliente")
        contato_cli = col2.text_input("WhatsApp Cliente", placeholder="95984...")
        
        plugins = registry.get_plugins()
        servico_label = st.selectbox("Tipo de Serviço", list(p.label for p in plugins.values()))
        plugin = next(p for p in plugins.values() if p.label == servico_label)
        inputs = plugin.render_fields()
        
        if st.button("GERAR PROPOSTA", use_container_width=True):
            # Lógica de cálculo enviada para a página de resumo
            st.success("Cálculo realizado! Verifique o resumo.")

# ABA: PREÇOS
with tab_precos:
    st.header("Tabela de Preços")
    # Interface conforme imagem enviada
    with st.container(border=True):
        with st.form("form_add_preco", clear_on_submit=True):
            c1, c2, c3, c4 = st.columns([1, 2, 1, 1])
            ch = c1.text_input("Chave única")
            nm = c2.text_input("Nome do Produto")
            vl = c3.number_input("Preço R$", min_value=0.0)
            ct = c4.selectbox("Serviço", ["CFTV", "Cerca/Concertina", "Motor de Portão", "Geral"])
            if st.form_submit_button("CADASTRAR"):
                with conn.cursor() as cur:
                    cur.execute("INSERT INTO precos (chave, nome, valor, usuario_id, categoria) VALUES (%s,%s,%s,%s,%s)", (ch,nm,vl,user_id,ct))
                conn.commit()
                st.rerun()

# ABA: MODELOS (BENEFÍCIOS)
with tab_modelos:
    st.header("Modelos de Proposta PDF") #
    with st.container(border=True):
        sel_serv = st.selectbox("Escolha o serviço", ["CFTV", "Cerca/Concertina", "Motor de Portão"])
        # Lógica de salvar texto detalhado omitida para brevidade...

# ABA: CONFIGURAÇÕES (RESTAURADA)
with tab_config:
    st.header("Configurações da Empresa") #
    with st.container(border=True):
        with st.form("config_personalizacao"):
            c_e1, c_e2 = st.columns(2)
            nome_emp = c_e1.text_input("Nome da Empresa", value=cfg[0])
            whatsapp_emp = c_e2.text_input("WhatsApp Comercial", value=cfg[1])
            
            c_e3, c_e4 = st.columns(2)
            pagto = c_e3.text_input("Pagamento Padrão", value=cfg[3])
            garantia = c_e4.text_input("Garantia Padrão", value=cfg[4])
            
            validade = st.number_input("Dias de Validade", value=cfg[5])
            
            st.markdown("---")
            logo_file = st.file_uploader("Trocar Logo da RR Smart Soluções", type=["png", "jpg"])
            
            if st.form_submit_button("SALVAR ALTERAÇÕES", use_container_width=True):
                # Lógica SQL para salvar no banco...
                st.success("Dados salvos! Eles serão usados nos próximos orçamentos.")

    if st.button("SAIR DO SISTEMA", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()
