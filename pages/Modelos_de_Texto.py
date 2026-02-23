import streamlit as st
from core.db import get_conn

if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.stop()

st.set_page_config(page_title="Vero | Textos", layout="wide", initial_sidebar_state="collapsed")
user_id = st.session_state.user_id

st.markdown("""
<style>
    header {visibility: hidden;} footer {visibility: hidden;}
    [data-testid="stSidebar"] { display: none; }
    .stApp { background: radial-gradient(circle at 50% 50%, #101a26 0%, #080d12 100%); color: white; font-family: 'Poppins', sans-serif; }
    .stButton > button { background-color: #ffffff !important; color: #080d12 !important; border-radius: 50px !important; font-weight: 800 !important; }
    .stTextArea textarea { background: rgba(255,255,255,0.05) !important; color: white !important; border-radius: 15px !important; }
</style>
""", unsafe_allow_html=True)

if st.button("VOLTAR"):
    st.switch_page("app.py")

st.title("Descricoes de Entrega")

# Lista de serviços conforme seus plugins
servicos = ['Concertina linear eletrificada (instalacao)', 'Camera IP externa (instalacao)', 'Motor de portao deslizante (instalacao)']
servico_sel = st.selectbox("Selecione o servico para personalizar", servicos)

def buscar_texto(uid, tipo):
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("SELECT texto_detalhado FROM modelos_texto WHERE usuario_id = %s AND servico_tipo = %s", (uid, tipo))
        res = cur.fetchone()
        return res[0] if res else ""

texto_atual = buscar_texto(user_id, servico_sel)

with st.form("form_texto"):
    novo_texto = st.text_area("Beneficios e Detalhes do Servico", value=texto_atual, height=300)
    if st.form_submit_button("SALVAR MODELO"):
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO modelos_texto (usuario_id, servico_tipo, texto_detalhado) 
                VALUES (%s, %s, %s)
                ON CONFLICT (usuario_id, servico_tipo) 
                DO UPDATE SET texto_detalhado = EXCLUDED.texto_detalhado
            """, (user_id, servico_sel, novo_texto))
        conn.commit()
        st.success("Texto atualizado com sucesso")
