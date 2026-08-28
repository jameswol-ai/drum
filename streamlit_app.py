# streamlit_app.py
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

from engineering.materials import CONCRETE_GRADES, STEEL_GRADES, TIMBER_CLASSES, WALL_TYPES, FINISHES
from engineering.beams import check_rc_beam, check_steel_beam, check_timber_beam, check_composite_beam
from engineering.columns import check_rc_column
from engineering.slabs import slab_thickness_estimate
from engineering.foundations import foundation_size
from engineering.piles import pile_capacity
from engineering.prestressed import check_prestressed_beam
from engineering.retaining import retaining_wall_stability
from engineering.truss import truss_analysis
from engineering.connections import steel_connection_check
from engineering.load_combinations import load_combinations
from engineering.seismic import seismic_base_shear
from engineering.cost import calculate_total_area, compute_floor_loads, check_structural_integrity, calculate_energy_score, estimate_cost
from engineering.pdf_report import generate_pdf_report, generate_analysis_report
from engineering.visualization import plot_beam_diagrams, plot_truss_deformed

import eurocodes.en1990 as ec0
import eurocodes.en1991 as ec1
import eurocodes.en1992 as ec2
import eurocodes.en1993 as ec3
import eurocodes.en1994 as ec4
import eurocodes.en1995 as ec5
import eurocodes.en1996 as ec6
import eurocodes.en1997 as ec7
import eurocodes.en1998 as ec8
import eurocodes.en1999 as ec9

st.set_page_config(page_title="DRUM Studio", page_icon="🏗️", layout="wide",
                   initial_sidebar_state="expanded",
                   menu_items={"Get Help": None, "Report a bug": None, "About": None})

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.user_data = None
    st.session_state.memory = DEFAULT_STATE.copy()
    st.session_state.active_building = None
    st.session_state.unit_system = "metric"
    st.session_state.eng_params = {
        "live_load": 2.5,
        "slab_thickness": 0.2,
        "additional_dead": 1.0,
        "concrete_cost": 250,
        "steel_cost": 50,
        "glass_cost": 150,
        "labor_cost": 100,
        "glazing_ratio": 0.2,
        "orientation": "south",
    }
    st.session_state.page = "Project Dashboard"
    st.session_state.show_grid = True
    st.session_state.grid_spacing_mm = 500
    st.session_state.show_north = False
    st.session_state.show_dimensions = True
    st.session_state.project_name = ""
    st.session_state.active_floor = 1

if not load_users():
    admin_user = os.environ.get("DRUM_ADMIN_USER", "admin")
    admin_pass = os.environ.get("DRUM_ADMIN_PASS", None)
    if admin_pass is None:
        admin_pass = "admin123"
        print("WARNING: Using default admin password. Set DRUM_ADMIN_PASS env variable.")
    create_user(admin_user, admin_pass, role="admin")

# Theme
theme = "dark"
if st.session_state.get("logged_in") and st.session_state.get("username"):
    theme = get_theme(st.session_state.username)

if theme == "light":
    bg_color = "#F8FAFC"
    text_color = "#1E293B"
    card_bg = "#FFFFFF"
    border_color = "#E2E8F0"
else:
    bg_color = "#0F172A"
    text_color = "#E2E8F0"
    card_bg = "#1E293B"
    border_color = "#334155"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

html, body, .stApp {{
    font-family: 'Inter', sans-serif;
    background: {bg_color}; color: {text_color};
}}
h1, h2, h3 {{ color: {text_color}; font-weight: 600; }}

.stButton>button {{
    background: linear-gradient(135deg, #3B82F6, #2563EB);
    color: white; border: none; border-radius: 8px;
    padding: 0.5rem 1.5rem; font-weight: 600;
    transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    background-size: 200% auto;
}}
.stButton>button:hover {{
    transform: translateY(-2px);
    box-shadow: 0 8px 16px rgba(59, 130, 246, 0.4);
}}

.stNumberInput>div>div>input,
.stTextInput>div>div>input {{
    background: {card_bg}; color: {text_color};
    border: 1px solid {border_color};
}}

.stSelectbox>div>div>select {{
    background: {card_bg}; color: {text_color};
}}

.stTabs [data-baseweb="tab-list"] {{ gap: 8px; }}
.stTabs [data-baseweb="tab"] {{
    background-color: {card_bg};
    border-radius: 8px 8px 0 0;
    padding: 8px 16px;
    color: #94A3B8;
}}
.stTabs [aria-selected="true"] {{
    background-color: {border_color};
    color: {text_color};
}}

.stExpander {{
    background: {card_bg};
    border: 1px solid {border_color};
    border-radius: 12px;
    margin-bottom: 10px;
}}

.news-card {{
    background: {card_bg};
    border: 1px solid {border_color};
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 12px;
}}
.news-title {{ font-weight: 600; color: {text_color}; font-size: 1.1rem; }}
.news-date {{ color: #94A3B8; font-size: 0.8rem; }}
.news-summary {{ color: {text_color}; font-size: 0.9rem; line-height: 1.5; }}
.project-header {{
    background: linear-gradient(135deg, {card_bg}, {border_color});
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 20px;
    border: 1px solid #3B82F6;
}}

/* Mobile responsive */
@media (max-width: 768px) {{
    .stButton>button {{ width: 100%; }}
}}
</style>
""", unsafe_allow_html=True)

def input_metric(value, unit_type):
    if st.session_state.unit_system == "imperial":
        conversions = {
            "length": 0.3048,
            "length_mm": 0.0254,
            "area": 0.092903,
            "force": 4.44822,
            "pressure": 6.89476,
            "moment": 1.35582,
            "weight_density": 0.157087
        }
        if unit_type in conversions:
            return value * conversions[unit_type]
    return value

def output_metric(value, unit_type):
    if st.session_state.unit_system == "imperial":
        conversions = {
            "length": 3.28084,
            "length_mm": 39.3701,
            "area": 10.7639,
            "force": 0.224809,
            "pressure": 0.145038,
            "moment": 0.737562,
            "weight_density": 6.36588,
            "stress": 0.145038
        }
        if unit_type in conversions:
            return value * conversions[unit_type]
    return value

def unit_label(unit_type):
    labels = {
        "length": "m" if st.session_state.unit_system == "metric" else "ft",
        "length_mm": "mm" if st.session_state.unit_system == "metric" else "in",
        "area": "m²" if st.session_state.unit_system == "metric" else "ft²",
        "force": "kN" if st.session_state.unit_system == "metric" else "kip",
        "pressure": "kPa" if st.session_state.unit_system == "metric" else "psi",
        "moment": "kNm" if st.session_state.unit_system == "metric" else "kip-ft",
        "weight_density": "kN/m³" if st.session_state.unit_system == "metric" else "pcf",
        "stress": "MPa" if st.session_state.unit_system == "metric" else "ksi",
    }
    return labels.get(unit_type, "")

def generate_svg_string(plan, width=800, height=500,
                        show_grid=False, grid_spacing_mm=1000,
                        show_north=False, orientation="north",
                        show_dimensions=True):
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" id="plan-svg" style="width:100%; background:{bg_color};">'
    if show_grid and grid_spacing_mm > 0:
        x = 0
        while x <= width:
            svg += f'<line x1="{x}" y1="0" x2="{x}" y2="{height}" stroke="{border_color}" stroke-width="0.5" stroke-dasharray="4,4"/>'
            x += grid_spacing_mm
        y = 0
        while y <= height:
            svg += f'<line x1="0" y1="{y}" x2="{width}" y2="{y}" stroke="{border_color}" stroke-width="0.5" stroke-dasharray="4,4"/>'
            y += grid_spacing_mm
    for item in plan:
        x, y, w, h = item["x"], item["y"], item["w"], item["h"]
        color = item.get("color", "#4f46e5")
        name = item["name"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        svg += f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{color}" fill-opacity="0.4" stroke="#94a3b8" stroke-width="2"/>'
        svg += f'<text x="{x+w/2}" y="{y+h/2 - 8}" font-size="12" fill="{text_color}" text-anchor="middle" dominant-baseline="middle">{name}</text>'
        if show_dimensions:
            dims = f"{w}×{h} mm"
            svg += f'<text x="{x+w/2}" y="{y+h/2 + 12}" font-size="10" fill="#94a3b8" text-anchor="middle" dominant-baseline="middle">{dims}</text>'
    if show_north:
        arrow_x = width - 70
        arrow_y = 40
        svg += f'''
        <g transform="translate({arrow_x},{arrow_y})">
            <line x1="0" y1="20" x2="0" y2="0" stroke="#FBBF24" stroke-width="3"/>
            <polygon points="-6,8 0,0 6,8" fill="#FBBF24"/>
            <text x="0" y="30" text-anchor="middle" font-size="14" fill="#FBBF24" font-weight="bold">N</text>
        </g>
        '''
    svg += '</svg>'
    return svg

def update_building_plan(building, mem, username):
    for i, b in enumerate(mem["buildings"]):
        if b["id"] == building.id:
            mem["buildings"][i] = building.to_dict()
            break
    save_memory(username, mem)

def generate_safe_plan(building, num_rooms=4, grid_spacing_mm=500):
    colors = [
        "#3B82F6", "#EF4444", "#10B981", "#F59E0B", "#8B5CF6",
        "#EC4899", "#06B6D4", "#84CC16", "#F97316", "#6366F1"
    ]
    plan = []
    
    hall_w = min(600, max(grid_spacing_mm, round(random.randint(400, 600) / grid_spacing_mm) * grid_spacing_mm))
    hall_h = min(500, max(grid_spacing_mm, round(random.randint(400, 500) / grid_spacing_mm) * grid_spacing_mm))
    hall_x = max(0, round((400 - hall_w // 2) / grid_spacing_mm) * grid_spacing_mm)
    hall_y = max(0, round((250 - hall_h // 2) / grid_spacing_mm) * grid_spacing_mm)
    hall_x = min(hall_x, 800 - hall_w)
    hall_y = min(hall_y, 500 - hall_h)
    
    plan.append({
        "x": hall_x, "y": hall_y, "w": hall_w, "h": hall_h,
        "name": "Hall", "color": "#94A3B8"
    })
    
    directions = ["top", "bottom", "left", "right"]
    for i in range(num_rooms):
        parent = random.choice(plan)
        dir = random.choice(directions)
        
        new_w = min(600, max(grid_spacing_mm, round(random.randint(200, 600) / grid_spacing_mm) * grid_spacing_mm))
        new_h = min(400, max(grid_spacing_mm, round(random.randint(200, 400) / grid_spacing_mm) * grid_spacing_mm))
        
        gap = grid_spacing_mm
        
        if dir == "top":
            new_x = parent["x"] + (parent["w"] - new_w) // 2
            new_y = parent["y"] - new_h - gap
        elif dir == "bottom":
            new_x = parent["x"] + (parent["w"] - new_w) // 2
            new_y = parent["y"] + parent["h"] + gap
        elif dir == "left":
            new_x = parent["x"] - new_w - gap
            new_y = parent["y"] + (parent["h"] - new_h) // 2
        else:
            new_x = parent["x"] + parent["w"] + gap
            new_y = parent["y"] + (parent["h"] - new_h) // 2
        
        new_x = max(0, min(new_x, 800 - new_w))
        new_y = max(0, min(new_y, 500 - new_h))
        
        new_x = round(new_x / grid_spacing_mm) * grid_spacing_mm
        new_y = round(new_y / grid_spacing_mm) * grid_spacing_mm
        new_x = max(0, min(new_x, 800 - new_w))
        new_y = max(0, min(new_y, 500 - new_h))
        
        overlap = False
        for r in plan:
            if (new_x < r["x"] + r["w"] and new_x + new_w > r["x"] and
                new_y < r["y"] + r["h"] and new_y + new_h > r["y"]):
                overlap = True
                break
        if not overlap:
            plan.append({
                "x": new_x, "y": new_y, "w": new_w, "h": new_h,
                "name": f"Room {i+1}",
                "color": random.choice(colors)
            })
    building.plan = plan

def export_to_dxf(plan, filename):
    dxf_content = "0\nSECTION\n2\nENTITIES\n"
    for room in plan:
        x, y, w, h = room["x"], room["y"], room["w"], room["h"]
        dxf_content += f"0\nLINE\n8\n0\n10\n{x}\n20\n{y}\n11\n{x+w}\n21\n{y}\n"
        dxf_content += f"0\nLINE\n8\n0\n10\n{x+w}\n20\n{y}\n11\n{x+w}\n21\n{y+h}\n"
        dxf_content += f"0\nLINE\n8\n0\n10\n{x+w}\n20\n{y+h}\n11\n{x}\n21\n{y+h}\n"
        dxf_content += f"0\nLINE\n8\n0\n10\n{x}\n20\n{y+h}\n11\n{x}\n21\n{y}\n"
    dxf_content += "0\nENDSEC\n0\nEOF\n"
    with open(filename, "w") as f:
        f.write(dxf_content)
    return filename

def get_engineering_news():
    news = [
        {
            "title": "Eurocode Updates: EN 1992-1-1 Amendment Published",
            "date": "2024-11-15",
            "summary": "CEN has published an amendment to EN 1992-1-1 covering concrete structures."
        },
        {
            "title": "Advances in Structural Health Monitoring",
            "date": "2024-10-28",
            "summary": "New sensor technologies are enabling real-time monitoring of bridges and buildings."
        },
        {
            "title": "Mass Timber Construction Reaches New Heights",
            "date": "2024-10-05",
            "summary": "Cross-laminated timber (CLT) buildings are being constructed at record heights."
        },
        {
            "title": "AI in Structural Analysis: Machine Learning for Design",
            "date": "2024-09-20",
            "summary": "Machine learning algorithms are being integrated into structural analysis software."
        },
    ]
    return news

# ======================
# LOGIN PAGE
# ======================
if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""
        <div style="text-align:center; margin-bottom:10px;">
            <svg width="80" height="80" viewBox="0 0 80 80" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect width="80" height="80" rx="16" fill="url(#p0)"/>
                <path d="M24 56V32L40 24L56 32V56L40 64L24 56Z" stroke="white" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
                <circle cx="40" cy="44" r="6" fill="white"/>
                <path d="M40 36V28" stroke="white" stroke-width="3"/>
                <defs>
                    <linearGradient id="p0" x1="0" y1="0" x2="80" y2="80" gradientUnits="userSpaceOnUse">
                        <stop stop-color="#3B82F6"/>
                        <stop offset="1" stop-color="#2563EB"/>
                    </linearGradient>
                </defs>
            </svg>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<h1 style='text-align:center; font-weight:700; margin-bottom:0;'>DRUM Studio</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; color:#94A3B8;'>Structural Engineering Workstation</p>", unsafe_allow_html=True)
        with st.form("auth_form", clear_on_submit=True):
            uname = st.text_input("Username", placeholder="Enter username")
            pwd = st.text_input("Password", type="password", placeholder="Enter password")
            col1_btn, col2_btn = st.columns(2)
            with col1_btn:
                login_btn = st.form_submit_button("🔑 Login", use_container_width=True)
            with col2_btn:
                register_btn = st.form_submit_button("✨ Register", use_container_width=True)
            if login_btn:
                user = authenticate(uname, pwd)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.username = uname
                    st.session_state.user_data = user
                    st.session_state.memory = load_memory(uname)
                    st.rerun()
                else:
                    st.error("Invalid credentials.")
            if register_btn:
                if not uname or not pwd:
                    st.error("Fill all fields.")
                else:
                    try:
                        create_user(uname, pwd, role="engineer")
                        st.success("Account created! You can now log in.")
                    except ValueError as e:
                        st.error(str(e))
    st.stop()

# ======================
# MAIN APP
# ======================
username = st.session_state.username
user_data = st.session_state.user_data
mem = st.session_state.memory

with st.sidebar:
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 15px;">
        <svg width="40" height="40" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect width="40" height="40" rx="8" fill="url(#paint0_linear)"/>
            <path d="M12 28V16L20 12L28 16V28L20 32L12 28Z" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <circle cx="20" cy="22" r="3" fill="white"/>
            <path d="M20 18V14" stroke="white" stroke-width="2"/>
            <defs>
                <linearGradient id="paint0_linear" x1="0" y1="0" x2="40" y2="40" gradientUnits="userSpaceOnUse">
                    <stop stop-color="#3B82F6"/>
                    <stop offset="1" stop-color="#2563EB"/>
                </linearGradient>
            </defs>
        </svg>
        <div>
            <div style="font-weight: 700; font-size: 1.3rem; color: #F8FAFC; line-height: 1.2;">DRUM</div>
            <div style="font-size: 0.7rem; color: #94A3B8; letter-spacing: 1px;">STUDIO</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown(f"### {username}")
    st.caption(f"Role: {user_data.get('role', 'viewer')}")
    st.markdown("---")
    page = st.radio("Navigate",
                    ["Project Dashboard", "Structural Analysis", "Eurocodes", "Reports", "Archives"],
                    index=0,
                    key="nav_radio")
    st.session_state.page = page
    unit_choice = st.radio("Unit System", ["metric", "imperial"], index=0, key="unit_radio")
    st.session_state.unit_system = unit_choice

    with st.expander("Analysis Defaults"):
        st.session_state.eng_params["live_load"] = st.number_input(
            f"Live Load ({unit_label('pressure')})", 1.0, 10.0, st.session_state.eng_params["live_load"], 0.5, key="live_load")
        st.session_state.eng_params["slab_thickness"] = st.number_input(
            f"Slab Thickness ({unit_label('length')})", 0.1, 0.5, st.session_state.eng_params["slab_thickness"], 0.05, key="slab_thick")
        st.session_state.eng_params["additional_dead"] = st.number_input(
            f"Additional Dead ({unit_label('pressure')})", 0.0, 5.0, st.session_state.eng_params["additional_dead"], 0.1, key="add_dead")
        st.session_state.eng_params["glazing_ratio"] = st.slider("Glazing Ratio", 0.05, 0.8, st.session_state.eng_params["glazing_ratio"], key="glaz_ratio")
        st.session_state.eng_params["orientation"] = st.selectbox("Orientation", ["north","south","east","west"], key="orient")

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

    with st.expander("Appearance"):
        current_theme = get_theme(username)
        new_theme = st.radio("Theme", ["dark", "light"], index=0 if current_theme == "dark" else 1, key="theme_toggle")
        if new_theme != current_theme:
            update_theme(username, new_theme)
            st.rerun()

    if is_admin(user_data):
        with st.expander("User Management"):
            users_list = list_users()
            st.write("**Existing users**")
            for u in users_list:
                col_u1, col_u2, col_u3 = st.columns([2,1,1])
                col_u1.write(u["username"])
                new_role = col_u2.selectbox("Role", ["admin","engineer","viewer"],
                                            index=["admin","engineer","viewer"].index(u["role"]),
                                            key=f"role_{u['username']}")
                if new_role != u["role"]:
                    try:
                        update_user_role(u["username"], new_role)
                        st.success(f"Role updated for {u['username']}")
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))
                if col_u3.button("Delete", key=f"deluser_{u['username']}"):
                    try:
                        delete_user(u["username"])
                        st.success(f"Deleted {u['username']}")
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))

    saved = get_analyses(username)
    if saved:
        with st.expander(f"Saved Analyses ({len(saved)})"):
            for a in saved:
                col_s1, col_s2 = st.columns([3,1])
                col_s1.write(f"{a['type']} – {a['created_at'][:10]}")
                if col_s2.button("Delete", key=f"del_analysis_{a['id']}"):
                    delete_analysis(username, a['id'])
                    st.rerun()

    if st.button("Logout"):
        save_memory(username, mem)
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# ======================
# PAGE: PROJECT DASHBOARD
# ======================
if page == "Project Dashboard":
    st.title("Project Dashboard")

    if st.session_state.active_building:
        building = st.session_state.active_building
        plan = building.plan
        area = calculate_total_area(plan)
        load = compute_floor_loads(plan,
            live_load_kN_per_m2=st.session_state.eng_params["live_load"],
            slab_thickness_m=st.session_state.eng_params["slab_thickness"],
            additional_dead_load_kN_per_m2=st.session_state.eng_params["additional_dead"])
        integrity = check_structural_integrity(plan)
        cost = estimate_cost(plan)

        st.markdown(f"""
        <div class="project-header">
            <h2 style="margin:0; color:{text_color};">{building.name}</h2>
            <p style="margin:5px 0 0 0; color:#94A3B8;">Created: {building.created_at[:10]} | Type: {building.building_type} | Storeys: {building.storeys}</p>
        </div>
        """, unsafe_allow_html=True)

        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        col_m1.metric("Area", f"{output_metric(area, 'area'):.1f} {unit_label('area')}")
        col_m2.metric("Design Load", f"{output_metric(load, 'force'):.1f} {unit_label('force')}")
        col_m3.metric("Max Span", f"{output_metric(integrity['max_span_m'], 'length'):.2f} {unit_label('length')}")
        col_m4.metric("Est. Cost", f"${cost['total']:,.0f}")

        if integrity['pass']:
            st.success(f"Structural check passed – suggested beam: {integrity['suggested_beam']}")
        else:
            st.error(f"Span too large ({integrity['max_span_m']} m) – consider intermediate columns")
    else:
        st.info("Create or select a project to see live metrics.")

    st.markdown("---")

    left_col, right_col = st.columns([1, 3])

    with left_col:
        st.markdown("### Project Tools")
        if is_engineer(user_data):
            templates = get_project_templates()
            template_names = list(templates.keys())
            
            project_name = st.text_input("Project Name", key="project_name_input")
            template_choice = st.selectbox("Template", ["None"] + template_names, key="template_choice")
            num_storeys = st.number_input("Storeys", 1, 20, 1, key="num_storeys")
            
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

            if st.session_state.active_building:
                st.markdown("---")
                st.markdown("### Share Project")
                share_username = st.text_input("Share with username", key="share_username")
                if st.button("Share", key="share_btn"):
                    if share_username.strip():
                        if share_project(username, st.session_state.active_building.id, share_username):
                            st.success(f"Shared with {share_username}")
                        else:
                            st.info("Already shared")
                    else:
                        st.error("Enter a username")

        if mem["buildings"]:
            st.markdown("**Saved Projects**")
            for bdict in reversed(mem["buildings"][-10:]):
                b = Building.from_dict(bdict)
                col_a, col_b = st.columns([3,1])
                with col_a:
                    if st.button(f"{b.name}", key=f"sel_{b.id}"):
                        st.session_state.active_building = b
                        st.rerun()
                if is_engineer(user_data):
                    with col_b:
                        if st.button("Del", key=f"del_{b.id}"):
                            mem["buildings"] = [x for x in mem["buildings"] if x["id"] != b.id]
                            if st.session_state.active_building and st.session_state.active_building.id == b.id:
                                st.session_state.active_building = None
                            save_memory(username, mem)
                            st.rerun()

        st.markdown("---")
        st.markdown("### Engineering News")
        news_items = get_engineering_news()
        for news in news_items[:4]:
            st.markdown(f"""
            <div class="news-card">
                <div class="news-title">{news['title']}</div>
                <div class="news-date">{news['date']}</div>
                <div class="news-summary">{news['summary']}</div>
            </div>
            """, unsafe_allow_html=True)

    with right_col:
        if st.session_state.active_building:
            building = st.session_state.active_building
            plan = building.plan

            with st.expander("Grid & Orientation", expanded=True):
                col_g1, col_g2 = st.columns(2)
                with col_g1:
                    show_grid = st.checkbox("Show Grid", value=st.session_state.show_grid, key="show_grid_cb")
                    st.session_state.show_grid = show_grid
                    if show_grid:
                        if st.session_state.unit_system == "metric":
                            disp_spacing = st.session_state.grid_spacing_mm / 1000.0
                            label = "Grid spacing (m)"
                            step = 0.1
                        else:
                            disp_spacing = st.session_state.grid_spacing_mm / 304.8
                            label = "Grid spacing (ft)"
                            step = 1.0
                        new_sp = st.number_input(label, min_value=0.1, max_value=5.0,
                                                 value=float(disp_spacing), step=step, key="grid_space")
                        if st.session_state.unit_system == "metric":
                            st.session_state.grid_spacing_mm = new_sp * 1000
                        else:
                            st.session_state.grid_spacing_mm = new_sp * 304.8
                with col_g2:
                    show_north = st.checkbox("Show North Arrow", value=st.session_state.show_north, key="show_north_cb")
                    st.session_state.show_north = show_north
                    show_dim = st.checkbox("Show Dimensions", value=st.session_state.show_dimensions, key="show_dim_cb")
                    st.session_state.show_dimensions = show_dim

            st.markdown("#### 2D Floor Plan")
            if plan:
                svg_str = generate_svg_string(
                    plan,
                    show_grid=st.session_state.show_grid,
                    grid_spacing_mm=st.session_state.grid_spacing_mm,
                    show_north=st.session_state.show_north,
                    orientation=st.session_state.eng_params.get("orientation", "north"),
                    show_dimensions=st.session_state.show_dimensions
                )
                st.markdown(f'<div style="background:{card_bg}; border-radius:12px; padding:8px; border:1px solid {border_color};">{svg_str}</div>', unsafe_allow_html=True)
            else:
                st.info("No plan data.")

            if is_engineer(user_data):
                with st.expander("Edit Plan", expanded=False):
                    if st.button("Add Room"):
                        w = random.randint(100, 700)
                        h = random.randint(100, 400)
                        w = max(100, round(w / 500) * 500)
                        h = max(100, round(h / 500) * 500)
                        w = min(w, 800)
                        h = min(h, 500)
                        x = random.randint(0, max(0, 800 - w))
                        y = random.randint(0, max(0, 500 - h))
                        x = max(0, round(x / 500) * 500)
                        y = max(0, round(y / 500) * 500)
                        x = min(x, 800 - w)
                        y = min(y, 500 - h)
                        color_hex = f"#{random.randint(0,0xFFFFFF):06x}"
                        plan.append({
                            "x": x, "y": y, "w": w, "h": h,
                            "name": f"Room {len(plan)+1}",
                            "color": color_hex
                        })
                        building.plan = plan
                        update_building_plan(building, mem, username)
                        st.rerun()

                    st.write("**Room properties**")
                    for i, room in enumerate(plan):
                        with st.container():
                            cols = st.columns([2, 1, 1, 1, 1, 1])
                            cols[0].write(room["name"])
                            safe_w = max(100, min(room["w"], 800))
                            safe_h = max(100, min(room["h"], 500))
                            safe_x = max(0, min(room["x"], 800 - safe_w))
                            safe_y = max(0, min(room["y"], 500 - safe_h))
                            new_w = cols[1].number_input("W", 100, 800, safe_w, key=f"rw_{i}")
                            new_h = cols[2].number_input("H", 100, 500, safe_h, key=f"rh_{i}")
                            new_x = cols[3].number_input("X", 0, max(0, 800 - new_w), safe_x, key=f"rx_{i}")
                            new_y = cols[4].number_input("Y", 0, max(0, 500 - new_h), safe_y, key=f"ry_{i}")
                            new_color = cols[5].color_picker("", value=room.get("color", "#4f46e5"), key=f"rc_{i}")
                            if new_w != safe_w or new_h != safe_h or new_x != safe_x or new_y != safe_y or new_color != room.get("color", "#4f46e5"):
                                plan[i]["w"] = new_w
                                plan[i]["h"] = new_h
                                plan[i]["x"] = new_x
                                plan[i]["y"] = new_y
                                plan[i]["color"] = new_color
                                building.plan = plan
                                update_building_plan(building, mem, username)
                                st.rerun()

            st.markdown("---")
            with st.expander("Export & Share", expanded=False):
                if st.button("Download SVG"):
                    svg_content = generate_svg_string(plan, show_grid=False, show_north=False, show_dimensions=False)
                    st.download_button("Download SVG", svg_content, file_name=f"{building.name}_plan.svg", mime="image/svg+xml")
                if st.button("Export to DXF"):
                    dxf_filename = f"{building.name}_plan.dxf"
                    export_to_dxf(plan, dxf_filename)
                    with open(dxf_filename, "rb") as f:
                        st.download_button("Download DXF", f, file_name=dxf_filename, mime="application/dxf")
                if st.button("Export PDF"):
                    project_data = {
                        "Project Name": building.name,
                        "Engineer": username,
                        "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "Total Area": f"{output_metric(area, 'area'):.1f} {unit_label('area')}",
                        "Design Load": f"{output_metric(load, 'force'):.1f} {unit_label('force')}",
                    }
                    cost = estimate_cost(plan)
                    cost_breakdown = {
                        "Concrete": cost["concrete"],
                        "Steel": cost["steel"],
                        "Glass": cost["glass"],
                        "Labor": cost["labor"],
                        "Total": cost["total"],
                    }
                    plan_svg = generate_svg_string(plan, show_grid=False, show_north=False, show_dimensions=False)
                    filename, error = generate_pdf_report(project_data, plan_svg, None, cost_breakdown,
                                                          filename=f"{building.name}_report.pdf")
                    if error:
                        st.error(error)
                    else:
                        with open(filename, "rb") as f:
                            st.download_button("Download PDF", f, file_name=filename, mime="application/pdf")
                        st.success("Report generated!")

        else:
            st.info("Select a project or create a new one.")

# ======================
# PAGE: STRUCTURAL ANALYSIS
# ======================
elif page == "Structural Analysis":
    st.title("Structural Analysis Workstation")
    st.caption("Simplified checks for quick analysis.")

    if st.session_state.active_building:
        st.info(f"Active Project: **{st.session_state.active_building.name}**")

    def ui_number_input(label, min_val, max_val, value, step, key, unit_type):
        display_min = output_metric(min_val, unit_type) if st.session_state.unit_system=="imperial" else min_val
        display_max = output_metric(max_val, unit_type) if st.session_state.unit_system=="imperial" else max_val
        display_value = output_metric(value, unit_type) if st.session_state.unit_system=="imperial" else value
        display_step = output_metric(step, unit_type) if st.session_state.unit_system=="imperial" else step
        user_val = st.number_input(label, min_value=float(display_min), max_value=float(display_max),
                                   value=float(display_value), step=float(display_step), key=key)
        return input_metric(user_val, unit_type)

    tabs = st.tabs([
        "Beams", "Columns", "Slabs", "Foundations",
        "Piles", "Prestressed", "Truss", "Connections",
        "Load Combos", "Seismic"
    ])

    with tabs[0]:
        st.subheader("Beam Design")
        beam_mat = st.selectbox("Material", ["Reinforced Concrete", "Steel", "Timber", "Composite"], key="beam_mat")
        if beam_mat == "Reinforced Concrete":
            grade = st.selectbox("Concrete Grade", list(CONCRETE_GRADES.keys()), key="beam_rc_grade")
            b = ui_number_input(f"Width ({unit_label('length_mm')})", 100, 1000, 300, 10, "beam_b", "length_mm")
            h = ui_number_input(f"Height ({unit_label('length_mm')})", 200, 2000, 500, 10, "beam_h", "length_mm")
            d = h - 50
            span = ui_number_input(f"Span ({unit_label('length')})", 1.0, 30.0, 6.0, 0.1, "beam_span", "length")
            M_ed = ui_number_input(f"M_Ed ({unit_label('moment')})", 10.0, 1000.0, 120.0, 1.0, "beam_Med", "moment")
            V_ed = ui_number_input(f"V_Ed ({unit_label('force')})", 10.0, 500.0, 80.0, 1.0, "beam_Ved", "force")
            if st.button("Check RC Beam", key="check_rc_beam"):
                fck = CONCRETE_GRADES[grade]["fck"]
                res = check_rc_beam(b, h, d, fck, M_ed, V_ed, span)
                if res["pass"]: st.success("Beam OK")
                else: st.error("Beam fails")
                st.json(res)
                if st.button("Save", key="save_rc_beam"):
                    project_id = st.session_state.active_building.id if st.session_state.active_building else None
                    save_analysis(username, "RC Beam", {"inputs": {"b": b, "h": h, "span": span, "M_ed": M_ed, "V_ed": V_ed}, "results": res}, project_id)
                    st.success("Saved!")

        elif beam_mat == "Steel":
            grade = st.selectbox("Steel Grade", list(STEEL_GRADES.keys()), key="beam_steel_grade")
            section = st.selectbox("Section", ["IPE 160", "IPE 220", "IPE 300"], key="beam_sec")
            span = ui_number_input(f"Span ({unit_label('length')})", 2.0, 20.0, 6.0, 0.1, "beam_span_steel", "length")
            M_ed = ui_number_input(f"M_Ed ({unit_label('moment')})", 50.0, 1000.0, 100.0, 1.0, "beam_Med_steel", "moment")
            V_ed = ui_number_input(f"V_Ed ({unit_label('force')})", 20.0, 500.0, 50.0, 1.0, "beam_Ved_steel", "force")
            if st.button("Check Steel Beam", key="check_steel_beam"):
                steel = STEEL_GRADES[grade]
                res = check_steel_beam(section, M_ed, V_ed, span, steel)
                if res["pass"]: st.success("Beam OK")
                else: st.error("Beam fails")
                st.json(res)

        elif beam_mat == "Timber":
            timber_class = st.selectbox("Timber Class", list(TIMBER_CLASSES.keys()), key="beam_timber_class")
            b = ui_number_input(f"Width ({unit_label('length_mm')})", 50, 400, 100, 10, "beam_timber_b", "length_mm")
            h = ui_number_input(f"Depth ({unit_label('length_mm')})", 100, 600, 300, 10, "beam_timber_h", "length_mm")
            span = ui_number_input(f"Span ({unit_label('length')})", 1.0, 15.0, 5.0, 0.1, "beam_timber_span", "length")
            M_ed = ui_number_input(f"M_Ed ({unit_label('moment')})", 5.0, 200.0, 30.0, 1.0, "beam_timber_Med", "moment")
            V_ed = ui_number_input(f"V_Ed ({unit_label('force')})", 1.0, 100.0, 20.0, 1.0, "beam_timber_Ved", "force")
            if st.button("Check Timber Beam", key="check_timber_beam"):
                res = check_timber_beam(timber_class, b, h, M_ed, V_ed, span)
                if res["pass"]: st.success("Beam OK")
                else: st.error("Beam fails")
                st.json(res)

        elif beam_mat == "Composite":
            section = st.selectbox("Steel Section", ["IPE 160", "IPE 220", "IPE 300"], key="comp_section")
            slab_t = ui_number_input(f"Slab thickness ({unit_label('length_mm')})", 50, 200, 120, 10, "comp_slab_t", "length_mm")
            slab_w = ui_number_input(f"Slab width ({unit_label('length_mm')})", 500, 3000, 1500, 100, "comp_slab_w", "length_mm")
            fck = st.number_input("fck (MPa)", 20, 50, 30, key="comp_fck")
            M_ed = ui_number_input(f"M_Ed ({unit_label('moment')})", 50.0, 1000.0, 200.0, 1.0, "comp_Med", "moment")
            V_ed = ui_number_input(f"V_Ed ({unit_label('force')})", 20.0, 500.0, 100.0, 1.0, "comp_Ved", "force")
            span = ui_number_input(f"Span ({unit_label('length')})", 2.0, 20.0, 8.0, 0.1, "comp_span", "length")
            if st.button("Check Composite Beam", key="check_comp_beam"):
                steel = {"fy": 355, "E": 210e3}
                res = check_composite_beam(section, slab_t, slab_w, fck, M_ed, V_ed, span, steel)
                if res["pass"]: st.success("Beam OK")
                else: st.error("Beam fails")
                st.json(res)

    # Other tabs simplified for brevity
    with tabs[1]:
        st.subheader("Column Design")
        N_ed = ui_number_input(f"Axial load ({unit_label('force')})", 100.0, 5000.0, 500.0, 10.0, "col_Ned", "force")
        M_ed = ui_number_input(f"Moment ({unit_label('moment')})", 0.0, 500.0, 20.0, 1.0, "col_Med", "moment")
        b = ui_number_input(f"Width ({unit_label('length_mm')})", 200, 1000, 300, 10, "col_b", "length_mm")
        h = ui_number_input(f"Depth ({unit_label('length_mm')})", 200, 1000, 300, 10, "col_h", "length_mm")
        l0 = ui_number_input(f"Effective length ({unit_label('length')})", 2.0, 10.0, 3.0, 0.1, "col_l0", "length")
        if st.button("Check Column", key="check_col"):
            res = check_rc_column(N_ed, M_ed, b, h, 30, l0)
            if res["pass"]: st.success("Column OK")
            else: st.error("Column fails")
            st.json(res)

    with tabs[2]:
        st.subheader("Slab Thickness")
        span = ui_number_input(f"Span ({unit_label('length')})", 2.0, 15.0, 5.0, 0.1, "slab_span", "length")
        support = st.selectbox("Support", ["simply_supported", "continuous"], key="slab_support")
        t = slab_thickness_estimate(span, support)
        st.success(f"Thickness: **{output_metric(t*1000, 'length_mm'):.0f} {unit_label('length_mm')}**")

    with tabs[3]:
        st.subheader("Footing Sizing")
        load = ui_number_input(f"Load ({unit_label('force')})", 100.0, 10000.0, 500.0, 10.0, "fdn_load", "force")
        bearing = ui_number_input(f"Bearing ({unit_label('pressure')})", 50.0, 500.0, 150.0, 10.0, "fdn_bearing", "pressure")
        if st.button("Size Footing", key="size_fdn"):
            res = foundation_size(bearing, load)
            if "error" in res:
                st.error(res["error"])
            else:
                st.success(f"Side: **{output_metric(res['side_m'], 'length'):.2f} {unit_label('length')}**")

    with tabs[4]:
        st.subheader("Pile Capacity")
        dia = ui_number_input(f"Diameter ({unit_label('length')})", 0.3, 2.0, 0.6, 0.1, "pile_d", "length")
        length = ui_number_input(f"Length ({unit_label('length')})", 5.0, 40.0, 15.0, 1.0, "pile_L", "length")
        soil = st.selectbox("Soil", ["sand", "clay"], key="pile_soil")
        N = st.number_input("SPT N", 5, 60, 20, key="pile_N")
        if st.button("Calculate", key="pile_calc"):
            res = pile_capacity(dia, length, soil, N)
            st.metric("Allowable Capacity", f"{output_metric(res['Q_all_kN'], 'force'):.1f} {unit_label('force')}")

    with tabs[5]:
        st.subheader("Prestressed Beam")
        M_ext = ui_number_input(f"Moment ({unit_label('moment')})", 100.0, 5000.0, 500.0, 10.0, "pre_M", "moment")
        P = ui_number_input(f"Prestress ({unit_label('force')})", 100.0, 5000.0, 1000.0, 10.0, "pre_P", "force")
        e = ui_number_input(f"Eccentricity ({unit_label('length')})", 0.0, 1.0, 0.2, 0.01, "pre_e", "length")
        A = ui_number_input(f"Area ({unit_label('area')})", 0.05, 2.0, 0.3, 0.01, "pre_A", "area")
        I = st.number_input("I (m⁴)", 0.001, 0.2, 0.01, 0.001, key="pre_I")
        if st.button("Check", key="pre_check"):
            res = check_prestressed_beam(M_ext, P, e, A, I, 0.5, 0.5, 35)
            if res["pass"]: st.success("OK")
            else: st.error("Fails")

    with tabs[6]:
        st.subheader("Truss Solver")
        n_nodes = st.number_input("Nodes", 2, 10, 3, key="truss_nnodes")
        n_elem = st.number_input("Elements", 1, 20, 2, key="truss_nelem")
        nodes = {}
        for i in range(int(n_nodes)):
            c1, c2 = st.columns(2)
            x = c1.number_input(f"Node {i+1} X", value=0.0, key=f"tn_{i}_x")
            y = c2.number_input(f"Node {i+1} Y", value=0.0, key=f"tn_{i}_y")
            nodes[i+1] = (x, y)
        elements = []
        for i in range(int(n_elem)):
            c1, c2, c3, c4 = st.columns(4)
            n1 = c1.number_input(f"E{i+1} N1", 1, n_nodes, 1, key=f"te_{i}_n1")
            n2 = c2.number_input(f"E{i+1} N2", 1, n_nodes, 2, key=f"te_{i}_n2")
            E = c3.number_input(f"E{i+1} E", value=200000.0, key=f"te_{i}_E")
            A = c4.number_input(f"E{i+1} A", value=1000.0, key=f"te_{i}_A")
            elements.append((int(n1), int(n2), E, A))
        loads = {1: (0, -50)}
        supports = {1: (True, True), 2: (True, True)}
        if st.button("Solve", key="truss_solve"):
            res = truss_analysis(nodes, elements, loads, supports)
            if "error" in res:
                st.error(res["error"])
            else:
                st.success("Solved")
                st.json(res)

    with tabs[7]:
        st.subheader("Connections")
        load = ui_number_input(f"Force ({unit_label('force')})", 1.0, 1000.0, 100.0, 1.0, "conn_load", "force")
        bolt_dia = ui_number_input("Bolt dia (mm)", 12, 30, 20, 1, "conn_dia", "length_mm")
        num_bolts = st.number_input("Bolts", 1, 20, 4, key="conn_bolts")
        if st.button("Check", key="conn_check"):
            res = steel_connection_check("bolted", bolt_dia, "8.8", num_bolts, 10, 0, load)
            if res["status"] == "OK":
                st.success(f"OK – Util: {res['utilization']:.2f}")
            else:
                st.error(f"Fails – Util: {res['utilization']:.2f}")

    with tabs[8]:
        st.subheader("Load Combinations")
        dead = st.number_input("Dead", value=100.0, key="lc_dead")
        live = st.number_input("Live", value=50.0, key="lc_live")
        wind = st.number_input("Wind", value=30.0, key="lc_wind")
        if st.button("Generate", key="lc_gen"):
            combos = load_combinations({"dead": dead, "live": live, "wind": wind})
            table = {"Combo": [], "Value": []}
            for name, val in combos:
                table["Combo"].append(name)
                table["Value"].append(f"{val:.2f}")
            st.table(table)

    with tabs[9]:
        st.subheader("Seismic")
        Ss = st.number_input("Ss", 0.0, 3.0, 1.0, key="seis_Ss")
        S1 = st.number_input("S1", 0.0, 2.0, 0.4, key="seis_S1")
        site = st.selectbox("Site", ["A","B","C","D","E"], key="seis_site")
        if st.button("Calculate", key="seis_calc"):
            res = seismic_base_shear(Ss, S1, site, 5, 1.0, 0.5)
            st.metric("Cs", f"{res['Cs']:.4f}")

# ======================
# PAGE: EUROCODES
# ======================
elif page == "Eurocodes":
    st.title("Eurocode Design Modules")
    st.caption("Detailed design per European Standards")

    if st.session_state.active_building:
        st.info(f"Active Project: **{st.session_state.active_building.name}**")

    euro_tabs = st.tabs([
        "EN 1990", "EN 1992", "EN 1993", "EN 1994", "EN 1995",
        "EN 1996", "EN 1997", "EN 1998", "EN 1999"
    ])

    with euro_tabs[0]:
        st.subheader("EN 1990 – Load Combinations")
        dead = st.number_input("Dead", value=100.0, key="ec0_dead")
        live = st.number_input("Live", value=50.0, key="ec0_live")
        wind = st.number_input("Wind", value=30.0, key="ec0_wind")
        if st.button("Generate", key="ec0_gen"):
            combos = ec0.eurocode_uls_combinations(dead, live, wind)
            table = {"Combo": [], "Value": []}
            for name, val, _, _ in combos:
                table["Combo"].append(name)
                table["Value"].append(f"{val:.2f}")
            st.table(table)

    with euro_tabs[1]:
        st.subheader("EN 1992 – RC Beam")
        b = st.number_input("Width (mm)", 100, 1000, 300, key="ec2_b")
        h = st.number_input("Height (mm)", 200, 2000, 500, key="ec2_h")
        M_ed = st.number_input("Moment (kNm)", 10.0, 2000.0, 120.0, key="ec2_Med")
        V_ed = st.number_input("Shear (kN)", 10.0, 1000.0, 80.0, key="ec2_Ved")
        if st.button("Design", key="ec2_design"):
            res = ec2.en1992_rc_beam_design(b, h, h-50, 30, 500, M_ed, V_ed, 6)
            if "error" in res:
                st.error(res["error"])
            elif res["pass"]:
                st.success("OK")
            else:
                st.error("Fails")
            st.json(res)

    with euro_tabs[2]:
        st.subheader("EN 1993 – Steel Beam")
        section = st.selectbox("Section", ["IPE 160", "IPE 220", "IPE 300"], key="ec3_section")
        M_ed = st.number_input("Moment (kNm)", 50.0, 1000.0, 100.0, key="ec3_Med")
        V_ed = st.number_input("Shear (kN)", 20.0, 500.0, 50.0, key="ec3_Ved")
        if st.button("Design", key="ec3_design"):
            res = ec3.en1993_steel_beam_design(section, 355, M_ed, V_ed, 6, True)
            if "error" in res:
                st.error(res["error"])
            elif res["pass"]:
                st.success("OK")
            else:
                st.error("Fails")
            st.json(res)

    with euro_tabs[3]:
        st.subheader("EN 1994 – Composite")
        st.info("Composite beam design module")

    with euro_tabs[4]:
        st.subheader("EN 1995 – Timber")
        timber_class = st.selectbox("Class", ["C24", "GL24h"], key="ec5_class")
        b = st.number_input("Width (mm)", 50, 400, 100, key="ec5_b")
        h = st.number_input("Depth (mm)", 100, 600, 300, key="ec5_h")
        M_ed = st.number_input("Moment (kNm)", 5.0, 200.0, 30.0, key="ec5_Med")
        if st.button("Design", key="ec5_design"):
            res = ec5.en1995_timber_beam_design(timber_class, b, h, M_ed, 20, 5)
            if res["pass"]:
                st.success("OK")
            else:
                st.error("Fails")
            st.json(res)

    with euro_tabs[5]:
        st.subheader("EN 1996 – Masonry")
        st.info("Masonry wall design module")

    with euro_tabs[6]:
        st.subheader("EN 1997 – Geotechnical")
        load = st.number_input("Load (kN)", 100.0, 10000.0, 500.0, key="ec7_load")
        bearing = st.number_input("Bearing (kPa)", 50.0, 500.0, 150.0, key="ec7_bearing")
        if st.button("Size", key="ec7_size"):
            res = ec7.en1997_shallow_foundation(load, bearing)
            st.success(f"Side: {res['side_m']:.2f} m")

    with euro_tabs[7]:
        st.subheader("EN 1998 – Seismic")
        W = st.number_input("Weight (kN)", 100.0, 10000.0, 1000.0, key="ec8_W")
        ag = st.number_input("ag (g)", 0.05, 0.5, 0.25, key="ec8_ag")
        if st.button("Calculate", key="ec8_calc"):
            res = ec8.en1998_base_shear(W, ag, "C", 2.0, 0.5)
            st.metric("Base Shear", f"{res['V_base_kN']:.1f} kN")

    with euro_tabs[8]:
        st.subheader("EN 1999 – Aluminium")
        st.info("Aluminium design module")

# ======================
# PAGE: REPORTS
# ======================
elif page == "Reports":
    st.title("Project Reports")

    if st.session_state.active_building:
        building = st.session_state.active_building
        plan = building.plan
        area = calculate_total_area(plan)
        load = compute_floor_loads(plan, 2.5, 0.2, 1.0)
        integrity = check_structural_integrity(plan)
        cost = estimate_cost(plan)

        st.markdown(f"### {building.name} – Report")

        col_r1, col_r2, col_r3, col_r4 = st.columns(4)
        col_r1.metric("Area", f"{output_metric(area, 'area'):.1f} {unit_label('area')}")
        col_r2.metric("Load", f"{output_metric(load, 'force'):.1f} {unit_label('force')}")
        col_r3.metric("Max Span", f"{output_metric(integrity['max_span_m'], 'length'):.2f} {unit_label('length')}")
        col_r4.metric("Cost", f"${cost['total']:,.0f}")

        st.markdown("#### Floor Plan")
        svg_str = generate_svg_string(plan, show_grid=True, grid_spacing_mm=500, show_north=True, show_dimensions=True)
        st.markdown(f'<div style="background:{card_bg}; border-radius:12px; padding:8px; border:1px solid {border_color};">{svg_str}</div>', unsafe_allow_html=True)

        saved = get_analyses(username, project_id=building.id)
        if saved:
            st.markdown("#### Saved Analyses")
            for a in saved:
                with st.expander(f"{a['type']} – {a['created_at'][:10]}"):
                    st.json(a['data'])

        if st.button("Generate Full Report PDF"):
            project_data = {
                "Project Name": building.name,
                "Engineer": username,
                "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "Total Area": f"{output_metric(area, 'area'):.1f} {unit_label('area')}",
                "Design Load": f"{output_metric(load, 'force'):.1f} {unit_label('force')}",
            }
            cost_breakdown = {
                "Concrete": cost["concrete"],
                "Steel": cost["steel"],
                "Glass": cost["glass"],
                "Labor": cost["labor"],
                "Total": cost["total"],
            }
            plan_svg = generate_svg_string(plan, show_grid=False, show_north=False, show_dimensions=False)
            filename, error = generate_pdf_report(project_data, plan_svg, None, cost_breakdown,
                                                  filename=f"{building.name}_report.pdf")
            if error:
                st.error(error)
            else:
                with open(filename, "rb") as f:
                    st.download_button("Download Report", f, file_name=filename, mime="application/pdf")
                st.success("Report generated!")
    else:
        st.info("No active project.")

# ======================
# PAGE: ARCHIVES
# ======================
else:
    st.title("Project Archives")
    if mem["buildings"]:
        for bdict in reversed(mem["buildings"]):
            building = Building.from_dict(bdict)
            with st.expander(f"{building.name} – Score {building.score}"):
                if building.plan:
                    svg = generate_svg_string(building.plan, show_grid=False, show_north=False, show_dimensions=False)
                    st.markdown(f'<div style="background:{card_bg}; border-radius:12px; padding:8px; border:1px solid {border_color};">{svg}</div>', unsafe_allow_html=True)
                else:
                    st.write("No plan data.")
    else:
        st.info("No projects yet.")