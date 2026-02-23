import streamlit as st

# 1. CONFIGURAÇÃO OBRIGATÓRIA (SEMPRE A PRIMEIRA LINHA)
st.set_page_config(page_title="Vero | RR Smart", layout="wide", initial_sidebar_state="collapsed")

import pandas as pd
import io
import urllib.parse
from core.db import get_conn
from core.style import apply_vero_style
from core.materials import build_materials_list
import services.registry as registry

# 2. APLICA ESTILO E INICIA MEMÓRIA
apply_vero_style()

if 'logged_in' not in st.session_state: 
    st.session_state.logged_in = False
if 'orcamento_pronto' not in st.session_state: 
    st.session_state.orcamento_pronto = False

# 3. TELA DE LOGIN SEGURA
if not st.session_state.logged_in:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    _, col_login, _ = st.columns([1, 1.2, 1])
    with col_login:
        st.markdown("<div style='text-align:center;'><h1>VERO</h1><p style='color:#3b82f6; letter-spacing:5px;'>SMART SYSTEMS</p></div>", unsafe_allow_html=True)
        with st.container(border=True):
            with st.form("login_form"):
                email = st.text_input("Usuário")
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
    st.stop() # PARA TUDO SE NÃO ESTIVER LOGADO

# 4. CARREGAMENTO DE DADOS (ÁREA LOGADA)
user_id = st.session_state.user_id
conn = get_conn()

with conn.cursor() as cur:
    cur.execute("SELECT nome_empresa, whatsapp, logo, pagamento_padrao, garantia_padrao, validade_dias FROM config_empresa WHERE usuario_id = %s", (user_id,))
    cfg = cur.fetchone() or ("RR Smart", "95984187832", None, "A combinar", "90 dias", 7)

# 5. MENU SUPERIOR
tab_gerador, tab_precos, tab_modelos, tab_config = st.tabs([
    "📑 Gerador de Orçamento", "💰 Tabela de Preços", "✍️ Modelos", "⚙️ Configurações"
])

# --- ABA: GERADOR DE ORÇAMENTOS ---
with tab_gerador:
    # SE O ORÇAMENTO FOI GERADO (TELA DE RESULTADO)
    if st.session_state.orcamento_pronto and 'dados_finais' in st.session_state:
        d = st.session_state.dados_finais
        
        st.success(f"Orçamento calculado com sucesso para {d['cliente']}!")
        
        if st.button("⬅️ VOLTAR E CRIAR NOVO ORÇAMENTO"):
            st.session_state.orcamento_pronto = False
            st.rerun()

        col_r1, col_r2 = st.columns(2)
        with col_r1:
            with st.container(border=True):
                st.subheader("📄 Proposta Formal (PDF)")
                st.markdown(f"<h2 style='color:#3b82f6;'>R$ {d['total']:.2f}</h2>", unsafe_allow_html=True)
                from core.pdf.summary import render_summary_pdf
                pdf_io = io.BytesIO()
                render_summary_pdf(pdf_io, d['payload_pdf'])
                st.download_button("📥 BAIXAR PROPOSTA", pdf_io.getvalue(), f"Orcamento_{d['cliente']}.pdf", use_container_width=True)

        with col_r2:
            with st.container(border=True):
                st.subheader("📱 WhatsApp e Logística")
                msg_zap = f"*PROPOSTA: {cfg[0]}*\n\n{d['texto_beneficios']}\n\n*Total: R$ {d['total']:.2f}*"
                url_zap = f"https://wa.me/{d['whatsapp_cliente']}?text={urllib.parse.quote(msg_zap)}"
                st.markdown(f'<a href="{url_zap}" target="_blank"><button style="width:100%; height:45px; border-radius:10px; background:#25d366; color:white; border:none; font-weight:700; margin-bottom:10px;">ENVIAR WHATSAPP</button></a>', unsafe_allow_html=True)
                
                with st.expander("Ver Materiais do Fornecedor"):
                    lista_txt = "\n".join([f"• {m['qty']}x {m['desc']}" for m in d['materiais']])
                    st.text_area("Lista Técnica", lista_txt, height=100)

    # SE ESTÁ MODO DE EDIÇÃO (FORMULÁRIO)
    else:
        st.header("Gerador de Orçamentos")
        with st.container(border=True):
            c1, c2 = st.columns(2)
            cliente = c1.text_input("Nome do Cliente")
            zap_cli = c2.text_input("WhatsApp do Cliente", placeholder="95984...")
            
            plugins = registry.get_plugins()
            servico = st.selectbox("Selecione o Serviço", list(plugins.keys()))
            plugin = plugins[servico]
            inputs = plugin.render_fields()
            
            if st.button("CALCULAR E FINALIZAR PROPOSTA", use_container_width=True):
                if not cliente:
                    st.warning("Por favor, preencha o nome do cliente.")
                else:
                    # Cálculo principal
                    res = plugin.compute(conn, inputs)
                    
                    # Busca de textos
                    with conn.cursor() as cur:
                        cur.execute("SELECT texto_detalhado FROM modelos_texto WHERE usuario_id = %s", (user_id,))
                        t_row = cur.fetchone()
                    
                    # Salva na memória
                    st.session_state.dados_finais = {
                        "cliente": cliente, 
                        "whatsapp_cliente": zap_cli, 
                        "total": res['subtotal'],
                        "materiais": build_materials_list(res), 
                        "texto_beneficios": t_row[0] if t_row else "Instalação padrão.",
                        "payload_pdf": {
                            "logo_bytes": cfg[2], "empresa": cfg[0], "whatsapp": cfg[1], "cliente": cliente,
                            "servicos": [res], "total": res['subtotal'], "pagamento": cfg[3], "garantia": cfg[4], "validade_dias": cfg[5]
                        }
                    }
                    
                    # GATILHO DA TELA DE RESULTADO
                    st.session_state.orcamento_pronto = True
                    st.rerun()

# --- ABA: PREÇOS ---
with tab_precos:
    st.header("Tabela de Preços")
    df_precos = pd.read_sql("SELECT chave, nome, valor, categoria FROM precos WHERE usuario_id = %s", conn, params=(user_id,))
    st.dataframe(df_precos, use_container_width=True)

# --- ABA: CONFIGURAÇÕES E SAÍDA ---
with tab_config:
    st.header("Sistema")
    if st.button("SAIR DO SISTEMA"):
        st.session_state.logged_in = False
        st.rerun()
