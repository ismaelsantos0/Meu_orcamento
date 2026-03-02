import os
import psycopg2
import streamlit as st

@st.cache_resource
def get_conn():
    db_url = os.getenv("DATABASE_URL") or "postgresql://usuario:senha@localhost:5432/seu_banco"
    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True 
        return conn
    except Exception as e:
        st.error(f"Erro ao conectar ao banco de dados: {e}")
        raise e

def get_price(conn, key: str) -> float:
    """Busca o preço pela CHAVE FIXA e USUÁRIO logado no Streamlit."""
    if 'user_id' not in st.session_state:
        return 0.0
    
    with conn.cursor() as cur:
        # Usando cursor padrão para evitar bugs de dicionário no psycopg2
        cur.execute("SELECT valor FROM precos WHERE chave = %s AND usuario_id = %s", (key, st.session_state.user_id))
        row = cur.fetchone()
        return float(row[0]) if row else 0.0
