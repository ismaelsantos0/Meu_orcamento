import streamlit as st
import pandas as pd
import io
import urllib.parse
from datetime import datetime
from core.db import get_conn
from core.style import apply_vero_style
from core.materials import build_materials_list
import services.registry as registry

# 1. CONFIGURAÇÃO INICIAL (DEVE SER A PRIMEIRA LINHA)
st.set_page_config(page_title="Vero | RR Smart Soluções", layout="wide", initial_sidebar_state="collapsed")
apply_vero_style()

# 2. INICIALIZAÇÃO DE ESTADOS
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'view_mode' not in st.session_state:
    st.session_state.view_mode = "edit"

# --- 3. TELA DE LOGIN (SÓ CARREGA ISSO SE NÃO ESTIVER LOGADO) ---
if not st.session_state.logged_in:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    _, col_login, _ = st.columns([1, 1.2, 1])
    
    with col_login:
        st.markdown("<div style='text-align:center;'><h1>VERO</h1><p style='color:#3b82f6; letter-spacing:5px;'>SMART SYSTEMS</p></div>", unsafe_allow_html=True)
        with st.container(border=True):
            # Removido 'border=False' do form para garantir visibilidade
            with st.form("main_login_form"):
                st.markdown("<p style='text-align:center; opacity:0.7;'>Acesso RR Smart Soluções</p>", unsafe_allow_html=True)
                user_input = st.text_input("E-mail")
                pass_input = st.text_input("Senha", type="password")
                
                if st.form_submit_button("ENTRAR NO PAINEL", use_container_width=True):
                    conn = get_conn()
                    with conn.cursor() as cur:
                        cur.execute("SELECT id FROM usuarios WHERE email=%s AND senha=%s", (user_input, pass_input))
                        auth = cur.fetchone()
                    if auth:
                        st.session_state.logged_in = True
                        st.session_state.user_id = auth[0]
                        st.rerun()
                    else:
                        st.error("Usuário ou senha inválidos.")
    st.stop() # Mata o script aqui. Nada abaixo será lido se não logar.

# --- 4. ÁREA LOGADA (SÓ EXECUTA APÓS O LOGIN) ---
user_id = st.session_state.user_id
conn = get_conn()

# Busca configurações da RR Smart Soluções
with conn.cursor() as cur:
    cur.execute("SELECT nome_empresa, whatsapp, logo, pagamento_padrao, garantia_padrao, validade_dias FROM config_empresa WHERE usuario_id = %s", (user_id,))
    cfg = cur.fetchone() or ("RR Smart Soluções", "95984187832", None, "A combinar", "90 dias", 7)

# MENU SUPERIOR (TABS) - Estilo conforme imagem aprovada
tab_inicio, tab_gerador, tab_precos, tab_modelos, tab_config = st.tabs([
    "🏠 Início", "📑 Gerador", "💰 Tabela de Preços", "✍️ Modelos", "⚙️ Configurações"
])

with tab_inicio:
    st.markdown("<h1 style='text-align:center; padding: 40px;'>PAINEL ADMINISTRATIVO</h1>", unsafe_allow_html=True)
    st.markdown(f"<div style='text-align:center;'><h3>Bem-vindo, {cfg[0]}</h3></div>", unsafe_allow_html=True)

with tab_gerador:
    if st.session_state.view_mode == "result" and 'dados_orcamento' in st.session_state:
        # EXIBIÇÃO DE RESULTADO (PDF / ZAP)
        d = st.session_state.dados_orcamento
        if st.button("⬅️ NOVO ORÇAMENTO"):
            st.session_state.view_mode = "edit"
            st.rerun()
        
        c_res1, c_res2 = st.columns(2)
        with c_res1:
            with st.container(border=True):
                st.subheader("📄 Proposta")
                st.write(f"Cliente: {d['cliente']}")
                st.write(f"Total: R$ {d['total']:.2f}")
                # Aqui entra a chamada da função render_summary_pdf
        with c_res2:
            with st.container(border=True):
                st.subheader("📱 WhatsApp")
                # Lógica de link wa.me
    else:
        # FORMULÁRIO DO GERADOR
        st.header("Gerador de Orçamentos")
        with st.container(border=True):
            c1, c2 = st.columns(2)
            cli = c1.text_input("Nome do Cliente", key="c_name")
            zap = c2.text_input("WhatsApp", key="c_zap")
            
            # ... Lógica dos plugins e itens extras (mantenha a lógica anterior)
            
            if st.button("FINALIZAR ORÇAMENTO", use_container_width=True):
                # Processamento e st.session_state.view_mode = "result"
                st.session_state.view_mode = "result"
                st.rerun()

with tab_precos:
    st.header("Tabela de Preços")
    # LISTA REAL DOS ITENS DO BANCO
    df_precos = pd.read_sql("SELECT chave, nome, valor, categoria FROM precos WHERE usuario_id = %s", conn, params=(user_id,))
    st.data_editor(df_precos, use_container_width=True)

with tab_config:
    st.header("Configurações")
    # Campos de personalização da RR Smart Soluções
    if st.button("SAIR DO SISTEMA"):
        st.session_state.logged_in = False
        st.rerun()
