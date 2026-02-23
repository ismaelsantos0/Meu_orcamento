import streamlit as st

# 1. CONFIGURAÇÃO OBRIGATÓRIA (SEMPRE A PRIMEIRA LINHA)
st.set_page_config(page_title="Vero | RR Smart Soluções", layout="wide", initial_sidebar_state="collapsed")

import pandas as pd
import io
import urllib.parse
from core.db import get_conn
from core.style import apply_vero_style
from core.materials import build_materials_list
import services.registry as registry

# 2. APLICA ESTILO (Certifique-se que o seu core/style.py está com aquele visual escuro seguro que mandei antes)
apply_vero_style()

if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'orcamento_pronto' not in st.session_state: st.session_state.orcamento_pronto = False

# 3. TELA DE LOGIN
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

# 4. CARREGAMENTO DE DADOS GERAIS
user_id = st.session_state.user_id
conn = get_conn()

with conn.cursor() as cur:
    cur.execute("SELECT nome_empresa, whatsapp, logo, pagamento_padrao, garantia_padrao, validade_dias FROM config_empresa WHERE usuario_id = %s", (user_id,))
    cfg = cur.fetchone() or ("RR Smart Soluções", "95984187832", None, "A combinar", "90 dias", 7)

# 5. MENU SUPERIOR
tab_gerador, tab_precos, tab_modelos, tab_config = st.tabs([
    "📑 Gerador de Orçamento", "💰 Tabela de Preços", "✍️ Modelos de Texto", "⚙️ Configurações"
])

# ==========================================
# ABA 1: GERADOR DE ORÇAMENTOS E RESULTADOS
# ==========================================
with tab_gerador:
    if st.session_state.orcamento_pronto and 'dados_finais' in st.session_state:
        # --- TELA DE RESULTADO ---
        d = st.session_state.dados_finais
        st.success(f"Orçamento calculado com sucesso para {d['cliente']}!")
        
        if st.button("⬅️ VOLTAR E CRIAR NOVO ORÇAMENTO"):
            st.session_state.orcamento_pronto = False
            st.rerun()

        col_r1, col_r2, col_r3 = st.columns(3)
        
        with col_r1:
            with st.container(border=True):
                st.subheader("📄 Proposta Formal")
                st.markdown(f"<h2 style='color:#3b82f6;'>R$ {d['total']:.2f}</h2>", unsafe_allow_html=True)
                from core.pdf.summary import render_summary_pdf
                pdf_io = io.BytesIO()
                render_summary_pdf(pdf_io, d['payload_pdf'])
                st.download_button("📥 BAIXAR PDF", pdf_io.getvalue(), f"Orcamento_{d['cliente']}.pdf", use_container_width=True)

        with col_r2:
            with st.container(border=True):
                st.subheader("📱 WhatsApp Cliente")
                msg_zap = f"*PROPOSTA: {cfg[0]}*\n\n{d['texto_beneficios']}\n\n*Total: R$ {d['total']:.2f}*"
                st.text_area("Prévia:", msg_zap, height=120)
                url_zap = f"https://wa.me/{d['whatsapp_cliente']}?text={urllib.parse.quote(msg_zap)}"
                st.markdown(f'<a href="{url_zap}" target="_blank"><button style="width:100%; height:45px; border-radius:10px; background:#25d366; color:white; border:none; font-weight:700;">ENVIAR WHATSAPP</button></a>', unsafe_allow_html=True)
                
        with col_r3:
            with st.container(border=True):
                st.subheader("📦 Lista Fornecedor")
                lista_txt = "\n".join([f"• {m['qty']}x {m['desc']}" for m in d['materiais']])
                st.text_area("Materiais:", lista_txt, height=120)
                st.download_button("💾 BAIXAR LISTA .TXT", lista_txt, "pedido_fornecedor.txt", use_container_width=True)

    else:
        # --- TELA DE FORMULÁRIO ---
        st.header("Novo Orçamento")
        with st.container(border=True):
            c1, c2 = st.columns(2)
            cliente = c1.text_input("Nome do Cliente")
            zap_cli = c2.text_input("WhatsApp do Cliente", placeholder="95984...")
            
            plugins = registry.get_plugins()
            # CORREÇÃO: Mostrando o NOME (label) em vez do ID
            servico_label = st.selectbox("Selecione o Serviço", list(p.label for p in plugins.values()))
            plugin = next(p for p in plugins.values() if p.label == servico_label)
            
            inputs = plugin.render_fields()
            
            # Adicionais da Tabela de Preços
            cat_map = {"Camera": "CFTV", "Motor": "Motor de Portão", "Cerca": "Cerca/Concertina", "Concertina": "Cerca/Concertina"}
            cat_match = next((v for k, v in cat_map.items() if k in servico_label), "Geral")
            
            df_extras = pd.read_sql("SELECT chave, nome, valor FROM precos WHERE usuario_id = %s AND (categoria = %s OR categoria = 'Geral')", conn, params=(user_id, cat_match))
            extras_final = []
            
            if not df_extras.empty:
                st.markdown("---")
                st.subheader(f"Adicionais Extras ({cat_match})")
                opcoes_dict = {f"{r['nome']} (R$ {r['valor']:.2f})": r for _, r in df_extras.iterrows()}
                sel_extras = st.multiselect("Selecione itens extras", list(opcoes_dict.keys()))
                for s_item in sel_extras:
                    q_item = st.number_input(f"Qtd: {opcoes_dict[s_item]['nome']}", min_value=1, key=f"q_{s_item}")
                    extras_final.append({"info": opcoes_dict[s_item], "qtd": q_item})
            
            if st.button("CALCULAR E FINALIZAR PROPOSTA", use_container_width=True):
                if not cliente:
                    st.warning("Por favor, preencha o nome do cliente.")
                else:
                    # 1. Calcula itens do plugin e extras
                    res = plugin.compute(conn, inputs)
                    for ex in extras_final:
                        sub_ex = ex['qtd'] * ex['info']['valor']
                        res['items'].append({'desc': ex['info']['nome'], 'qty': ex['qtd'], 'unit': ex['info']['valor'], 'sub': sub_ex})
                        res['subtotal'] += sub_ex
                    
                    # 2. CORREÇÃO: Busca o texto detalhado correspondente ao serviço escolhido
                    with conn.cursor() as cur:
                        cur.execute("SELECT texto_detalhado FROM modelos_texto WHERE usuario_id = %s AND servico_tipo = %s", (user_id, cat_match))
                        t_row = cur.fetchone()
                    texto_pdf = t_row[0] if t_row else "Instalação profissional padrão."
                    res['summary_client'] = texto_pdf
                    
                    # 3. Salva os dados para a tela de resultado
                    st.session_state.dados_finais = {
                        "cliente": cliente, 
                        "whatsapp_cliente": zap_cli, 
                        "total": res['subtotal'],
                        "materiais": build_materials_list(res), 
                        "texto_beneficios": texto_pdf,
                        "payload_pdf": {
                            "logo_bytes": cfg[2], "empresa": cfg[0], "whatsapp": cfg[1], "cliente": cliente,
                            "servicos": [res], "total": res['subtotal'], "pagamento": cfg[3], "garantia": cfg[4], "validade_dias": cfg[5]
                        }
                    }
                    st.session_state.orcamento_pronto = True
                    st.rerun()

# ==========================================
# ABA 2: TABELA DE PREÇOS (RESTAURADA)
# ==========================================
with tab_precos:
    st.header("Gestão de Preços")
    with st.container(border=True):
        with st.form("form_novo_item", clear_on_submit=True):
            c_p1, c_p2, c_p3, c_p4 = st.columns([1, 2, 1, 1])
            p_ch = c_p1.text_input("Chave (Ex: CAM_01)")
            p_nm = c_p2.text_input("Nome Produto")
            p_vl = c_p3.number_input("Preço R$", min_value=0.0)
            p_ct = c_p4.selectbox("Categoria", ["CFTV", "Cerca/Concertina", "Motor de Portão", "Geral"])
            if st.form_submit_button("CADASTRAR ITEM"):
                with conn.cursor() as cur:
                    cur.execute("INSERT INTO precos (chave, nome, valor, usuario_id, categoria) VALUES (%s,%s,%s,%s,%s)", (p_ch, p_nm, p_vl, user_id, p_ct))
                conn.commit()
                st.rerun()

    st.markdown("### Itens Cadastrados")
    # CORREÇÃO: Restauração das Abas por Categoria
    sub_tabs = st.tabs(["Todos", "CFTV", "Cerca/Concertina", "Motor de Portão", "Geral"])
    cats = [None, "CFTV", "Cerca/Concertina", "Motor de Portão", "Geral"]
    
    for i, t_name in enumerate(sub_tabs):
        with t_name:
            query = "SELECT chave, nome, valor, categoria FROM precos WHERE usuario_id = %s"
            params = [user_id]
            if cats[i]:
                query += " AND categoria = %s"
                params.append(cats[i])
            df_lista = pd.read_sql(query, conn, params=params)
            if not df_lista.empty:
                st.data_editor(df_lista, use_container_width=True, key=f"editor_{i}")
            else:
                st.info("Nenhum item cadastrado nesta categoria.")

# ==========================================
# ABA 3: MODELOS DE TEXTO (RESTAURADA)
# ==========================================
with tab_modelos:
    st.header("Modelos de Proposta PDF")
    with st.container(border=True):
        sel_serv = st.selectbox("Escolha a Categoria do Serviço", ["CFTV", "Cerca/Concertina", "Motor de Portão", "Geral"])
        
        with conn.cursor() as cur:
            cur.execute("SELECT texto_detalhado FROM modelos_texto WHERE usuario_id = %s AND servico_tipo = %s", (user_id, sel_serv))
            res_txt = cur.fetchone()
        
        txt_atual = res_txt[0] if res_txt else ""
        novo_txt = st.text_area("Descrição detalhada (Benefícios que vão para o PDF)", value=txt_atual, height=250)
        
        if st.button("SALVAR MODELO DE TEXTO"):
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO modelos_texto (usuario_id, servico_tipo, texto_detalhado) 
                    VALUES (%s, %s, %s) ON CONFLICT (usuario_id, servico_tipo) 
                    DO UPDATE SET texto_detalhado = EXCLUDED.texto_detalhado
                """, (user_id, sel_serv, novo_txt))
            conn.commit()
            st.success("Texto salvo! Ele aparecerá nos próximos orçamentos desta categoria.")

# ==========================================
# ABA 4: CONFIGURAÇÕES (RESTAURADA)
# ==========================================
with tab_config:
    st.header("Configurações da Empresa")
    with st.container(border=True):
        with st.form("form_cfg_completo"):
            c_e1, c_e2 = st.columns(2)
            n_emp = c_e1.text_input("Nome da Empresa", value=cfg[0])
            w_emp = c_e2.text_input("WhatsApp de Contato", value=cfg[1])
            
            c_e3, c_e4 = st.columns(2)
            p_pad = c_e3.text_input("Pagamento Padrão", value=cfg[3])
            g_pad = c_e4.text_input("Garantia Padrão", value=cfg[4])
            
            v_pad = st.number_input("Validade do Orçamento (Dias)", value=cfg[5], min_value=1)
            
            if st.form_submit_button("SALVAR CONFIGURAÇÕES", use_container_width=True):
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE config_empresa 
                        SET nome_empresa=%s, whatsapp=%s, pagamento_padrao=%s, garantia_padrao=%s, validade_dias=%s 
                        WHERE usuario_id=%s
                    """, (n_emp, w_emp, p_pad, g_pad, v_pad, user_id))
                conn.commit()
                st.success("Configurações atualizadas com sucesso!")
                st.rerun()
                
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔴 SAIR DO SISTEMA", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()
