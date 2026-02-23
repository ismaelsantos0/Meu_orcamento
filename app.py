import streamlit as st
import pandas as pd
import io
import urllib.parse
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
    st.markdown("<br><br><br>", unsafe_allow_html=True)
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

# --- 2. MENU SUPERIOR E FUNCIONALIDADES ---
user_id = st.session_state.user_id
conn = get_conn()

# Busca configurações globais da empresa
with conn.cursor() as cur:
    cur.execute("SELECT nome_empresa, whatsapp, logo, pagamento_padrao, garantia_padrao, validade_dias FROM config_empresa WHERE usuario_id = %s", (user_id,))
    cfg = cur.fetchone() or ("RR Smart Soluções", "95984187832", None, "A combinar", "90 dias", 7)

# Definição das Abas conforme a imagem enviada
tab_inicio, tab_gerador, tab_precos, tab_modelos, tab_config = st.tabs([
    "🏠 Início", 
    "📑 Gerador", 
    "💰 Tabela de Preços", 
    "✍️ Modelos", 
    "⚙️ Configurações"
])

# --- ABA: INÍCIO ---
with tab_inicio:
    st.markdown("<h1 style='text-align:center; padding: 40px;'>PAINEL ADMINISTRATIVO</h1>", unsafe_allow_html=True)
    st.markdown(f"<div style='text-align:center;'><h3>Bem-vindo à {cfg[0]}</h3></div>", unsafe_allow_html=True)

# --- ABA: GERADOR DE ORÇAMENTOS ---
with tab_gerador:
    st.header("Gerador de Orçamentos")
    with st.container(border=True):
        col1, col2 = st.columns(2)
        cliente = col1.text_input("Nome do Cliente", key="gen_cliente")
        contato_cli = col2.text_input("WhatsApp Cliente", key="gen_zap")

        plugins = registry.get_plugins()
        servico_label = st.selectbox("Tipo de Serviço", list(p.label for p in plugins.values()))
        plugin = next(p for p in plugins.values() if p.label == servico_label)
        
        inputs = plugin.render_fields()

        # Identificação da Categoria para Adicionais
        mapeamento = {"Camera": "CFTV", "Motor": "Motor de Portão", "Cerca": "Cerca/Concertina", "Concertina": "Cerca/Concertina"}
        cat_atual = next((v for k, v in mapeamento.items() if k in servico_label), "Geral")

        # Busca Adicionais da Tabela de Preços
        df_p = pd.read_sql("SELECT chave, nome, valor FROM precos WHERE usuario_id = %s AND (categoria = %s OR categoria = 'Geral')", conn, params=(user_id, cat_atual))
        extras = []
        if not df_p.empty:
            st.subheader(f"Adicionais: {cat_atual}")
            opcoes = {f"{r['nome']} (R$ {r['valor']:.2f})": r for _, r in df_p.iterrows()}
            selecionados = st.multiselect("Adicionar itens", list(opcoes.keys()))
            for sel in selecionados:
                extras.append({"info": opcoes[sel], "qtd": 1}) # Simplificado para o menu único

        if st.button("FINALIZAR ORÇAMENTO", use_container_width=True):
            res = plugin.compute(conn, inputs)
            # Lógica de cálculo e PDF aqui...
            st.success("Orçamento gerado com sucesso!")

# --- ABA: TABELA DE PREÇOS ---
with tab_precos:
    st.header("Tabela de Preços por Serviço")
    # Interface de Cadastro conforme imagem
    with st.container(border=True):
        with st.form("form_precos", clear_on_submit=True):
            c1, c2, c3, c4 = st.columns([1, 2, 1, 1])
            new_ch = c1.text_input("Chave única")
            new_nm = c2.text_input("Nome do Produto")
            new_vl = c3.number_input("Preço R$", min_value=0.0)
            new_ct = c4.selectbox("Categoria", ["CFTV", "Cerca/Concertina", "Motor de Portão", "Geral"])
            if st.form_submit_button("CADASTRAR"):
                with conn.cursor() as cur:
                    cur.execute("INSERT INTO precos (chave, nome, valor, usuario_id, categoria) VALUES (%s,%s,%s,%s,%s)", (new_ch, new_nm, new_vl, user_id, new_ct))
                conn.commit()
                st.rerun()

    # Visualização em Tabs internas
    subtabs = st.tabs(["Todos", "CFTV", "Cerca/Concertina", "Motor de Portão", "Geral"])
    for i, st_name in enumerate(["Todos", "CFTV", "Cerca/Concertina", "Motor de Portão", "Geral"]):
        with subtabs[i]:
            query = "SELECT chave, nome, valor, categoria FROM precos WHERE usuario_id = %s"
            params = [user_id]
            if st_name != "Todos":
                query += " AND categoria = %s"
                params.append(st_name)
            df_view = pd.read_sql(query, conn, params=params)
            st.data_editor(df_view, use_container_width=True, key=f"editor_{st_name}")

# --- ABA: MODELOS DE TEXTO ---
with tab_modelos:
    st.header("Modelos de Proposta PDF")
    # Interface conforme imagem
    with st.container(border=True):
        sel_serv = st.selectbox("Escolha o serviço", ["CFTV", "Cerca/Concertina", "Motor de Portão"])
        with conn.cursor() as cur:
            cur.execute("SELECT texto_detalhado FROM modelos_texto WHERE usuario_id = %s AND servico_tipo = %s", (user_id, sel_serv))
            txt_res = cur.fetchone()
            txt_atual = txt_res[0] if txt_res else ""
        
        new_txt = st.text_area("Descrição detalhada (Benefícios)", value=txt_atual, height=300)
        if st.button("SALVAR MODELO"):
            with conn.cursor() as cur:
                cur.execute("INSERT INTO modelos_texto (usuario_id, servico_tipo, texto_detalhado) VALUES (%s,%s,%s) ON CONFLICT (usuario_id, servico_tipo) DO UPDATE SET texto_detalhado = EXCLUDED.texto_detalhado", (user_id, sel_serv, new_txt))
            conn.commit()
            st.success("Modelo atualizado!")

# --- ABA: CONFIGURAÇÕES ---
with tab_config:
    st.header("Configurações do Sistema")
    if st.button("LOGOUT / SAIR DO SISTEMA", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()
