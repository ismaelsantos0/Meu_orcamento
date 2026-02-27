import streamlit as st
import hashlib
import re

# 1. CONFIGURAÇÃO OBRIGATÓRIA
st.set_page_config(page_title="VERO Smart Systems", layout="wide", initial_sidebar_state="collapsed")

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

# ==========================================
# 4. TELA DE LOGIN E CADASTRO (SaaS VERO)
# ==========================================
if not st.session_state.logged_in:
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, col_login, _ = st.columns([1, 1.2, 1])
    
    with col_login:
        st.markdown("<div style='text-align:center;'><h1>VERO</h1><p style='color:#3b82f6; letter-spacing:5px;'>SMART SYSTEMS</p></div><br>", unsafe_allow_html=True)
        
        tab_login, tab_cadastro = st.tabs(["🔐 Entrar", "📝 Criar Conta"])
        
        with tab_login:
            with st.container(border=True):
                email_login = st.text_input("E-mail", key="log_email")
                senha_login = st.text_input("Senha", type="password", key="log_senha")
                
                if st.button("ENTRAR NO SISTEMA", use_container_width=True):
                    if email_login and senha_login:
                        senha_hash = hashlib.sha256(senha_login.encode()).hexdigest()
                        conn = get_conn()
                        with conn.cursor() as cur:
                            cur.execute("SELECT id FROM usuarios WHERE email=%s AND senha=%s", (email_login, senha_hash))
                            user = cur.fetchone()
                        if user:
                            st.session_state.logged_in = True
                            st.session_state.user_id = user[0]
                            st.rerun()
                        else:
                            st.error("E-mail ou senha inválidos.")

        with tab_cadastro:
            with st.container(border=True):
                st.write("Junte-se à VERO e automatize seus orçamentos.")
                novo_nome = st.text_input("Nome da Empresa ou Instalador")
                novo_email = st.text_input("E-mail (Login)")
                novo_whats = st.text_input("WhatsApp com DDD")
                col_s1, col_s2 = st.columns(2)
                nova_senha = col_s1.text_input("Senha", type="password")
                conf_senha = col_s2.text_input("Confirme a Senha", type="password")
                
                if st.button("CRIAR MINHA CONTA", use_container_width=True):
                    nome_limpo = novo_nome.strip()
                    whats_limpo = re.sub(r'\D', '', novo_whats)
                    
                    if not nome_limpo or not whats_limpo or len(whats_limpo) < 10:
                        st.warning("Preencha todos os campos e um WhatsApp válido.")
                    elif nova_senha != conf_senha:
                        st.error("As senhas não coincidem.")
                    else:
                        senha_hash = hashlib.sha256(nova_senha.encode()).hexdigest()
                        conn = get_conn()
                        try:
                            with conn.cursor() as cur:
                                # 1. Cria Usuário
                                cur.execute("INSERT INTO usuarios (nome, email, whatsapp, senha) VALUES (%s, %s, %s, %s) RETURNING id", 
                                            (nome_limpo, novo_email.strip(), whats_limpo, senha_hash))
                                novo_id = cur.fetchone()[0]
                                
                                # 2. Configurações Iniciais
                                cur.execute("INSERT INTO config_empresa (usuario_id, nome_empresa, whatsapp) VALUES (%s, %s, %s)", 
                                            (novo_id, nome_limpo, whats_limpo))

                                # 3. Popula Tabela de Preços com IDs Fixos
                                itens_saas = [
                                    ('bateria', 'Bateria 12V', 'Cerca/Concertina'),
                                    ('cabo_alta_50m', 'Cabo de alta isolação (50m)', 'Cerca/Concertina'),
                                    ('central_sh1800', 'Central SH1800', 'Cerca/Concertina'),
                                    ('concertina_10m', 'Concertina 30cm (10m)', 'Cerca/Concertina'),
                                    ('concertina_linear_20m', 'Concertina linear (20m)', 'Cerca/Concertina'),
                                    ('fio_aco_200m', 'Fio de aço (200m)', 'Cerca/Concertina'),
                                    ('haste_canto', 'Haste de canto', 'Cerca/Concertina'),
                                    ('haste_reta', 'Haste reta', 'Cerca/Concertina'),
                                    ('kit_aterramento', 'Kit Aterramento', 'Cerca/Concertina'),
                                    ('kit_isoladores', 'Kit Isoladores (100un)', 'Cerca/Concertina'),
                                    ('kit_placas', 'Kit Placas de Aviso', 'Cerca/Concertina'),
                                    ('sirene', 'Sirene', 'Cerca/Concertina'),
                                    ('mao_cerca_base', 'Mão de obra: Cerca Elétrica (Base)', 'Cerca/Concertina'),
                                    ('mao_cerca_por_m', 'Mão de obra: Cerca Elétrica (Metro)', 'Cerca/Concertina'),
                                    ('mao_concertina_base', 'Mão de obra: Concertina em Cerca (Base)', 'Cerca/Concertina'),
                                    ('mao_concertina_por_m', 'Mão de obra: Concertina em Cerca (Metro)', 'Cerca/Concertina'),
                                    ('mao_linear_base', 'Mão de obra: Concertina Linear (Base)', 'Cerca/Concertina'),
                                    ('mao_linear_por_m', 'Mão de obra: Concertina Linear (Metro)', 'Cerca/Concertina'),
                                    ('cftv_balun', 'Balun de Vídeo', 'CFTV'),
                                    ('cftv_cabo_cat5_m', 'Cabo Cat5e (Metro)', 'CFTV'),
                                    ('cftv_caixa_hermetica', 'Caixa Hermética', 'CFTV'),
                                    ('cftv_camera', 'Câmera CFTV', 'CFTV'),
                                    ('cftv_conector_p4_femea', 'Conector P4 Fêmea', 'CFTV'),
                                    ('cftv_conector_p4_macho', 'Conector P4 Macho', 'CFTV'),
                                    ('cftv_dvr', 'DVR', 'CFTV'),
                                    ('cftv_fonte_colmeia', 'Fonte Colmeia', 'CFTV'),
                                    ('cftv_hd', 'HD para DVR', 'CFTV'),
                                    ('cftv_suporte_camera', 'Suporte para Câmera', 'CFTV'),
                                    ('mao_cftv_dvr', 'Mão de obra: Instalação DVR', 'CFTV'),
                                    ('mao_cftv_por_camera_inst', 'Mão de obra: Instalar Câmera (un)', 'CFTV'),
                                    ('mao_cftv_por_camera_defeito', 'Mão de obra: Manutenção Câmera', 'CFTV'),
                                    ('mao_motor_inst', 'Mão de obra: Instalação Motor', 'Motor de Portão'),
                                    ('mao_motor_man', 'Mão de obra: Manutenção Motor', 'Motor de Portão')
                                ]
                                for chave, nome, cat in itens_saas:
                                    cur.execute("INSERT INTO precos (chave, nome, valor, usuario_id, categoria) VALUES (%s, %s, 0, %s, %s)", 
                                                (chave, nome, novo_id, cat))
                            conn.commit()
                            st.success("🎉 Conta criada! Faça login e preencha seus preços.")
                        except Exception as e:
                            conn.rollback()
                            st.error(f"Erro: {e}")
    st.stop()

# 5. CARREGAMENTO DE DADOS (Pós-login)
user_id = st.session_state.user_id
conn = get_conn()
with conn.cursor() as cur:
    cur.execute("SELECT nome_empresa, whatsapp, logo, pagamento_padrao, garantia_padrao, validade_dias FROM config_empresa WHERE usuario_id = %s", (user_id,))
    cfg = cur.fetchone() or ("Sua Empresa", "Contato", None, "A combinar", "90 dias", 7)

# 6. MENU SUPERIOR
tabs = st.tabs(["📊 Histórico & Funil", "📑 Gerador", "💰 Preços", "✍️ Textos", "⚙️ Configs"])
with tabs[0]: render_historico(conn, user_id)
with tabs[1]: render_gerador(conn, user_id, cfg)
with tabs[2]: render_precos(conn, user_id)
with tabs[3]: render_modelos(conn, user_id)
with tabs[4]: render_configuracoes(conn, user_id, cfg)
