import streamlit as st

def apply_vero_style():
    st.markdown("""
    <style>
        /* EXTERMINA A BARRA LATERAL, NAVEGAÇÃO E O CABEÇALHO PADRÃO */
        header {visibility: hidden !important;}
        footer {visibility: hidden !important;}
        
        /* Remove a navegação automática da pasta 'pages/' e a seta de abrir */
        [data-testid="stSidebarNav"] {display: none !important;}
        [data-testid="collapsedControl"] {display: none !important;}
        section[data-testid="stSidebar"] {display: none !important; width: 0px !important;}
        
        /* Fundo escuro padrão VERO */
        .stApp {
            background-color: #0b0f19;
            color: #ffffff;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }

        /* Menu Superior (Abas) - Design Seguro */
        .stTabs [data-baseweb="tab-list"] {
            background-color: #1a2235;
            padding: 10px;
            border-radius: 15px;
            gap: 10px;
            border: 1px solid #2d3748;
        }

        .stTabs [data-baseweb="tab"] {
            color: #a0aec0;
            font-weight: 600;
            padding: 10px 20px;
            border-radius: 8px;
            background-color: transparent;
            border: none;
        }

        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
            color: white !important;
        }

        /* Caixas de Texto e Inputs Visíveis */
        .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"], .stTextArea textarea {
            background-color: #1a2235 !important;
            color: white !important;
            border: 1px solid #2d3748 !important;
            border-radius: 8px !important;
        }

        /* Botão Principal */
        .stButton > button {
            background-color: #1a2235 !important;
            color: white !important;
            border: 1px solid #2d3748 !important;
            border-radius: 10px !important;
            height: 50px !important;
            font-weight: bold !important;
            transition: 0.3s;
        }

        .stButton > button:hover {
            border-color: #3b82f6 !important;
            background-color: #2563eb !important;
        }
    </style>
    """, unsafe_allow_html=True)
