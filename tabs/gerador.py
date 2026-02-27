import streamlit as st

def render_gerador(conn, user_id, cfg):
    st.header("📋 Gerador de Orçamentos")

    # 1. INICIALIZAÇÃO DO ESTADO (O "pulo do gato" para evitar o erro)
    if "orcamento_pronto" not in st.session_state:
        st.session_state.orcamento_pronto = False
    
    if "dados_finais" not in st.session_state:
        st.session_state.dados_finais = {}

    # 2. FORMULÁRIO DE ENTRADA
    with st.form("form_orcamento"):
        st.subheader("Dados do Cliente e Serviço")
        cliente = st.text_input("Nome do Cliente")
        servico = st.selectbox("Tipo de Instalação", 
                              ["Fechadura Sobrepor (Madeira Nova)", 
                               "Fechadura Embutir (Madeira Nova)", 
                               "Configuração Smart/Wi-Fi"])
        
        valor_sugerido = 0.0
        if "Sobrepor" in servico: valor_sugerido = 250.0
        elif "Embutir" in servico: valor_sugerido = 450.0
        else: valor_sugerido = 100.0

        preco = st.number_input("Valor do Serviço (R$)", value=valor_sugerido)
        
        btn_gerar = st.form_submit_button("Gerar Orçamento")

        if btn_gerar:
            # Aqui definimos os dados e mudamos o estado para True
            st.session_state.dados_finais = {
                "cliente": cliente,
                "servico": servico,
                "preco": preco
            }
            st.session_state.orcamento_pronto = True
            st.rerun() # Recarrega para mostrar o resultado abaixo

    st.divider()

    # 3. EXIBIÇÃO DO RESULTADO (A linha 91 que estava dando erro)
    if st.session_state.orcamento_pronto:
        dados = st.session_state.dados_finais
        
        st.success("✅ Orçamento gerado com sucesso!")
        
        # Layout do Orçamento para o cliente
        orcamento_texto = f"""
        *ORÇAMENTO - RR SMART SOLUÇÕES*
        ------------------------------
        *Cliente:* {dados['cliente']}
        *Serviço:* {dados['servico']}
        *Total:* R$ {dados['preco']:.2f}
        ------------------------------
        *Pagamento:* PIX ou Cartão
        *Validade:* 7 dias
        """
        
        st.code(orcamento_texto, language="markdown")
        
        # Botão para limpar e fazer outro
        if st.button("Criar Novo Orçamento"):
            st.session_state.orcamento_pronto = False
            st.session_state.dados_finais = {}
            st.rerun()
