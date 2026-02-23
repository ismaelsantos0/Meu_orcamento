import streamlit as st
import pandas as pd
from core.db import get_conn

st.set_page_config(page_title="Configurações da Empresa", page_icon="⚙️", layout="wide")

# O mesmo CSS mágico para manter o padrão Premium
st.markdown("""
<style>
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #262933 !important;
        border-radius: 12px !important;
        border: 1px solid #333845 !important;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2) !important;
        padding: 1.5rem !important;
    }
    .stButton > button {
        border-radius: 8px !important;
        font-weight: 600 !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("⚙️ Configurações da Empresa")
st.write("Personalize os dados que vão aparecer nos seus orçamentos e PDFs.")

# 1. CRIA A TABELA SE ELA NÃO EXISTIR (Mágica acontecendo nos bastidores)
def inicializar_tabela():
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS config_empresa (
                    id SERIAL PRIMARY KEY,
                    nome_empresa VARCHAR(255),
                    whatsapp VARCHAR(50),
                    pagamento_padrao TEXT,
                    garantia_padrao VARCHAR(100),
                    validade_dias INTEGER
                )
            """)
        conn.commit()
    except Exception as e:
        st.error(f"Erro ao inicializar tabela: {e}")
    # SEM conn.close() AQUI!

inicializar_tabela()

# 2. BUSCA OS DADOS ATUAIS (Para preencher o formulário se já houver dados)
def buscar_dados():
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            # Por enquanto pegamos o ID 1. No futuro SaaS, buscaremos pelo ID do usuário!
            cur.execute("SELECT * FROM config_empresa WHERE id = 1")
            dados = cur.fetchone()
        return dados
    except Exception as e:
        return None
    # SEM conn.close() AQUI!

dados_atuais = buscar_dados()

# Se não houver dados, criamos valores vazios por padrão
if not dados_atuais:
    dados_atuais = (1, "", "", "À vista ou 50% entrada / 50% na entrega", "90 dias", 7)

# 3. O FORMULÁRIO (A Interface)
with st.container(border=True):
    st.subheader("🏢 Perfil da Empresa")
    
    with st.form("form_config"):
        col1, col2 = st.columns(2)
        with col1:
            nome_empresa = st.text_input("Nome da Empresa", value=dados_atuais[1], placeholder="Ex: RR Smart Soluções")
            whatsapp = st.text_input("WhatsApp para Contato", value=dados_atuais[2], placeholder="(95) 90000-0000")
        
        with col2:
            garantia = st.text_input("Garantia Padrão", value=dados_atuais[4], placeholder="Ex: 90 dias")
            validade = st.number_input("Validade do Orçamento (Dias)", value=dados_atuais[5], min_value=1, step=1)
            
        pagamento = st.text_input("Condições de Pagamento Padrão", value=dados_atuais[3])
        
        salvar = st.form_submit_button("💾 Guardar Configurações", type="primary", use_container_width=True)
        
        if salvar:
            if nome_empresa and whatsapp:
                try:
                    conn = get_conn()
                    with conn.cursor() as cur:
                        # Se já existe (ID 1), atualiza. Se não, insere.
                        if buscar_dados():
                            cur.execute("""
                                UPDATE config_empresa 
                                SET nome_empresa=%s, whatsapp=%s, pagamento_padrao=%s, garantia_padrao=%s, validade_dias=%s 
                                WHERE id = 1
                            """, (nome_empresa, whatsapp, pagamento, garantia, validade))
                        else:
                            cur.execute("""
                                INSERT INTO config_empresa (id, nome_empresa, whatsapp, pagamento_padrao, garantia_padrao, validade_dias)
                                VALUES (1, %s, %s, %s, %s, %s)
                            """, (nome_empresa, whatsapp, pagamento, garantia, validade))
                    conn.commit()
                    # SEM conn.close() AQUI TAMBÉM!
                    st.success("Configurações guardadas com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao guardar configurações: {e}")
            else:
                st.warning("O Nome da Empresa e o WhatsApp são obrigatórios!")
