import streamlit as st
import pandas as pd
from core.db import get_conn

st.set_page_config(page_title="Tabela de Preços", page_icon="💰", layout="wide")
st.title("💰 Configuração de Preços")
st.write("Edite os valores diretamente na tabela abaixo e clique em Salvar.")

# =========================
# Conexão DB
# =========================
try:
    conn = get_conn()
except Exception as e:
    st.error(f"Falha ao conectar no banco de dados: {e}")
    st.stop()

# =========================
# Função Automática de Setup
# =========================
def setup_database():
    sql = """
    CREATE TABLE IF NOT EXISTS precos (
        chave VARCHAR(100) PRIMARY KEY,
        valor NUMERIC(10, 2) NOT NULL
    );

    INSERT INTO precos (chave, valor) VALUES
    ('cftv_camera', 150.00), ('cftv_dvr', 450.00), ('cftv_hd', 300.00), ('cftv_fonte_colmeia', 70.00),
    ('cftv_cabo_cat5_m', 3.50), ('cftv_balun', 15.00), ('cftv_conector_p4_macho', 4.00),
    ('cftv_conector_p4_femea', 4.00), ('cftv_suporte_camera', 10.00), ('cftv_caixa_hermetica', 12.00),
    ('mao_cftv_dvr', 120.00), ('mao_cftv_por_camera_inst', 80.00), ('mao_cftv_por_camera_defeito', 60.00),
    ('haste_reta', 18.00), ('haste_canto', 28.00), ('fio_aco_200m', 65.00), ('central_sh1800', 380.00),
    ('bateria', 85.00), ('sirene', 35.00), ('kit_isoladores', 45.00), ('cabo_alta_50m', 55.00),
    ('kit_placas', 25.00), ('kit_aterramento', 40.00), ('concertina_linear_20m', 140.00),
    ('concertina_10m', 95.00), ('mao_cerca_base', 150.00), ('mao_cerca_por_m', 6.00),
    ('mao_linear_base', 120.00), ('mao_linear_por_m', 8.00), ('mao_concertina_base', 100.00),
    ('mao_concertina_por_m', 12.00), ('mao_motor_inst', 250.00), ('mao_motor_man', 150.00)
    ON CONFLICT (chave) DO NOTHING;
    """
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
        st.success("✅ Banco de dados inicializado com sucesso!")
        st.rerun() # Recarrega a página automaticamente
    except Exception as e:
        st.error(f"Erro ao inicializar: {e}")
        conn.rollback()

# =========================
# Busca os dados atuais
# =========================
df = pd.DataFrame()
try:
    with conn.cursor() as cur:
        # Tenta buscar os dados
        cur.execute("SELECT chave, valor FROM precos ORDER BY chave")
        rows = cur.fetchall()
        
        if rows and isinstance(rows[0], tuple):
            df = pd.DataFrame(rows, columns=["chave", "valor"])
        elif rows:
            df = pd.DataFrame(rows)
            
except Exception as e:
    # Se der erro (ex: a tabela não existe), o Postgres exige um rollback
    conn.rollback() 
    st.warning("⚠️ O banco de dados ainda não foi configurado (A tabela 'precos' não existe).")
    if st.button("🚀 Inicializar Banco de Dados Automagicamente", type="primary"):
        setup_database()
    st.stop()

if df.empty:
    st.warning("A tabela existe, mas não tem nenhum preço cadastrado.")
    if st.button("🚀 Inserir Valores Padrão", type="primary"):
        setup_database()
    st.stop()

# =========================
# Editor Visual de Tabela
# =========================
df["valor"] = df["valor"].astype(float)

st.write("### Tabela Atual")
edited_df = st.data_editor(
    df,
    disabled=["chave"], # Bloqueia a chave para não quebrar os cálculos
    use_container_width=True,
    hide_index=True,
    column_config={
        "chave": st.column_config.TextColumn("Identificador (Chave)"),
        "valor": st.column_config.NumberColumn(
            "Valor em R$",
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
            for index, row in edited_df.iterrows():
                cur.execute(
                    "UPDATE precos SET valor = %s WHERE chave = %s",
                    (row["valor"], row["chave"])
                )
        st.success("✅ Preços atualizados com sucesso no banco de dados!")
    except Exception as e:
        st.error(f"Erro ao atualizar: {e}")
        conn.rollback()
