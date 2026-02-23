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

# --- TELA DE LOGIN ---
if not st.session_state.logged_in:
    # ... (Mantenha seu código de login aqui)
    st.stop()

# --- DADOS DO USUÁRIO ---
user_id = st.session_state.user_id
conn = get_conn()

# Busca configurações da empresa para usar no PDF e WhatsApp
with conn.cursor() as cur:
    cur.execute("SELECT nome_empresa, whatsapp, logo, pagamento_padrao, garantia_padrao, validade_dias FROM config_empresa WHERE usuario_id = %s", (user_id,))
    cfg = cur.fetchone() or ("RR Smart Soluções", "95984187832", None, "A combinar", "90 dias", 7)

# --- MENU SUPERIOR (TABS) ---
tab_inicio, tab_gerador, tab_precos, tab_modelos, tab_config = st.tabs([
    "🏠 Início", "📑 Gerador", "💰 Tabela de Preços", "✍️ Modelos", "⚙️ Configurações"
])

# --- ABA: GERADOR (CORRIGIDA) ---
with tab_gerador:
    st.header("Novo Orçamento")
    with st.container(border=True):
        c1, c2 = st.columns(2)
        cliente = c1.text_input("Nome do Cliente")
        whatsapp_cli = c2.text_input("WhatsApp Cliente", placeholder="95984...")

        plugins = registry.get_plugins()
        servico_label = st.selectbox("Tipo de Serviço", list(p.label for p in plugins.values()))
        plugin = next(p for p in plugins.values() if p.label == servico_label)
        
        # Renderiza os campos específicos do plugin (Cameras, Metros, etc)
        inputs = plugin.render_fields()

        # Adicionais da Tabela de Preços
        mapeamento = {"Camera": "CFTV", "Motor": "Motor de Portão", "Cerca": "Cerca/Concertina", "Concertina": "Cerca/Concertina"}
        cat_atual = next((v for k, v in mapeamento.items() if k in servico_label), "Geral")
        
        # BUSCA REAL DOS ITENS PARA O GERADOR
        df_extras = pd.read_sql("SELECT chave, nome, valor FROM precos WHERE usuario_id = %s AND (categoria = %s OR categoria = 'Geral')", conn, params=(user_id, cat_atual))
        
        lista_extras_selecionados = []
        if not df_extras.empty:
            st.markdown("---")
            st.subheader(f"Itens Adicionais ({cat_atual})")
            opcoes = {f"{r['nome']} (R$ {r['valor']:.2f})": r for _, r in df_extras.iterrows()}
            selecionados = st.multiselect("Selecione itens para somar ao orçamento", list(opcoes.keys()))
            
            if selecionados:
                col_ex = st.columns(3)
                for idx, sel in enumerate(selecionados):
                    with col_ex[idx % 3]:
                        qtd = st.number_input(f"Qtd: {opcoes[sel]['nome']}", min_value=1, key=f"extra_qtd_{idx}")
                        lista_extras_selecionados.append({"info": opcoes[sel], "qtd": qtd})

        if st.button("FINALIZAR E GERAR APRESENTAÇÃO", use_container_width=True):
            # CÁLCULO FINAL
            res = plugin.compute(conn, inputs)
            for item in lista_extras_selecionados:
                sub = item['qtd'] * item['info']['valor']
                res['items'].append({'desc': item['info']['nome'], 'qty': item['qtd'], 'unit': item['info']['valor'], 'sub': sub})
                res['subtotal'] += sub
            
            # Busca texto de benefícios
            with conn.cursor() as cur:
                cur.execute("SELECT texto_detalhado FROM modelos_texto WHERE usuario_id = %s AND servico_tipo = %s", (user_id, cat_atual))
                t_det = cur.fetchone()
                res['summary_client'] = t_det[0] if t_det else "Instalação profissional padrão."

            # Salva na sessão e envia para a visualização de resumo
            st.session_state.dados_orcamento = {
                "cliente": cliente, "whatsapp_cliente": whatsapp_cli, "servico": servico_label,
                "total": res['subtotal'], "materiais": build_materials_list(res),
                "texto_beneficios": res['summary_client'], "config_empresa": cfg,
                "payload_pdf": {
                    "logo_bytes": cfg[2], "empresa": cfg[0], "whatsapp": cfg[1], "cliente": cliente,
                    "servicos": [res], "total": res['subtotal'], "pagamento": cfg[3], "garantia": cfg[4], "validade_dias": cfg[5]
                }
            }
            # Mostra o sucesso e um botão para ver o resumo (ou redireciona)
            st.success(f"Orçamento para {cliente} calculado!")
            if st.button("VER RESUMO E ENVIAR"): st.switch_page("pages/Resumo_do_Orcamento.py")

# --- ABA: PREÇOS (CORRIGIDA) ---
with tab_precos:
    st.header("Gestão de Materiais e Preços")
    
    with st.container(border=True):
        with st.form("add_preco_novo", clear_on_submit=True):
            c1, c2, c3, c4 = st.columns([1, 2, 1, 1])
            f_ch = c1.text_input("Chave (Ex: CAM_01)")
            f_nm = c2.text_input("Nome do Produto")
            f_vl = c3.number_input("Valor Unitário R$", min_value=0.0)
            f_ct = c4.selectbox("Categoria", ["CFTV", "Cerca/Concertina", "Motor de Portão", "Geral"])
            if st.form_submit_button("SALVAR NA TABELA"):
                with conn.cursor() as cur:
                    cur.execute("INSERT INTO precos (chave, nome, valor, usuario_id, categoria) VALUES (%s,%s,%s,%s,%s)", (f_ch, f_nm, f_vl, user_id, f_ct))
                conn.commit()
                st.rerun()

    # EXIBIÇÃO DA TABELA (O que estava faltando)
    st.markdown("### Itens Cadastrados")
    sub_tabs = st.tabs(["Todos", "CFTV", "Cerca/Concertina", "Motor de Portão", "Geral"])
    categorias_lista = [None, "CFTV", "Cerca/Concertina", "Motor de Portão", "Geral"]

    for i, s_tab in enumerate(sub_tabs):
        with s_tab:
            query = "SELECT chave, nome, valor, categoria FROM precos WHERE usuario_id = %s"
            params = [user_id]
            if categorias_lista[i]:
                query += " AND categoria = %s"
                params.append(categorias_lista[i])
            
            df_lista = pd.read_sql(query, conn, params=params)
            if not df_lista.empty:
                st.data_editor(df_lista, use_container_width=True, key=f"editor_{i}")
            else:
                st.info("Nenhum item cadastrado nesta categoria.")

# --- ABA: CONFIGURAÇÕES ---
with tab_config:
    # ... (Mantenha o código de configurações que enviei antes)
