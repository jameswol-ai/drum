# streamlit_app.py
import streamlit as st
from main import load_users, create_user, authenticate, save_memory, load_memory
from utils import inject_css
from pages.project_dashboard import render_project_dashboard
from pages.structural_analysis import render_structural_analysis
from pages.archives import render_archives

# ---------- Page Config ----------
st.set_page_config(page_title="DRUM Studio", page_icon="🏗️", layout="wide",
                   initial_sidebar_state="expanded",
                   menu_items={"Get Help": None, "Report a bug": None, "About": None})

inject_css()

# ---------- Session State ----------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.user_data = None
    st.session_state.memory = None
    st.session_state.active_building = None
    st.session_state.unit_system = "metric"
    # ... other defaults (eng_params, etc.)

# Auto‑create admin if no users exist
if not load_users():
    create_user("admin", "admin123", role="admin")

# ---------- Login ----------
if not st.session_state.logged_in:
    # ... login/register form (unchanged) ...
    st.stop()

# ---------- Sidebar (shared) ----------
username = st.session_state.username
user_data = st.session_state.user_data
mem = st.session_state.memory

with st.sidebar:
    # Logo and user info (same as before)
    st.markdown("""...""", unsafe_allow_html=True)
    st.markdown(f"### 👷 {username}")
    st.caption("Structural Engineer")

    # Page navigation
    page = st.radio("Navigate",
                    ["Project Dashboard", "Structural Analysis", "Archives"],
                    index=["Project Dashboard", "Structural Analysis", "Archives"].index(st.session_state.page) if "page" in st.session_state else 0)
    st.session_state.page = page

    # Unit system
    unit_choice = st.radio("Unit System", ["metric", "imperial"], index=0)
    st.session_state.unit_system = unit_choice

    # Analysis defaults (expandable)
    with st.expander("🔧 Analysis Defaults"):
        # ... same number_inputs ...
        pass

    if st.button("🚪 Logout"):
        save_memory(username, st.session_state.memory)
        # Clear session
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# ---------- Render Page ----------
if page == "Project Dashboard":
    render_project_dashboard()
elif page == "Structural Analysis":
    render_structural_analysis()
else:  # Archives
    render_archives()