import streamlit as st

def apply_vero_style():
    st.markdown("""
    <style>
        /* Limpeza de interface */
        header, footer, [data-testid="stSidebar"] { visibility: hidden; display: none; }
        
        /* Fundo Sólido para evitar que elementos sumam */
        .stApp {
            background-color: #0e1117;
            color: #ffffff;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }

        /* Navbar Superior Azul (Estilo Abas) */
        .stTabs [data-baseweb="tab-list"] {
            background-color: #161b22;
            border-radius: 10px;
            padding: 5px;
            border: 1px solid #30363d;
            justify-content: center;
        }

        .stTabs [data-baseweb="tab"] {
            color: #8b949e;
            font-weight: bold;
        }

        .stTabs [aria-selected="true"] {
            background-color: #238636 !important; /* Verde ou Azul de sua preferência */
            border-radius: 8px;
            color: white !important;
        }

        /* Containers Visíveis (Cards) */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #161b22 !important;
            border: 1px solid #30363d !important;
            border-radius: 15px !important;
            padding: 20px !important;
            margin-bottom: 20px !important;
        }

        /* Botões visíveis */
        .stButton > button {
            border-radius: 10px !important;
            background-color: #21262d !important;
            color: white !important;
            border: 1px solid #30363d !important;
            height: 45px;
        }

        .stButton > button:hover {
            border-color: #8b949e !important;
        }
    </style>
    """, unsafe_allow_html=True)
