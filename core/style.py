import streamlit as st

def apply_vero_style():
    st.markdown("""
    <style>
        header, footer, [data-testid="stSidebar"] { visibility: hidden; display: none; }
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;700;800&display=swap');
        
        .stApp {
            background: #0d1117;
            font-family: 'Plus Jakarta Sans', sans-serif;
            color: #ffffff;
        }

        /* Menu Superior (Tabs) Estilo Cápsula */
        .stTabs [data-baseweb="tab-list"] {
            gap: 10px;
            background-color: #161b22;
            padding: 8px 15px;
            border-radius: 20px;
            border: 1px solid rgba(255,255,255,0.1);
            justify-content: center;
            position: sticky;
            top: 10px;
            z-index: 999;
        }

        .stTabs [data-baseweb="tab"] {
            height: 45px;
            background-color: transparent;
            border-radius: 12px;
            color: #8b949e;
            font-weight: 600;
            border: none;
            padding: 0 20px;
        }

        /* Estilo Azul para o Tab Selecionado conforme imagem */
        .stTabs [aria-selected="true"] {
            background-image: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
            color: white !important;
            box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
        }

        /* Cards de Conteúdo Arredondados */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background: rgba(22, 27, 34, 0.5) !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            border-radius: 28px !important;
            padding: 25px !important;
        }

        .stButton > button {
            border-radius: 16px !important;
            height: 50px !important;
            font-weight: 700 !important;
            transition: 0.3s !important;
        }
    </style>
    """, unsafe_allow_html=True)
