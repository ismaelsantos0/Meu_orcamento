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

        /* Navbar Estilo Cápsula */
        .navbar {
            background: rgba(22, 27, 34, 0.8);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            padding: 10px 30px;
            display: flex;
            justify-content: center;
            gap: 20px;
            position: sticky;
            top: 10px;
            z-index: 999;
            margin-bottom: 40px;
        }

        /* Estilização dos Tabs do Streamlit para parecerem com o Menu */
        .stTabs [data-baseweb="tab-list"] {
            gap: 15px;
            background-color: #161b22;
            padding: 8px;
            border-radius: 20px;
            border: 1px solid rgba(255,255,255,0.1);
            justify-content: center;
        }

        .stTabs [data-baseweb="tab"] {
            height: 50px;
            white-space: pre;
            background-color: transparent;
            border-radius: 12px;
            color: #8b949e;
            font-weight: 600;
            border: none;
            transition: 0.3s;
        }

        .stTabs [aria-selected="true"] {
            background-image: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
            color: white !important;
        }

        /* Cards de Conteúdo */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background: rgba(22, 27, 34, 0.5) !important;
            border: 1px solid rgba(255, 255, 255, 0.05) !important;
            border-radius: 24px !important;
        }
    </style>
    """, unsafe_allow_html=True)
