import streamlit as st

def render_configuracoes(conn, user_id, cfg):
    st.header("Configurações da Empresa")
    
    with st.container(border=True):
        c_e1, c_e2 = st.columns(2)
        n_emp = c_e1.text_input("Nome da Empresa", value=cfg[0])
        w_emp = c_e2.text_input("WhatsApp de Contato", value=cfg[1])
        
        c_e3, c_e4 = st.columns(2)
        p_pad = c_e3.text_input("Pagamento Padrão", value=cfg[3])
        g_pad = c_e4.text_input("Garantia Padrão", value=cfg[4])
        
        v_pad = st.number_input("Validade do Orçamento (Dias)", value=cfg[5], min_value=1)
        
        st.markdown("---")
        st.subheader("Identidade Visual")
        logo_file = st.file_uploader("Upload da Logo (PNG/JPG)", type=["png", "jpg", "jpeg"])
        
        if st.button("SALVAR CONFIGURAÇÕES", use_container_width=True):
            logo_bytes = logo_file.read() if logo_file else cfg[2]
            
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM config_empresa WHERE usuario_id = %s", (user_id,))
                existe_cfg = cur.fetchone()
                
                if existe_cfg:
                    cur.execute("""
                        UPDATE config_empresa 
                        SET nome_empresa=%s, whatsapp=%s, logo=%s, pagamento_padrao=%s, garantia_padrao=%s, validade_dias=%s 
                        WHERE usuario_id=%s
                    """, (n_emp, w_emp, logo_bytes, p_pad, g_pad, v_pad, user_id))
                else:
                    cur.execute("""
                        INSERT INTO config_empresa 
                        (usuario_id, nome_empresa, whatsapp, logo, pagamento_padrao, garantia_padrao, validade_dias) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (user_id, n_emp, w_emp, logo_bytes, p_pad, g_pad, v_pad))
                    
            conn.commit()
            st.success("Configurações atualizadas com sucesso!")
            st.rerun()
                
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔴 SAIR DO SISTEMA", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()
