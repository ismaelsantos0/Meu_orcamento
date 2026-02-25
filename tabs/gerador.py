import streamlit as st
import pandas as pd
import io
import urllib.parse
import re
from core.materials import build_materials_list
from core.pdf.summary import render_summary_pdf
import services.registry as registry

def render_gerador(conn, user_id, cfg):
    st.header("Novo Orçamento")
    
    # ==========================================
    # 1. FORMULÁRIO (Sempre Visível)
    # ==========================================
    with st.container(border=True):
        c1, c2 = st.columns(2)
        cliente = c1.text_input("Nome do Cliente")
        
        # --- PLACEHOLDER INTELIGENTE (DDD DINÂMICO) ---
        # Extrai apenas os números do telefone do instalador logado e pega os 2 primeiros (DDD)
        numero_usuario = re.sub(r'\D', '', str(cfg[1]))
        ddd_local = numero_usuario[:2] if len(numero_usuario) >= 2 else "11"
        placeholder_inteligente = f"({ddd_local}) 99999-9999"
        
        zap_cli = c2.text_input("WhatsApp do Cliente", placeholder=placeholder_inteligente)
        # ----------------------------------------------
        
        plugins = registry.get_plugins()
        servico_label = st.selectbox("Selecione o Serviço", list(p.label for p in plugins.values()))
        plugin = next(p for p in plugins.values() if p.label == servico_label)
        
        inputs = plugin.render_fields()
        
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
                res = plugin.compute(conn, inputs)
                for ex in extras_final:
                    sub_ex = ex['qtd'] * ex['info']['valor']
                    res['items'].append({'desc': ex['info']['nome'], 'qty': ex['qtd'], 'unit': ex['info']['valor'], 'sub': sub_ex})
                    res['subtotal'] += sub_ex
                
                with conn.cursor() as cur:
                    cur.execute("SELECT texto_detalhado FROM modelos_texto WHERE usuario_id = %s AND servico_tipo = %s", (user_id, cat_match))
                    t_row = cur.fetchone()
                texto_pdf = t_row[0] if t_row else "Instalação profissional padrão."
                res['summary_client'] = texto_pdf
                
                # Salva no histórico
                try:
                    with conn.cursor() as cur:
                        cur.execute("""
                            INSERT INTO historico_orcamentos (usuario_id, cliente, valor, status) 
                            VALUES (%s, %s, %s, 'Pendente')
                        """, (user_id, cliente, res['subtotal']))
                    conn.commit()
                except Exception:
                    conn.rollback() 
                
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

    # ==========================================
    # 2. RESULTADOS E DETALHAMENTO
    # ==========================================
    if st.session_state.orcamento_pronto and 'dados_finais' in st.session_state:
        st.markdown("---")
        d = st.session_state.dados_finais
        st.success(f"Orçamento calculado com sucesso para {d['cliente']}!")
        
        col_r1, col_r2, col_r3 = st.columns(3)
        
        with col_r1:
            with st.container(border=True):
                st.subheader("📄 Proposta Formal")
                st.markdown(f"<h2 style='color:#3b82f6;'>R$ {d['total']:.2
