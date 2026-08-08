# pages/project_dashboard.py
import streamlit as st
import random
import uuid
from main import Building, generate_plan, save_memory, log_event
from engineering import calculate_total_area, compute_floor_loads, check_structural_integrity, estimate_cost, generate_analysis_report
from utils import render_svg_plan_with_grid, generate_3d_html, output_metric, unit_label

def render_project_dashboard():
    st.title("🏢 Project Dashboard")
    mem = st.session_state.memory
    building = st.session_state.active_building

    # ---- Top metrics for active project ----
    if building:
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
            log_event(st.session_state.username, mem, f"Created new project: {new_building.name}")
            save_memory(st.session_state.username, mem)
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
                        save_memory(st.session_state.username, mem)
                        st.rerun()

        st.markdown("---")
        st.markdown("### 📊 Compare Projects")
        if len(mem["buildings"]) >= 2:
            names = [b["name"] for b in mem["buildings"]]
            compare_a = st.selectbox("Project A", names, key="comp_a")
            compare_b = st.selectbox("Project B", names, key="comp_b")
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
        if building:
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
                        save_memory(st.session_state.username, mem)
                        st.rerun()
                with col_edit2:
                    if len(plan) > 1:
                        room_names = [r["name"] for r in plan]
                        room_to_remove = st.selectbox("Remove room", room_names, key="remove_room")
                        if st.button("🗑️ Remove Selected"):
                            plan = [r for r in plan if r["name"] != room_to_remove]
                            building.plan = plan
                            for i, b in enumerate(mem["buildings"]):
                                if b["id"] == building.id:
                                    mem["buildings"][i] = building.to_dict()
                            save_memory(st.session_state.username, mem)
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
                        save_memory(st.session_state.username, mem)
                        st.rerun()

            # 2D Plan
            # 2D Plan with Grid & Orientation Controls
st.markdown("#### 📐 2D Floor Plan")

# --- Grid & Orientation Controls ---
with st.expander("🧭 Grid & Orientation", expanded=False):
    col_grid1, col_grid2 = st.columns(2)
    with col_grid1:
        show_grid = st.checkbox("Show Grid", value=False, key="show_grid")
        if show_grid:
            # Grid spacing input in user's unit system
            # Convert from displayed unit to mm internally
            if st.session_state.unit_system == "metric":
                grid_label = "Grid spacing (m)"
                step = 0.1
                display_spacing = grid_spacing_mm / 1000.0   # m
            else:
                grid_label = "Grid spacing (ft)"
                step = 1.0
                display_spacing = grid_spacing_mm / 304.8    # ft
            new_spacing = st.number_input(grid_label, min_value=0.1, max_value=10.0,
                                          value=float(display_spacing), step=step, key="grid_space")
            # Convert back to mm
            if st.session_state.unit_system == "metric":
                grid_spacing_mm = new_spacing * 1000
            else:
                grid_spacing_mm = new_spacing * 304.8
            st.session_state.grid_spacing_mm = grid_spacing_mm
    with col_grid2:
        show_north = st.checkbox("Show North Arrow", value=False, key="show_north")

if plan:
    # Use the new grid-aware SVG renderer
    svg = render_svg_plan_with_grid(
        plan,
        show_grid=show_grid,
        grid_spacing_mm=st.session_state.get("grid_spacing_mm", 1000),
        show_north=show_north,
        orientation=st.session_state.eng_params.get("orientation", "north")
    )
    st.markdown(f'<div style="background:#0F172A; border-radius:12px; padding:8px; border:1px solid #334155;">{svg}</div>', unsafe_allow_html=True)
else:
    st.info("No plan data.")

# --- Room Nudge (move selected room with buttons) ---
if plan:
    with st.expander("↕️ Nudge Room Position", expanded=False):
        room_names = [r["name"] for r in plan]
        selected_room = st.selectbox("Select room to nudge", room_names, key="nudge_room")
        if selected_room:
            # Find the room index
            room_idx = next(i for i, r in enumerate(plan) if r["name"] == selected_room)
            room = plan[room_idx]
            nudge_step = st.number_input("Nudge step (mm)", value=100, step=10, key="nudge_step")

            col_n1, col_n2, col_n3, col_n4 = st.columns(4)
            with col_n1:
                if st.button("⬅️ Left", key="nudge_left"):
                    plan[room_idx]["x"] = max(0, room["x"] - nudge_step)
                    # save changes back
                    building.plan = plan
                    for i, b in enumerate(mem["buildings"]):
                        if b["id"] == building.id:
                            mem["buildings"][i] = building.to_dict()
                    save_memory(st.session_state.username, mem)
                    st.rerun()
            with col_n2:
                if st.button("➡️ Right", key="nudge_right"):
                    plan[room_idx]["x"] = room["x"] + nudge_step
                    building.plan = plan
                    for i, b in enumerate(mem["buildings"]):
                        if b["id"] == building.id:
                            mem["buildings"][i] = building.to_dict()
                    save_memory(st.session_state.username, mem)
                    st.rerun()
            with col_n3:
                if st.button("⬆️ Up", key="nudge_up"):
                    plan[room_idx]["y"] = max(0, room["y"] - nudge_step)
                    building.plan = plan
                    for i, b in enumerate(mem["buildings"]):
                        if b["id"] == building.id:
                            mem["buildings"][i] = building.to_dict()
                    save_memory(st.session_state.username, mem)
                    st.rerun()
            with col_n4:
                if st.button("⬇️ Down", key="nudge_down"):
                    plan[room_idx]["y"] = room["y"] + nudge_step
                    building.plan = plan
                    for i, b in enumerate(mem["buildings"]):
                        if b["id"] == building.id:
                            mem["buildings"][i] = building.to_dict()
                    save_memory(st.session_state.username, mem)
                    st.rerun()
            st.caption(f"Current position: x={room['x']} mm, y={room['y']} mm") style="background:#0F172A; border-radius:12px; padding:8px; border:1px solid #334155;">{svg}</div>', unsafe_allow_html=True)
            else:
                st.info("No plan data.")

            # 3D Model
            st.markdown("#### 🧊 Interactive 3D Model")
            if plan:
                three_html = generate_3d_html(plan)
                st.components.v1.html(three_html, height=500, scrolling=False)
            else:
                st.info("3D view requires a building plan.")

            # Cost Breakdown
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

            # Export & Share
            st.markdown("---")
            with st.expander("📤 Export & Share", expanded=False):
                if st.button("📄 Download Plan as SVG"):
                    svg_content = render_svg_plan(plan)
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

    # Recent Activity
    st.markdown("---")
    st.subheader("🕓 Recent Activity")
    if mem.get("logs"):
        for log in reversed(mem["logs"][-5:]):
            st.caption(f"`{log['time'][11:19]}` – {log['msg']}")
    else:
        st.caption("No activity yet.")