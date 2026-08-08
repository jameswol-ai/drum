import streamlit as st
from main import Building
from utils import render_svg_plan

def render_archives():
    st.title("🗄️ Project Archives")
    mem = st.session_state.memory
    # ... loop over buildings and render plans ...