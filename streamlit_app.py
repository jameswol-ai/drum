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
    # New controls for dashboard enhancements
    st.session_state.show_grid = False
    st.session_state.grid_spacing_mm = 1000
    st.session_state.show_north = False
    st.session_state.click_to_place = False
    st.session_state.click_counter = 0
    st.session_state.show_dimensions = True

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

# ---------- SVG Renderer (with all new features) ----------
def generate_svg_string(plan, width=800, height=500,
                        show_grid=False, grid_spacing_mm=1000,
                        show_north=False, orientation="north",
                        show_dimensions=True):
    """Return an SVG string for the plan, with optional grid/north/dimensions."""
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" id="plan-svg" style="width:100%; background:#0F172A;">'
    
    # ---- Grid lines ----
    if show_grid and grid_spacing_mm > 0:
        x = 0
        while x <= width:
            svg += f'<line x1="{x}" y1="0" x2="{x}" y2="{height}" stroke="#334155" stroke-width="0.5" stroke-dasharray="4,4"/>'
            x += grid_spacing_mm
        y = 0
        while y <= height:
            svg += f'<line x1="0" y1="{y}" x2="{width}" y2="{y}" stroke="#334155" stroke-width="0.5" stroke-dasharray="4,4"/>'
            y += grid_spacing_mm

    # ---- Rooms ----
    for item in plan:
        x, y, w, h = item["x"], item["y"], item["w"], item["h"]
        color = item.get("color", "#4f46e5")
        name = item["name"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        svg += f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{color}" fill-opacity="0.4" stroke="#94a3b8" stroke-width="2"/>'
        svg += f'<text x="{x+w/2}" y="{y+h/2 - 8}" font-size="12" fill="white" text-anchor="middle" dominant-baseline="middle">{name}</text>'
        if show_dimensions:
            dims = f"{w}×{h} mm"
            svg += f'<text x="{x+w/2}" y="{y+h/2 + 12}" font-size="10" fill="#94a3b8" text-anchor="middle" dominant-baseline="middle">{dims}</text>'

    # ---- North arrow ----
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

# ---------- Interactive Plan Component (click‑to‑place) ----------
def interactive_plan_component(svg_string, key_suffix):
    """Renders the SVG and returns coordinates when user clicks on the plan."""
    comp_key = f"plan_{key_suffix}"
    html = f"""
    <html>
    <body style="margin:0; overflow:hidden;">
        {svg_string}
        <script>
        const svg = document.getElementById('plan-svg');
        svg.addEventListener('click', function(e) {{
            const rect = svg.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            const viewBox = svg.viewBox.baseVal;
            const scaleX = viewBox.width / rect.width;
            const scaleY = viewBox.height / rect.height;
            const svgX = Math.round(x * scaleX);
            const svgY = Math.round(y * scaleY);
            window.parent.postMessage({{
                type: "streamlit:setComponentValue",
                value: [svgX, svgY]
            }}, "*");
        }});
        </script>
    </body>
    </html>
    """
    return st.components.v1.html(html, height=500, key=comp_key)

# ---------- Helpers for nudge & coordinate edit ----------
def update_building_plan(building, mem, username):
    """Persist building changes to memory and disk."""
    for i, b in enumerate(mem["buildings"]):
        if b["id"] == building.id:
            mem["buildings"][i] = building.to_dict()
            break
    save_memory(username, mem)

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
        for key in ["logged_in","username","user_data","memory","active_building","show_grid","grid_spacing_mm","show_north","click_to_place","click_counter","show_dimensions"]:
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
                b = Building.from_dict(bdict)
                col_a, col_b = st.columns([3,1])
                with col_a:
                    if st.button(f"📂 {b.name}", key=f"sel_{b.id}"):
                        st.session_state.active_building = b
                        st.rerun()
                with col_b:
                    if st.button("🗑️", key=f"del_{b.id}"):
                        mem["buildings"] = [x for x in mem["buildings"] if x["id"] != b.id]
                        if st.session_state.active_building and st.session_state.active_building.id == b.id:
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

        # ---- Live Area Breakdown ----
        if st.session_state.active_building:
            st.markdown("---")
            st.markdown("### 📏 Room Areas")
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

    with right_col:
        if st.session_state.active_building:
            building = st.session_state.active_building
            plan = building.plan

            # ---- Grid & Orientation Controls ----
            with st.expander("🧭 Grid & Orientation", expanded=False):
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
                        new_sp = st.number_input(label, min_value=0.1, max_value=10.0,
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
                click_place = st.checkbox("Click‑to‑place room", value=st.session_state.click_to_place, key="click_place_cb")
                st.session_state.click_to_place = click_place
                if click_place:
                    st.caption("Click on the plan background to add a new room at that position.")

            # ---- 2D Plan (interactive if click‑to‑place enabled) ----
            st.markdown("#### 📐 2D Floor Plan")
            if plan:
                svg_str = generate_svg_string(
                    plan,
                    show_grid=st.session_state.show_grid,
                    grid_spacing_mm=st.session_state.grid_spacing_mm,
                    show_north=st.session_state.show_north,
                    orientation=st.session_state.eng_params.get("orientation", "north"),
                    show_dimensions=st.session_state.show_dimensions
                )
                if st.session_state.click_to_place:
                    # Use interactive component; returns [x,y] when clicked
                    comp_key = f"{building.id}_{st.session_state.click_counter}"
                    coords = interactive_plan_component(svg_str, comp_key)
                    if coords and isinstance(coords, list) and len(coords) == 2:
                        x, y = coords[0], coords[1]
                        # Add a new room at (x,y) with random size
                        w = random.randint(100, 200) * 5
                        h = random.randint(100, 200) * 5
                        color_hex = f"#{random.randint(0,0xFFFFFF):06x}"
                        plan.append({
                            "x": int(x), "y": int(y), "w": w, "h": h,
                            "name": f"Room {len(plan)+1}",
                            "color": color_hex
                        })
                        building.plan = plan
                        update_building_plan(building, mem, username)
                        log_event(username, mem, f"Added room via click at ({x},{y})")
                        st.session_state.click_counter += 1
                        st.rerun()
                else:
                    # Static SVG
                    st.markdown(f'<div style="background:#0F172A; border-radius:12px; padding:8px; border:1px solid #334155;">{svg_str}</div>', unsafe_allow_html=True)
            else:
                st.info("No plan data.")

            # ---- Plan Editor (extended) ----
            with st.expander("✏️ Edit Plan (Add / Remove / Modify Rooms)", expanded=False):
                col_edit1, col_edit2 = st.columns(2)
                with col_edit1:
                    if st.button("➕ Add Random Room"):
                        w = random.randint(100, 200) * 5
                        h = random.randint(100, 200) * 5
                        x = random.randint(0, 700)
                        y = random.randint(0, 400)
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
                        if st.button("🗑️ Remove Selected"):
                            plan = [r for r in plan if r["name"] != room_to_remove]
                            building.plan = plan
                            update_building_plan(building, mem, username)
                            st.rerun()

                st.write("**Room properties**")
                for i, room in enumerate(plan):
                    with st.container():
                        cols = st.columns([2, 1, 1, 1, 1, 1])
                        # Name
                        cols[0].write(room["name"])
                        # Width
                        new_w = cols[1].number_input("W", 100, 2000, room["w"], key=f"rw_{i}")
                        # Height
                        new_h = cols[2].number_input("H", 100, 2000, room["h"], key=f"rh_{i}")
                        # X
                        new_x = cols[3].number_input("X", 0, 800, room["x"], key=f"rx_{i}")
                        # Y
                        new_y = cols[4].number_input("Y", 0, 500, room["y"], key=f"ry_{i}")
                        # Color
                        new_color = cols[5].color_picker("", value=room.get("color", "#4f46e5"), key=f"rc_{i}")
                        # Check changes
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

                # ---- Nudge selected room ----
                if plan:
                    st.markdown("---")
                    st.markdown("**↕️ Nudge selected room**")
                    room_names = [r["name"] for r in plan]
                    nudge_room = st.selectbox("Select room", room_names, key="nudge_room_sel")
                    nudge_step = st.number_input("Step (mm)", value=100, step=10, key="nudge_step")
                    col_n1, col_n2, col_n3, col_n4 = st.columns(4)
                    idx = next(i for i, r in enumerate(plan) if r["name"] == nudge_room)
                    room = plan[idx]
                    if col_n1.button("⬅️ Left", key="nudge_left"):
                        plan[idx]["x"] = max(0, room["x"] - nudge_step)
                        building.plan = plan
                        update_building_plan(building, mem, username)
                        st.rerun()
                    if col_n2.button("➡️ Right", key="nudge_right"):
                        plan[idx]["x"] = room["x"] + nudge_step
                        building.plan = plan
                        update_building_plan(building, mem, username)
                        st.rerun()
                    if col_n3.button("⬆️ Up", key="nudge_up"):
                        plan[idx]["y"] = max(0, room["y"] - nudge_step)
                        building.plan = plan
                        update_building_plan(building, mem, username)
                        st.rerun()
                    if col_n4.button("⬇️ Down", key="nudge_down"):
                        plan[idx]["y"] = room["y"] + nudge_step
                        building.plan = plan
                        update_building_plan(building, mem, username)
                        st.rerun()

            # ---- 3D Model ----
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

            # ---- Cost & Material Estimate ----
            st.markdown("---")
            with st.expander("💰 Cost & Material Estimate", expanded=False):
                if st.button("Calculate Estimate", key="calc_cost"):
                    cost = estimate_cost(plan)
                    st.table({
                        "Item": ["Concrete", "Steel", "Glass", "Labor", "Total"],
                        "Cost (USD)": [f"${cost['concrete']:,.2f}", f"${cost['steel']:,.2f}",
                                       f"${cost['glass']:,.2f}", f"${cost['labor']:,.2f}",
                                       f"${cost['total']:,.2f}"]
                    })

            # ---- Export & Share ----
            st.markdown("---")
            with st.expander("📤 Export & Share", expanded=False):
                if st.button("📄 Download Plan as SVG"):
                    svg_content = generate_svg_string(plan, show_grid=False, show_north=False, show_dimensions=False)
                    st.download_button("Download SVG", svg_content, file_name=f"{building.name}_plan.svg", mime="image/svg+xml")
                if st.button("📊 Export Summary PDF"):
                    report_data = {"Project": building.name, "Area": f"{output_metric(area, 'area'):.1f} {unit_label('area')}",
                                   "Load": f"{output_metric(load, 'force'):.1f} {unit_label('force')}"}
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

    # ... (keep all structural analysis tabs unchanged)
    # (I’m not repeating them here for brevity – they are identical to your original file)

# ======================
# PAGE: ARCHIVES
# ======================
else:
    st.title("🗄️ Project Archives")
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