import streamlit as st
import pandas as pd
from core.db import get_conn

# --- SEGURANÇA ---
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.stop()

st.set_page_config(page_title="Vero | Preços", layout="wide", initial_sidebar_state="collapsed")
user_id = st.session_state.user_id
conn = get_conn()

# --- ESTILO VERO (SEM EMOJIS) ---
st.markdown("""
<style>
    header {visibility: hidden;} footer {visibility: hidden;}
    [data-testid="stSidebar"] { display: none; }
    .stApp { background: radial-gradient(circle at 50% 50%, #101a26 0%, #080d12 100%); color: white; font-family: 'Poppins', sans-serif; }
    .stButton > button { background-color: #ffffff !important; color: #080d12 !important; border-radius: 50px !important; font-weight: 800 !important; }
    [data-testid="stVerticalBlockBorderWrapper"] { background: rgba(255,255,255,0.03) !important; border: 1px solid rgba(255,255,255,0.1) !important; border-radius: 20px !important; }
</style>
""", unsafe_allow_html=True)

if st.button("VOLTAR", key="back_tabela_precos"):
    st.switch_page("app.py")

st.title("Tabela de Precos por Servico")

# --- CADASTRO DE ITENS (SINCRONIZADO COM SUAS CATEGORIAS) ---
with st.container(border=True):
    with st.form("add_p_v4", clear_on_submit=True):
        c1, c2, c3, c4 = st.columns([2, 2, 1, 1.5])
        ch = c1.text_input("Chave unica")
        nm = c2.text_input("Nome do Produto")
        vl = c3.number_input("Preco R$", min_value=0.0)
        # Nomes exatos conforme sua lista enviada anteriormente
        ct = c4.selectbox("Categoria do Servico", ["CFTV", "Cerca/Concertina", "Motor de Portão", "Geral"])
        
        if st.form_submit_button("CADASTRAR PRODUTO"):
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO precos (chave, nome, valor, usuario_id, categoria) 
                    VALUES (%s, %s, %s, %s, %s)
                """, (ch, nm, vl, user_id, ct))
            conn.commit()
            st.success(f"Item cadastrado em {ct}")
            st.rerun()

# --- ABAS DE VISUALIZAÇÃO COM FILTRO CORRETO ---
# Definimos as abas com os nomes que o usuário verá
abas_titulos = ["Todos", "CFTV", "Cerca/Concertina", "Motor de Portão", "Geral"]
abas = st.tabs(abas_titulos)

def carregar_aba_filtrada(filtro_banco=None, key_suffix=""):
    query = "SELECT chave, nome, valor, categoria FROM precos WHERE usuario_id = %s"
    params = [user_id]
    
    if filtro_banco:
        query += " AND categoria = %s"
        params.append(filtro_banco)
    
    query += " ORDER BY nome ASC"
    
    df = pd.read_sql(query, conn, params=params)
    if not df.empty:
        st.data_editor(df, use_container_width=True, key=f"editor_tab_{key_suffix}")
    else:
        st.info(f"Nenhum item cadastrado na categoria {filtro_banco if filtro_banco else 'Geral'}.")

# Preenche cada aba chamando a função com o nome exato do banco
with abas[0]: carregar_aba_filtrada(None, "todos")
with abas[1]: carregar_aba_filtrada("CFTV", "cftv")
with abas[2]: carregar_aba_filtrada("Cerca/Concertina", "cerca")
with abas[3]: carregar_aba_filtrada("Motor de Portão", "motor")
with abas[4]: carregar_aba_filtrada("Geral", "geral")
