import streamlit as st
import pandas as pd
from core.db import get_conn

# =========================
# Configuração da Página e CSS Mágico
# =========================
st.set_page_config(page_title="Tabela de Preços", page_icon="💰", layout="wide")

st.markdown("""
<style>
    /* Estilizando os Cards modernos */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #262933 !important;
        border-radius: 12px !important;
        border: 1px solid #333845 !important;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2) !important;
        padding: 1.5rem !important;
    }
    
    /* Botões Padrão */
    .stButton > button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
    }
    
    /* Estilizando as Tabelas de Dados nativas do Streamlit */
    [data-testid="stDataFrame"] {
        border-radius: 8px !important;
        overflow: hidden !important;
        border: 1px solid #333845 !important;
    }

    /* MÁGICA: TRANSFORMA AS TABS NATIVAS EM PASTAS ORGANIZADORAS */
    [data-testid="stTabs"] > div[data-baseweb="tab-list"] {
        gap: 6px;
        border-bottom: 3px solid #3b82f6 !important; 
        padding-bottom: 0 !important;
    }
    [data-testid="stTabs"] button[role="tab"] {
        background-color: #1a1c23 !important;
        border: 1px solid #333845 !important;
        border-bottom: none !important;
        border-radius: 12px 12px 0 0 !important; 
        padding: 10px 24px !important;
        margin: 0 !important;
        opacity: 0.6;
        color: #ffffff !important;
        transition: all 0.3s ease !important;
    }
    [data-testid="stTabs"] button[role="tab"]:hover {
        opacity: 0.9;
        background-color: #262933 !important;
    }
    [data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
        background-color: #3b82f6 !important;
        border-color: #3b82f6 !important;
        opacity: 1;
        font-weight: bold !important;
    }
    [data-testid="stTabs"] [data-baseweb="tab-highlight"] {
        display: none !important;
    }
    [data-testid="stTabs"] [data-baseweb="tab-panel"] {
        padding-top: 1.5rem !important;
    }
</style>
""", unsafe_allow_html=True)


st.title("💰 Configuração de Preços")
st.write("Faça a gestão dos valores de peças e serviços da RR Smart Soluções.")

# =========================
# CARD 1: Adicionar Novo Item
# =========================
with st.container(border=True):
    st.subheader("➕ Adicionar Novo Item")
    
    with st.form("form_novo_item", clear_on_submit=True):
        col1, col2, col3 = st.columns([2, 3, 1])
        
        with col1:
            nova_chave = st.text_input("Identificador (Chave)", placeholder="Ex: cftv_cabo_rede")
        with col2:
            novo_nome = st.text_input("Nome do Item (Aparece no PDF)", placeholder="Ex: Cabo de Rede CAT5e")
        with col3:
            novo_valor = st.number_input("Valor (R$)", min_value=0.0, step=0.5, format="%.2f")
            
        btn_adicionar = st.form_submit_button("✅ Guardar Item", use_container_width=True)
        
        if btn_adicionar:
            if nova_chave and novo_nome:
                try:
                    conn = get_conn()
                    with conn.cursor() as cur:
                        cur.execute(
                            "INSERT INTO precos (chave, nome, valor) VALUES (%s, %s, %s) ON CONFLICT (chave) DO UPDATE SET nome = EXCLUDED.nome, valor = EXCLUDED.valor",
                            (nova_chave.strip(), novo_nome.strip(), novo_valor)
                        )
                    conn.commit()
                    # AQUI FOI REMOVIDO O conn.close()
                    st.success(f"Item '{novo_nome}' adicionado com sucesso!")
                    st.rerun() 
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")
            else:
                st.warning("Preencha a chave e o nome do item.")


# =========================
# Busca os dados no Banco para as Tabelas
# =========================
df = pd.DataFrame()
try:
    conn = get_conn()
    df = pd.read_sql("SELECT chave, nome, valor FROM precos ORDER BY chave", conn)
    # AQUI FOI REMOVIDO O conn.close()
except Exception as e:
    st.error(f"Erro ao carregar os preços: {e}")


# =========================
# CARD 2: Tabela de Preços
# =========================
st.write("") 
with st.container(border=True):
    st.subheader("📋 Tabela de Preços Atuais")
    st.write("Altere os valores diretamente na tabela abaixo e guarde as alterações.")
    
    if not df.empty:
        df_cftv = df[df['chave'].str.contains('cftv', case=False, na=False)].copy()
        df_cerca = df[df['chave'].str.contains('cerca|concertina|haste', case=False, na=False)].copy()
        df_motor = df[df['chave'].str.contains('motor|portao|cremalheira', case=False, na=False)].copy()
        df_outros = df[~df['chave'].isin(df_cftv['chave'].tolist() + df_cerca['chave'].tolist() + df_motor['chave'].tolist())].copy()

        aba_cftv, aba_cerca, aba_motor, aba_outros = st.tabs([
            f"📷 CFTV ({len(df_cftv)})", 
            f"⚡ Cerca/Concertina ({len(df_cerca)})", 
            f"🚪 Motor de Portão ({len(df_motor)})", 
            f"🔧 Outros ({len(df_outros)})"
        ])

        def render_editor(dataframe, categoria_nome):
            if dataframe.empty:
                st.info(f"Nenhum item encontrado para a categoria {categoria_nome}.")
                return

            edited_df = st.data_editor(
                dataframe,
                use_container_width=True,
                num_rows="dynamic", 
                column_config={
                    "chave": st.column_config.TextColumn("Chave (Não mude a menos que saiba)", disabled=True),
                    "nome": st.column_config.TextColumn("Nome do Item", required=True),
                    "valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f", min_value=0.0)
                },
                key=f"editor_{categoria_nome}"
            )

            if st.button(f"💾 Guardar alterações de {categoria_nome}", type="primary"):
                try:
                    conn = get_conn()
                    with conn.cursor() as cur:
                        for index, row in edited_df.iterrows():
                            cur.execute(
                                "UPDATE precos SET nome = %s, valor = %s WHERE chave = %s",
                                (row['nome'], row['valor'], row['chave'])
                            )
                    conn.commit()
                    # AQUI FOI REMOVIDO O conn.close()
                    st.success(f"Preços de {categoria_nome} atualizados com sucesso!")
                except Exception as e:
                    st.error(f"Erro ao atualizar o banco: {e}")

        with aba_cftv:
            render_editor(df_cftv, "CFTV")
            
        with aba_cerca:
            render_editor(df_cerca, "Cerca e Concertina")
            
        with aba_motor:
            render_editor(df_motor, "Motor de Portão")
            
        with aba_outros:
            render_editor(df_outros, "Outros Itens")

    else:
        st.warning("O seu banco de dados está vazio. Adicione um item acima.")
