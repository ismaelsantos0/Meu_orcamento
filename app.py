import streamlit as st
import hashlib
import re  # Importação para limpar e validar números

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
        
        # --- ABA DE LOGIN ---
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
                    else:
                        st.warning("Preencha o e-mail e a senha.")
                
                st.markdown("<div style='text-align:center; margin-top:10px;'><a href='https://wa.me/5595984187832?text=Olá,%20esqueci%20minha%20senha%20na%20VERO.' target='_blank' style='color:#a0aec0; text-decoration:none; font-size:14px;'>Esqueceu a senha? Fale com o Suporte</a></div>", unsafe_allow_html=True)

        # --- ABA DE CADASTRO PARA NOVOS CLIENTES ---
        with tab_cadastro:
            with st.container(border=True):
                st.write("Junte-se à VERO e automatize seus orçamentos.")
                
                novo_nome = st.text_input("Nome da Empresa ou Instalador")
                novo_email = st.text_input("E-mail (Será seu login)")
                novo_whats = st.text_input("WhatsApp com DDD (Ex: 95 98418...)")
                
                col_s1, col_s2 = st.columns(2)
                nova_senha = col_s1.text_input("Crie uma Senha", type="password")
                confirma_senha = col_s2.text_input("Confirme a Senha", type="password")
                
                if st.button("CRIAR MINHA CONTA", use_container_width=True):
                    # Limpeza de dados para validação rigorosa
                    nome_limpo = novo_nome.strip()
                    email_limpo = novo_email.strip()
                    whats_limpo = re.sub(r'\D', '', novo_whats)  # Arranca tudo que não for número
                    
                    if not nome_limpo or not email_limpo or not whats_limpo or not nova_senha:
                        st.warning("⚠️ Por favor, preencha todos os campos obrigatoriamente.")
                    elif len(whats_limpo) < 10:
                        st.warning("⚠️ Insira um número de WhatsApp válido com o DDD.")
                    elif nova_senha != confirma_senha:
                        st.error("⚠️ As senhas digitadas não coincidem.")
                    else:
                        senha_hash = hashlib.sha256(nova_senha.encode()).hexdigest()
                        
                        conn = get_conn()
                        try:
                            with conn.cursor() as cur:
                                cur.execute("""
                                    INSERT INTO usuarios (nome, email, whatsapp, senha) 
                                    VALUES (%s, %s, %s, %s) RETURNING id
                                """, (nome_limpo, email_limpo, whats_limpo, senha_hash))
                                
                                novo_id = cur.fetchone()[0]
                                
                                cur.execute("""
                                    INSERT INTO config_empresa 
                                    (usuario_id, nome_empresa, whatsapp, pagamento_padrao, garantia_padrao, validade_dias) 
                                    VALUES (%s, %s, %s, 'A combinar', '90 dias', 7)
                                """, (novo_id, nome_limpo, whats_limpo))
                                
                            conn.commit()
                            st.success("🎉 Conta criada com sucesso! Mude para a aba 'Entrar' e faça seu login.")
                        except Exception as e:
                            conn.rollback()
                            if "unique constraint" in str(e).lower() or "duplicate key" in str(e).lower():
                                st.error("⚠️ Este E-mail ou WhatsApp já está cadastrado na VERO.")
                            else:
                                st.error(f"Erro no banco de dados: {e}")
    st.stop()

# ==========================================
# 5. CARREGAMENTO DE DADOS PRINCIPAIS
# ==========================================
user_id = st.session_state.user_id
conn = get_conn()

with conn.cursor() as cur:
    cur.execute("SELECT nome_empresa, whatsapp, logo, pagamento_padrao, garantia_padrao, validade_dias FROM config_empresa WHERE usuario_id = %s", (user_id,))
    cfg = cur.fetchone() or ("Sua Empresa", "Contato", None, "A combinar", "90 dias", 7)

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
