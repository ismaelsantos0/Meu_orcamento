import streamlit as st
import pandas as pd
import re
import unicodedata
from core.db import get_conn

st.set_page_config(page_title="Tabela de Preços", page_icon="💰", layout="wide")
st.title("💰 Configuração de Preços")

# =========================
# Conexão DB
# =========================
try:
    conn = get_conn()
except Exception as e:
    st.error(f"Falha ao ligar à base de dados: {e}")
    st.stop()

# =========================
# Função para gerar Chave Automática
# =========================
def gerar_chave(nome: str) -> str:
    """Transforma 'Câmara 1080p' em 'camara_1080p' para uso no código Python"""
    nfkd = unicodedata.normalize('NFKD', nome)
    nome_sem_acento = u"".join([c for c in nfkd if not unicodedata.combining(c)])
    nome_limpo = re.sub(r'[^a-zA-Z0-9\s_]', '', nome_sem_acento).strip().lower()
    return re.sub(r'\s+', '_', nome_limpo)

# =========================
# Migração / Setup do Banco
# =========================
def upgrade_database():
    """Garante que a tabela existe e atualiza a estrutura com ID e Nome."""
    try:
        with conn.cursor() as cur:
            # Garante que a tabela base existe
            cur.execute("""
                CREATE TABLE IF NOT EXISTS precos (
                    chave VARCHAR(100) PRIMARY KEY,
                    valor NUMERIC(10, 2) NOT NULL
                );
            """)
            # Adiciona categoria
            cur.execute("ALTER TABLE precos ADD COLUMN IF NOT EXISTS categoria VARCHAR(50) DEFAULT 'Outros';")
            
            # 1. Adiciona coluna para ID automático
            cur.execute("ALTER TABLE precos ADD COLUMN IF NOT EXISTS id SERIAL;")
            
            # 2. Adiciona coluna para o Nome legível
            cur.execute("ALTER TABLE precos ADD COLUMN IF NOT EXISTS nome VARCHAR(200);")
            
            # 3. Preenche nomes vazios baseando-se na chave (apenas para os itens antigos)
            cur.execute("UPDATE precos SET nome = INITCAP(REPLACE(chave, '_', ' ')) WHERE nome IS NULL;")
            
            # Atualiza categorias antigas
            cur.execute("UPDATE precos SET categoria = 'CFTV' WHERE chave LIKE '%cftv%';")
            cur.execute("UPDATE precos SET categoria = 'Motor de Portão' WHERE chave LIKE 'mao_motor%';")
            cur.execute("""
                UPDATE precos SET categoria = 'Cerca/Concertina' 
                WHERE chave LIKE 'haste%' OR chave LIKE 'mao_cerca%' OR chave LIKE 'mao_linear%' 
                OR chave LIKE 'mao_concertina%' OR chave LIKE 'concertina%' OR chave LIKE 'fio%'
                OR chave IN ('central_sh1800', 'bateria', 'sirene', 'kit_isoladores', 'cabo_alta_50m', 'kit_placas', 'kit_aterramento');
            """)
    except Exception as e:
        conn.rollback()
        st.error(f"Erro ao preparar a base de dados: {e}")

upgrade_database()

# =========================
# Adicionar Novo Item
# =========================
categorias_disponiveis = ["CFTV", "Cerca/Concertina", "Motor de Portão", "Outros"]

with st.expander("➕ Adicionar Novo Item de Serviço", expanded=False):
    st.info("Só precisa de preencher o Nome e o Valor. O sistema irá gerar o código e o ID automaticamente para si.")
    with st.form("form_novo_item", clear_on_submit=True):
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            novo_nome = st.text_input("Nome do Item (ex: Cabo de Aço 8mm)")
        with col2:
            novo_valor = st.number_input("Valor Unitário (R$)", min_value=0.0, step=0.5, format="%.2f")
        with col3:
            nova_categoria = st.selectbox("Categoria", categorias_disponiveis)
        
        submit_novo = st.form_submit_button("Salvar Novo Item", type="primary")
        
        if submit_novo:
            if not novo_nome.strip():
                st.warning("O Nome do item não pode estar vazio.")
            else:
                try:
                    # Gera a chave invisível para o sistema
                    chave_gerada = gerar_chave(novo_nome)
                    
                    with conn.cursor() as cur:
                        cur.execute(
                            "INSERT INTO precos (chave, nome, valor, categoria) VALUES (%s, %s, %s, %s) ON CONFLICT (chave) DO NOTHING",
                            (chave_gerada, novo_nome.strip(), novo_valor, nova_categoria)
                        )
                    st.success(f"Item '{novo_nome}' adicionado com sucesso! Código gerado: {chave_gerada}")
                    st.rerun()
                except Exception as e:
                    conn.rollback()
                    st.error(f"Erro ao adicionar item: {e}")

# =========================
# Busca os dados atuais
# =========================
df = pd.DataFrame()
try:
    with conn.cursor() as cur:
        # Trazemos o ID e o Nome agora
        cur.execute("SELECT id, chave, nome, valor, categoria FROM precos ORDER BY id")
        rows = cur.fetchall()
        if rows:
            df = pd.DataFrame(rows, columns=["id", "chave", "nome", "valor", "categoria"])
            df["valor"] = df["valor"].astype(float)
except Exception as e:
    conn.rollback()
    st.error(f"Erro ao ler base de dados: {e}")
    st.stop()

if df.empty:
    st.warning("Nenhum preço encontrado. Use o formulário acima para adicionar.")
    st.stop()

# =========================
# Interface em Abas
# =========================
st.write("### Tabela de Preços")
st.write("Edite os nomes e valores abaixo. De seguida clique no botão **Salvar Alterações** da respetiva aba.")

categorias_existentes = sorted(list(set(df["categoria"].dropna().unique()) | set(categorias_disponiveis)))
abas = st.tabs(categorias_existentes)

for i, cat in enumerate(categorias_existentes):
    with abas[i]:
        df_cat = df[df["categoria"] == cat].copy()
        
        if df_cat.empty:
            st.info(f"Nenhum item registado na categoria {cat}.")
            continue

        # Novo editor com colunas reordenadas e personalizadas
        edited_df = st.data_editor(
            df_cat,
            disabled=["id", "chave", "categoria"], # O utilizador só pode editar Nome e Valor
            use_container_width=True,
            hide_index=True,
            key=f"editor_{cat}",
            column_order=["id", "nome", "valor", "chave"], # Mostra o ID e o Nome primeiro
            column_config={
                "id": st.column_config.NumberColumn("ID", format="%d"),
                "nome": st.column_config.TextColumn("Nome do Item (Visual)"),
                "categoria": None, 
                "valor": st.column_config.NumberColumn(
                    "Valor em R$",
                    min_value=0.0,
                    step=0.5,
                    format="R$ %.2f"
                ),
                "chave": st.column_config.TextColumn(
                    "Código (Para Python)", 
                    help="Copie este código quando precisar de criar um serviço no ficheiro .py"
                )
            }
        )
        
        if st.button(f"💾 Salvar alterações de {cat}", key=f"btn_salvar_{cat}", type="secondary"):
            try:
                with conn.cursor() as cur:
                    for index, row in edited_df.iterrows():
                        cur.execute(
                            "UPDATE precos SET valor = %s, nome = %s WHERE chave = %s",
                            (row["valor"], row["nome"], row["chave"])
                        )
                st.success(f"✅ Alterações guardadas com sucesso!")
            except Exception as e:
                conn.rollback()
                st.error(f"Erro ao atualizar: {e}")
