import os
import psycopg2
from psycopg2.extras import RealDictCursor
import streamlit as st

@st.cache_resource
def get_conn():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        db_url = "postgresql://usuario:senha@localhost:5432/seu_banco"
        
    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True 
        return conn
    except Exception as e:
        st.error(f"Erro ao conectar ao banco de dados: {e}")
        raise e

def get_price(conn, key: str) -> float:
    """
    Busca EXATA pelo ID (chave) no banco de dados. Sem achismos.
    Se o plugin pedir "haste_reta", ele busca estritamente "haste_reta".
    """
    if 'user_id' not in st.session_state:
        return 0.0
        
    user_id = st.session_state.user_id
    
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Busca exata usando a coluna 'chave'
        cur.execute("SELECT valor FROM precos WHERE chave=%s AND usuario_id=%s LIMIT 1", (key, user_id))
        row = cur.fetchone()
        
        return float(row["valor"]) if row else 0.0
