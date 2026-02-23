import streamlit as st

def apply_vero_style():
    st.markdown("""
    <style>
        /* Estilo base do VERO */
        header, footer, [data-testid="stSidebar"] { visibility: hidden; display: none; }
        
        .stApp {
            background: #020617;
            background-image: radial-gradient(at 0% 0%, rgba(59, 130, 246, 0.05) 0px, transparent 50%);
        }

        /* Cards Arredondados com Glassmorphism Avançado */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background: rgba(255, 255, 255, 0.02) !important;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.05) !important;
            border-radius: 30px !important;
            padding: 30px !important;
            transition: border 0.3s ease, box-shadow 0.3s ease !important;
        }

        div[data-testid="stVerticalBlockBorderWrapper"]:hover {
            border-color: rgba(59, 130, 246, 0.4) !important;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4) !important;
        }

        /* Botões com Glow Effect */
        .stButton > button {
            border-radius: 20px !important;
            background: linear-gradient(135deg, #ffffff 0%, #f1f5f9 100%) !important;
            border: none !important;
            color: #020617 !important;
            font-weight: 800 !important;
            box-shadow: 0 0 0 rgba(59, 130, 246, 0);
            transition: 0.4s !important;
        }

        .stButton > button:hover {
            box-shadow: 0 0 20px rgba(59, 130, 246, 0.4) !important;
            background: #3b82f6 !important;
            color: white !important;
        }
    </style>
    """, unsafe_allow_html=True)
