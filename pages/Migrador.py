import streamlit as st
from core.db import get_conn

st.set_page_config(page_title="Migração SaaS", page_icon="🏗️")

st.title("🏗️ Assistente de Migração SaaS")
st.write("Este painel vai transformar o seu banco de dados atual num sistema Multi-Tenant (Múltiplos Usuários).")
st.warning("⚠️ Só clique no botão abaixo UMA VEZ. Depois que o processo terminar e der sucesso, você pode apagar este arquivo (Migrador.py) do seu projeto.")

if st.button("🚀 Executar Migração para SaaS", type="primary"):
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            # 1. CRIAR A TABELA DE USUÁRIOS (A Portaria)
            st.write("⏳ Criando tabela de usuários...")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    telefone VARCHAR(50) UNIQUE,
                    senha VARCHAR(255) NOT NULL,
                    is_admin BOOLEAN DEFAULT FALSE,
                    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 2. INSERIR VOCÊ COMO O DONO (ID 1)
            st.write("⏳ Cadastrando o Administrador (Ismael)...")
            cur.execute("""
                INSERT INTO usuarios (id, email, telefone, senha, is_admin) 
                VALUES (1, 'ismaelifrr@gmail.com', '95984187832', 'Admin@123', TRUE)
                ON CONFLICT (id) DO NOTHING
            """)

            # 3. ETIQUETAR A CONFIGURAÇÃO DA EMPRESA (A Fachada)
            st.write("⏳ Vinculando as configurações da RR Smart ao seu usuário...")
            cur.execute("ALTER TABLE config_empresa ADD COLUMN IF NOT EXISTS usuario_id INTEGER;")
            cur.execute("UPDATE config_empresa SET usuario_id = 1 WHERE usuario_id IS NULL;")
            
            # 4. ETIQUETAR A TABELA DE PREÇOS (O Estoque)
            st.write("⏳ Vinculando todos os seus preços atuais ao seu usuário...")
            cur.execute("ALTER TABLE precos ADD COLUMN IF NOT EXISTS usuario_id INTEGER;")
            cur.execute("UPDATE precos SET usuario_id = 1 WHERE usuario_id IS NULL;")

            # 5. MUDAR A REGRA DA CHAVE ÚNICA NA TABELA DE PREÇOS
            # Tenta remover a restrição antiga (se existir) e cria a nova regra de "Inquilino"
            st.write("⏳ Atualizando as regras de privacidade do banco...")
            try:
                cur.execute("ALTER TABLE precos DROP CONSTRAINT IF EXISTS precos_chave_key;")
            except:
                pass # Se a restrição tiver outro nome ou não existir, ele ignora e segue
                
            try:
                # A nova regra: A mesma chave pode existir, desde que seja de usuários diferentes!
                cur.execute("ALTER TABLE precos ADD CONSTRAINT precos_usuario_chave_unique UNIQUE (usuario_id, chave);")
            except:
                pass

        conn.commit()
        st.success("🎉 MULLTI-TENANT ATIVADO COM SUCESSO! O seu banco de dados agora é um SaaS.")
        st.balloons()
        
    except Exception as e:
        st.error(f"❌ Ocorreu um erro durante a migração: {e}")
        # Se der erro, ele desfaz tudo o que tentou fazer nesta execução para não quebrar o banco
        if 'conn' in locals():
            conn.rollback()
