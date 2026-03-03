import streamlit as st

def apply_vero_style():
    st.markdown("""
    <style>
        /* Oculta o cabeçalho e rodapé padrão do Streamlit */
        header {visibility: hidden !important;}
        footer {visibility: hidden !important;}
        
        /* 1. FUNDO GERAL DO APP (Cinza ultra escuro, como na referência) */
        .stApp {
            background-color: #17181c !important; 
        }

        /* 2. ESTILO DOS CARDS (Transforma st.container(border=True) em Cards modernos) */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #26272f !important; /* Cinza um pouco mais claro para destacar */
            border: none !important;              /* Remove a linha de borda dura */
            border-radius: 16px !important;       /* Cantos bem arredondados */
            padding: 5px !important;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3) !important; /* Sombra suave de profundidade */
        }

        /* 3. CORES DE TEXTO PADRÃO */
        h1, h2, h3, p, span, label, li {
            color: #e2e8f0 !important;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
        }

        /* 4. CAMPOS DE INPUT (Caixas de texto e números) */
        .stTextInput input, .stNumberInput input, div[data-baseweb="select"], .stTextArea textarea {
            background-color: #1e1e24 !important; /* Fundo mais escuro para afundar no card */
            color: white !important;
            border: 1px solid #3b3d4a !important;
            border-radius: 8px !important;
        }

        /* 5. BOTÕES ESTILO DASHBOARD (Borda Ciano) */
        .stButton > button {
            background-color: #26272f !important;
            color: #4bc0c0 !important; /* Cor ciano da sua referência */
            border: 1px solid #4bc0c0 !important; 
            border-radius: 8px !important;
            height: 45px !important;
            font-weight: bold !important;
            transition: 0.3s;
        }

        /* Efeito Hover: Quando passa o mouse no botão, ele preenche de Ciano */
        .stButton > button:hover {
            background-color: #4bc0c0 !important;
            color: #17181c !important;
        }
        
        /* Ajuste do fundo de itens selecionados no multiselect */
        span[data-baseweb="tag"] {
            background-color: #4bc0c0 !important;
            color: #17181c !important;
        }
    </style>
    """, unsafe_allow_html=True)
