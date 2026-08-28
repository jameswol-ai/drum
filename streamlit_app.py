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
    log_event, DEFAULT_STATE,
    list_users, update_user_role, delete_user, is_admin, is_engineer,
    create_project, get_projects, get_project, update_project, delete_project,
    add_member, get_members, update_member, delete_member,
    add_member_analysis, delete_member_analysis,
    add_drawing, get_drawings, delete_drawing,
    save_analysis, get_analyses, delete_analysis,
    get_material_costs, update_material_costs, get_theme, update_theme,
    init_quests, update_quests, grant_quest_rewards
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
from engineering.cost import estimate_cost
from engineering.pdf_report import generate_pdf_report
from engineering.visualization import plot_beam_diagrams, plot_truss_deformed

import eurocodes.en1990 as ec0
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
    st.session_state.active_project = None
    st.session_state.active_member = None
    st.session_state.unit_system = "metric"
    st.session_state.page = "Projects"

if not load_users():
    admin_user = os.environ.get("DRUM_ADMIN_USER", "admin")
    admin_pass = os.environ.get("DRUM_ADMIN_PASS", None)
    if admin_pass is None:
        admin_pass = "admin123"
    create_user(admin_user, admin_pass, role="admin")

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
    transition: all 0.3s ease;
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
.news-title {{ font-weight: 600; color: {text_color}; }}
.news-date {{ color: #94A3B8; font-size: 0.8rem; }}
.news-summary {{ color: {text_color}; font-size: 0.9rem; }}
.project-header {{
    background: linear-gradient(135deg, {card_bg}, {border_color});
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 20px;
    border: 1px solid #3B82F6;
}}
.member-card {{
    background: {card_bg};
    border: 1px solid {border_color};
    border-radius: 10px;
    padding: 12px;
    margin-bottom: 8px;
}}
</style>
""", unsafe_allow_html=True)

def input_metric(value, unit_type):
    if st.session_state.unit_system == "imperial":
        conversions = {
            "length": 0.3048, "length_mm": 0.0254, "area": 0.092903,
            "force": 4.44822, "pressure": 6.89476, "moment": 1.35582,
            "weight_density": 0.157087
        }
        if unit_type in conversions:
            return value * conversions[unit_type]
    return value

def output_metric(value, unit_type):
    if st.session_state.unit_system == "imperial":
        conversions = {
            "length": 3.28084, "length_mm": 39.3701, "area": 10.7639,
            "force": 0.224809, "pressure": 0.145038, "moment": 0.737562,
            "weight_density": 6.36588, "stress": 0.145038
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
        "stress": "MPa" if st.session_state.unit_system == "metric" else "ksi",
    }
    return labels.get(unit_type, "")

def get_engineering_news():
    return [
        {"title": "Eurocode Updates: EN 1992-1-1 Amendment", "date": "2024-11-15",
         "summary": "CEN published amendment to EN 1992-1-1 with revised shear design provisions."},
        {"title": "Structural Health Monitoring Advances", "date": "2024-10-28",
         "summary": "Fiber optic sensors enable real-time strain monitoring of critical members."},
        {"title": "AI in Structural Analysis", "date": "2024-09-20",
         "summary": "Machine learning accelerates structural optimization and failure prediction."},
    ]

# ====================== LOGIN ======================
if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align:center;'>DRUM Studio</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; color:#94A3B8;'>Structural Member Analysis Platform</p>", unsafe_allow_html=True)
        with st.form("auth_form", clear_on_submit=True):
            uname = st.text_input("Username")
            pwd = st.text_input("Password", type="password")
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
                        st.success("Account created!")
                    except ValueError as e:
                        st.error(str(e))
    st.stop()

# ====================== MAIN APP ======================
username = st.session_state.username
user_data = st.session_state.user_data
mem = st.session_state.memory

with st.sidebar:
    st.markdown("### DRUM Studio")
    st.markdown(f"**{username}** ({user_data.get('role', 'viewer')})")
    st.markdown("---")
    page = st.radio("Navigate",
                    ["Projects", "Structural Analysis", "Eurocodes", "Reports", "News"],
                    index=0, key="nav_radio")
    st.session_state.page = page
    unit_choice = st.radio("Units", ["metric", "imperial"], index=0, key="unit_radio")
    st.session_state.unit_system = unit_choice

    with st.expander("Appearance"):
        current_theme = get_theme(username)
        new_theme = st.radio("Theme", ["dark", "light"], index=0 if current_theme == "dark" else 1)
        if new_theme != current_theme:
            update_theme(username, new_theme)
            st.rerun()

    if is_admin(user_data):
        with st.expander("User Management"):
            for u in list_users():
                col_u1, col_u2 = st.columns([2,1])
                col_u1.write(u["username"])
                new_role = col_u2.selectbox("Role", ["admin","engineer","viewer"],
                                            index=["admin","engineer","viewer"].index(u["role"]),
                                            key=f"role_{u['username']}")
                if new_role != u["role"]:
                    update_user_role(u["username"], new_role)
                    st.rerun()

    if st.button("Logout"):
        save_memory(username, mem)
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# ====================== PROJECTS ======================
if page == "Projects":
    st.title("Structural Projects")

    if is_engineer(user_data):
        with st.expander("Create New Project", expanded=False):
            project_name = st.text_input("Project Name")
            project_desc = st.text_area("Description")
            col_p1, col_p2 = st.columns(2)
            project_type = col_p1.selectbox("Type", ["building", "bridge", "tower", "industrial", "other"])
            project_level = col_p2.selectbox("Level", ["substructure", "superstructure"])
            if st.button("Create Project", use_container_width=True):
                if project_name.strip():
                    create_project(username, project_name, project_desc, project_type, project_level)
                    st.success(f"Project created!")
                    st.rerun()
                else:
                    st.error("Enter a project name.")

    projects = get_projects(username)
    if projects:
        st.markdown("### Projects")
        for p in projects:
            with st.expander(f"{p.name} – {p.level} ({len(p.members)} members)"):
                st.write(f"**Type:** {p.project_type}")
                st.write(f"**Description:** {p.description or 'N/A'}")
                st.write(f"**Level:** {p.level}")

                if is_engineer(user_data):
                    col_e1, col_e2, col_e3, col_e4 = st.columns(4)
                    new_name = col_e1.text_input("Name", value=p.name, key=f"ename_{p.id}")
                    new_desc = col_e2.text_input("Desc", value=p.description, key=f"edesc_{p.id}")
                    new_type = col_e3.selectbox("Type", ["building","bridge","tower","industrial","other"],
                                                index=["building","bridge","tower","industrial","other"].index(p.project_type),
                                                key=f"etype_{p.id}")
                    new_level = col_e4.selectbox("Level", ["substructure","superstructure"],
                                                 index=["substructure","superstructure"].index(p.level),
                                                 key=f"elevel_{p.id}")
                    if st.button("Update", key=f"upd_{p.id}"):
                        update_project(username, p.id, new_name, new_desc, new_type, new_level)
                        st.success("Updated!")
                        st.rerun()
                    if st.button("Delete Project", key=f"delproj_{p.id}"):
                        delete_project(username, p.id)
                        st.rerun()

                # Drawings
                st.markdown("**Drawings**")
                drawings = get_drawings(username, p.id)
                if drawings:
                    for d in drawings:
                        st.write(f"- {d['name']} ({d['type']}, {d['level']})")
                        if is_engineer(user_data):
                            if st.button("Del", key=f"deldwg_{d['id']}"):
                                delete_drawing(username, p.id, d['id'])
                                st.rerun()
                else:
                    st.caption("No drawings imported.")

                if is_engineer(user_data):
                    st.markdown("**Import Drawing**")
                    col_d1, col_d2, col_d3 = st.columns(3)
                    dwg_name = col_d1.text_input("Drawing Name", key=f"dwgname_{p.id}")
                    dwg_type = col_d2.selectbox("Type", ["plan", "section", "elevation", "detail"], key=f"dwgtype_{p.id}")
                    dwg_level = col_d3.selectbox("Level", ["substructure", "superstructure"], key=f"dwglevel_{p.id}")
                    uploaded_file = st.file_uploader("Upload Drawing (optional)", type=["png", "jpg", "pdf", "dxf"], key=f"dwgupload_{p.id}")
                    if st.button("Add Drawing", key=f"adddwg_{p.id}"):
                        if dwg_name.strip():
                            file_data = uploaded_file.read() if uploaded_file else None
                            add_drawing(username, p.id, dwg_name, dwg_type, dwg_level, file_data)
                            st.success("Drawing added!")
                            st.rerun()

                # Members
                st.markdown("**Members**")
                members = get_members(username, p.id)
                if members:
                    for m in members:
                        st.markdown(f"- **{m['name']}** ({m['type']}, {m.get('level','superstructure')}) – {len(m.get('analyses',[]))} analyses")
                        if is_engineer(user_data):
                            if st.button("Del Member", key=f"delmem_{m['id']}"):
                                delete_member(username, p.id, m['id'])
                                st.rerun()
                else:
                    st.caption("No members yet.")

                if is_engineer(user_data):
                    st.markdown("**Add Member**")
                    col_m1, col_m2, col_m3 = st.columns(3)
                    member_name = col_m1.text_input("Member Name", key=f"mname_{p.id}")
                    member_type = col_m2.selectbox("Type", ["Beam", "Column", "Slab", "Footing", "Pile", "Connection", "Wall"], key=f"mtype_{p.id}")
                    member_level = col_m3.selectbox("Level", ["substructure", "superstructure"], key=f"mlevel_{p.id}")
                    if st.button("Add Member", key=f"addmem_{p.id}"):
                        if member_name.strip():
                            add_member(username, p.id, member_type.lower(), member_name, {}, member_level)
                            st.success("Member added!")
                            st.rerun()
    else:
        st.info("No projects yet.")

# ====================== STRUCTURAL ANALYSIS ======================
elif page == "Structural Analysis":
    st.title("Structural Analysis")

    projects = get_projects(username)
    if not projects:
        st.info("Create a project first.")
    else:
        project_names = [p.name for p in projects]
        selected_project = st.selectbox("Select Project", project_names)
        project = next(p for p in projects if p.name == selected_project)
        st.session_state.active_project = project

        members = get_members(username, project.id)
        if members:
            member_names = [m['name'] for m in members]
            selected_member = st.selectbox("Select Member", member_names)
            member = next(m for m in members if m['name'] == selected_member)
            st.session_state.active_member = member

            st.markdown(f"### {member['name']} ({member['type']}, {member.get('level','superstructure')})")

            tabs = st.tabs([
                "Beams", "Columns", "Slabs", "Foundations",
                "Piles", "Prestressed", "Truss", "Connections",
                "Load Combos", "Seismic", "Saved Analyses"
            ])

            with tabs[0]:
                st.subheader("Beam Design")
                beam_mat = st.selectbox("Material", ["RC", "Steel", "Timber", "Composite"], key="beam_mat")
                if beam_mat == "RC":
                    grade = st.selectbox("Concrete Grade", list(CONCRETE_GRADES.keys()))
                    b = st.number_input("Width (mm)", 100, 1000, 300)
                    h = st.number_input("Height (mm)", 200, 2000, 500)
                    span = st.number_input("Span (m)", 1.0, 30.0, 6.0)
                    M_ed = st.number_input("Moment (kNm)", 10.0, 1000.0, 120.0)
                    V_ed = st.number_input("Shear (kN)", 10.0, 500.0, 80.0)
                    if st.button("Analyze RC Beam"):
                        fck = CONCRETE_GRADES[grade]["fck"]
                        res = check_rc_beam(b, h, h-50, fck, M_ed, V_ed, span)
                        st.json(res)
                        if res["pass"]: st.success("Beam OK")
                        else: st.error("Beam fails")
                        if st.button("Save to Member"):
                            add_member_analysis(username, project.id, member['id'], "RC Beam", res)
                            st.success("Saved!")
                elif beam_mat == "Steel":
                    section = st.selectbox("Section", ["IPE 160", "IPE 220", "IPE 300"])
                    span = st.number_input("Span (m)", 2.0, 20.0, 6.0)
                    M_ed = st.number_input("Moment (kNm)", 50.0, 1000.0, 100.0)
                    V_ed = st.number_input("Shear (kN)", 20.0, 500.0, 50.0)
                    if st.button("Analyze Steel Beam"):
                        steel = {"fy": 355, "E": 210e3}
                        res = check_steel_beam(section, M_ed, V_ed, span, steel)
                        st.json(res)
                        if res["pass"]: st.success("Beam OK")
                        else: st.error("Beam fails")
                elif beam_mat == "Timber":
                    timber_class = st.selectbox("Timber Class", list(TIMBER_CLASSES.keys()))
                    b = st.number_input("Width (mm)", 50, 400, 100)
                    h = st.number_input("Depth (mm)", 100, 600, 300)
                    span = st.number_input("Span (m)", 1.0, 15.0, 5.0)
                    M_ed = st.number_input("Moment (kNm)", 5.0, 200.0, 30.0)
                    V_ed = st.number_input("Shear (kN)", 1.0, 100.0, 20.0)
                    if st.button("Analyze Timber Beam"):
                        res = check_timber_beam(timber_class, b, h, M_ed, V_ed, span)
                        st.json(res)
                        if res["pass"]: st.success("Beam OK")
                        else: st.error("Beam fails")
                elif beam_mat == "Composite":
                    section = st.selectbox("Steel Section", ["IPE 160", "IPE 220", "IPE 300"])
                    slab_t = st.number_input("Slab thickness (mm)", 50, 200, 120)
                    slab_w = st.number_input("Slab width (mm)", 500, 3000, 1500)
                    M_ed = st.number_input("Moment (kNm)", 50.0, 1000.0, 200.0)
                    V_ed = st.number_input("Shear (kN)", 20.0, 500.0, 100.0)
                    span = st.number_input("Span (m)", 2.0, 20.0, 8.0)
                    if st.button("Analyze Composite Beam"):
                        steel = {"fy": 355, "E": 210e3}
                        res = check_composite_beam(section, slab_t, slab_w, 30, M_ed, V_ed, span, steel)
                        st.json(res)
                        if res["pass"]: st.success("Beam OK")
                        else: st.error("Beam fails")

            with tabs[1]:
                st.subheader("Column Design")
                N_ed = st.number_input("Axial Load (kN)", 100.0, 5000.0, 500.0)
                M_ed = st.number_input("Moment (kNm)", 0.0, 500.0, 20.0)
                b = st.number_input("Width (mm)", 200, 1000, 300)
                h = st.number_input("Depth (mm)", 200, 1000, 300)
                l0 = st.number_input("Effective Length (m)", 2.0, 10.0, 3.0)
                if st.button("Analyze Column"):
                    res = check_rc_column(N_ed, M_ed, b, h, 30, l0)
                    st.json(res)
                    if res["pass"]: st.success("Column OK")
                    else: st.error("Column fails")

            with tabs[2]:
                st.subheader("Slab Thickness")
                span = st.number_input("Span (m)", 2.0, 15.0, 5.0)
                support = st.selectbox("Support", ["simply_supported", "continuous"])
                t = slab_thickness_estimate(span, support)
                st.success(f"Thickness: {t*1000:.0f} mm")

            with tabs[3]:
                st.subheader("Footing Sizing")
                load = st.number_input("Load (kN)", 100.0, 10000.0, 500.0)
                bearing = st.number_input("Bearing (kPa)", 50.0, 500.0, 150.0)
                if st.button("Size Footing"):
                    res = foundation_size(bearing, load)
                    if "error" in res: st.error(res["error"])
                    else: st.success(f"Side: {res['side_m']:.2f} m")

            with tabs[4]:
                st.subheader("Pile Capacity")
                dia = st.number_input("Diameter (m)", 0.3, 2.0, 0.6)
                length = st.number_input("Length (m)", 5.0, 40.0, 15.0)
                soil = st.selectbox("Soil", ["sand", "clay"])
                N = st.number_input("SPT N", 5, 60, 20)
                if st.button("Calculate"):
                    res = pile_capacity(dia, length, soil, N)
                    st.metric("Allowable Capacity", f"{res['Q_all_kN']:.1f} kN")

            with tabs[5]:
                st.subheader("Prestressed Beam")
                M_ext = st.number_input("Moment (kNm)", 100.0, 5000.0, 500.0)
                P = st.number_input("Prestress (kN)", 100.0, 5000.0, 1000.0)
                e = st.number_input("Eccentricity (m)", 0.0, 1.0, 0.2)
                A = st.number_input("Area (m²)", 0.05, 2.0, 0.3)
                I = st.number_input("I (m⁴)", 0.001, 0.2, 0.01)
                if st.button("Check"):
                    res = check_prestressed_beam(M_ext, P, e, A, I, 0.5, 0.5, 35)
                    if res["pass"]: st.success("OK")
                    else: st.error("Fails")

            with tabs[6]:
                st.subheader("Truss Solver")
                n_nodes = st.number_input("Nodes", 2, 10, 3)
                n_elem = st.number_input("Elements", 1, 20, 2)
                nodes = {}
                for i in range(int(n_nodes)):
                    c1, c2 = st.columns(2)
                    x = c1.number_input(f"N{i+1} X", value=0.0, key=f"tn_{i}_x")
                    y = c2.number_input(f"N{i+1} Y", value=0.0, key=f"tn_{i}_y")
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
                if st.button("Solve"):
                    res = truss_analysis(nodes, elements, loads, supports)
                    if "error" in res: st.error(res["error"])
                    else:
                        st.success("Solved")
                        st.json(res)

            with tabs[7]:
                st.subheader("Connections")
                load = st.number_input("Force (kN)", 1.0, 1000.0, 100.0)
                bolt_dia = st.number_input("Bolt dia (mm)", 12, 30, 20)
                num_bolts = st.number_input("Bolts", 1, 20, 4)
                if st.button("Check"):
                    res = steel_connection_check("bolted", bolt_dia, "8.8", num_bolts, 10, 0, load)
                    if res["status"] == "OK": st.success(f"OK – {res['utilization']:.2f}")
                    else: st.error(f"Fails – {res['utilization']:.2f}")

            with tabs[8]:
                st.subheader("Load Combinations")
                dead = st.number_input("Dead", value=100.0)
                live = st.number_input("Live", value=50.0)
                wind = st.number_input("Wind", value=30.0)
                if st.button("Generate"):
                    combos = load_combinations({"dead": dead, "live": live, "wind": wind})
                    for name, val in combos:
                        st.write(f"{name}: {val:.2f}")

            with tabs[9]:
                st.subheader("Seismic")
                Ss = st.number_input("Ss", 0.0, 3.0, 1.0)
                S1 = st.number_input("S1", 0.0, 2.0, 0.4)
                site = st.selectbox("Site", ["A","B","C","D","E"])
                if st.button("Calculate"):
                    res = seismic_base_shear(Ss, S1, site, 5, 1.0, 0.5)
                    st.metric("Cs", f"{res['Cs']:.4f}")

            with tabs[10]:
                st.subheader("Saved Analyses")
                for a in member.get('analyses', []):
                    with st.expander(f"{a['type']} – {a['created_at'][:10]}"):
                        st.json(a['data'])
                        if st.button("Delete", key=f"dela_{a['id']}"):
                            delete_member_analysis(username, project.id, member['id'], a['id'])
                            st.rerun()
        else:
            st.info("Add members to this project first.")

# ====================== EUROCODES ======================
elif page == "Eurocodes":
    st.title("Eurocode Analysis")
    tabs = st.tabs(["EN 1990", "EN 1992", "EN 1993", "EN 1994", "EN 1995", "EN 1996", "EN 1997", "EN 1998", "EN 1999"])
    
    with tabs[0]:
        st.subheader("Load Combinations")
        dead = st.number_input("Dead", value=100.0)
        live = st.number_input("Live", value=50.0)
        wind = st.number_input("Wind", value=30.0)
        if st.button("Generate"):
            combos = ec0.eurocode_uls_combinations(dead, live, wind)
            for name, val, _, _ in combos:
                st.write(f"{name}: {val:.2f}")
    with tabs[1]:
        st.subheader("RC Beam")
        b = st.number_input("Width (mm)", 100, 1000, 300)
        h = st.number_input("Height (mm)", 200, 2000, 500)
        M_ed = st.number_input("Moment (kNm)", 10.0, 2000.0, 120.0)
        if st.button("Design Beam"):
            res = ec2.en1992_rc_beam_design(b, h, h-50, 30, 500, M_ed, 80, 6)
            st.json(res)
    with tabs[2]:
        st.subheader("Steel Beam")
        section = st.selectbox("Section", ["IPE 160", "IPE 220", "IPE 300"])
        M_ed = st.number_input("Moment (kNm)", 50.0, 1000.0, 100.0)
        if st.button("Design Steel"):
            res = ec3.en1993_steel_beam_design(section, 355, M_ed, 50, 6, True)
            st.json(res)
    with tabs[3]:
        st.subheader("Composite")
        st.info("EN 1994 module")
    with tabs[4]:
        st.subheader("Timber")
        tc = st.selectbox("Class", ["C24", "GL24h"])
        b = st.number_input("Width", 50, 400, 100)
        h = st.number_input("Depth", 100, 600, 300)
        M = st.number_input("Moment", 5.0, 200.0, 30.0)
        if st.button("Design Timber"):
            res = ec5.en1995_timber_beam_design(tc, b, h, M, 20, 5)
            st.json(res)
    with tabs[5]:
        st.subheader("Masonry")
        st.info("EN 1996 module")
    with tabs[6]:
        st.subheader("Geotechnical")
        load = st.number_input("Load (kN)", 100.0, 10000.0, 500.0)
        bearing = st.number_input("Bearing (kPa)", 50.0, 500.0, 150.0)
        if st.button("Size"):
            res = ec7.en1997_shallow_foundation(load, bearing)
            st.success(f"Side: {res['side_m']:.2f} m")
    with tabs[7]:
        st.subheader("Seismic")
        W = st.number_input("Weight (kN)", 100.0, 10000.0, 1000.0)
        ag = st.number_input("ag (g)", 0.05, 0.5, 0.25)
        if st.button("Calculate"):
            res = ec8.en1998_base_shear(W, ag, "C", 2.0, 0.5)
            st.metric("Base Shear", f"{res['V_base_kN']:.1f} kN")
    with tabs[8]:
        st.subheader("Aluminium")
        st.info("EN 1999 module")

# ====================== REPORTS ======================
elif page == "Reports":
    st.title("Project Reports")
    projects = get_projects(username)
    if projects:
        pnames = [p.name for p in projects]
        selected = st.selectbox("Project", pnames)
        project = next(p for p in projects if p.name == selected)
        st.markdown(f"### {project.name}")
        st.write(f"Type: {project.project_type} | Level: {project.level}")
        members = get_members(username, project.id)
        if members:
            for m in members:
                with st.expander(f"{m['name']} ({m['type']})"):
                    for a in m.get('analyses', []):
                        st.write(f"**{a['type']}**")
                        st.json(a['data'])
        if st.button("Generate PDF"):
            data = {"Project": project.name, "Type": project.project_type, "Level": project.level, "Members": len(members)}
            filename, error = generate_pdf_report(data, filename=f"{project.name}_report.pdf")
            if error: st.error(error)
            else:
                with open(filename, "rb") as f:
                    st.download_button("Download", f, file_name=filename)
    else:
        st.info("No projects.")

# ====================== NEWS ======================
else:
    st.title("Engineering & Structural Analysis News")
    for news in get_engineering_news():
        st.markdown(f"""
        <div class="news-card">
            <div class="news-title">{news['title']}</div>
            <div class="news-date">{news['date']}</div>
            <div class="news-summary">{news['summary']}</div>
        </div>
        """, unsafe_allow_html=True)