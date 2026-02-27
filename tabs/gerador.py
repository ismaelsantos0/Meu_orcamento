import streamlit as st

def render_gerador(conn, user_id, cfg):
    # 1. RECUPERAÇÃO DE VARIÁVEIS DE CONFIGURAÇÃO
    # Busca os dados do objeto cfg, com valores padrão caso estejam vazios
    nome_loja = cfg.get("nome_loja", "Sua Empresa")
    telefone_loja = cfg.get("telefone_contato", "00 00000-0000")
    
    st.header(f"📋 Gerador de Orçamentos")
    st.caption(f"Operando como: **{nome_loja}**")

    # 2. INICIALIZAÇÃO DO SESSION STATE (Evita o AttributeError)
    if "orcamento_pronto" not in st.session_state:
        st.session_state.orcamento_pronto = False
    
    if "dados_finais" not in st.session_state:
        st.session_state.dados_finais = {}

    # 3. FORMULÁRIO DE ENTRADA DE DADOS
    with st.form("form_orcamento"):
        col1, col2 = st.columns(2)
        
        with col1:
            cliente = st.text_input("Nome do Cliente", placeholder="Ex: João Silva")
            contato_cliente = st.text_input("WhatsApp do Cliente", placeholder="(95) 9XXXX-XXXX")
        
        with col2:
            servico = st.selectbox(
                "Tipo de Instalação", 
                [
                    "Fechadura Sobrepor (Porta Madeira Nova)", 
                    "Fechadura Embutir (Porta Madeira Nova)", 
                    "Configuração Hub Wi-Fi / Automação",
                    "Manutenção Técnica"
                ]
            )
            
            # Lógica básica de preço (pode ser personalizada no banco depois)
            if "Sobrepor" in servico: valor_base = 250.0
            elif "Embutir" in servico: valor_base = 450.0
            elif "Configuração" in servico: valor_base = 150.0
            else: valor_base = 0.0

            preco = st.number_input("Valor do Serviço (R$)", value=valor_base, min_value=0.0)
        
        observacoes = st.text_area("Observações Técnicas (opcional)")
        
        btn_gerar = st.form_submit_button("Gerar Orçamento Profissional")

        if btn_gerar:
            if not cliente:
                st.error("Por favor, preencha o nome do cliente.")
            else:
                # Salva os dados no estado da sessão para persistência
                st.session_state.dados_finais = {
                    "empresa": nome_loja,
                    "telefone": telefone_loja,
                    "cliente": cliente,
                    "servico": servico,
                    "preco": preco,
                    "obs": observacoes
                }
                st.session_state.orcamento_pronto = True
                st.rerun()

    st.divider()

    # 4. EXIBIÇÃO E EXPORTAÇÃO (SÓ APARECE APÓS GERAR)
    if st.session_state.orcamento_pronto:
        d = st.session_state.dados_finais
        
        st.success("Orçamento gerado com sucesso!")
        
        # Formatação do texto para copiar e colar no WhatsApp
        texto_whatsapp = (
            f"Olá {d['cliente']}!\n\n"
            f"Segue o orçamento conforme solicitado:\n\n"
            f"*📄 ORÇAMENTO - {d['empresa']}*\n"
            f"----------------------------------\n"
            f"*Serviço:* {d['servico']}\n"
            f"*Valor Total:* R$ {d['preco']:.2f}\n"
            f"{f'*Obs:* {d['obs']}' if d['obs'] else ''}\n"
            f"----------------------------------\n"
            f"*Contato:* {d['telefone']}\n\n"
            f"Ficamos à disposição para agendamento!"
        )
        
        st.subheader("Visualização do Orçamento")
        st.info("Copie o texto abaixo para enviar ao cliente:")
        st.code(texto_whatsapp, language="text")
        
        # Botões de ação
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("🔄 Novo Orçamento"):
                st.session_state.orcamento_pronto = False
                st.session_state.dados_finais = {}
                st.rerun()
        
        with col_btn2:
            # Link direto para o WhatsApp (opcional)
            link_zap = f"https://wa.me/{d['telefone'].replace(' ', '').replace('-', '')}"
            st.link_button("Ir para o WhatsApp", link_zap)
