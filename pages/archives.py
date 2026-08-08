# pages/archives.py
import streamlit as st
from main import Building
from utils import render_svg_plan

def render_archives():
    st.title("🗄️ Project Archives")
    mem = st.session_state.memory
    if mem.get("buildings"):
        for bdict in reversed(mem["buildings"]):
            building = Building.from_dict(bdict)
            with st.expander(f"{building.name} – Score {building.score}"):
                if building.plan:
                    svg = render_svg_plan(building.plan)
                    st.markdown(f'<div style="background:#0F172A; border-radius:12px; padding:8px; border:1px solid #334155;">{svg}</div>', unsafe_allow_html=True)
                else:
                    st.write("No plan data.")
    else:
        st.info("No projects yet. Go to the Project Dashboard to create one.")