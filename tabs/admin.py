import streamlit as st
import time

# Configure o seu e-mail de administrador aqui
EMAIL_ADMIN = "ismaelifrr@gmail.com"

def render_admin(conn, user_id):
    # Busca o e-mail do usuário logado no banco de dados
    with conn.cursor() as cur:
        cur.execute("SELECT email FROM usuarios WHERE id = %s", (user_id,))
        user_record = cur.fetchone()
        
    email_logado = user_record[0] if user_record else ""

    # Trava de segurança: Se não for o seu e-mail, bloqueia a tela.
    if email_logado != EMAIL_ADMIN:
        st.warning("⚠️ Acesso Restrito. Esta área é exclusiva para a administração da plataforma.")
        return

    # Se for você, renderiza o painel
    st.header("👑 Painel do Administrador")
    st.markdown("---")
    
    st.subheader("🛠️ Manutenção do Banco de Dados")
    with st.container(border=True):
        st.error("⚠️ ZONA DE PERIGO: As ações abaixo afetam a base de dados de TODOS os usuários do sistema.")
        st.write("Utilize o botão abaixo para forçar a limpeza da tabela de preços. Isso fará com que o sistema injete o Catálogo Mestre atualizado na próxima vez que cada usuário logar.")
        
        if st.button("🚨 RESETAR TABELA DE PREÇOS (TODOS OS USUÁRIOS)", type="primary"):
            with conn.cursor() as cur:
                cur.execute("DELETE FROM precos")
            conn.commit()
            st.success("Tabela de preços limpa com sucesso! O novo catálogo será injetado nos perfis.")
            time.sleep(3)
            st.rerun()
