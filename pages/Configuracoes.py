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
st.write("Personalize os dados e a Logo que vão aparecer nos seus orçamentos e PDFs.")

# 1. CRIA A TABELA E A COLUNA DE LOGO (Mágica acontecendo nos bastidores)
def inicializar_tabela():
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            # Garante que a tabela existe
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
            # Adiciona a coluna de imagem (BYTEA) caso ela ainda não exista
            cur.execute("""
                ALTER TABLE config_empresa ADD COLUMN IF NOT EXISTS logo BYTEA
            """)
        conn.commit()
    except Exception as e:
        st.error(f"Erro ao inicializar tabela: {e}")

inicializar_tabela()

# 2. BUSCA OS DADOS ATUAIS
def buscar_dados():
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            # Trazemos todos os dados, incluindo a logo
            cur.execute("SELECT nome_empresa, whatsapp, pagamento_padrao, garantia_padrao, validade_dias, logo FROM config_empresa WHERE id = 1")
            dados = cur.fetchone()
        return dados
    except Exception as e:
        return None

dados_atuais = buscar_dados()

# Se não houver dados, criamos valores vazios por padrão (o último None é a logo)
if not dados_atuais:
    dados_atuais = ("", "", "À vista ou 50% entrada / 50% na entrega", "90 dias", 7, None)

# 3. O FORMULÁRIO (A Interface)
with st.container(border=True):
    st.subheader("🏢 Perfil da Empresa")
    
    with st.form("form_config"):
        col1, col2 = st.columns(2)
        with col1:
            nome_empresa = st.text_input("Nome da Empresa", value=dados_atuais[0], placeholder="Ex: RR Smart Soluções")
            whatsapp = st.text_input("WhatsApp para Contato", value=dados_atuais[1], placeholder="(95) 90000-0000")
            
            # --- UPLOAD DE LOGO AQUI ---
            st.markdown("**Logo da Empresa (Máx: 2MB | PNG, JPG)**")
            uploaded_logo = st.file_uploader("Selecione a imagem", type=['png', 'jpg', 'jpeg'], label_visibility="collapsed")
            
            # Se já existir uma logo salva no banco, mostra um aviso visual
            if dados_atuais[5] is not None and uploaded_logo is None:
                st.info("🖼️ Você já tem uma logo salva no sistema. Envie uma nova para alterar.")
                
        with col2:
            garantia = st.text_input("Garantia Padrão", value=dados_atuais[3], placeholder="Ex: 90 dias")
            validade = st.number_input("Validade do Orçamento (Dias)", value=dados_atuais[4], min_value=1, step=1)
            pagamento = st.text_input("Condições de Pagamento Padrão", value=dados_atuais[2])
        
        st.markdown("---")
        salvar = st.form_submit_button("💾 Guardar Configurações", type="primary", use_container_width=True)
        
        if salvar:
            # Validação do tamanho da imagem (2MB = 2 * 1024 * 1024 bytes)
            logo_bytes = None
            if uploaded_logo is not None:
                if uploaded_logo.size > 2097152: # 2MB em bytes
                    st.error("❌ A imagem é muito grande! O limite é de 2MB. Por favor, comprima a imagem e tente novamente.")
                    st.stop()
                else:
                    logo_bytes = uploaded_logo.read() # Transforma a imagem em código binário!

            if nome_empresa and whatsapp:
                try:
                    conn = get_conn()
                    with conn.cursor() as cur:
                        if buscar_dados():
                            # O COALESCE(%s, logo) significa: se eu não enviar uma logo nova, mantenha a antiga!
                            cur.execute("""
                                UPDATE config_empresa 
                                SET nome_empresa=%s, whatsapp=%s, pagamento_padrao=%s, garantia_padrao=%s, validade_dias=%s, logo=COALESCE(%s, logo)
                                WHERE id = 1
                            """, (nome_empresa, whatsapp, pagamento, garantia, validade, logo_bytes))
                        else:
                            cur.execute("""
                                INSERT INTO config_empresa (id, nome_empresa, whatsapp, pagamento_padrao, garantia_padrao, validade_dias, logo)
                                VALUES (1, %s, %s, %s, %s, %s, %s)
                            """, (nome_empresa, whatsapp, pagamento, garantia, validade, logo_bytes))
                    conn.commit()
                    st.success("Configurações e Logo guardadas com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao guardar configurações: {e}")
            else:
                st.warning("O Nome da Empresa e o WhatsApp são obrigatórios!")
