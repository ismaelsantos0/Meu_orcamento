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

# --- 2. DADOS DO USUÁRIO ---
user_id = st.session_state.user_id
conn = get_conn()

with conn.cursor() as cur:
    cur.execute("SELECT nome_empresa, whatsapp, logo, pagamento_padrao, garantia_padrao, validade_dias FROM config_empresa WHERE usuario_id = %s", (user_id,))
    cfg = cur.fetchone() or ("RR Smart Soluções", "95984187832", None, "A combinar", "90 dias", 7)

# --- 3. MENU SUPERIOR (TABS) ---
tab_inicio, tab_gerador, tab_precos, tab_modelos, tab_config = st.tabs([
    "🏠 Início", "📑 Gerador", "💰 Tabela de Preços", "✍️ Modelos", "⚙️ Configurações"
])

# --- ABA: INÍCIO ---
with tab_inicio:
    st.markdown("<h1 style='text-align:center; padding: 40px;'>PAINEL ADMINISTRATIVO</h1>", unsafe_allow_html=True)
    st.markdown(f"<div style='text-align:center;'><h3>Bem-vindo à {cfg[0]}</h3><p>Use o menu superior para navegar.</p></div>", unsafe_allow_html=True)

# --- ABA: GERADOR ---
with tab_gerador:
    st.header("Novo Orçamento")
    with st.container(border=True):
        c1, c2 = st.columns(2)
        cliente = c1.text_input("Nome do Cliente")
        whatsapp_cli = c2.text_input("WhatsApp Cliente", placeholder="95984...")

        plugins = registry.get_plugins()
        serv_label = st.selectbox("Tipo de Serviço", list(p.label for p in plugins.values()))
        plugin = next(p for p in plugins.values() if p.label == serv_label)
        inputs = plugin.render_fields()

        mapeamento = {"Camera": "CFTV", "Motor": "Motor de Portão", "Cerca": "Cerca/Concertina"}
        cat_atual = next((v for k, v in mapeamento.items() if k in serv_label), "Geral")
        
        df_extras = pd.read_sql("SELECT chave, nome, valor FROM precos WHERE usuario_id = %s AND (categoria = %s OR categoria = 'Geral')", conn, params=(user_id, cat_atual))
        
        lista_extras = []
        if not df_extras.empty:
            st.markdown("---")
            st.subheader(f"Itens Adicionais ({cat_atual})")
            opcoes = {f"{r['nome']} (R$ {r['valor']:.2f})": r for _, r in df_extras.iterrows()}
            selecionados = st.multiselect("Adicionar itens", list(opcoes.keys()))
            for idx, sel in enumerate(selecionados):
                q = st.number_input(f"Qtd: {opcoes[sel]['nome']}", min_value=1, key=f"ex_{idx}")
                lista_extras.append({"info": opcoes[sel], "qtd": q})

        if st.button("FINALIZAR E GERAR", use_container_width=True):
            res = plugin.compute(conn, inputs)
            for item in lista_extras:
                sub = item['qtd'] * item['info']['valor']
                res['items'].append({'desc': item['info']['nome'], 'qty': item['qtd'], 'unit': item['info']['valor'], 'sub': sub})
                res['subtotal'] += sub
            st.session_state.dados_orcamento = {"cliente": cliente, "total": res['subtotal'], "servico": serv_label}
            st.success(f"Orçamento para {cliente} calculado!")

# --- ABA: PREÇOS ---
with tab_precos:
    st.header("Gestão de Preços")
    with st.container(border=True):
        with st.form("f_precos", clear_on_submit=True):
            c1, c2, c3, c4 = st.columns([1, 2, 1, 1])
            f_ch = c1.text_input("Chave")
            f_nm = c2.text_input("Nome")
            f_vl = c3.number_input("Valor R$", min_value=0.0)
            f_ct = c4.selectbox("Categoria", ["CFTV", "Cerca/Concertina", "Motor de Portão", "Geral"])
            if st.form_submit_button("CADASTRAR"):
                with conn.cursor() as cur:
                    cur.execute("INSERT INTO precos (chave, nome, valor, usuario_id, categoria) VALUES (%s,%s,%s,%s,%s)", (f_ch, f_nm, f_vl, user_id, f_ct))
                conn.commit()
                st.rerun()
    df_lista = pd.read_sql("SELECT chave, nome, valor, categoria FROM precos WHERE usuario_id = %s", conn, params=(user_id,))
    st.data_editor(df_lista, use_container_width=True)

# --- ABA: MODELOS ---
with tab_modelos:
    st.header("Modelos de Texto")
    with st.container(border=True):
        sel_s = st.selectbox("Serviço", ["CFTV", "Cerca/Concertina", "Motor de Portão"])
        with conn.cursor() as cur:
            cur.execute("SELECT texto_detalhado FROM modelos_texto WHERE usuario_id = %s AND servico_tipo = %s", (user_id, sel_s))
            txt = cur.fetchone()
        novo_txt = st.text_area("Descrição", value=txt[0] if txt else "", height=200)
        if st.button("SALVAR TEXTO"):
            with conn.cursor() as cur:
                cur.execute("INSERT INTO modelos_texto (usuario_id, servico_tipo, texto_detalhado) VALUES (%s,%s,%s) ON CONFLICT (usuario_id, servico_tipo) DO UPDATE SET texto_detalhado = EXCLUDED.texto_detalhado", (user_id, sel_s, novo_txt))
            conn.commit()
            st.success("Salvo!")

# --- ABA: CONFIGURAÇÕES (RESOLVIDO) ---
with tab_config:
    st.header("Configurações da Empresa")
    with st.container(border=True):
        with st.form("form_cfg"):
            c_e1, c_e2 = st.columns(2)
            n_emp = c_e1.text_input("Nome da Empresa", value=cfg[0])
            w_emp = c_e2.text_input("WhatsApp", value=cfg[1])
            c_e3, c_e4 = st.columns(2)
            p_pad = c_e3.text_input("Pagamento", value=cfg[3])
            g_pad = c_e4.text_input("Garantia", value=cfg[4])
            v_pad = st.number_input("Validade (Dias)", value=cfg[5])
            if st.form_submit_button("SALVAR"):
                with conn.cursor() as cur:
                    cur.execute("UPDATE config_empresa SET nome_empresa=%s, whatsapp=%s, pagamento_padrao=%s, garantia_padrao=%s, validade_dias=%s WHERE usuario_id=%s", (n_emp, w_emp, p_pad, g_pad, v_pad, user_id))
                conn.commit()
                st.success("Atualizado!")
    if st.button("SAIR"):
        st.session_state.logged_in = False
        st.rerun()
