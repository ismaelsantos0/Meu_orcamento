import streamlit as st

def apply_vero_style():
    st.markdown("""
    <style>
        header {visibility: hidden;} 
        footer {visibility: hidden;}
        [data-testid="stSidebar"] { display: none; }
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
        
        .stApp {
            background: radial-gradient(circle at 20% 20%, #0f172a 0%, #020617 100%);
            font-family: 'Inter', sans-serif;
            color: #f8fafc;
        }

        /* CORREÇÃO: Remove a sobreposição de cards */
        [data-testid="stVerticalBlock"] > div:has(div[data-testid="stVerticalBlockBorderWrapper"]) {
            padding: 0px !important;
            margin-bottom: 1rem !important;
        }

        div[data-testid="stVerticalBlockBorderWrapper"] {
            background: rgba(255, 255, 255, 0.03) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 24px !important;
            padding: 30px !important;
            margin: 0px !important;
            height: 100% !important;
            box-shadow: 0 4px 20px rgba(0,0,0,0.2) !important;
        }

        /* Ajuste de Botões para não ficarem colados */
        .stButton > button {
            margin-top: 15px !important;
            border-radius: 14px !important;
            height: 50px !important;
            background: #ffffff !important;
            color: #020617 !important;
            font-weight: 700 !important;
            border: none !important;
            width: 100% !important;
        }

        .stButton > button:hover {
            background: #3b82f6 !important;
            color: white !important;
            transform: translateY(-2px);
        }

        /* Títulos mais limpos */
        h1, h2, h3 {
            margin-bottom: 1rem !important;
            font-weight: 800 !important;
        }
    </style>
    """, unsafe_allow_html=True)
