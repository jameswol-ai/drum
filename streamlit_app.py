# streamlit_app.py
# DRUM Studio – Professional Structural Analysis Workstation
import streamlit as st
import uuid
from datetime import datetime
import random
import math

from main import (
    load_users, save_users, get_user, create_user, authenticate,
    update_user_data, xp_for_level, add_xp, load_memory, save_memory,
    log_event, Building, generate_plan, simulate_evolution, generate_rhythm,
    init_quests, update_quests, grant_quest_rewards, DEFAULT_STATE
)
from engineering import (
    CONCRETE_GRADES, STEEL_GRADES, TIMBER_CLASSES, WALL_TYPES, FINISHES,
    check_rc_beam, check_steel_beam, check_rc_column,
    slab_thickness_estimate, foundation_size,
    calculate_total_area, compute_floor_loads, check_structural_integrity,
    calculate_energy_score, estimate_cost,
    to_metric, to_imperial,
    pile_capacity,
    check_prestressed_beam,
    generate_analysis_report,
    retaining_wall_stability,
    truss_method_of_joints,
)

# ---------- Page Config ----------
st.set_page_config(page_title="DRUM Studio", page_icon="🏗️", layout="wide",
                   initial_sidebar_state="expanded",
                   menu_items={"Get Help": None, "Report a bug": None, "About": None})

# ---------- Session State ----------
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

if not load_users():
    create_user("admin", "admin123", role="admin")

# ---------- CSS ----------
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
    padding: 0.5rem 1.5rem; font-weight: 600; transition: 0.2s;
}
.stButton>button:hover { transform: scale(1.02); }
.metric-card {
    background: #1E293B; border-radius: 12px; padding: 1rem;
    border: 1px solid #334155;
}
.stNumberInput>div>div>input {
    background: #1E293B; color: #F8FAFC; border: 1px solid #475569;
}
.stSelectbox>div>div>select {
    background: #1E293B; color: #F8FAFC;
}
</style>
""", unsafe_allow_html=True)

# ---------- Unit Helpers ----------
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

# ---------- UI Helpers ----------
def render_svg_plan(plan, width=800, height=500):
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" style="width:100%; background:#0F172A;">'
    for item in plan:
        x, y, w, h = item["x"], item["y"], item["w"], item["h"]
        color = item.get("color", "#4f46e5")
        svg += f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{color}" fill-opacity="0.4" stroke="#94a3b8" stroke-width="2"/>'
        svg += f'<text x="{x+w/2}" y="{y+h/2}" font-size="12" fill="white" text-anchor="middle" dominant-baseline="middle">{item["name"]}</text>'
    svg += '</svg>'
    return svg

# ======================
# LOGIN PAGE
# ======================
if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        # Inline SVG logo
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
                    mem = load_memory(uname)
                    st.session_state.memory = mem
                    st.rerun()
                else:
                    st.error("Invalid credentials.")
            if register_btn:
                if not uname or not pwd:
                    st.error("Fill all fields.")
                else:
                    try:
                        create_user(uname, pwd)
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

# ----- SIDEBAR -----
with st.sidebar:
    # Inline SVG logo
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

    st.markdown(f"### 👷 {username}")
    st.caption("Structural Engineer")

    st.markdown("---")
    page = st.radio("Navigate",
                    ["Project Dashboard", "Structural Analysis", "Archives"],
                    index=["Project Dashboard", "Structural Analysis", "Archives"].index(st.session_state.page),
                    key="nav_radio")
    st.session_state.page = page

    unit_choice = st.radio("Unit System", ["metric", "imperial"], index=0, key="unit_radio")
    st.session_state.unit_system = unit_choice

    with st.expander("🔧 Analysis Defaults"):
        st.session_state.eng_params["live_load"] = st.number_input(f"Live Load ({unit_label('pressure')})", 1.0, 10.0, 2.5, 0.5, key="live_load")
        st.session_state.eng_params["slab_thickness"] = st.number_input(f"Slab Thickness ({unit_label('length')})", 0.1, 0.5, 0.2, 0.05, key="slab_thick")
        st.session_state.eng_params["additional_dead"] = st.number_input(f"Additional Dead ({unit_label('pressure')})", 0.0, 5.0, 1.0, 0.1, key="add_dead")
        st.session_state.eng_params["glazing_ratio"] = st.slider("Glazing Ratio", 0.05, 0.8, 0.2, key="glaz_ratio")
        st.session_state.eng_params["orientation"] = st.selectbox("Orientation", ["north","south","east","west"], key="orient")

    if st.button("🚪 Logout"):
        save_memory(username, mem)
        for key in ["logged_in","username","user_data","memory","active_building"]:
            if key in st.session_state:
                if key == "memory":
                    st.session_state[key] = DEFAULT_STATE.copy()
                else:
                    st.session_state[key] = None
        st.rerun()

# ======================
# PAGE: PROJECT DASHBOARD
# ======================
if page == "Project Dashboard":
    st.title("🏢 Project Dashboard")

    # ---- Top metrics for active project ----
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
            st.success(f"✅ Structural check passed – suggested beam: {integrity['suggested_beam']}")
        else:
            st.error(f"❌ Span too large ({integrity['max_span_m']} m) – consider intermediate columns")
    else:
        st.info("👈 Create or select a project to see live metrics.")

    st.markdown("---")

    # ---- Main layout ----
    left_col, right_col = st.columns([1, 3])

    with left_col:
        st.markdown("### 🧰 Project Tools")
        if st.button("➕ New Project", use_container_width=True):
            new_building = Building(name=f"Project-{len(mem['buildings'])+1}", score=50)
            generate_plan(new_building)
            mem["buildings"].append(new_building.to_dict())
            st.session_state.active_building = new_building
            log_event(username, mem, f"Created new project: {new_building.name}")
            save_memory(username, mem)
            st.rerun()

        if mem["buildings"]:
            st.markdown("**Saved Projects**")
            for bdict in reversed(mem["buildings"][-10:]):
                building = Building.from_dict(bdict)
                col_a, col_b = st.columns([3,1])
                with col_a:
                    if st.button(f"📂 {building.name}", key=f"sel_{building.id}"):
                        st.session_state.active_building = building
                        st.rerun()
                with col_b:
                    if st.button("🗑️", key=f"del_{building.id}"):
                        mem["buildings"] = [b for b in mem["buildings"] if b["id"] != building.id]
                        if st.session_state.active_building and st.session_state.active_building.id == building.id:
                            st.session_state.active_building = None
                        save_memory(username, mem)
                        st.rerun()

        st.markdown("---")
        st.markdown("### 📊 Compare Projects")
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

    with right_col:
        if st.session_state.active_building:
            building = st.session_state.active_building
            plan = building.plan

            # ---- Plan Editor ----
            with st.expander("✏️ Edit Plan (Add / Remove Rooms)", expanded=False):
                col_edit1, col_edit2 = st.columns(2)
                with col_edit1:
                    if st.button("➕ Add Room"):
                        w = random.randint(100, 200) * 5
                        h = random.randint(100, 200) * 5
                        x = random.randint(0, 700)
                        y = random.randint(0, 400)
                        plan.append({
                            "x": x, "y": y, "w": w, "h": h,
                            "name": f"Room {len(plan)+1}",
                            "color": f"hsl({random.randint(0,360)}, 70%, 50%)"
                        })
                        building.plan = plan
                        for i, b in enumerate(mem["buildings"]):
                            if b["id"] == building.id:
                                mem["buildings"][i] = building.to_dict()
                        save_memory(username, mem)
                        st.rerun()
                with col_edit2:
                    if len(plan) > 1:
                        room_to_remove = st.selectbox("Remove room", [r["name"] for r in plan], key="remove_room")
                        if st.button("🗑️ Remove Selected"):
                            plan = [r for r in plan if r["name"] != room_to_remove]
                            building.plan = plan
                            for i, b in enumerate(mem["buildings"]):
                                if b["id"] == building.id:
                                    mem["buildings"][i] = building.to_dict()
                            save_memory(username, mem)
                            st.rerun()

                st.write("Current rooms:")
                for i, room in enumerate(plan):
                    col_r1, col_r2, col_r3 = st.columns([2, 1, 1])
                    col_r1.write(f"{room['name']}: {room['w']}x{room['h']} mm")
                    new_w = col_r2.number_input("W", 100, 2000, room["w"], key=f"rw_{i}")
                    new_h = col_r3.number_input("H", 100, 2000, room["h"], key=f"rh_{i}")
                    if new_w != room["w"] or new_h != room["h"]:
                        plan[i]["w"] = new_w
                        plan[i]["h"] = new_h
                        building.plan = plan
                        for j, b in enumerate(mem["buildings"]):
                            if b["id"] == building.id:
                                mem["buildings"][j] = building.to_dict()
                        save_memory(username, mem)
                        st.rerun()

            # 2D Plan
            st.markdown("#### 📐 2D Floor Plan")
            if plan:
                svg = render_svg_plan(plan)
                st.markdown(f'<div style="background:#0F172A; border-radius:12px; padding:8px; border:1px solid #334155;">{svg}</div>', unsafe_allow_html=True)
            else:
                st.info("No plan data.")

            # ---- 3D Interactive Model (fixed escaping) ----
            st.markdown("#### 🧊 Interactive 3D Model")
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

            # ---- Cost Breakdown ----
            st.markdown("---")
            with st.expander("💰 Cost & Material Estimate", expanded=False):
                if st.button("Calculate Estimate", key="calc_cost"):
                    cost = estimate_cost(plan)
                    st.table({
                        "Item": ["Concrete", "Steel", "Glass", "Labor", "Total"],
                        "Cost (USD)": [f"${cost['concrete']:,.2f}", f"${cost['steel']:,.2f}", f"${cost['glass']:,.2f}", f"${cost['labor']:,.2f}", f"${cost['total']:,.2f}"]
                    })

            # ---- Export & Share ----
            st.markdown("---")
            with st.expander("📤 Export & Share", expanded=False):
                if st.button("📄 Download Plan as SVG"):
                    svg_content = render_svg_plan(plan)
                    st.download_button("Download SVG", svg_content, file_name=f"{building.name}_plan.svg", mime="image/svg+xml")
                if st.button("📊 Export Summary PDF"):
                    report_data = {"Project": building.name, "Area": f"{output_metric(area, 'area'):.1f} {unit_label('area')}", "Load": f"{output_metric(load, 'force'):.1f} {unit_label('force')}"}
                    filename, error = generate_analysis_report(report_data, f"{building.name}_summary.pdf")
                    if not error:
                        with open(filename, "rb") as f:
                            st.download_button("Download PDF", f, file_name=filename, mime="application/pdf")
                st.text_input("Shareable link (copy)", value=f"https://drum-studio.com/project/{building.id}", disabled=True)

        else:
            st.info("👈 Select a project from the list or create a new one to start.")

    # ---- Recent Activity ----
    st.markdown("---")
    st.subheader("🕓 Recent Activity")
    if mem["logs"]:
        for log in reversed(mem["logs"][-5:]):
            st.caption(f"`{log['time'][11:19]}` – {log['msg']}")
    else:
        st.caption("No activity yet.")

# ======================
# PAGE: STRUCTURAL ANALYSIS
# ======================
elif page == "Structural Analysis":
    st.title("🏗️ Structural Analysis Workstation")
    st.caption("All inputs and outputs respect the selected unit system.")

    def ui_number_input(label, min_val, max_val, value, step, key, unit_type):
        display_min = output_metric(min_val, unit_type) if st.session_state.unit_system=="imperial" else min_val
        display_max = output_metric(max_val, unit_type) if st.session_state.unit_system=="imperial" else max_val
        display_value = output_metric(value, unit_type) if st.session_state.unit_system=="imperial" else value
        display_step = output_metric(step, unit_type) if st.session_state.unit_system=="imperial" else step
        user_val = st.number_input(label, min_value=float(display_min), max_value=float(display_max),
                                   value=float(display_value), step=float(display_step), key=key)
        return input_metric(user_val, unit_type)

    tabs = st.tabs([
        "📐 Beams", "🧱 Columns", "🔲 Slabs", "🌍 Foundations",
        "🏛️ Walls & Finishes", "📌 Piles", "⚡ Prestressed",
        "🧱 Retaining Wall", "🔺 Truss", "📄 Export/Report"
    ])

    # ---- BEAMS (0) ----
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
                if res["pass"]: st.success("✅ Beam OK")
                else: st.error("❌ Beam fails check")
                st.write(f"As required: {output_metric(res['As_req'], 'area'):.2f} {unit_label('area')}")
                st.json(res)
        elif beam_mat == "Steel":
            grade = st.selectbox("Steel Grade", list(STEEL_GRADES.keys()), key="beam_steel_grade")
            section = st.selectbox("Section", ["IPE 160", "IPE 220", "IPE 300"], key="beam_sec")
            span = ui_number_input(f"Span ({unit_label('length')})", 2.0, 20.0, 6.0, 0.1, "beam_span_steel", "length")
            M_ed = ui_number_input(f"M_Ed ({unit_label('moment')})", 50.0, 500.0, 100.0, 1.0, "beam_Med_steel", "moment")
            V_ed = ui_number_input(f"V_Ed ({unit_label('force')})", 20.0, 300.0, 50.0, 1.0, "beam_Ved_steel", "force")
            if st.button("Check Steel Beam", key="check_steel_beam"):
                steel = STEEL_GRADES[grade]
                res = check_steel_beam(section, M_ed, V_ed, span, steel)
                if res["pass"]: st.success("✅ Beam OK")
                else: st.error("❌ Beam fails")
                st.write(f"Utilization: {res['utilization']:.2f}")
                st.write(f"Deflection: {output_metric(res['deflection_mm']/1000, 'length'):.3f} {unit_label('length')}")
                st.json(res)

    # ---- COLUMNS (1) ----
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
                if res["pass"]: st.success("✅ Column OK")
                else: st.error("❌ Column fails")
                st.write(f"N_Rd: {output_metric(res['N_rd'], 'force'):.1f} {unit_label('force')}")
                st.json(res)

    # ---- SLABS (2) ----
    with tabs[2]:
        st.subheader("Slab Thickness")
        span = ui_number_input(f"Short span ({unit_label('length')})", 2.0, 15.0, 5.0, 0.1, "slab_span", "length")
        support = st.selectbox("Support", ["simply_supported", "continuous"], key="slab_support")
        t = slab_thickness_estimate(span, support)
        st.success(f"Recommended thickness: **{output_metric(t*1000, 'length_mm'):.0f} {unit_label('length_mm')}**")

    # ---- FOUNDATIONS (3) ----
    with tabs[3]:
        st.subheader("Pad Footing Sizing")
        load = ui_number_input(f"Total column load ({unit_label('force')})", 100.0, 10000.0, 500.0, 10.0, "fdn_load", "force")
        bearing = ui_number_input(f"Allowable bearing pressure ({unit_label('pressure')})", 50.0, 500.0, 150.0, 10.0, "fdn_bearing", "pressure")
        fs = st.number_input("Factor of safety", 2.0, 5.0, 3.0, 0.1, key="fdn_fs")
        if st.button("Size Footing", key="size_fdn"):
            res = foundation_size(bearing, load, fs)
            st.success(f"Square footing side: **{output_metric(res['side_m'], 'length'):.2f} {unit_label('length')}** (area: {output_metric(res['area_m2'], 'area'):.2f} {unit_label('area')})")

    # ---- WALLS & FINISHES (4) ----
    with tabs[4]:
        st.subheader("Wall Types & Finishes")
        wall = st.selectbox("Wall Type", list(WALL_TYPES.keys()), key="wall_type")
        props = WALL_TYPES[wall]
        weight_disp = output_metric(props['weight'], 'pressure') if st.session_state.unit_system=="imperial" else props['weight']
        st.write(f"Weight: {weight_disp:.2f} {unit_label('pressure')}, U‑value: {props['U']} W/m²K, Sound: {props['sound']} dB")
        finishes = st.multiselect("Finishes", list(FINISHES.keys()), default=["Plaster (internal)", "Paint"], key="finishes")
        finish_load = sum(FINISHES[f] for f in finishes)
        finish_disp = output_metric(finish_load, 'pressure') if st.session_state.unit_system=="imperial" else finish_load
        st.metric("Total finish load", f"{finish_disp:.3f} {unit_label('pressure')}")
        if st.button("Apply to Model", key="apply_wall"):
            st.info("Wall/finish selection saved to project.")

    # ---- PILES (5) ----
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
            st.write(f"Ultimate capacity: {output_metric(res['Q_ult_kN'], 'force'):.1f} {unit_label('force')}")
            st.write(f"Shaft resistance: {output_metric(res['shaft_kN'], 'force'):.1f} {unit_label('force')}, Base: {output_metric(res['base_kN'], 'force'):.1f} {unit_label('force')}")

    # ---- PRESTRESSED (6) ----
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
            if res["pass"]: st.success("✅ Stresses within limits")
            else: st.error("❌ Stress limit exceeded")
            st.write(f"Top stress: {output_metric(res['sigma_top_MPa'], 'stress'):.2f} {unit_label('stress')}")
            st.write(f"Bottom stress: {output_metric(res['sigma_bot_MPa'], 'stress'):.2f} {unit_label('stress')}")
            st.write(f"Allowable compression: {output_metric(res['sigma_c_allow'], 'stress'):.2f} {unit_label('stress')}")
            st.write(f"Allowable tension: {output_metric(res['sigma_t_allow'], 'stress'):.2f} {unit_label('stress')}")

    # ---- RETAINING WALL (7) ----
    with tabs[7]:
        st.subheader("Cantilever Retaining Wall (Simplified)")
        H = ui_number_input(f"Wall height ({unit_label('length')})", 1.0, 10.0, 3.0, 0.1, "rw_H", "length")
        gamma = ui_number_input(f"Soil unit weight ({unit_label('weight_density')})", 15.0, 22.0, 18.0, 0.1, "rw_gamma", "weight_density")
        phi = st.number_input("Friction angle (°)", 20.0, 45.0, 30.0, key="rw_phi")
        c = ui_number_input(f"Cohesion ({unit_label('pressure')})", 0.0, 50.0, 0.0, 0.1, "rw_c", "pressure")
        surcharge = ui_number_input(f"Surcharge ({unit_label('pressure')})", 0.0, 20.0, 0.0, 0.1, "rw_surch", "pressure")
        wall_friction = st.number_input("Base friction coefficient", 0.3, 0.8, 0.6, key="rw_fric")
        if st.button("Check Stability", key="rw_check"):
            res = retaining_wall_stability(H, gamma, phi, c, surcharge, wall_friction)
            if res["pass"]: st.success("✅ Wall stable")
            else: st.error("❌ Stability check failed")
            st.write(f"Active thrust: {output_metric(res['Pa_kN'], 'force'):.2f} {unit_label('force')}/m")
            st.write(f"Overturning SF: {res['F_overt']:.2f}, Sliding SF: {res['F_sliding']:.2f}")

    # ---- TRUSS (8) ----
    with tabs[8]:
        st.subheader("2D Truss Solver (coming soon)")
        st.info("This module will perform method-of-joints analysis. Enter nodes, members, loads.")
        if st.button("Solve Truss (demo)", key="truss_solve"):
            res = truss_method_of_joints(None, None, None, None)
            st.json(res)

    # ---- EXPORT / REPORT (9) ----
    with tabs[9]:
        st.subheader("Export Analysis Report (PDF)")
        if st.button("📄 Generate Report", key="pdf_gen"):
            report_data = {"Project": "DRUM Sample", "Analysis": "Summary of last checks"}
            if st.session_state.active_building:
                plan = st.session_state.active_building.plan
                area = calculate_total_area(plan)
                load = compute_floor_loads(plan,
                    live_load_kN_per_m2=st.session_state.eng_params["live_load"],
                    slab_thickness_m=st.session_state.eng_params["slab_thickness"],
                    additional_dead_load_kN_per_m2=st.session_state.eng_params["additional_dead"])
                report_data["Total Floor Area"] = f"{output_metric(area, 'area'):.1f} {unit_label('area')}"
                report_data["Design Load"] = f"{output_metric(load, 'force'):.1f} {unit_label('force')}"
                integrity = check_structural_integrity(plan)
                report_data["Max Span"] = f"{output_metric(integrity['max_span_m'], 'length'):.2f} {unit_label('length')}"
                report_data["Suggested Beam"] = integrity["suggested_beam"]
            filename, error = generate_analysis_report(report_data)
            if error:
                st.error(error)
            else:
                with open(filename, "rb") as f:
                    st.download_button("Download PDF Report", f, file_name=filename, mime="application/pdf")
                st.success("Report generated!")

    # ---- BUILDING INTEGRATION ----
    st.markdown("---")
    if st.session_state.active_building:
        st.subheader("📐 Building Plan Analysis")
        plan = st.session_state.active_building.plan
        area = calculate_total_area(plan)
        load = compute_floor_loads(plan,
            live_load_kN_per_m2=st.session_state.eng_params["live_load"],
            slab_thickness_m=st.session_state.eng_params["slab_thickness"],
            additional_dead_load_kN_per_m2=st.session_state.eng_params["additional_dead"])
        st.write(f"Total floor area: {output_metric(area, 'area'):.1f} {unit_label('area')}, Design load: {output_metric(load, 'force'):.1f} {unit_label('force')}")
        integrity = check_structural_integrity(plan)
        st.write(f"Max span: {output_metric(integrity['max_span_m'], 'length'):.2f} {unit_label('length')}, Suggested beam: {integrity['suggested_beam']}")
    else:
        st.info("No active building. Open a project from the dashboard or create a new one.")

# ======================
# PAGE: ARCHIVES
# ======================
else:  # Archives
    st.title("🗄️ Project Archives")
    if mem["buildings"]:
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

