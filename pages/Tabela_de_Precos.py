import streamlit as st
import pandas as pd
from core.db import get_conn

# --- SEGURANÇA E ESTILO ---
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.stop()

st.set_page_config(page_title="Vero | Preços", layout="wide", initial_sidebar_state="collapsed")
user_id = st.session_state.user_id

# --- MANTENÇÃO AUTOMÁTICA DO BANCO (RESOLVE SEU ERRO) ---
def realizar_manutencao():
    conn = get_conn()
    with conn.cursor() as cur:
        # 1. Cria a coluna categoria se ela não existir
        cur.execute("ALTER TABLE precos ADD COLUMN IF NOT EXISTS categoria VARCHAR(50) DEFAULT 'Geral';")
        
        # 2. Tenta organizar itens antigos automaticamente baseado no nome
        # Isso vai tirar os itens da aba 'Geral' e colocar nas abas certas
        cur.execute("UPDATE precos SET categoria = 'Concertinas' WHERE (nome ILIKE '%concertina%' OR nome ILIKE '%linear%') AND categoria = 'Geral';")
        cur.execute("UPDATE precos SET categoria = 'Cercas' WHERE nome ILIKE '%cerca%' AND categoria = 'Geral';")
        cur.execute("UPDATE precos SET categoria = 'Cameras' WHERE nome ILIKE '%camera%' AND categoria = 'Geral';")
        cur.execute("UPDATE precos SET categoria = 'Motores' WHERE nome ILIKE '%motor%' AND categoria = 'Geral';")
    conn.commit()

realizar_manutencao()

# --- ESTILO VISUAL ---
st.markdown("<style>header {visibility: hidden;} footer {visibility: hidden;} [data-testid='stSidebar'] { display: none; } .stApp { background: radial-gradient(circle at 50% 50%, #101a26 0%, #080d12 100%); color: white; }</style>", unsafe_allow_html=True)

if st.button("VOLTAR", key="back_tabela"):
    st.switch_page("app.py")

st.title("Tabela de Preços por Serviço")

conn = get_conn()

# --- CADASTRO DE NOVOS ITENS ---
with st.container(border=True):
    with st.form("add_item_v3"):
        c1, c2, c3, c4 = st.columns([2, 2, 1, 1])
        chave = c1.text_input("Chave única")
        nome = c2.text_input("Nome do Produto")
        valor = c3.number_input("Preço R$", min_value=0.0)
        cat = c4.selectbox("Serviço", ["Cameras", "Cercas", "Motores", "Concertinas", "Geral"])
        
        if st.form_submit_button("CADASTRAR"):
            with conn.cursor() as cur:
                cur.execute("INSERT INTO precos (chave, nome, valor, usuario_id, categoria) VALUES (%s, %s, %s, %s, %s)", 
                            (chave, nome, valor, user_id, cat))
            conn.commit()
            st.success(f"Item salvo em {cat}!")
            st.rerun()

# --- ABAS DE VISUALIZAÇÃO ---
tabs = st.tabs(["Todos", "Cameras", "Cercas", "Motores", "Concertinas", "Geral"])

def carregar_aba(categoria_filtro=None):
    query = "SELECT chave, nome, valor, categoria FROM precos WHERE usuario_id = %s"
    params = [user_id]
    if categoria_filtro:
        query += " AND categoria = %s"
        params.append(categoria_filtro)
    
    df = pd.read_sql(query, conn, params=params)
    if not df.empty:
        st.data_editor(df, use_container_width=True, key=f"editor_{categoria_filtro}")
    else:
        st.info(f"Nenhum item em {categoria_filtro if categoria_filtro else 'Todas as categorias'}")

with tabs[0]: carregar_aba(None)
with tabs[1]: carregar_aba("Cameras")
with tabs[2]: carregar_aba("Cercas")
with tabs[3]: carregar_aba("Motores")
with tabs[4]: carregar_aba("Concertinas")
with tabs[5]: carregar_aba("Geral")
