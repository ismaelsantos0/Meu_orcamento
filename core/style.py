import streamlit as st

def apply_vero_style():
    st.markdown("""
    <style>
        /* Oculta o cabeçalho e rodapé */
        header {visibility: hidden !important;}
        footer {visibility: hidden !important;}
        
        /* 1. FUNDO GERAL SUPER CLEAN (Cinza chumbo sólido) */
        .stApp {
            background-color: #131418 !important; 
        }

        /* 2. CARDS MINIMALISTAS */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #1c1d24 !important; /* Um tom um pouco mais claro que o fundo */
            border: 1px solid #2b2d38 !important; /* Borda super fina e discreta */
            border-radius: 12px !important;       /* Cantos arredondados, mas não exagerados */
            padding: 15px !important;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3) !important; /* Sombra suave embaixo */
        }

        /* 3. TIPOGRAFIA CLEAN */
        h1, h2, h3, p, span, label, li {
            color: #d1d5db !important; /* Branco levemente acinzentado para não doer a vista */
            font-family: 'Inter', 'Segoe UI', sans-serif !important;
        }
        
        /* Título VERO Smart Systems */
        h1 {
            color: #ffffff !important;
            font-weight: 700 !important;
        }

        /* 4. CAMPOS DE DIGITAÇÃO LIMPOS */
        .stTextInput input, .stNumberInput input, div[data-baseweb="select"], .stTextArea textarea {
            background-color: #131418 !important; /* Fundo do input afunda na mesma cor da tela */
            color: #ffffff !important;
            border: 1px solid #2b2d38 !important;
            border-radius: 8px !important;
            padding: 12px !important;
        }
        
        /* Foco ao digitar (A linha fica Ciano) */
        .stTextInput input:focus, .stNumberInput input:focus {
            border: 1px solid #4bc0c0 !important;
            box-shadow: none !important;
        }

        /* 5. BOTÕES "OUTLINE" MODERNOS */
        .stButton > button {
            background-color: transparent !important;
            color: #4bc0c0 !important; 
            border: 1px solid #4bc0c0 !important; 
            border-radius: 8px !important;
            height: 45px !important;
            font-weight: 600 !important;
            letter-spacing: 1px !important;
            transition: 0.2s !important;
        }

        /* Efeito Hover do Botão */
        .stButton > button:hover {
            background-color: #4bc0c0 !important;
            color: #131418 !important;
        }
        
        /* 6. ESTILIZANDO AS ABAS (Login / Cadastro) */
        button[data-baseweb="tab"] {
            background-color: transparent !important;
            color: #6b7280 !important;
        }
        button[data-baseweb="tab"][aria-selected="true"] {
            color: #4bc0c0 !important;
            border-bottom: 2px solid #4bc0c0 !important;
        }
        button[data-baseweb="tab"] p {
            font-size: 16px !important;
            font-weight: 600 !important;
        }
    </style>
    """, unsafe_allow_html=True)
