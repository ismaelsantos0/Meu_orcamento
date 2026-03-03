import streamlit as st

def apply_vero_style():
    st.markdown("""
    <style>
        /* Oculta cabeçalho e rodapé */
        header {visibility: hidden !important;}
        footer {visibility: hidden !important;}
        
        /* 1. FUNDO GERAL (Quase preto, igual à referência) */
        .stApp {
            background-color: #0a0a0b !important; 
        }

        /* 2. REMOVER BORDAS DOS CONTAINERS (Deixa o form "flat" na tela) */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: transparent !important; 
            border: none !important;              
            box-shadow: none !important; 
            padding: 0px !important;
        }

        /* 3. TIPOGRAFIA CLEAN */
        h1, h2, h3, p, span, label, li {
            color: #ffffff !important;
            font-family: 'Inter', 'Segoe UI', sans-serif !important;
        }

        /* 4. CAMPOS DE DIGITAÇÃO MINIMALISTAS */
        .stTextInput input, .stNumberInput input, div[data-baseweb="select"], .stTextArea textarea {
            background-color: transparent !important; 
            color: #ffffff !important;
            border: 1px solid #333333 !important; /* Borda bem fina e escura */
            border-radius: 6px !important;
            padding: 14px !important;
        }
        
        /* Foco ao digitar (Borda fica azul clara) */
        .stTextInput input:focus, .stNumberInput input:focus {
            border: 1px solid #3b82f6 !important;
            box-shadow: none !important;
        }

        /* 5. BOTÃO PRINCIPAL (Azul Vibrante Sólido) */
        .stButton > button {
            background-color: #2563eb !important; /* Azul da referência */
            color: #ffffff !important; 
            border: none !important; 
            border-radius: 6px !important;
            height: 50px !important;
            font-weight: 600 !important;
            letter-spacing: 0.5px !important;
            transition: 0.3s !important;
            width: 100% !important; /* Botão largo */
        }

        /* Hover do Botão */
        .stButton > button:hover {
            background-color: #1d4ed8 !important; /* Azul mais escuro no hover */
            color: #ffffff !important;
        }
        
        /* 6. ESTILIZANDO AS ABAS (Login / Cadastro) */
        button[data-baseweb="tab"] {
            background-color: transparent !important;
            color: #6b7280 !important;
            padding-left: 0 !important; /* Alinha à esquerda */
        }
        button[data-baseweb="tab"][aria-selected="true"] {
            color: #ffffff !important;
            border-bottom: 2px solid #2563eb !important;
        }
        
        /* 7. IMAGEM DA DIREITA */
        .img-direita img {
            border-radius: 16px;
            object-fit: cover;
            height: 75vh;
            width: 100%;
            opacity: 0.8;
        }
    </style>
    """, unsafe_allow_html=True)
