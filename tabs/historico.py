import streamlit as st
import pandas as pd

def rodar_automacoes_funil(conn, user_id):
    """Muda Pendente > Reprovado após 10 dias. Deleta Reprovados após 10 dias."""
    with conn.cursor() as cur:
        # 1. Vence orçamentos pendentes antigos
        cur.execute("""
            UPDATE historico_orcamentos 
            SET status = 'Reprovado', data_atualizacao = CURRENT_TIMESTAMP 
            WHERE status = 'Pendente' AND usuario_id = %s 
            AND data_criacao <= CURRENT_TIMESTAMP - INTERVAL '10 days'
        """, (user_id,))
        
        # 2. Limpa a lixeira (deleta reprovados há mais de 10 dias)
        cur.execute("""
            DELETE FROM historico_orcamentos 
            WHERE status = 'Reprovado' AND usuario_id = %s 
            AND data_atualizacao <= CURRENT_TIMESTAMP - INTERVAL '10 days'
        """, (user_id,))
    conn.commit()

def render_historico(conn, user_id):
    st.header("📊 Funil de Vendas e Histórico")
    
    # 1. BOTÃO DE SETUP (CRIA A TABELA NO BANCO)
    with st.expander("🛠️ Setup Inicial (Clique apenas na primeira vez)", expanded=False):
        st.write("Cria a estrutura no banco de dados para salvar os orçamentos.")
        if st.button("Criar Tabela de Histórico", use_container_width=True):
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS historico_orcamentos (
                        id SERIAL PRIMARY KEY,
                        usuario_id INTEGER,
                        cliente VARCHAR(255),
                        valor NUMERIC(10, 2),
                        status VARCHAR(50) DEFAULT 'Pendente',
                        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
            conn.commit()
            st.success("Tabela criada com sucesso! O histórico já está funcionando.")
            st.rerun()

    # Tenta carregar os dados. Se a tabela não existir, avisa o usuário.
    try:
        # Roda as regras de 10 dias de forma invisível
        rodar_automacoes_funil(conn, user_id)
        
        # Busca os orçamentos
        df = pd.read_sql("""
            SELECT id, cliente as "Cliente", valor as "Valor (R$)", status as "Status", 
                   TO_CHAR(data_criacao, 'DD/MM/YYYY') as "Data"
            FROM historico_orcamentos 
            WHERE usuario_id = %s 
            ORDER BY data_criacao DESC
        """, conn, params=(user_id,))
    except Exception as e:
        st.warning("⚠️ O sistema não encontrou a tabela de histórico. Abra o menu 'Setup Inicial' acima e crie a tabela.")
        return
    
    if df.empty:
        st.info("Nenhum orçamento gerado ainda. Crie sua primeira proposta na aba Gerador!")
        return

    # --- MÉTRICAS DE DASHBOARD ---
    aprovados = df[df['Status'] == 'Aprovado']['Valor (R$)'].sum()
    pendentes = df[df['Status'] == 'Pendente']['Valor (R$)'].sum()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Faturamento (Aprovados)", f"R$ {aprovados:,.2f}")
    col2.metric("⏳ Em Negociação (Pendentes)", f"R$ {pendentes:,.2f}")
    col3.metric("📝 Total de Propostas", len(df))
    
    st.markdown("---")
    st.subheader("Alterar Status Manualmente")
    
    # Interface para alterar o status
    with st.container(border=True):
        c_sel1, c_sel2, c_sel3 = st.columns([2, 1, 1])
        opcoes = {f"{row['Cliente']} - R$ {row['Valor (R$)']}": row['id'] for _, row in df.iterrows()}
        
        orcamento_selecionado = c_sel1.selectbox("Selecione o Orçamento", list(opcoes.keys()))
        novo_status = c_sel2.selectbox("Novo Status", ["Aprovado", "Pendente", "Reprovado"])
        
        st.markdown("<br>", unsafe_allow_html=True)
        if c_sel3.button("SALVAR STATUS", use_container_width=True):
            id_orc = opcoes[orcamento_selecionado]
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE historico_orcamentos 
                    SET status = %s, data_atualizacao = CURRENT_TIMESTAMP 
                    WHERE id = %s AND usuario_id = %s
                """, (novo_status, id_orc, user_id))
            conn.commit()
            st.success("Status atualizado!")
            st.rerun()

    # --- TABELA DE VISUALIZAÇÃO GERAL ---
    st.markdown("### Lista Completa")
    def colorir_status(val):
        color = '#25d366' if val == 'Aprovado' else '#ff4b4b' if val == 'Reprovado' else '#f5b041'
        return f'color: {color}; font-weight: bold;'
    
    st.dataframe(df.style.map(colorir_status, subset=['Status']), use_container_width=True, hide_index=True)
