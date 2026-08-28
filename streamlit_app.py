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
    list_users, update_user_role, delete_user, is_admin, is_engineer
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

if not load_users():
    admin_user = os.environ.get("DRUM_ADMIN_USER", "admin")
    admin_pass = os.environ.get("DRUM_ADMIN_PASS", None)
    if admin_pass is None:
        admin_pass = "admin123"
        print("WARNING: Using default admin password. Set DRUM_ADMIN_PASS env variable.")
    create_user(admin_user, admin_pass, role="admin")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

html, body, .stApp {
    font-family: 'Inter', sans-serif;
    background: #0F172A; color: #E2E8F0;
}
h1, h2, h3 { color: #F8FAFC; font-weight: 600; }

.sidebar .sidebar-content { background: #1E293B; }

.stButton>button {
    background: linear-gradient(135deg, #3B82F6, #2563EB);
    color: white; border: none; border-radius: 8px;
    padding: 0.5rem 1.5rem; font-weight: 600;
    transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    background-size: 200% auto;
}
.stButton>button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 16px rgba(59, 130, 246, 0.4);
    background: linear-gradient(135deg, #3B82F6, #1D4ED8);
    animation: gradientShift 1.5s ease infinite;
}
.stButton>button:active {
    transform: translateY(0);
    box-shadow: 0 2px 4px rgba(59, 130, 246, 0.3);
}

.metric-card {
    background: #1E293B; border-radius: 12px; padding: 1rem;
    border: 1px solid #334155;
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}
.metric-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 24px rgba(0,0,0,0.3);
}

.stNumberInput>div>div>input,
.stTextInput>div>div>input {
    background: #1E293B; color: #F8FAFC;
    border: 1px solid #475569;
    transition: border-color 0.3s ease, box-shadow 0.3s ease;
}
.stNumberInput>div>div>input:focus,
.stTextInput>div>div>input:focus {
    border-color: #3B82F6;
    box-shadow: 0 0 0 3px rgba(59,130,246,0.2);
}

.stSelectbox>div>div>select {
    background: #1E293B; color: #F8FAFC;
    transition: border-color 0.3s ease;
}
.stSelectbox>div>div>select:hover {
    border-color: #3B82F6;
}

.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
}
.stTabs [data-baseweb="tab"] {
    background-color: #1E293B;
    border-radius: 8px 8px 0 0;
    padding: 8px 16px;
    color: #94A3B8;
    transition: background-color 0.3s ease, color 0.3s ease, transform 0.2s ease;
}
.stTabs [data-baseweb="tab"]:hover {
    background-color: #334155;
    color: #F8FAFC;
    transform: translateY(-2px);
}
.stTabs [aria-selected="true"] {
    background-color: #334155;
    color: #F8FAFC;
}

.stExpander {
    background: #1E293B;
    border: 1px solid #334155;
    border-radius: 12px;
    margin-bottom: 10px;
    transition: border-color 0.3s ease, box-shadow 0.3s ease;
}
.stExpander:hover {
    border-color: #3B82F6;
    box-shadow: 0 4px 12px rgba(59,130,246,0.2);
}

.stTable {
    background: #1E293B;
    border-radius: 8px;
    overflow: hidden;
}

.main .block-container {
    animation: fadeIn 0.5s ease-out;
}
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

.stDownloadButton>button {
    transition: all 0.3s ease;
}
.stDownloadButton>button:hover {
    transform: scale(1.02);
    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
}

.stRadio label,
.stCheckbox label {
    transition: color 0.3s ease;
}
.stRadio label:hover,
.stCheckbox label:hover {
    color: #F8FAFC;
}

@keyframes gradientShift {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

.news-card {
    background: #1E293B;
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 12px;
    transition: all 0.3s ease;
}
.news-card:hover {
    border-color: #3B82F6;
    box-shadow: 0 4px 12px rgba(59,130,246,0.2);
    transform: translateY(-2px);
}
.news-title {
    font-weight: 600;
    color: #F8FAFC;
    font-size: 1.1rem;
    margin-bottom: 8px;
}
.news-date {
    color: #94A3B8;
    font-size: 0.8rem;
    margin-bottom: 8px;
}
.news-summary {
    color: #CBD5E1;
    font-size: 0.9rem;
    line-height: 1.5;
}
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
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" id="plan-svg" style="width:100%; background:#0F172A;">'
    if show_grid and grid_spacing_mm > 0:
        x = 0
        while x <= width:
            svg += f'<line x1="{x}" y1="0" x2="{x}" y2="{height}" stroke="#334155" stroke-width="0.5" stroke-dasharray="4,4"/>'
            x += grid_spacing_mm
        y = 0
        while y <= height:
            svg += f'<line x1="0" y1="{y}" x2="{width}" y2="{y}" stroke="#334155" stroke-width="0.5" stroke-dasharray="4,4"/>'
            y += grid_spacing_mm
    for item in plan:
        x, y, w, h = item["x"], item["y"], item["w"], item["h"]
        color = item.get("color", "#4f46e5")
        name = item["name"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        svg += f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{color}" fill-opacity="0.4" stroke="#94a3b8" stroke-width="2"/>'
        svg += f'<text x="{x+w/2}" y="{y+h/2 - 8}" font-size="12" fill="white" text-anchor="middle" dominant-baseline="middle">{name}</text>'
        if show_dimensions:
            dims = f"{w}×{h} mm"
            svg += f'<text x="{x+w/2}" y="{y+h/2 + 12}" font-size="10" fill="#94a3b8" text-anchor="middle" dominant-baseline="middle">{dims}</text>'
    if show_north:
        arrow_x = width - 70
        arrow_y = 40
        rotation_map = {"north": 0, "east": 90, "south": 180, "west": 270}
        angle = rotation_map.get(orientation, 0)
        svg += f'''
        <g transform="translate({arrow_x},{arrow_y}) rotate({angle})">
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

def generate_random_plan(building, num_rooms=4, grid_spacing_mm=500):
    colors = [
        "#3B82F6", "#EF4444", "#10B981", "#F59E0B", "#8B5CF6",
        "#EC4899", "#06B6D4", "#84CC16", "#F97316", "#6366F1"
    ]
    plan = []
    
    hall_w = random.randint(400, 600)
    hall_h = random.randint(400, 600)
    hall_w = round(hall_w / grid_spacing_mm) * grid_spacing_mm
    hall_h = round(hall_h / grid_spacing_mm) * grid_spacing_mm
    hall_x = round((400 - hall_w // 2) / grid_spacing_mm) * grid_spacing_mm
    hall_y = round((250 - hall_h // 2) / grid_spacing_mm) * grid_spacing_mm
    
    plan.append({
        "x": hall_x, "y": hall_y, "w": hall_w, "h": hall_h,
        "name": "Hall", "color": "#94A3B8"
    })
    
    directions = ["top", "bottom", "left", "right"]
    for i in range(num_rooms):
        parent = random.choice(plan)
        dir = random.choice(directions)
        
        new_w = random.randint(200, 500)
        new_h = random.randint(200, 500)
        new_w = round(new_w / grid_spacing_mm) * grid_spacing_mm
        new_h = round(new_h / grid_spacing_mm) * grid_spacing_mm
        
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
        
        new_x = round(new_x / grid_spacing_mm) * grid_spacing_mm
        new_y = round(new_y / grid_spacing_mm) * grid_spacing_mm
        
        new_x = max(0, min(new_x, 800 - new_w))
        new_y = max(0, min(new_y, 500 - new_h))
        
        new_x = round(new_x / grid_spacing_mm) * grid_spacing_mm
        new_y = round(new_y / grid_spacing_mm) * grid_spacing_mm
        
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

# ======================
# NEWS DATA
# ======================
def get_engineering_news():
    """Return a list of engineering and structural analysis news items."""
    news = [
        {
            "title": "Eurocode Updates: EN 1992-1-1 Amendment Published",
            "date": "2024-11-15",
            "summary": "CEN has published an amendment to EN 1992-1-1 covering concrete structures. The update includes revised shear design provisions and new guidance on high-strength concrete."
        },
        {
            "title": "Advances in Structural Health Monitoring",
            "date": "2024-10-28",
            "summary": "New sensor technologies are enabling real-time monitoring of bridges and buildings. Fiber optic sensors can now detect strain changes with unprecedented accuracy."
        },
        {
            "title": "Mass Timber Construction Reaches New Heights",
            "date": "2024-10-05",
            "summary": "Cross-laminated timber (CLT) buildings are being constructed at record heights. The latest projects demonstrate timber's viability as a sustainable structural material."
        },
        {
            "title": "AI in Structural Analysis: Machine Learning for Design",
            "date": "2024-09-20",
            "summary": "Machine learning algorithms are being integrated into structural analysis software, enabling faster optimization of building designs and more accurate failure prediction."
        },
        {
            "title": "Seismic Design Guidelines Updated",
            "date": "2024-09-01",
            "summary": "New seismic design guidelines incorporate lessons learned from recent earthquakes. The updates focus on improved ductility requirements and better performance-based design methods."
        },
        {
            "title": "3D Printing in Construction: Structural Applications",
            "date": "2024-08-15",
            "summary": "3D-printed concrete structures are moving from experimental to practical applications. Engineers are developing new design approaches for printed structural elements."
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
                    ["Project Dashboard", "Structural Analysis", "Eurocodes", "Archives"],
                    index=["Project Dashboard", "Structural Analysis", "Eurocodes", "Archives"].index(st.session_state.page),
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
            if st.button("New Project", use_container_width=True):
                new_building = Building(name=f"Project-{len(mem['buildings'])+1}", score=50)
                generate_plan(new_building)
                mem["buildings"].append(new_building.to_dict())
                st.session_state.active_building = new_building
                st.session_state.show_grid = True
                st.session_state.grid_spacing_mm = 500
                log_event(username, mem, f"Created new project: {new_building.name}")
                save_memory(username, mem)
                st.rerun()
            if st.button("Generate Random Plan", use_container_width=True):
                new_building = Building(name=f"Random-{len(mem['buildings'])+1}", score=60)
                generate_random_plan(new_building, num_rooms=random.randint(4, 8), grid_spacing_mm=500)
                mem["buildings"].append(new_building.to_dict())
                st.session_state.active_building = new_building
                st.session_state.show_grid = True
                st.session_state.grid_spacing_mm = 500
                log_event(username, mem, f"Generated random plan: {new_building.name}")
                save_memory(username, mem)
                st.rerun()
        else:
            st.info("Viewer access – editing disabled.")

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
                        if st.button("Delete", key=f"del_{b.id}"):
                            mem["buildings"] = [x for x in mem["buildings"] if x["id"] != b.id]
                            if st.session_state.active_building and st.session_state.active_building.id == b.id:
                                st.session_state.active_building = None
                            save_memory(username, mem)
                            st.rerun()

        st.markdown("---")
        st.markdown("### Compare Projects")
        if len(mem["buildings"]) >= 2:
            compare_a = st.selectbox("Project A", [b["name"] for b in mem["buildings"]], key="comp_a")
            compare_b = st.selectbox("Project B", [b["name"] for b in mem["buildings"]], key="comp_b")
            if st.button("Compare", use_container_width=True):
                b1 = next(b for b in mem["buildings"] if b["name"] == compare_a)
                b2 = next(b for b in mem["buildings"] if b["name"] == compare_b)
                c1, c2 = st.columns(2)
                with c1:
                    st.write(f"**{b1['name']}**")
                    st.write(f"Score: {b1['score']}")
                    st.write(f"Rooms: {len(b1['plan'])}")
                with c2:
                    st.write(f"**{b2['name']}**")
                    st.write(f"Score: {b2['score']}")
                    st.write(f"Rooms: {len(b2['plan'])}")
        else:
            st.caption("Need at least 2 projects to compare.")

        if st.session_state.active_building:
            st.markdown("---")
            st.markdown("### Room Areas")
            plan = st.session_state.active_building.plan
            if plan:
                total = 0
                for room in plan:
                    w, h = room["w"], room["h"]
                    area_m2 = w * h / 1e6
                    st.caption(f"{room['name']}: {output_metric(area_m2, 'area'):.2f} {unit_label('area')}")
                    total += area_m2
                st.metric("Total Area", f"{output_metric(total, 'area'):.2f} {unit_label('area')}")
            else:
                st.caption("No rooms yet.")

        # News Section
        st.markdown("---")
        st.markdown("### Engineering News")
        news_items = get_engineering_news()
        for news in news_items[:4]:  # Show top 4 news items
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
                st.markdown(f'<div style="background:#0F172A; border-radius:12px; padding:8px; border:1px solid #334155;">{svg_str}</div>', unsafe_allow_html=True)
            else:
                st.info("No plan data.")

            if is_engineer(user_data):
                with st.expander("Edit Plan (Add / Remove / Modify Rooms)", expanded=False):
                    col_edit1, col_edit2 = st.columns(2)
                    with col_edit1:
                        if st.button("Add Random Room"):
                            w = random.randint(100, 800)
                            h = random.randint(100, 500)
                            w = round(w / 500) * 500
                            h = round(h / 500) * 500
                            x = random.randint(0, 800 - w)
                            y = random.randint(0, 500 - h)
                            x = round(x / 500) * 500
                            y = round(y / 500) * 500
                            color_hex = f"#{random.randint(0,0xFFFFFF):06x}"
                            plan.append({
                                "x": x, "y": y, "w": w, "h": h,
                                "name": f"Room {len(plan)+1}",
                                "color": color_hex
                            })
                            building.plan = plan
                            update_building_plan(building, mem, username)
                            st.rerun()
                    with col_edit2:
                        if len(plan) > 1:
                            room_names = [r["name"] for r in plan]
                            room_to_remove = st.selectbox("Remove room", room_names, key="remove_room")
                            if st.button("Remove Selected"):
                                plan = [r for r in plan if r["name"] != room_to_remove]
                                building.plan = plan
                                update_building_plan(building, mem, username)
                                st.rerun()

                    st.write("**Room properties**")
                    for i, room in enumerate(plan):
                        with st.container():
                            cols = st.columns([2, 1, 1, 1, 1, 1])
                            cols[0].write(room["name"])
                            new_w = cols[1].number_input("W", 100, 800, room["w"], key=f"rw_{i}")
                            new_h = cols[2].number_input("H", 100, 500, room["h"], key=f"rh_{i}")
                            new_x = cols[3].number_input("X", 0, 800 - room["w"], room["x"], key=f"rx_{i}")
                            new_y = cols[4].number_input("Y", 0, 500 - room["h"], room["y"], key=f"ry_{i}")
                            new_color = cols[5].color_picker("", value=room.get("color", "#4f46e5"), key=f"rc_{i}")
                            changed = False
                            if new_w != room["w"] or new_h != room["h"] or new_x != room["x"] or new_y != room["y"] or new_color != room["color"]:
                                plan[i]["w"] = new_w
                                plan[i]["h"] = new_h
                                plan[i]["x"] = new_x
                                plan[i]["y"] = new_y
                                plan[i]["color"] = new_color
                                changed = True
                            if changed:
                                building.plan = plan
                                update_building_plan(building, mem, username)
                                st.rerun()

                    if plan:
                        st.markdown("---")
                        st.markdown("**Nudge selected room**")
                        room_names = [r["name"] for r in plan]
                        nudge_room = st.selectbox("Select room", room_names, key="nudge_room_sel")
                        nudge_step = st.number_input("Step (mm)", value=500, step=500, key="nudge_step")
                        col_n1, col_n2, col_n3, col_n4 = st.columns(4)
                        idx = next(i for i, r in enumerate(plan) if r["name"] == nudge_room)
                        room = plan[idx]
                        if col_n1.button("Left", key="nudge_left"):
                            plan[idx]["x"] = max(0, room["x"] - nudge_step)
                            building.plan = plan
                            update_building_plan(building, mem, username)
                            st.rerun()
                        if col_n2.button("Right", key="nudge_right"):
                            plan[idx]["x"] = min(room["x"] + nudge_step, 800 - room["w"])
                            building.plan = plan
                            update_building_plan(building, mem, username)
                            st.rerun()
                        if col_n3.button("Up", key="nudge_up"):
                            plan[idx]["y"] = max(0, room["y"] - nudge_step)
                            building.plan = plan
                            update_building_plan(building, mem, username)
                            st.rerun()
                        if col_n4.button("Down", key="nudge_down"):
                            plan[idx]["y"] = min(room["y"] + nudge_step, 500 - room["h"])
                            building.plan = plan
                            update_building_plan(building, mem, username)
                            st.rerun()

            st.markdown("#### Interactive 3D Model")
            if plan:
                rooms_js = ""
                for room in plan:
                    x = room["x"] / 1000
                    z = room["y"] / 1000
                    w = room["w"] / 1000
                    d = room["h"] / 1000
                    h = 3.0
                    color = room.get("color", "#4f46e5")
                    rooms_js += f"""
            geometry = new THREE.BoxGeometry({w}, {h}, {d});
            material = new THREE.MeshPhongMaterial({{color: '{color}', opacity: 0.7, transparent: true}});
            cube = new THREE.Mesh(geometry, material);
            cube.position.set({x + w/2}, {h/2}, {z + d/2});
            scene.add(cube);
            """
                three_js_html = f"""
            <html>
            <head>
                <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
                <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
            </head>
            <body style="margin:0; overflow:hidden;">
                <script>
                    var scene = new THREE.Scene();
                    scene.background = new THREE.Color(0x0f172a);
                    var camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 100);
                    camera.position.set(8, 6, 10);
                    var renderer = new THREE.WebGLRenderer();
                    renderer.setSize(window.innerWidth, window.innerHeight);
                    document.body.appendChild(renderer.domElement);
                    var controls = new THREE.OrbitControls(camera, renderer.domElement);
                    controls.target.set(4, 1.5, 2.5);
                    controls.update();
                    var light = new THREE.DirectionalLight(0xffffff, 1);
                    light.position.set(5, 10, 7);
                    scene.add(light);
                    var ambient = new THREE.AmbientLight(0x404040);
                    scene.add(ambient);
                    var geometry, material, cube;
                    {rooms_js}
                    function animate() {{
                        requestAnimationFrame(animate);
                        controls.update();
                        renderer.render(scene, camera);
                    }}
                    animate();
                </script>
            </body>
            </html>
            """
                st.components.v1.html(three_js_html, height=500, scrolling=False)
            else:
                st.info("3D view requires a building plan.")

            st.markdown("---")
            with st.expander("Cost & Material Estimate", expanded=False):
                if st.button("Calculate Estimate", key="calc_cost"):
                    cost = estimate_cost(plan)
                    st.table({
                        "Item": ["Concrete", "Steel", "Glass", "Labor", "Total"],
                        "Cost (USD)": [f"${cost['concrete']:,.2f}", f"${cost['steel']:,.2f}",
                                       f"${cost['glass']:,.2f}", f"${cost['labor']:,.2f}",
                                       f"${cost['total']:,.2f}"]
                    })

            st.markdown("---")
            with st.expander("Export & Share", expanded=False):
                if st.button("Download Plan as SVG"):
                    svg_content = generate_svg_string(plan, show_grid=False, show_north=False, show_dimensions=False)
                    st.download_button("Download SVG", svg_content, file_name=f"{building.name}_plan.svg", mime="image/svg+xml")
                if st.button("Export Summary PDF"):
                    project_data = {
                        "Project Name": building.name,
                        "Engineer": username,
                        "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "Total Area": f"{output_metric(area, 'area'):.1f} {unit_label('area')}",
                        "Design Load": f"{output_metric(load, 'force'):.1f} {unit_label('force')}",
                    }
                    analysis_results = {
                        "Max Span": f"{output_metric(integrity['max_span_m'], 'length'):.2f} {unit_label('length')}",
                        "Suggested Beam": integrity['suggested_beam'],
                        "Structural Integrity": "Pass" if integrity['pass'] else "Fail",
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
                    filename, error = generate_pdf_report(project_data, plan_svg, analysis_results, cost_breakdown,
                                                          filename=f"{building.name}_report.pdf")
                    if error:
                        st.error(error)
                    else:
                        with open(filename, "rb") as f:
                            st.download_button("Download PDF Report", f, file_name=filename, mime="application/pdf")
                        st.success("Report generated!")
                st.text_input("Shareable link (copy)", value=f"https://drum-studio.com/project/{building.id}", disabled=True)

        else:
            st.info("Select a project from the list or create a new one to start.")

    st.markdown("---")
    st.subheader("Recent Activity")
    if mem["logs"]:
        for log in reversed(mem["logs"][-5:]):
            st.caption(f"{log['time'][11:19]} – {log['msg']}")
    else:
        st.caption("No activity yet.")

# ======================
# PAGE: STRUCTURAL ANALYSIS
# ======================
elif page == "Structural Analysis":
    st.title("Structural Analysis Workstation")
    st.caption("Simplified checks for quick analysis.")

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
        "Walls & Finishes", "Piles", "Prestressed",
        "Retaining Wall", "Truss", "Connections",
        "Load Combos", "Seismic"
    ])

    # ---- BEAMS ----
    with tabs[0]:
        st.subheader("Beam Design")
        beam_mat = st.selectbox("Material", ["Reinforced Concrete", "Steel", "Timber", "Composite"], key="beam_mat")
        if beam_mat == "Reinforced Concrete":
            grade = st.selectbox("Concrete Grade", list(CONCRETE_GRADES.keys()), key="beam_rc_grade")
            b = ui_number_input(f"Width ({unit_label('length_mm')})", 100, 1000, 300, 10, "beam_b", "length_mm")
            h = ui_number_input(f"Total height ({unit_label('length_mm')})", 200, 2000, 500, 10, "beam_h", "length_mm")
            d = h - 50e-3
            span = ui_number_input(f"Span ({unit_label('length')})", 1.0, 30.0, 6.0, 0.1, "beam_span", "length")
            M_ed = ui_number_input(f"Design Moment M_Ed ({unit_label('moment')})", 10.0, 1000.0, 120.0, 1.0, "beam_Med", "moment")
            V_ed = ui_number_input(f"Design Shear V_Ed ({unit_label('force')})", 10.0, 500.0, 80.0, 1.0, "beam_Ved", "force")
            if st.button("Check RC Beam", key="check_rc_beam"):
                fck = CONCRETE_GRADES[grade]["fck"]
                res = check_rc_beam(b, h, d, fck, M_ed, V_ed, span)
                if res["pass"]: st.success("Beam OK")
                else: st.error("Beam fails check")
                st.write(f"As required: {output_metric(res['As_req'], 'area'):.2f} {unit_label('area')}")
                st.json(res)
            st.markdown("---")
            st.subheader("Beam Diagrams")
            col_diag1, col_diag2, col_diag3 = st.columns(3)
            load_type = col_diag1.selectbox("Load type", ["udl", "point", "none"], key="diag_load_type")
            if load_type == "udl":
                load_val = col_diag2.number_input("UDL (kN/m)", value=10.0, key="diag_udl")
                point_pos = 0.0
            elif load_type == "point":
                load_val = col_diag2.number_input("Point load (kN)", value=50.0, key="diag_point")
                point_pos = col_diag3.number_input("Position from left (m)", value=span/2, key="diag_point_pos")
            else:
                load_val = 0.0
                point_pos = 0.0
            if st.button("Plot Diagrams", key="plot_beam"):
                fig = plot_beam_diagrams("simply_supported", span, load_type, load_val, point_pos)
                st.pyplot(fig)
                plt.close(fig)

        elif beam_mat == "Steel":
            grade = st.selectbox("Steel Grade", list(STEEL_GRADES.keys()), key="beam_steel_grade")
            section = st.selectbox("Section", ["IPE 160", "IPE 220", "IPE 300", "IPE 400", "IPE 500"], key="beam_sec")
            span = ui_number_input(f"Span ({unit_label('length')})", 2.0, 20.0, 6.0, 0.1, "beam_span_steel", "length")
            M_ed = ui_number_input(f"M_Ed ({unit_label('moment')})", 50.0, 1000.0, 100.0, 1.0, "beam_Med_steel", "moment")
            V_ed = ui_number_input(f"V_Ed ({unit_label('force')})", 20.0, 500.0, 50.0, 1.0, "beam_Ved_steel", "force")
            if st.button("Check Steel Beam", key="check_steel_beam"):
                steel = STEEL_GRADES[grade]
                res = check_steel_beam(section, M_ed, V_ed, span, steel)
                if res["pass"]: st.success("Beam OK")
                else: st.error("Beam fails")
                st.write(f"Utilization: {res['utilization']:.2f}")
                st.write(f"Deflection: {output_metric(res['deflection_mm']/1000, 'length'):.3f} {unit_label('length')}")
                st.json(res)

        elif beam_mat == "Timber":
            timber_class = st.selectbox("Timber Class", list(TIMBER_CLASSES.keys()), key="beam_timber_class")
            b = ui_number_input(f"Width ({unit_label('length_mm')})", 50, 400, 100, 10, "beam_timber_b", "length_mm")
            h = ui_number_input(f"Depth ({unit_label('length_mm')})", 100, 600, 300, 10, "beam_timber_h", "length_mm")
            span = ui_number_input(f"Span ({unit_label('length')})", 1.0, 15.0, 5.0, 0.1, "beam_timber_span", "length")
            M_ed = ui_number_input(f"Design Moment M_Ed ({unit_label('moment')})", 5.0, 200.0, 30.0, 1.0, "beam_timber_Med", "moment")
            V_ed = ui_number_input(f"Design Shear V_Ed ({unit_label('force')})", 1.0, 100.0, 20.0, 1.0, "beam_timber_Ved", "force")
            load_duration = st.selectbox("Load duration", ["short", "medium", "long"], key="beam_timber_loaddur")
            if st.button("Check Timber Beam", key="check_timber_beam"):
                res = check_timber_beam(timber_class, b, h, M_ed, V_ed, span, load_duration)
                if "error" in res:
                    st.error(res["error"])
                elif res["pass"]:
                    st.success("Timber beam OK")
                else:
                    st.error("Timber beam fails")
                st.write(f"Moment utilization: {res['utilization_moment']:.2f}")
                st.write(f"Shear utilization: {res['utilization_shear']:.2f}")
                st.write(f"Deflection: {output_metric(res['deflection_mm']/1000, 'length'):.3f} {unit_label('length')}")
                st.json(res)

        elif beam_mat == "Composite":
            section = st.selectbox("Steel Section", ["IPE 160", "IPE 220", "IPE 300"], key="comp_section")
            grade = st.selectbox("Steel Grade", list(STEEL_GRADES.keys()), key="comp_steel_grade")
            slab_t = ui_number_input(f"Slab thickness ({unit_label('length_mm')})", 50, 200, 120, 10, "comp_slab_t", "length_mm")
            slab_w = ui_number_input(f"Slab effective width ({unit_label('length_mm')})", 500, 3000, 1500, 100, "comp_slab_w", "length_mm")
            fck = st.number_input("Concrete fck (MPa)", 20, 50, 30, key="comp_fck")
            span = ui_number_input(f"Span ({unit_label('length')})", 2.0, 20.0, 8.0, 0.1, "comp_span", "length")
            M_ed = ui_number_input(f"Design Moment M_Ed ({unit_label('moment')})", 50.0, 1000.0, 200.0, 1.0, "comp_Med", "moment")
            V_ed = ui_number_input(f"Design Shear V_Ed ({unit_label('force')})", 20.0, 500.0, 100.0, 1.0, "comp_Ved", "force")
            if st.button("Check Composite Beam", key="check_comp_beam"):
                steel = STEEL_GRADES[grade]
                res = check_composite_beam(section, slab_t, slab_w, fck, M_ed, V_ed, span, steel)
                if "error" in res:
                    st.error(res["error"])
                elif res["pass"]:
                    st.success("Composite beam OK")
                else:
                    st.error("Composite beam fails")
                st.write(f"Moment utilization: {res['utilization_moment']:.2f}")
                st.write(f"Shear utilization: {res['utilization_shear']:.2f}")
                st.write(f"Deflection: {output_metric(res['deflection_mm']/1000, 'length'):.3f} {unit_label('length')}")
                st.json(res)

    # ---- COLUMNS ----
    with tabs[1]:
        st.subheader("Column Design")
        col_mat = st.selectbox("Material", ["RC", "Steel", "Timber"], key="col_mat")
        if col_mat == "RC":
            N_ed = ui_number_input(f"Axial load N_Ed ({unit_label('force')})", 100.0, 5000.0, 500.0, 10.0, "col_Ned", "force")
            M_ed = ui_number_input(f"Moment M_Ed ({unit_label('moment')})", 0.0, 500.0, 20.0, 1.0, "col_Med", "moment")
            b = ui_number_input(f"Width ({unit_label('length_mm')})", 200, 1000, 300, 10, "col_b", "length_mm")
            h = ui_number_input(f"Depth ({unit_label('length_mm')})", 200, 1000, 300, 10, "col_h", "length_mm")
            l0 = ui_number_input(f"Effective length ({unit_label('length')})", 2.0, 10.0, 3.0, 0.1, "col_l0", "length")
            grade = st.selectbox("Concrete Grade", list(CONCRETE_GRADES.keys()), key="col_grade")
            if st.button("Check Column", key="check_col"):
                fck = CONCRETE_GRADES[grade]["fck"]
                res = check_rc_column(N_ed, M_ed, b, h, fck, l0)
                if res["pass"]: st.success("Column OK")
                else: st.error("Column fails")
                st.write(f"N_Rd: {output_metric(res['N_rd'], 'force'):.1f} {unit_label('force')}")
                st.json(res)

    # ---- SLABS ----
    with tabs[2]:
        st.subheader("Slab Thickness")
        span = ui_number_input(f"Short span ({unit_label('length')})", 2.0, 15.0, 5.0, 0.1, "slab_span", "length")
        support = st.selectbox("Support", ["simply_supported", "continuous"], key="slab_support")
        t = slab_thickness_estimate(span, support)
        st.success(f"Recommended thickness: **{output_metric(t*1000, 'length_mm'):.0f} {unit_label('length_mm')}**")

    # ---- FOUNDATIONS ----
    with tabs[3]:
        st.subheader("Pad Footing Sizing")
        load = ui_number_input(f"Total column load ({unit_label('force')})", 100.0, 10000.0, 500.0, 10.0, "fdn_load", "force")
        bearing = ui_number_input(f"Allowable bearing pressure ({unit_label('pressure')})", 50.0, 500.0, 150.0, 10.0, "fdn_bearing", "pressure")
        fs = st.number_input("Factor of safety", 2.0, 5.0, 3.0, 0.1, key="fdn_fs")
        if st.button("Size Footing", key="size_fdn"):
            res = foundation_size(bearing, load, fs)
            if "error" in res:
                st.error(res["error"])
            else:
                st.success(f"Square footing side: **{output_metric(res['side_m'], 'length'):.2f} {unit_label('length')}** (area: {output_metric(res['area_m2'], 'area'):.2f} {unit_label('area')})")

    # ---- WALLS & FINISHES ----
    with tabs[4]:
        st.subheader("Wall Types & Finishes")
        wall = st.selectbox("Wall Type", list(WALL_TYPES.keys()), key="wall_type")
        props = WALL_TYPES[wall]
        weight_disp = output_metric(props['weight'], 'pressure') if st.session_state.unit_system=="imperial" else props['weight']
        st.write(f"Weight: {weight_disp:.2f} {unit_label('pressure')}, U-value: {props['U']} W/m²K, Sound: {props['sound']} dB")
        finishes = st.multiselect("Finishes", list(FINISHES.keys()), default=["Plaster (internal)", "Paint"], key="finishes")
        finish_load = sum(FINISHES[f] for f in finishes)
        finish_disp = output_metric(finish_load, 'pressure') if st.session_state.unit_system=="imperial" else finish_load
        st.metric("Total finish load", f"{finish_disp:.3f} {unit_label('pressure')}")

    # ---- PILES ----
    with tabs[5]:
        st.subheader("Pile Foundation Design (Simplified EC7)")
        pile_type = st.selectbox("Pile type", ["Bored", "Driven"], key="pile_type")
        diameter = ui_number_input(f"Pile diameter ({unit_label('length')})", 0.3, 2.0, 0.6, 0.1, "pile_d", "length")
        length = ui_number_input(f"Pile length ({unit_label('length')})", 5.0, 40.0, 15.0, 1.0, "pile_L", "length")
        soil = st.selectbox("Soil type", ["sand", "clay"], key="pile_soil")
        N = st.number_input("SPT N-value", 5, 60, 20, key="pile_N")
        safety = st.number_input("Factor of safety", 2.0, 4.0, 2.5, 0.1, key="pile_fs")
        if st.button("Calculate Capacity", key="pile_calc"):
            res = pile_capacity(diameter, length, soil, N, safety)
            st.metric("Allowable Capacity", f"{output_metric(res['Q_all_kN'], 'force'):.1f} {unit_label('force')}")

    # ---- PRESTRESSED ----
    with tabs[6]:
        st.subheader("Prestressed Concrete Beam (Stress Check)")
        M_ext = ui_number_input(f"External moment ({unit_label('moment')})", 100.0, 5000.0, 500.0, 10.0, "pre_M", "moment")
        P = ui_number_input(f"Prestressing force ({unit_label('force')})", 100.0, 5000.0, 1000.0, 10.0, "pre_P", "force")
        e = ui_number_input(f"Eccentricity ({unit_label('length')})", 0.0, 1.0, 0.2, 0.01, "pre_e", "length")
        A = ui_number_input(f"Cross-sectional area ({unit_label('area')})", 0.05, 2.0, 0.3, 0.01, "pre_A", "area")
        I = st.number_input("Second moment of area I (m⁴)", 0.001, 0.2, 0.01, 0.001, key="pre_I")
        y_top = ui_number_input(f"y_top ({unit_label('length')})", 0.1, 1.0, 0.5, 0.01, "pre_ytop", "length")
        y_bot = ui_number_input(f"y_bot ({unit_label('length')})", 0.1, 1.0, 0.5, 0.01, "pre_ybot", "length")
        fck = st.number_input("fck (MPa)", 20, 60, 35, key="pre_fck")
        if st.button("Check Stresses", key="pre_check"):
            res = check_prestressed_beam(M_ext, P, e, A, I, y_top, y_bot, fck)
            if res["pass"]: st.success("Stresses within limits")
            else: st.error("Stress limit exceeded")

    # ---- RETAINING WALL ----
    with tabs[7]:
        st.subheader("Cantilever Retaining Wall (Simplified)")
        H = ui_number_input(f"Wall height ({unit_label('length')})", 1.0, 10.0, 3.0, 0.1, "rw_H", "length")
        gamma = ui_number_input(f"Soil unit weight ({unit_label('weight_density')})", 15.0, 22.0, 18.0, 0.1, "rw_gamma", "weight_density")
        phi = st.number_input("Friction angle (°)", 20.0, 45.0, 30.0, key="rw_phi")
        if st.button("Check Stability", key="rw_check"):
            res = retaining_wall_stability(H, gamma, phi, 0, 0, 0.6)
            if res["pass"]: st.success("Wall stable")
            else: st.error("Stability check failed")

    # ---- TRUSS ----
    with tabs[8]:
        st.subheader("2D Truss Solver (Stiffness Method)")
        st.markdown("Define nodes (x, y in mm), elements (connections), loads (kN), and supports.")
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            n_nodes = st.number_input("Number of nodes", min_value=2, max_value=20, value=3, key="truss_nnodes")
        with col_t2:
            n_elem = st.number_input("Number of elements", min_value=1, max_value=30, value=2, key="truss_nelem")

        nodes = {}
        st.markdown("**Nodes**")
        for i in range(int(n_nodes)):
            c1, c2 = st.columns(2)
            x = c1.number_input(f"Node {i+1} X (mm)", value=0.0, key=f"tn_{i}_x")
            y = c2.number_input(f"Node {i+1} Y (mm)", value=0.0, key=f"tn_{i}_y")
            nodes[i+1] = (x, y)

        elements = []
        st.markdown("**Elements**")
        for i in range(int(n_elem)):
            c1, c2, c3, c4 = st.columns(4)
            n1 = c1.number_input(f"Elem {i+1} Node1", min_value=1, max_value=n_nodes, value=1, key=f"te_{i}_n1")
            n2 = c2.number_input(f"Elem {i+1} Node2", min_value=1, max_value=n_nodes, value=2, key=f"te_{i}_n2")
            E = c3.number_input(f"Elem {i+1} E (MPa)", value=200000.0, key=f"te_{i}_E")
            A = c4.number_input(f"Elem {i+1} A (mm²)", value=1000.0, key=f"te_{i}_A")
            elements.append((int(n1), int(n2), E, A))

        loads = {}
        st.markdown("**Loads (kN)** – leave 0 if none")
        for i in range(int(n_nodes)):
            c1, c2 = st.columns(2)
            fx = c1.number_input(f"Node {i+1} Fx (kN)", value=0.0, key=f"tl_{i}_fx")
            fy = c2.number_input(f"Node {i+1} Fy (kN)", value=0.0, key=f"tl_{i}_fy")
            if fx != 0 or fy != 0:
                loads[i+1] = (fx, fy)

        supports = {}
        st.markdown("**Supports** – check fixed directions")
        for i in range(int(n_nodes)):
            c1, c2 = st.columns(2)
            sx = c1.checkbox(f"Node {i+1} X fixed", value=False, key=f"ts_{i}_sx")
            sy = c2.checkbox(f"Node {i+1} Y fixed", value=False, key=f"ts_{i}_sy")
            if sx or sy:
                supports[i+1] = (sx, sy)

        if st.button("Solve Truss", key="truss_solve"):
            if not supports:
                st.error("Add at least one support.")
            else:
                result = truss_analysis(nodes, elements, loads, supports)
                if "error" in result:
                    st.error(result["error"])
                else:
                    st.success("Analysis complete")
                    col_r1, col_r2 = st.columns(2)
                    with col_r1:
                        st.markdown("**Displacements (mm)**")
                        disp_data = {"Node": [], "ux": [], "uy": []}
                        for nid, (ux, uy) in result["displacements"].items():
                            disp_data["Node"].append(nid)
                            disp_data["ux"].append(f"{ux:.3f}")
                            disp_data["uy"].append(f"{uy:.3f}")
                        st.table(disp_data)
                    with col_r2:
                        st.markdown("**Element Forces (kN)**")
                        force_data = {"Element": [], "Force": []}
                        for idx, f in enumerate(result["forces"], start=1):
                            force_data["Element"].append(idx)
                            force_data["Force"].append(f"{f:.3f}")
                        st.table(force_data)

    # ---- CONNECTIONS ----
    with tabs[9]:
        st.subheader("Steel Connection Design (Simplified)")
        conn_type = st.selectbox("Connection type", ["bolted", "welded"], key="conn_type")
        load = ui_number_input(f"Applied force ({unit_label('force')})", 1.0, 1000.0, 100.0, 1.0, "conn_load", "force")
        if conn_type == "bolted":
            bolt_dia = ui_number_input("Bolt diameter (mm)", 12, 30, 20, 1, "conn_bolt_dia", "length_mm")
            bolt_grade = st.selectbox("Bolt grade", ["4.6", "8.8", "10.9"], key="conn_bolt_grade")
            num_bolts = st.number_input("Number of bolts", 1, 20, 4, key="conn_num_bolts")
            plate_thickness = ui_number_input("Plate thickness (mm)", 5, 40, 10, 1, "conn_plate_t", "length_mm")
            if st.button("Check Connection", key="conn_check"):
                res = steel_connection_check("bolted", bolt_dia, bolt_grade, num_bolts, plate_thickness, 0, load)
                if res["status"] == "OK":
                    st.success(f"Connection OK – Utilization: {res['utilization']:.2f}")
                else:
                    st.error(f"Connection FAILS – Utilization: {res['utilization']:.2f}")

    # ---- LOAD COMBINATIONS ----
    with tabs[10]:
        st.subheader("Load Combinations")
        code = st.selectbox("Design code", ["eurocode", "asce"], key="lc_code")
        c1, c2, c3, c4, c5 = st.columns(5)
        dead = c1.number_input("Dead (G)", value=0.0, key="lc_dead")
        live = c2.number_input("Live (Q)", value=0.0, key="lc_live")
        wind = c3.number_input("Wind (W)", value=0.0, key="lc_wind")
        snow = c4.number_input("Snow (S)", value=0.0, key="lc_snow")
        seismic = c5.number_input("Seismic (E)", value=0.0, key="lc_seis")
        if st.button("Generate Combinations", key="lc_generate"):
            combos = load_combinations({"dead":dead,"live":live,"wind":wind,"snow":snow,"seismic":seismic}, code)
            st.markdown("**Combinations**")
            table = {"Combination": [], "Value": []}
            for name, val in combos:
                table["Combination"].append(name)
                table["Value"].append(f"{val:.2f}")
            st.table(table)

    # ---- SEISMIC ----
    with tabs[11]:
        st.subheader("Seismic Base Shear (Simplified ASCE 7-10)")
        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
        Ss = col_s1.number_input("Ss (g)", min_value=0.0, value=1.0, key="seis_Ss")
        S1 = col_s2.number_input("S1 (g)", min_value=0.0, value=0.4, key="seis_S1")
        site_class = col_s3.selectbox("Site Class", ["A","B","C","D","E"], key="seis_site")
        R = col_s4.number_input("R factor", min_value=1.0, value=5.0, key="seis_R")
        if st.button("Calculate Base Shear", key="seis_calc"):
            res = seismic_base_shear(Ss, S1, site_class, R, 1.0, 0.5)
            st.metric("Seismic response coefficient Cs", f"{res['Cs']:.4f}")

# ======================
# PAGE: EUROCODES
# ======================
elif page == "Eurocodes":
    st.title("Eurocode Design Modules")
    st.caption("Detailed design per European Standards (EN 1990 – EN 1999)")

    euro_tabs = st.tabs([
        "EN 1990", "EN 1991", "EN 1992", "EN 1993", "EN 1994",
        "EN 1995", "EN 1996", "EN 1997", "EN 1998", "EN 1999"
    ])

    # EN 1990 - Load Combinations
    with euro_tabs[0]:
        st.subheader("EN 1990 – Load Combinations")
        code_type = st.radio("Combination type", ["ULS", "SLS"], key="ec0_type")
        c1, c2, c3, c4, c5 = st.columns(5)
        dead = c1.number_input("Dead (G)", value=100.0, key="ec0_dead")
        live = c2.number_input("Live (Q)", value=50.0, key="ec0_live")
        wind = c3.number_input("Wind (W)", value=30.0, key="ec0_wind")
        snow = c4.number_input("Snow (S)", value=20.0, key="ec0_snow")
        seismic = c5.number_input("Seismic (E)", value=0.0, key="ec0_seismic")
        if code_type == "ULS":
            if st.button("Generate ULS Combinations", key="ec0_uls"):
                combos = ec0.eurocode_uls_combinations(dead, live, wind, snow, seismic)
                table = {"Combination": [], "Value": []}
                for name, val, _, _ in combos:
                    table["Combination"].append(name)
                    table["Value"].append(f"{val:.2f}")
                st.table(table)
        else:
            if st.button("Generate SLS Combinations", key="ec0_sls"):
                combos = ec0.eurocode_sls_combinations(dead, live, wind, snow)
                table = {"Combination": [], "Value": []}
                for name, val in combos:
                    table["Combination"].append(name)
                    table["Value"].append(f"{val:.2f}")
                st.table(table)

    # EN 1991 - Actions
    with euro_tabs[1]:
        st.subheader("EN 1991 – Actions on Structures")
        building_type = st.selectbox("Building type", ["residential", "office", "assembly", "retail", "storage", "industrial"], key="ec1_btype")
        imposed = ec1.en1991_imposed_loads(building_type)
        st.metric(f"Imposed load ({building_type})", f"{imposed} kN/m²")
        st.markdown("---")
        altitude = st.number_input("Altitude (m)", 0, 3000, 0, key="ec1_alt")
        snow = ec1.en1991_snow_load(altitude_m=altitude)
        st.metric("Snow load", f"{snow:.2f} kN/m²")
        st.markdown("---")
        wind_speed = st.number_input("Basic wind speed (m/s)", 10, 50, 25, key="ec1_wind")
        terrain = st.selectbox("Terrain category", ["0", "I", "II", "III", "IV"], key="ec1_terrain")
        wind_pressure = ec1.en1991_wind_load(wind_speed, terrain)
        st.metric("Wind pressure", f"{wind_pressure:.2f} kPa")

    # EN 1992 - Concrete
    with euro_tabs[2]:
        st.subheader("EN 1992 – Concrete Structures")
        col1, col2 = st.columns(2)
        with col1:
            b = st.number_input("Width (mm)", 100, 1000, 300, key="ec2_b")
            h = st.number_input("Height (mm)", 200, 2000, 500, key="ec2_h")
            d = st.number_input("Effective depth (mm)", 100, 1900, 450, key="ec2_d")
            fck = st.selectbox("Concrete grade", list(CONCRETE_GRADES.keys()), key="ec2_fck")
            fyk = st.number_input("Steel yield (MPa)", 400, 600, 500, key="ec2_fyk")
        with col2:
            M_ed = st.number_input("Design moment (kNm)", 10.0, 2000.0, 120.0, key="ec2_Med")
            V_ed = st.number_input("Design shear (kN)", 10.0, 1000.0, 80.0, key="ec2_Ved")
            span = st.number_input("Span (m)", 1.0, 30.0, 6.0, key="ec2_span")
        if st.button("Design RC Beam (EN 1992)", key="ec2_beam"):
            fck_val = CONCRETE_GRADES[fck]["fck"]
            res = ec2.en1992_rc_beam_design(b, h, d, fck_val, fyk, M_ed, V_ed, span)
            if "error" in res:
                st.error(res["error"])
            elif res["pass"]:
                st.success("RC beam OK per EN 1992")
            else:
                st.error("RC beam fails per EN 1992")
            st.json(res)

    # EN 1993 - Steel
    with euro_tabs[3]:
        st.subheader("EN 1993 – Steel Structures")
        section = st.selectbox("Section", ["IPE 160", "IPE 220", "IPE 300", "IPE 400", "IPE 500"], key="ec3_section")
        fy = st.selectbox("Steel grade", list(STEEL_GRADES.keys()), key="ec3_fy")
        M_ed = st.number_input("Design moment (kNm)", 50.0, 2000.0, 100.0, key="ec3_Med")
        V_ed = st.number_input("Design shear (kN)", 20.0, 1000.0, 50.0, key="ec3_Ved")
        span = st.number_input("Span (m)", 2.0, 30.0, 6.0, key="ec3_span")
        buckling = st.checkbox("Check LTB", value=True, key="ec3_ltb")
        if st.button("Design Steel Beam (EN 1993)", key="ec3_beam"):
            fy_val = STEEL_GRADES[fy]["fy"]
            res = ec3.en1993_steel_beam_design(section, fy_val, M_ed, V_ed, span, buckling)
            if "error" in res:
                st.error(res["error"])
            elif res["pass"]:
                st.success("Steel beam OK per EN 1993")
            else:
                st.error("Steel beam fails per EN 1993")
            st.json(res)

    # EN 1994 - Composite
    with euro_tabs[4]:
        st.subheader("EN 1994 – Composite Structures")
        section = st.selectbox("Steel Section", ["IPE 160", "IPE 220", "IPE 300"], key="ec4_section")
        slab_t = st.number_input("Slab thickness (mm)", 50, 200, 120, key="ec4_slabt")
        slab_w = st.number_input("Slab width (mm)", 500, 3000, 1500, key="ec4_slabw")
        fck = st.selectbox("Concrete grade", list(CONCRETE_GRADES.keys()), key="ec4_fck")
        fy = st.selectbox("Steel grade", list(STEEL_GRADES.keys()), key="ec4_fy")
        M_ed = st.number_input("Design moment (kNm)", 50.0, 2000.0, 200.0, key="ec4_Med")
        V_ed = st.number_input("Design shear (kN)", 20.0, 1000.0, 100.0, key="ec4_Ved")
        span = st.number_input("Span (m)", 2.0, 30.0, 8.0, key="ec4_span")
        if st.button("Design Composite Beam (EN 1994)", key="ec4_beam"):
            fck_val = CONCRETE_GRADES[fck]["fck"]
            fy_val = STEEL_GRADES[fy]["fy"]
            res = ec4.en1994_composite_beam_design(section, slab_t, slab_w, fck_val, fy_val, M_ed, V_ed, span)
            if "error" in res:
                st.error(res["error"])
            elif res["pass"]:
                st.success("Composite beam OK per EN 1994")
            else:
                st.error("Composite beam fails per EN 1994")
            st.json(res)

    # EN 1995 - Timber
    with euro_tabs[5]:
        st.subheader("EN 1995 – Timber Structures")
        timber_class = st.selectbox("Timber class", list(TIMBER_CLASSES.keys()), key="ec5_class")
        b = st.number_input("Width (mm)", 50, 400, 100, key="ec5_b")
        h = st.number_input("Depth (mm)", 100, 600, 300, key="ec5_h")
        M_ed = st.number_input("Design moment (kNm)", 5.0, 200.0, 30.0, key="ec5_Med")
        V_ed = st.number_input("Design shear (kN)", 1.0, 100.0, 20.0, key="ec5_Ved")
        span = st.number_input("Span (m)", 1.0, 15.0, 5.0, key="ec5_span")
        service_class = st.selectbox("Service class", [1, 2, 3], key="ec5_sc")
        load_duration = st.selectbox("Load duration", ["short", "medium", "long"], key="ec5_ld")
        if st.button("Design Timber Beam (EN 1995)", key="ec5_beam"):
            res = ec5.en1995_timber_beam_design(timber_class, b, h, M_ed, V_ed, span, service_class, load_duration)
            if "error" in res:
                st.error(res["error"])
            elif res["pass"]:
                st.success("Timber beam OK per EN 1995")
            else:
                st.error("Timber beam fails per EN 1995")
            st.json(res)

    # EN 1996 - Masonry
    with euro_tabs[6]:
        st.subheader("EN 1996 – Masonry Structures")
        wall_t = st.number_input("Wall thickness (mm)", 100, 500, 215, key="ec6_t")
        wall_h = st.number_input("Wall height (m)", 1.0, 10.0, 3.0, key="ec6_h")
        fk = st.number_input("Masonry strength fk (MPa)", 2.0, 20.0, 5.0, key="ec6_fk")
        N_ed = st.number_input("Axial load (kN/m)", 10.0, 1000.0, 100.0, key="ec6_N")
        if st.button("Check Masonry Wall (EN 1996)", key="ec6_wall"):
            res = ec6.en1996_masonry_wall_design(wall_t, wall_h, fk, N_ed)
            if "error" in res:
                st.error(res["error"])
            elif res["pass"]:
                st.success("Masonry wall OK per EN 1996")
            else:
                st.error("Masonry wall fails per EN 1996")
            st.json(res)

    # EN 1997 - Geotechnical
    with euro_tabs[7]:
        st.subheader("EN 1997 – Geotechnical Design")
        st.markdown("**Shallow Foundation**")
        load = st.number_input("Column load (kN)", 100.0, 10000.0, 500.0, key="ec7_load")
        bearing = st.number_input("Bearing capacity (kPa)", 50.0, 500.0, 150.0, key="ec7_bearing")
        if st.button("Size Footing (EN 1997)", key="ec7_footing"):
            res = ec7.en1997_shallow_foundation(load, bearing)
            if "error" in res:
                st.error(res["error"])
            else:
                st.success(f"Footing side: {res['side_m']:.2f} m")
        st.markdown("---")
        st.markdown("**Pile Capacity**")
        dia = st.number_input("Pile diameter (m)", 0.3, 2.0, 0.6, key="ec7_dia")
        length = st.number_input("Pile length (m)", 5.0, 40.0, 15.0, key="ec7_len")
        soil = st.selectbox("Soil type", ["sand", "clay"], key="ec7_soil")
        N = st.number_input("SPT N-value", 5, 60, 20, key="ec7_N")
        if st.button("Calculate Pile Capacity (EN 1997)", key="ec7_pile"):
            res = ec7.en1997_pile_capacity(dia, length, soil, N)
            if "error" in res:
                st.error(res["error"])
            else:
                st.metric("Allowable Capacity", f"{res['Q_all_kN']:.1f} kN")

    # EN 1998 - Seismic
    with euro_tabs[8]:
        st.subheader("EN 1998 – Seismic Design")
        W = st.number_input("Seismic weight (kN)", 100.0, 10000.0, 1000.0, key="ec8_W")
        ag = st.number_input("Ground acceleration ag (g)", 0.05, 0.5, 0.25, key="ec8_ag")
        soil_class = st.selectbox("Soil class", ["A", "B", "C", "D", "E"], key="ec8_soil")
        q_factor = st.number_input("Behaviour factor q", 1.0, 5.0, 2.0, key="ec8_q")
        T = st.number_input("Period T (s)", 0.1, 4.0, 0.5, key="ec8_T")
        if st.button("Calculate Base Shear (EN 1998)", key="ec8_shear"):
            res = ec8.en1998_base_shear(W, ag, soil_class, q_factor, T)
            st.metric("Base Shear", f"{res['V_base_kN']:.1f} kN")

    # EN 1999 - Aluminium
    with euro_tabs[9]:
        st.subheader("EN 1999 – Aluminium Structures")
        alloy = st.selectbox("Alloy", ["6082-T6", "6061-T6", "7075-T6"], key="ec9_alloy")
        W = st.number_input("Section modulus (mm³)", 10000, 1000000, 100000, key="ec9_W")
        M_ed = st.number_input("Design moment (kNm)", 10.0, 500.0, 50.0, key="ec9_Med")
        V_ed = st.number_input("Design shear (kN)", 5.0, 200.0, 20.0, key="ec9_Ved")
        span = st.number_input("Span (m)", 1.0, 20.0, 5.0, key="ec9_span")
        if st.button("Check Aluminium Beam (EN 1999)", key="ec9_beam"):
            res = ec9.en1999_aluminium_beam_design(alloy, W, M_ed, V_ed, span)
            if "error" in res:
                st.error(res["error"])
            elif res["pass"]:
                st.success("Aluminium beam OK per EN 1999")
            else:
                st.error("Aluminium beam fails per EN 1999")
            st.json(res)

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
                    st.markdown(f'<div style="background:#0F172A; border-radius:12px; padding:8px; border:1px solid #334155;">{svg}</div>', unsafe_allow_html=True)
                else:
                    st.write("No plan data.")
    else:
        st.info("No projects yet. Go to the Project Dashboard to create one.")
