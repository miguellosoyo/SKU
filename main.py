# Importrar librerías de trabajo
import streamlit as st

# Integrar configuración
st.set_page_config(page_title='SKU - Stock Keeping Unit for TWW Positions', page_icon=':bar_chart:', layout='wide')

# Integrar título
st.title('Stock Keeping Unit App 🧠')

# Integrar un sidebar
sidebar = st.sidebar
with sidebar:
    st.title('Navegador')