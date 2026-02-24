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
    Traduz os códigos antigos dos plugins para palavras-chave e busca
    o valor do item pelo NOME na tabela do usuário logado de forma inteligente.
    Se não achar, retorna 0.0 (pra não quebrar o app).
    """
    # Se não houver usuário logado (ex: na tela de login), retorna 0 para evitar erros
    if 'user_id' not in st.session_state:
        return 0.0
        
    user_id = st.session_state.user_id
    
    # Dicionário de tradução: Código do Plugin -> Palavra-chave que deve ter no nome do produto
    tradutor = {
        # === CERCA E CONCERTINA ===
        "haste_reta": "Haste reta",
        "haste_canto": "Haste de canto",
        "concertina_linear_20m": "Concertina",
        "concertina_10m": "Concertina",
        "fio_aco_200m": "Fio de aço",
        "central_sh1800": "Central",
        "bateria": "Bateria",
        "sirene": "Sirene",
        "cabo_alta_50m": "Cabo de alta",
        "kit_aterramento": "Aterramento",
        "kit_placas": "Placa",
        "kit_isoladores": "Isolador",
        
        # === MÃO DE OBRA CERCA/CONCERTINA ===
        "mao_linear_base": "Instalação",
        "mao_linear_por_m": "Metro",
        "mao_cerca_base": "Instalação",
        "mao_cerca_por_m": "Metro",
        "mao_concertina_base": "Instalação",
        "mao_concertina_por_m": "Metro",
        
        # === CFTV ===
        "cftv_camera": "Câmera",
        "cftv_dvr": "DVR",
        "cftv_hd": "HD",
        "cftv_fonte_colmeia": "Fonte",
        "cftv_cabo_cat5_m": "Cabo",
        "cftv_balun": "Balun",
        "cftv_conector_p4_macho": "P4 Macho",
        "cftv_conector_p4_femea": "P4 Fêmea",
        "cftv_suporte_camera": "Suporte",
        "cftv_caixa_hermetica": "Caixa hermética",
        
        # === MÃO DE OBRA CFTV E MOTORES ===
        "mao_cftv_dvr": "Instalação DVR",
        "mao_cftv_por_camera_inst": "Instalação Câmera",
        "mao_cftv_por_camera_defeito": "Manutenção Câmera",
        "mao_motor_inst": "Instalação Motor",
        "mao_motor_man": "Manutenção Motor"
    }
    
    # Pega a palavra-chave correta (se não achar no tradutor, usa a própria key enviada)
    palavra_chave = tradutor.get(key, key)
    
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Busca flexível: ILIKE %palavra% encontra o item mesmo se o usuário tiver digitado nomes diferentes
        # Exemplo: Se a palavra é "Câmera", ele encontra "Câmera Intelbras VIP" ou "Câmera Analógica"
        busca_flexivel = f"%{palavra_chave}%"
        
        cur.execute("""
            SELECT valor FROM precos 
            WHERE nome ILIKE %s AND usuario_id = %s 
            LIMIT 1
        """, (busca_flexivel, user_id))
        
        row = cur.fetchone()
        
        return float(row["valor"]) if row else 0.0
