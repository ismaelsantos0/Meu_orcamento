import streamlit as st
import pandas as pd
import time

def render_precos(conn, user_id):
    st.header("Gestão de Preços")
    
    # 1. BLOCO DE ADICIONAR / ATUALIZAR
    with st.container(border=True):
        st.write("Cadastre um novo item ou digite o nome de um já existente para atualizar o seu valor.")
        
        c_p1, c_p2, c_p3 = st.columns([2, 1, 1])
        p_nm = c_p1.text_input("Nome do Produto (Ex: Câmera IP 1080p)", key="k_nome")
        p_vl = c_p2.number_input("Preço R$", min_value=0.0, key="k_preco")
        p_ct = c_p3.selectbox("Categoria", ["CFTV", "Cerca/Concertina", "Motor de Portão", "Geral"], key="k_cat")
        
        if st.button("SALVAR ITEM", use_container_width=True):
            if p_nm:
                with conn.cursor() as cur:
                    cur.execute("SELECT chave FROM precos WHERE nome = %s AND usuario_id = %s", (p_nm, user_id))
                    existe_produto = cur.fetchone()
                    
                    if existe_produto:
                        chave_existente = existe_produto[0]
                        cur.execute("""
                            UPDATE precos 
                            SET valor = %s, categoria = %s 
                            WHERE chave = %s AND usuario_id = %s
                        """, (p_vl, p_ct, chave_existente, user_id))
                        msg = f"✅ Preço do item '{p_nm}' atualizado!"
                    else:
                        chave_automatica = f"ITEM_{int(time.time())}"
                        cur.execute("""
                            INSERT INTO precos (chave, nome, valor, usuario_id, categoria) 
                            VALUES (%s, %s, %s, %s, %s)
                        """, (chave_automatica, p_nm, p_vl, user_id, p_ct))
                        msg = f"✅ Novo item '{p_nm}' adicionado com sucesso!"
                        
                conn.commit()
                st.success(msg)
                st.rerun()
            else:
                st.warning("⚠️ Por favor, preencha o nome do produto.")

    # 2. BLOCO DE EXCLUIR ITEM
    with st.expander("🗑️ Excluir um Produto"):
        st.write("Selecione um produto abaixo para removê-lo permanentemente.")
        
        with conn.cursor() as cur:
            cur.execute("SELECT nome FROM precos WHERE usuario_id = %s ORDER BY nome ASC", (user_id,))
            lista_produtos = [row[0] for row in cur.fetchall()]
        
        if lista_produtos:
            col_del1, col_del2 = st.columns([3, 1])
            item_para_excluir = col_del1.selectbox("Produto a excluir", [""] + lista_produtos)
            
            st.markdown("<br>", unsafe_allow_html=True)
            if col_del2.button("❌ EXCLUIR", use_container_width=True):
                if item_para_excluir:
                    with conn.cursor() as cur:
                        cur.execute("DELETE FROM precos WHERE nome = %s AND usuario_id = %s", (item_para_excluir, user_id))
                    conn.commit()
                    st.success(f"O produto '{item_para_excluir}' foi removido com sucesso!")
                    st.rerun()
                else:
                    st.warning("Selecione um produto na lista primeiro.")
        else:
            st.info("Não há produtos registrados para excluir.")

    st.markdown("---")
    st.markdown("### Itens Registrados")
    
    sub_tabs = st.tabs(["Todos", "CFTV", "Cerca/Concertina", "Motor de Portão", "Geral"])
    cats = [None, "CFTV", "Cerca/Concertina", "Motor de Portão", "Geral"]
    
    for i, t_name in enumerate(sub_tabs):
        with t_name:
            query = "SELECT nome as \"Produto\", valor as \"Preço (R$)\", categoria as \"Categoria\" FROM precos WHERE usuario_id = %s"
            params = [user_id]
            if cats[i]:
                query += " AND categoria = %s"
                params.append(cats[i])
            
            query += " ORDER BY nome ASC"
            df_lista = pd.read_sql(query, conn, params=params)
            
            if not df_lista.empty:
                st.dataframe(df_lista, use_container_width=True, hide_index=True)
            else:
                st.info("Nenhum item registrado nesta categoria.")
