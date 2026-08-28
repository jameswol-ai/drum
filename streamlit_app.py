# streamlit_app.py
# (Full file with all 10 features integrated)

import streamlit as st
import uuid
from datetime import datetime
import random
import math
import os
import json
import matplotlib.pyplot as plt

from main import (
    load_users, save_users, get_user, create_user, authenticate,
    update_user_data, xp_for_level, add_xp, load_memory, save_memory,
    log_event, Building, generate_plan, simulate_evolution, generate_rhythm,
    init_quests, update_quests, grant_quest_rewards, DEFAULT_STATE,
    list_users, update_user_role, delete_user, is_admin, is_engineer,
    save_analysis, get_analyses, delete_analysis, update_analysis,
    get_project_templates, get_material_costs, update_material_costs,
    get_theme, update_theme, share_project, get_shared_projects
)

# ... (imports remain the same)

# Theme handling
theme = get_theme(st.session_state.username) if st.session_state.get("logged_in") else "dark"

if theme == "light":
    background = "#F8FAFC"
    text = "#1E293B"
    card_bg = "#FFFFFF"
    border = "#E2E8F0"
else:
    background = "#0F172A"
    text = "#E2E8F0"
    card_bg = "#1E293B"
    border = "#334155"

# Dynamic CSS based on theme
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

html, body, .stApp {{
    font-family: 'Inter', sans-serif;
    background: {background}; color: {text};
}}
h1, h2, h3 {{ color: {text}; font-weight: 600; }}

.stButton>button {{
    background: linear-gradient(135deg, #3B82F6, #2563EB);
    color: white; border: none; border-radius: 8px;
    padding: 0.5rem 1.5rem; font-weight: 600;
    transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
}}

.stNumberInput>div>div>input,
.stTextInput>div>div>input {{
    background: {card_bg}; color: {text};
    border: 1px solid {border};
}}

.stSelectbox>div>div>select {{
    background: {card_bg}; color: {text};
}}

.stExpander {{
    background: {card_bg};
    border: 1px solid {border};
    border-radius: 12px;
}}
</style>
""", unsafe_allow_html=True)

# ... (rest of the app with new features)

# Project Dashboard - Create Project with Template
if page == "Project Dashboard":
    st.title("Project Dashboard")

    left_col, right_col = st.columns([1, 3])

    with left_col:
        st.markdown("### Project Tools")
        if is_engineer(user_data):
            # Project Template Selection
            templates = get_project_templates()
            template_names = list(templates.keys())
            
            project_name = st.text_input("Project Name", key="project_name_input")
            template_choice = st.selectbox("Template (optional)", ["None"] + template_names, key="template_choice")
            num_storeys = st.number_input("Number of Storeys", 1, 20, 1, key="num_storeys")
            
            if st.button("Create Project", use_container_width=True):
                if project_name.strip() == "":
                    st.error("Please enter a project name.")
                else:
                    new_building = Building(
                        name=project_name,
                        score=50,
                        building_type=template_choice if template_choice != "None" else "custom",
                        storeys=num_storeys
                    )
                    generate_safe_plan(new_building, num_rooms=4, grid_spacing_mm=500)
                    mem["buildings"].append(new_building.to_dict())
                    st.session_state.active_building = new_building
                    st.session_state.show_grid = True
                    st.session_state.grid_spacing_mm = 500
                    log_event(username, mem, f"Created project: {new_building.name}")
                    save_memory(username, mem)
                    st.rerun()

            # Share Project
            if st.session_state.active_building:
                st.markdown("---")
                st.markdown("### Share Project")
                share_username = st.text_input("Share with username", key="share_username")
                if st.button("Share", key="share_btn"):
                    if share_username.strip():
                        if share_project(username, st.session_state.active_building.id, share_username):
                            st.success(f"Shared with {share_username}")
                        else:
                            st.info("Already shared with this user")
                    else:
                        st.error("Enter a username")

        # Multi-storey floors
        if st.session_state.active_building:
            st.markdown("---")
            st.markdown("### Floors")
            building = st.session_state.active_building
            for floor_num in range(1, building.storeys + 1):
                if st.button(f"Floor {floor_num}", key=f"floor_{floor_num}", use_container_width=True):
                    st.session_state.active_floor = floor_num
                    st.rerun()

# Material Costs Page (in sidebar)
with st.sidebar:
    # ... existing sidebar content ...
    
    # Material Costs Editor
    with st.expander("Material Costs"):
        costs = get_material_costs(username)
        new_concrete = st.number_input("Concrete ($/m²)", 50, 500, costs.get("concrete", 150), key="cost_concrete")
        new_steel = st.number_input("Steel ($/m²)", 20, 300, costs.get("steel", 80), key="cost_steel")
        new_glass = st.number_input("Glass ($/m²)", 50, 500, costs.get("glass", 120), key="cost_glass")
        new_labor = st.number_input("Labor ($/m²)", 20, 300, costs.get("labor", 100), key="cost_labor")
        if st.button("Update Costs", key="update_costs"):
            update_material_costs(username, {
                "concrete": new_concrete,
                "steel": new_steel,
                "glass": new_glass,
                "labor": new_labor,
            })
            st.success("Costs updated!")

    # Theme Toggle
    with st.expander("Appearance"):
        current_theme = get_theme(username)
        new_theme = st.radio("Theme", ["dark", "light"], index=0 if current_theme == "dark" else 1, key="theme_toggle")
        if new_theme != current_theme:
            update_theme(username, new_theme)
            st.rerun()

# Export to DXF (simplified)
def export_to_dxf(plan, filename):
    """Export plan to DXF format."""
    dxf_content = "0\nSECTION\n2\nENTITIES\n"
    for room in plan:
        x, y, w, h = room["x"], room["y"], room["w"], room["h"]
        # LINE entity
        dxf_content += f"0\nLINE\n8\n0\n10\n{x}\n20\n{y}\n11\n{x+w}\n21\n{y}\n"
        dxf_content += f"0\nLINE\n8\n0\n10\n{x+w}\n20\n{y}\n11\n{x+w}\n21\n{y+h}\n"
        dxf_content += f"0\nLINE\n8\n0\n10\n{x+w}\n20\n{y+h}\n11\n{x}\n21\n{y+h}\n"
        dxf_content += f"0\nLINE\n8\n0\n10\n{x}\n20\n{y+h}\n11\n{x}\n21\n{y}\n"
    dxf_content += "0\nENDSEC\n0\nEOF\n"
    with open(filename, "w") as f:
        f.write(dxf_content)
    return filename

# In Export section, add DXF export
with st.expander("Export & Share", expanded=False):
    if st.button("Download Plan as SVG"):
        svg_content = generate_svg_string(plan, show_grid=False, show_north=False, show_dimensions=False)
        st.download_button("Download SVG", svg_content, file_name=f"{building.name}_plan.svg", mime="image/svg+xml")
    if st.button("Export to DXF"):
        dxf_filename = f"{building.name}_plan.dxf"
        export_to_dxf(plan, dxf_filename)
        with open(dxf_filename, "rb") as f:
            st.download_button("Download DXF", f, file_name=dxf_filename, mime="application/dxf")
    if st.button("Export Summary PDF"):
        # ... PDF export code