# pages/structural_analysis.py
import streamlit as st
from main import save_memory, log_event
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
from utils import input_metric, output_metric, unit_label

def ui_number_input(label, min_val, max_val, value, step, key, unit_type):
    """Reusable number input that respects the unit system."""
    display_min = output_metric(min_val, unit_type) if st.session_state.unit_system == "imperial" else min_val
    display_max = output_metric(max_val, unit_type) if st.session_state.unit_system == "imperial" else max_val
    display_value = output_metric(value, unit_type) if st.session_state.unit_system == "imperial" else value
    display_step = output_metric(step, unit_type) if st.session_state.unit_system == "imperial" else step
    user_val = st.number_input(label, min_value=float(display_min), max_value=float(display_max),
                               value=float(display_value), step=float(display_step), key=key)
    return input_metric(user_val, unit_type)

def render_structural_analysis():
    st.title("🏗️ Structural Analysis Workstation")
    st.caption("All inputs and outputs respect the selected unit system.")

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
        # Timber and Composite can be added similarly

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
                building = st.session_state.active_building
                plan = building.plan
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

    # ---- Building Integration ----
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