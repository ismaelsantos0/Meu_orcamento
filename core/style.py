import streamlit as st

def apply_vero_style():
    st.markdown("""
    <style>
        /* Oculta o cabeçalho e rodapé padrão do Streamlit */
        header {visibility: hidden !important;}
        footer {visibility: hidden !important;}
        
        /* 1. FUNDO GERAL COM GRADIENTE (Muda o preto chapado para um fundo azul-petróleo escuro profundo) */
        .stApp {
            background: radial-gradient(circle at top left, #1a2a3a, #17181c, #0f141a) !important; 
        }

        /* 2. EFEITO GLASSMORPHISM NOS CARDS (O Segredo do Vidro Fosco) */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background: rgba(30, 32, 38, 0.45) !important; /* Fundo quase transparente */
            backdrop-filter: blur(16px) !important;        /* O desfoque que cria o vidro */
            -webkit-backdrop-filter: blur(16px) !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important; /* Borda branca bem suave dando brilho */
            border-radius: 20px !important;       /* Cantos bem redondos */
            padding: 10px !important;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.4) !important; /* Sombra projetada para dar profundidade */
        }

        /* 3. CORES DE TEXTO PADRÃO */
        h1, h2, h3, p, span, label, li {
            color: #e2e8f0 !important;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
        }

        /* 4. CAMPOS DE INPUT (Ficam escuros e semi-transparentes para não quebrar o vidro) */
        .stTextInput input, .stNumberInput input, div[data-baseweb="select"], .stTextArea textarea {
            background: rgba(0, 0, 0, 0.25) !important; 
            color: white !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 10px !important;
        }
        
        /* Quando o usuário clica para digitar, a borda brilha em ciano */
        .stTextInput input:focus, .stNumberInput input:focus {
            border: 1px solid #4bc0c0 !important;
            box-shadow: 0 0 8px rgba(75, 192, 192, 0.3) !important;
        }

        /* 5. BOTÕES PREMIUM COM GRADIENTE */
        .stButton > button {
            background: linear-gradient(135deg, rgba(38, 39, 47, 0.8), rgba(23, 24, 28, 0.8)) !important;
            color: #4bc0c0 !important; 
            border: 1px solid rgba(75, 192, 192, 0.4) !important; 
            border-radius: 12px !important;
            height: 48px !important;
            font-weight: bold !important;
            transition: all 0.3s ease-in-out !important;
        }

        /* Efeito Hover do Botão: Acende ao passar o mouse */
        .stButton > button:hover {
            background: #4bc0c0 !important;
            color: #17181c !important;
            box-shadow: 0 0 15px rgba(75, 192, 192, 0.5) !important;
            border: 1px solid #4bc0c0 !important; 
        }
        
        /* Ajuste sutil para os botões das Abas de Login (Entrar / Criar Conta) */
        button[data-baseweb="tab"] p {
            font-size: 16px !important;
            font-weight: 500 !important;
        }
    </style>
    """, unsafe_allow_html=True)
