import streamlit as st
import pandas as pd
import io
import urllib.parse
from datetime import datetime
from core.db import get_conn
from core.style import apply_vero_style
from core.materials import build_materials_list
import services.registry as registry

# Configurações de Identidade RR Smart Soluções
st.set_page_config(page_title="Vero | RR Smart Soluções", layout="wide", initial_sidebar_state="collapsed")
apply_vero_style()

# Inicialização de Estados Críticos
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'view_mode' not in st.session_state: st.session_state.view_mode = "edit"

# --- 1. TELA DE LOGIN ---
if not st.session_state.logged_in:
    # ... (Mantenha seu código de login funcional aqui)
    st.stop()

# --- 2. CONEXÃO E CONFIGURAÇÕES ---
user_id = st.session_state.user_id
conn = get_conn()

with conn.cursor() as cur:
    cur.execute("SELECT nome_empresa, whatsapp, logo, pagamento_padrao, garantia_padrao, validade_dias FROM config_empresa WHERE usuario_id = %s", (user_id,))
    cfg = cur.fetchone() or ("RR Smart Soluções", "95984187832", None, "A combinar", "90 dias", 7)

# --- 3. MENU SUPERIOR (TABS) ---
# Alinhado com o estilo visual da Navbar azul
tab_inicio, tab_gerador, tab_precos, tab_modelos, tab_config = st.tabs([
    "🏠 Início", "📑 Gerador", "💰 Tabela de Preços", "✍️ Modelos", "⚙️ Configurações"
])

# --- ABA: GERADOR (CORREÇÃO DE EXIBIÇÃO) ---
with tab_gerador:
    if st.session_state.view_mode == "result" and 'dados_orcamento' in st.session_state:
        # TELA DE RESULTADOS (PDF E WHATSAPP)
        d = st.session_state.dados_orcamento
        st.markdown(f"## ✅ Proposta: {d['cliente']}")
        
        if st.button("⬅️ VOLTAR PARA EDIÇÃO"):
            st.session_state.view_mode = "edit"
            st.rerun()

        col_res1, col_res2 = st.columns(2, gap="large")
        with col_res1:
            with st.container(border=True):
                st.markdown("### 📄 Proposta Formal")
                st.markdown(f"<h2 style='color:#3b82f6;'>Total: R$ {d['total']:.2f}</h2>", unsafe_allow_html=True)
                from core.pdf.summary import render_summary_pdf
                pdf_io = io.BytesIO()
                render_summary_pdf(pdf_io, d['payload_pdf'])
                st.download_button("📥 BAIXAR PDF", pdf_io.getvalue(), f"Orcamento_{d['cliente']}.pdf", use_container_width=True)

        with col_res2:
            with st.container(border=True):
                st.markdown("### 📱 Enviar p/ Cliente")
                msg_zap = f"*PROPOSTA: {cfg[0]}*\n\n{d['texto_beneficios']}\n\n*Investimento: R$ {d['total']:.2f}*"
                st.text_area("Texto WhatsApp:", msg_zap, height=150)
                url_zap = f"https://wa.me/{d['whatsapp_cliente']}?text={urllib.parse.quote(msg_zap)}"
                st.markdown(f'<a href="{url_zap}" target="_blank"><button style="width:100%; height:50px; border-radius:18px; background:#25d366; color:white; border:none; font-weight:700;">ENVIAR AGORA</button></a>', unsafe_allow_html=True)
    else:
        # TELA DE FORMULÁRIO (GERADOR)
        st.header("Gerador de Orçamentos")
        with st.container(border=True):
            c1, c2 = st.columns(2)
            cli = c1.text_input("Nome do Cliente", key="in_cli")
            zap_cli = c2.text_input("WhatsApp", key="in_zap", placeholder="95984...")

            plugins = registry.get_plugins()
            serv_label = st.selectbox("Serviço", list(p.label for p in plugins.values()))
            plugin = next(p for p in plugins.values() if p.label == serv_label)
            inputs = plugin.render_fields()

            # Lógica de Itens Extras
            cat_map = {"Camera": "CFTV", "Motor": "Motor de Portão", "Cerca": "Cerca/Concertina"}
            cat_match = next((v for k, v in cat_map.items() if k in serv_label), "Geral")
            
            df_extras = pd.read_sql("SELECT chave, nome, valor FROM precos WHERE usuario_id = %s AND (categoria = %s OR categoria = 'Geral')", conn, params=(user_id, cat_match))
            
            extras_final = []
            if not df_extras.empty:
                st.markdown("---")
                st.subheader(f"Adicionais: {cat_match}")
                opcoes_dict = {f"{r['nome']} (R$ {r['valor']:.2f})": r for _, r in df_extras.iterrows()}
                sel_extras = st.multiselect("Itens extras", list(opcoes_dict.keys()))
                for s_item in sel_extras:
                    q_item = st.number_input(f"Qtd: {opcoes_dict[s_item]['nome']}", min_value=1, key=f"q_{s_item}")
                    extras_final.append({"info": opcoes_dict[s_item], "qtd": q_item})

            if st.button("FINALIZAR E GERAR PDF", use_container_width=True):
                calc_res = plugin.compute(conn, inputs)
                for ex in extras_final:
                    sub_ex = ex['qtd'] * ex['info']['valor']
                    calc_res['items'].append({'desc': ex['info']['nome'], 'qty': ex['qtd'], 'unit': ex['info']['valor'], 'sub': sub_ex})
                    calc_res['subtotal'] += sub_ex
                
                with conn.cursor() as cur:
                    cur.execute("SELECT texto_detalhado FROM modelos_texto WHERE usuario_id = %s AND servico_tipo = %s", (user_id, cat_match))
                    t_row = cur.fetchone()
                
                st.session_state.dados_orcamento = {
                    "cliente": cli, "whatsapp_cliente": zap_cli, "total": calc_res['subtotal'],
                    "materiais": build_materials_list(calc_res), "texto_beneficios": t_row[0] if t_row else "Instalação profissional.",
                    "payload_pdf": {
                        "logo_bytes": cfg[2], "empresa": cfg[0], "whatsapp": cfg[1], "cliente": cli,
                        "servicos": [calc_res], "total": calc_res['subtotal'], "pagamento": cfg[3], "garantia": cfg[4], "validade_dias": cfg[5]
                    }
                }
                st.session_state.view_mode = "result"
                st.rerun()

# --- ABA: PREÇOS (RESTAURAÇÃO COMPLETA) ---
with tab_precos:
    st.header("Tabela de Preços")
    with st.container(border=True):
        with st.form("form_novo_item", clear_on_submit=True):
            c_p1, c_p2, c_p3, c_p4 = st.columns([1, 2, 1, 1])
            p_ch = c_p1.text_input("Chave")
            p_nm = c_p2.text_input("Nome Produto")
            p_vl = c_p3.number_input("Preço R$", min_value=0.0)
            p_ct = c_p4.selectbox("Categoria", ["CFTV", "Cerca/Concertina", "Motor de Portão", "Geral"])
            if st.form_submit_button("CADASTRAR ITEM"):
                with conn.cursor() as cur:
                    cur.execute("INSERT INTO precos (chave, nome, valor, usuario_id, categoria) VALUES (%s,%s,%s,%s,%s)", (p_ch, p_nm, p_vl, user_id, p_ct))
                conn.commit()
                st.rerun()

    # Exibição Real dos Dados
    df_full = pd.read_sql("SELECT chave, nome, valor, categoria FROM precos WHERE usuario_id = %s", conn, params=(user_id,))
    if not df_full.empty:
        st.data_editor(df_full, use_container_width=True, key="main_table_editor")
    else:
        st.info("Sua tabela de preços está vazia.")

# --- ABA: CONFIGURAÇÕES (RESTAURADA) ---
with tab_config:
    st.header("Personalização da Empresa")
    with st.container(border=True):
        with st.form("form_cfg_final"):
            col_c1, col_c2 = st.columns(2)
            n_emp = col_c1.text_input("Nome Empresa", value=cfg[0])
            w_emp = col_c2.text_input("WhatsApp", value=cfg[1])
            c_val = st.number_input("Validade Orçamento (Dias)", value=cfg[5])
            if st.form_submit_button("SALVAR CONFIGURAÇÕES"):
                with conn.cursor() as cur:
                    cur.execute("UPDATE config_empresa SET nome_empresa=%s, whatsapp=%s, validade_dias=%s WHERE usuario_id=%s", (n_emp, w_emp, c_val, user_id))
                conn.commit()
                st.success("Configurações atualizadas!")
                st.rerun()
    if st.button("🔴 SAIR DO SISTEMA"):
        st.session_state.logged_in = False
        st.rerun()
