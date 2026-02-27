import streamlit as st
import hashlib
import re

st.set_page_config(page_title="VERO Smart Systems", layout="wide", initial_sidebar_state="collapsed")

from core.db import get_conn
from core.style import apply_vero_style
from tabs.historico import render_historico
from tabs.gerador import render_gerador
from tabs.precos import render_precos
from tabs.modelos import render_modelos
from tabs.configuracoes import render_configuracoes

apply_vero_style()

if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, col_login, _ = st.columns([1, 1.2, 1])
    with col_login:
        st.markdown("<div style='text-align:center;'><h1>VERO</h1><p style='color:#3b82f6; letter-spacing:5px;'>SMART SYSTEMS</p></div><br>", unsafe_allow_html=True)
        tab_login, tab_cadastro = st.tabs(["🔐 Entrar", "📝 Criar Conta"])
        
        with tab_login:
            with st.container(border=True):
                email_log = st.text_input("E-mail", key="log_email")
                senha_log = st.text_input("Senha", type="password", key="log_senha")
                if st.button("ENTRAR", use_container_width=True):
                    senha_hash = hashlib.sha256(senha_log.encode()).hexdigest()
                    conn = get_conn()
                    with conn.cursor() as cur:
                        cur.execute("SELECT id FROM usuarios WHERE email=%s AND senha=%s", (email_log, senha_hash))
                        user = cur.fetchone()
                    if user:
                        st.session_state.logged_in = True
                        st.session_state.user_id = user[0]
                        st.rerun()

        with tab_cadastro:
            with st.container(border=True):
                n_nome = st.text_input("Nome da Empresa")
                n_email = st.text_input("E-mail (Login)")
                n_whats = st.text_input("WhatsApp com DDD")
                c_s1, c_s2 = st.columns(2)
                n_senha = c_s1.text_input("Senha", type="password")
                n_conf = c_s2.text_input("Confirme", type="password")
                
                if st.button("CRIAR MINHA CONTA", use_container_width=True):
                    whats_limpo = re.sub(r'\D', '', n_whats)
                    if n_senha == n_conf and len(whats_limpo) >= 10:
                        s_hash = hashlib.sha256(n_senha.encode()).hexdigest()
                        conn = get_conn()
                        try:
                            with conn.cursor() as cur:
                                cur.execute("INSERT INTO usuarios (nome, email, whatsapp, senha) VALUES (%s, %s, %s, %s) RETURNING id", (n_nome, n_email, whats_limpo, s_hash))
                                u_id = cur.fetchone()[0]
                                cur.execute("INSERT INTO config_empresa (usuario_id, nome_empresa, whatsapp) VALUES (%s, %s, %s)", (u_id, n_nome, whats_limpo))
                                
                                # LISTA DE IDS FIXOS (IDs da sua planilha que o sistema usa para calcular)
                                itens = [
                                    ('bateria', 'Bateria 12V', 'Cerca/Concertina'),
                                    ('haste_reta', 'Haste Reta', 'Cerca/Concertina'),
                                    ('haste_canto', 'Haste de Canto', 'Cerca/Concertina'),
                                    ('central_sh1800', 'Central SH1800', 'Cerca/Concertina'),
                                    ('mao_cerca_base', 'Mão de obra: Cerca (Base)', 'Cerca/Concertina'),
                                    ('cftv_camera', 'Câmera CFTV', 'CFTV'),
                                    ('cftv_dvr', 'DVR', 'CFTV'),
                                    ('mao_cftv_dvr', 'Mão de obra: Instalação DVR', 'CFTV')
                                ]
                                for ch, nm, ct in itens:
                                    cur.execute("INSERT INTO precos (chave, nome, valor, usuario_id, categoria) VALUES (%s, %s, 0, %s, %s)", (ch, nm, u_id, ct))
                            conn.commit()
                            st.success("Conta criada! Acesse a aba Preços para preencher seus valores.")
                        except Exception as e: st.error(f"Erro: {e}")
    st.stop()

user_id = st.session_state.user_id
conn = get_conn()
with conn.cursor() as cur:
    cur.execute("SELECT nome_empresa, whatsapp, logo, pagamento_padrao, garantia_padrao, validade_dias FROM config_empresa WHERE usuario_id = %s", (user_id,))
    cfg = cur.fetchone() or ("Sua Empresa", "999999999", None, "A combinar", "90 dias", 7)

tabs = st.tabs(["📊 Histórico", "📑 Gerador", "💰 Preços", "✍️ Textos", "⚙️ Configs"])
with tabs[0]: render_historico(conn, user_id)
with tabs[1]: render_gerador(conn, user_id, cfg)
with tabs[2]: render_precos(conn, user_id)
with tabs[3]: render_modelos(conn, user_id)
with tabs[4]: render_configuracoes(conn, user_id, cfg)
