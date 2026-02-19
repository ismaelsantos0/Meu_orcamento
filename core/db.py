# core/db.py
from __future__ import annotations

import os
import sqlite3
import streamlit as st


def get_db_path() -> str:
    """
    Nome do arquivo do banco.
    Se você usa outro, troque aqui OU defina a env DB_PATH no Railway.
    """
    return os.getenv("DB_PATH", "data.db")


@st.cache_resource
def get_conn() -> sqlite3.Connection:
    path = get_db_path()
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def get_price(conn: sqlite3.Connection, key: str) -> float:
    """
    Busca preço na tabela `precos` (chave, valor).
    Se não achar, retorna 0.0 (pra não quebrar o app).
    """
    cur = conn.execute("SELECT valor FROM precos WHERE chave=?", (key,))
    row = cur.fetchone()
    return float(row["valor"]) if row else 0.0
