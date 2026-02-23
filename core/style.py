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

        /* CORREÇÃO DE SOBREPOSIÇÃO: Limpa bordas duplas */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background: rgba(255, 255, 255, 0.03) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 24px !important;
            padding: 25px !important;
            margin-bottom: 10px !important;
            box-shadow: 0 4px 20px rgba(0,0,0,0.2) !important;
        }

        .stButton > button {
            border-radius: 14px !important;
            height: 50px !important;
            background: #ffffff !important;
            color: #020617 !important;
            font-weight: 700 !important;
            border: none !important;
            transition: all 0.3s ease !important;
        }

        .stButton > button:hover {
            background: #3b82f6 !important;
            color: white !important;
            transform: translateY(-2px);
        }

        .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
            background-color: rgba(255, 255, 255, 0.05) !important;
            border-radius: 12px !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            color: white !important;
        }
    </style>
    """, unsafe_allow_html=True)
