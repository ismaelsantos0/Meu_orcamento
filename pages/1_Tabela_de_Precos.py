import streamlit as st
import pandas as pd
from core.db import get_conn

st.set_page_config(page_title="Tabela de Preços", page_icon="💰", layout="wide")
st.title("💰 Configuração de Preços")
st.write("Edite os valores diretamente na tabela abaixo e clique em Salvar. Não altere os nomes das chaves, apenas os valores.")

# =========================
# Conexão DB
# =========================
try:
    conn = get_conn()
except Exception as e:
    st.error(f"Falha ao conectar no banco de dados: {e}")
    st.stop()

# =========================
# Busca os dados atuais
# =========================
try:
    with conn.cursor() as cur:
        cur.execute("SELECT chave, valor FROM precos ORDER BY chave")
        rows = cur.fetchall()
        
    df = pd.DataFrame(rows)
    if not df.empty:
        # Garante que a coluna de valor é tratada como decimal/float para o editor
        df["valor"] = df["valor"].astype(float)
    else:
        st.warning("A tabela de preços está vazia. Rode o script SQL no Railway primeiro.")
        st.stop()
        
except Exception as e:
    st.error(f"Erro ao buscar preços: {e}")
    st.stop()

# =========================
# Editor Visual de Tabela
# =========================
# O st.data_editor permite editar o dataframe como se fosse o Excel
edited_df = st.data_editor(
    df,
    disabled=["chave"], # Bloqueia a edição da coluna 'chave' para evitar quebrar o sistema
    use_container_width=True,
    hide_index=True,
    column_config={
        "chave": st.column_config.TextColumn("Identificador (Chave)"),
        "valor": st.column_config.NumberColumn(
            "Valor em R$",
            help="Preço atual do item",
            min_value=0.0,
            step=0.5,
            format="R$ %.2f"
        )
    }
)

# =========================
# Salvar Alterações
# =========================
if st.button("💾 Salvar Alterações", type="primary", use_container_width=True):
    try:
        with conn.cursor() as cur:
            # Varre a tabela editada e atualiza o banco de dados
            for index, row in edited_df.iterrows():
                cur.execute(
                    "UPDATE precos SET valor = %s WHERE chave = %s",
                    (row["valor"], row["chave"])
                )
        st.success("✅ Preços atualizados com sucesso! Os novos orçamentos já usarão estes valores.")
        
    except Exception as e:
        st.error(f"Erro ao atualizar o banco de dados: {e}")
    finally:
        if conn:
            conn.close()
