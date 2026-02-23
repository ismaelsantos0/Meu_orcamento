import streamlit as st

def apply_vero_style():
    st.markdown("""
    <style>
        header, footer, [data-testid="stSidebar"] { visibility: hidden; display: none; }
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;700;800&display=swap');
        
        .stApp {
            background: #05080a;
            background-image: radial-gradient(at 0% 0%, rgba(59, 130, 246, 0.1) 0px, transparent 50%);
            font-family: 'Plus Jakarta Sans', sans-serif;
            color: #ffffff;
        }

        /* Container de Cards Arredondados */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background: rgba(255, 255, 255, 0.03) !important;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 32px !important;
            padding: 30px !important;
            margin-bottom: 20px !important;
        }

        /* Botões com Design Moderno */
        .stButton > button {
            border-radius: 20px !important;
            background: linear-gradient(135deg, #ffffff 0%, #e2e8f0 100%) !important;
            color: #020617 !important;
            font-weight: 800 !important;
            height: 55px !important;
            border: none !important;
            transition: 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
        }

        .stButton > button:hover {
            transform: scale(1.03) !important;
            background: #3b82f6 !important;
            color: white !important;
            box-shadow: 0 15px 30px rgba(59, 130, 246, 0.4) !important;
        }

        /* Inputs Arredondados */
        .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
            background-color: rgba(255, 255, 255, 0.05) !important;
            border-radius: 18px !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            color: white !important;
        }
    </style>
    """, unsafe_allow_html=True)
