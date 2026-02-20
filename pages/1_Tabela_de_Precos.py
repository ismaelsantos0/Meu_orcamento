import streamlit as st
import pandas as pd
from core.db import get_conn

st.set_page_config(page_title="Tabela de Preços", page_icon="💰", layout="wide")
st.title("💰 Configuração de Preços")

# =========================
# Conexão DB
# =========================
try:
    conn = get_conn()
except Exception as e:
    st.error(f"Falha ao conectar no banco de dados: {e}")
    st.stop()

# =========================
# Migração / Setup do Banco
# =========================
def upgrade_database():
    """Garante que a tabela existe e cria a coluna de categoria."""
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS precos (
                    chave VARCHAR(100) PRIMARY KEY,
                    valor NUMERIC(10, 2) NOT NULL
                );
            """)
            cur.execute("""
                ALTER TABLE precos ADD COLUMN IF NOT EXISTS categoria VARCHAR(50) DEFAULT 'Outros';
            """)
            cur.execute("UPDATE precos SET categoria = 'CFTV' WHERE chave LIKE '%cftv%';")
            cur.execute("UPDATE precos SET categoria = 'Motor de Portão' WHERE chave LIKE 'mao_motor%';")
            cur.execute("""
                UPDATE precos SET categoria = 'Cerca/Concertina' 
                WHERE chave LIKE 'haste%' OR chave LIKE 'mao_cerca%' OR chave LIKE 'mao_linear%' 
                OR chave LIKE 'mao_concertina%' OR chave LIKE 'concertina%' OR chave LIKE 'fio%'
                OR chave IN ('central_sh1800', 'bateria', 'sirene', 'kit_isoladores', 'cabo_alta_50m', 'kit_placas', 'kit_aterramento');
            """)
    except Exception as e:
        conn.rollback()
        st.error(f"Erro ao preparar o banco: {e}")

upgrade_database()

# =========================
# Adicionar Novo Item
# =========================
categorias_disponiveis = ["CFTV", "Cerca/Concertina", "Motor de Portão", "Outros"]

with st.expander("➕ Adicionar Novo Item de Serviço", expanded=False):
    st.info("Lembre-se: Após adicionar um item aqui, você precisará editar o código em `services/` para que o sistema saiba quando cobrar este item.")
    with st.form("form_novo_item", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            nova_chave = st.text_input("Chave do Item (ex: cftv_cabo_rede)", placeholder="sem_espacos_ou_acentos")
        with col2:
            novo_valor = st.number_input("Valor Unitário (R$)", min_value=0.0, step=0.5, format="%.2f")
        with col3:
            nova_categoria = st.selectbox("Categoria", categorias_disponiveis)
        
        submit_novo = st.form_submit_button("Salvar Novo Item", type="primary")
        
        if submit_novo:
            if not nova_chave.strip():
                st.warning("A chave do item não pode estar vazia.")
            else:
                try:
                    chave_limpa = nova_chave.strip().lower().replace(" ", "_")
                    with conn.cursor() as cur:
                        cur.execute(
                            "INSERT INTO precos (chave, valor, categoria) VALUES (%s, %s, %s) ON CONFLICT (chave) DO NOTHING",
                            (chave_limpa, novo_valor, nova_categoria)
                        )
                    st.success(f"Item '{chave_limpa}' adicionado com sucesso!")
                    st.rerun()
                except Exception as e:
                    conn.rollback()
                    st.error(f"Erro ao adicionar item: {e}")

# =========================
# Busca os dados atuais
# =========================
df = pd.DataFrame()
try:
    with conn.cursor() as cur:
        cur.execute("SELECT chave, valor, categoria FROM precos ORDER BY chave")
        rows = cur.fetchall()
        if rows:
            # AQUI ESTÁ A CORREÇÃO: Forçamos o Pandas a saber o nome das colunas!
            df = pd.DataFrame(rows, columns=["chave", "valor", "categoria"])
            df["valor"] = df["valor"].astype(float)
except Exception as e:
    conn.rollback()
    st.error(f"Erro ao ler banco de dados: {e}")
    st.stop() # Para a execução se o banco falhar

if df.empty:
    st.warning("Nenhum preço encontrado. Use o formulário acima para adicionar.")
    st.stop()

# =========================
# Interface em Abas
# =========================
st.write("### Tabela de Preços")
st.write("Edite os valores abaixo e clique no botão **Salvar Alterações** correspondente à aba.")

categorias_existentes = sorted(list(set(df["categoria"].dropna().unique()) | set(categorias_disponiveis)))
abas = st.tabs(categorias_existentes)

for i, cat in enumerate(categorias_existentes):
    with abas[i]:
        df_cat = df[df["categoria"] == cat].copy()
        
        if df_cat.empty:
            st.info(f"Nenhum item cadastrado na categoria {cat}.")
            continue

        edited_df = st.data_editor(
            df_cat,
            disabled=["chave", "categoria"],
            use_container_width=True,
            hide_index=True,
            key=f"editor_{cat}",
            column_config={
                "chave": st.column_config.TextColumn("Identificador (Chave)"),
                "categoria": None, 
                "valor": st.column_config.NumberColumn(
                    "Valor em R$",
                    min_value=0.0,
                    step=0.5,
                    format="R$ %.2f"
                )
            }
        )
        
        if st.button(f"💾 Salvar preços de {cat}", key=f"btn_salvar_{cat}", type="secondary"):
            try:
                with conn.cursor() as cur:
                    for index, row in edited_df.iterrows():
                        cur.execute(
                            "UPDATE precos SET valor = %s WHERE chave = %s",
                            (row["valor"], row["chave"])
                        )
                st.success(f"✅ Preços de {cat} atualizados!")
            except Exception as e:
                conn.rollback()
                st.error(f"Erro ao atualizar: {e}")
