import streamlit as st
import pandas as pd
import io
import urllib.parse
import re
from core.db import get_price
from core.materials import build_materials_list
from core.pdf.summary import render_summary_pdf
import services.registry as registry

def render_gerador(conn, user_id, cfg):
    st.header("📋 Gerador de Orçamentos Profissionais")
    
    # 1. INICIALIZAÇÃO DO SESSION STATE
    if "orcamento_pronto" not in st.session_state:
        st.session_state.orcamento_pronto = False
    if "dados_finais" not in st.session_state:
        st.session_state.dados_finais = {}

    # 2. FORMULÁRIO DE ENTRADA (Sempre visível para facilitar edição rápida)
    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            cliente = st.text_input("Nome do Cliente", placeholder="Ex: João Silva")
            zap_cli = st.text_input("WhatsApp do Cliente", placeholder="(95) 9XXXX-XXXX")
        
        with col2:
            # Puxa os plugins registrados (Câmeras, Cerca, Concertina, etc.)
            plugins = registry.get_plugins()
            servico_label = st.selectbox("Selecione o Serviço", list(p.label for p in plugins.values()))
            plugin = next(p for p in plugins.values() if p.label == servico_label)
        
        # Renderiza os campos específicos do serviço escolhido
        inputs = plugin.render_fields()
        
        # Mapeamento para categorias
        cat_map = {"Camera": "CFTV", "Motor": "Motor de Portão", "Cerca": "Cerca/Concertina", "Concertina": "Cerca/Concertina"}
        cat_match = next((v for k, v in cat_map.items() if k in servico_label), "Geral")
        
        # Busca itens extras
        df_extras = pd.read_sql("SELECT chave, nome, valor FROM precos WHERE usuario_id = %s AND (categoria = %s OR categoria = 'Geral')", conn, params=(user_id, cat_match))
        extras_final = []
        
        if not df_extras.empty:
            st.markdown("---")
            st.subheader(f"Adicionais Extras ({cat_match})")
            opcoes_dict = {f"{r['nome']} (R$ {r['valor']:.2f})": r for _, r in df_extras.iterrows()}
            sel_extras = st.multiselect("Selecione itens extras (opcional)", list(opcoes_dict.keys()))
            for s_item in sel_extras:
                q_item = st.number_input(f"Qtd: {opcoes_dict[s_item]['nome']}", min_value=1, key=f"q_{s_item}")
                extras_final.append({"info": opcoes_dict[s_item], "qtd": q_item})
        
        if st.button("CALCULAR E FINALIZAR PROPOSTA", use_container_width=True):
            if not cliente:
                st.error("Por favor, preencha o nome do cliente.")
            else:
                # Executa o cálculo usando os IDs FIXOS do banco
                res = plugin.compute(conn, inputs)
                
                # Soma os extras
                for ex in extras_final:
                    sub_ex = ex['qtd'] * ex['info']['valor']
                    res['items'].append({'desc': ex['info']['nome'], 'qty': ex['qtd'], 'unit': ex['info']['valor'], 'sub': sub_ex})
                    res['subtotal'] += sub_ex
                
                # Busca texto de benefícios
                with conn.cursor() as cur:
                    cur.execute("SELECT texto_detalhado FROM modelos_texto WHERE usuario_id = %s AND servico_tipo = %s", (user_id, cat_match))
                    t_row = cur.fetchone()
                texto_pdf = t_row[0] if t_row else "Instalação profissional com garantia."
                
                # Salva no histórico
                try:
                    with conn.cursor() as cur:
                        cur.execute("""
                            INSERT INTO historico_orcamentos (usuario_id, cliente, valor, status) 
                            VALUES (%s, %s, %s, 'Pendente')
                        """, (user_id, cliente, res['subtotal']))
                except Exception:
                    conn.rollback() 
                
                # Prepara dados para exibição
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

    # 3. EXIBIÇÃO DOS RESULTADOS
    if st.session_state.orcamento_pronto and st.session_state.dados_finais:
        st.divider()
        d = st.session_state.dados_finais
        
        col_r1, col_r2, col_r3 = st.columns(3)
        
        with col_r1:
            with st.container(border=True):
                st.subheader("📄 PDF Profissional")
                st.markdown(f"<h2 style='color:#3b82f6;'>R$ {d['total']:.2f}</h2>", unsafe_allow_html=True)
                pdf_io = io.BytesIO()
                render_summary_pdf(pdf_io, d['payload_pdf'])
                st.download_button("📥 BAIXAR PROPOSTA", pdf_io.getvalue(), f"Orcamento_{d['cliente']}.pdf", use_container_width=True)

        with col_r2:
            with st.container(border=True):
                st.subheader("📱 WhatsApp")
                msg_zap = f"*ORÇAMENTO: {cfg[0]}*\n\nOlá {d['cliente']}!\n{d['texto_beneficios']}\n\n*Total: R$ {d['total']:.2f}*"
                st.text_area("Prévia do texto:", msg_zap, height=120)
                
                zap_limpo = re.sub(r'\D', '', d['whatsapp_cliente'])
                if len(zap_limpo) >= 10 and not zap_limpo.startswith('55'): zap_limpo = '55' + zap_limpo
                
                url_zap = f"https://wa.me/{zap_limpo}?text={urllib.parse.quote(msg_zap)}"
                st.markdown(f'<a href="{url_zap}" target="_blank"><button style="width:100%; height:45px; border-radius:10px; background:#25d366; color:white; border:none; font-weight:700; cursor:pointer;">ENVIAR PARA CLIENTE</button></a>', unsafe_allow_html=True)
                
        with col_r3:
            with st.container(border=True):
                st.subheader("📦 Lista de Materiais")
                lista_txt = "\n".join([f"• {m['qty']}x {m['desc']}" for m in d['materiais']])
                st.text_area("Para fornecedor:", lista_txt, height=120)
                st.download_button("💾 SALVAR TXT", lista_txt, "lista_materiais.txt", use_container_width=True)

        if st.button("🔄 Limpar e Novo Orçamento"):
            st.session_state.orcamento_pronto = False
            st.session_state.dados_finais = {}
            st.rerun()
