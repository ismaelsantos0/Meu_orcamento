import streamlit as st

def render_modelos(conn, user_id):
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
                cur.execute("SELECT id FROM modelos_texto WHERE usuario_id = %s AND servico_tipo = %s", (user_id, sel_serv))
                existe_modelo = cur.fetchone()
                
                if existe_modelo:
                    cur.execute("UPDATE modelos_texto SET texto_detalhado = %s WHERE usuario_id = %s AND servico_tipo = %s", (novo_txt, user_id, sel_serv))
                else:
                    cur.execute("INSERT INTO modelos_texto (usuario_id, servico_tipo, texto_detalhado) VALUES (%s, %s, %s)", (user_id, sel_serv, novo_txt))
            conn.commit()
            st.success("Texto salvo com sucesso!")
