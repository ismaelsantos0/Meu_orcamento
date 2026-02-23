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

        /* Cards Arredondados */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background: rgba(255, 255, 255, 0.03) !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            border-radius: 28px !important;
            padding: 20px !important;
        }

        /* Botões Premium */
        .stButton > button {
            border-radius: 18px !important;
            height: 55px !important;
            background: #ffffff !important;
            color: #020617 !important;
            font-weight: 700 !important;
            border: none !important;
            transition: all 0.3s ease !important;
        }

        .stButton > button:hover {
            transform: translateY(-2px) !important;
            background: #3b82f6 !important;
            color: white !important;
            box-shadow: 0 10px 20px rgba(59, 130, 246, 0.3) !important;
        }

        .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
            background-color: rgba(255, 255, 255, 0.05) !important;
            border-radius: 15px !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            color: white !important;
        }
    </style>
    """, unsafe_allow_html=True)
