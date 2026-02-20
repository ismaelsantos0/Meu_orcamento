import os
import psycopg2
from psycopg2.extras import RealDictCursor
import streamlit as st

@st.cache_resource
def get_conn():
    """
    Conecta ao PostgreSQL usando a variável DATABASE_URL fornecida pelo Railway.
    """
    # O Railway injeta a variável DATABASE_URL automaticamente quando você linka o banco
    db_url = os.getenv("DATABASE_URL")
    
    # Fallback para desenvolvimento local (caso queira rodar na sua máquina)
    if not db_url:
        db_url = "postgresql://usuario:senha@localhost:5432/seu_banco" # Troque se usar local
        
    try:
        conn = psycopg2.connect(db_url)
        # Garantir que as transações sejam commitadas automaticamente ou tratadas na query
        conn.autocommit = True 
        return conn
    except Exception as e:
        st.error(f"Erro ao conectar ao banco de dados: {e}")
        raise e

def get_price(conn, key: str) -> float:
    """
    Busca preço na tabela `precos` (chave, valor).
    Se não achar, retorna 0.0 (pra não quebrar o app).
    """
    # Usamos o RealDictCursor para que o retorno aja como um dicionário (igual ao sqlite3.Row)
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # ATENÇÃO: No PostgreSQL usamos %s em vez de ? para variáveis
        cur.execute("SELECT valor FROM precos WHERE chave=%s", (key,))
        row = cur.fetchone()
        return float(row["valor"]) if row else 0.0
