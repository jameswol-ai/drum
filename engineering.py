# engineering.py
# Structural engineering calculations for DRUM Studio
import math
import json
import numpy as np  # for truss solver
from datetime import datetime
import os

# ======================
# MATERIAL DATABASES
# ======================
CONCRETE_GRADES = {
    "C20/25": {"fck": 20.0, "fcm": 28.0, "Ecm": 30e3},
    "C25/30": {"fck": 25.0, "fcm": 33.0, "Ecm": 31e3},
    "C30/37": {"fck": 30.0, "fcm": 38.0, "Ecm": 33e3},
    "C35/45": {"fck": 35.0, "fcm": 43.0, "Ecm": 34e3},
    "C40/50": {"fck": 40.0, "fcm": 48.0, "Ecm": 35e3},
}

STEEL_GRADES = {
    "S235": {"fy": 235.0, "fu": 360.0, "E": 210e3},
    "S275": {"fy": 275.0, "fu": 430.0, "E": 210e3},
    "S355": {"fy": 355.0, "fu": 510.0, "E": 210e3},
    "S450": {"fy": 440.0, "fu": 550.0, "E": 210e3},
}

TIMBER_CLASSES = {
    "C14": {"fm_k": 14.0, "fv_k": 2.0, "E0_mean": 7e3},
    "C16": {"fm_k": 16.0, "fv_k": 2.0, "E0_mean": 8e3},
    "C24": {"fm_k": 24.0, "fv_k": 2.5, "E0_mean": 11e3},
    "GL24h": {"fm_k": 24.0, "fv_k": 2.7, "E0_mean": 11.5e3},
}

WALL_TYPES = {
    "Brick cavity": {"weight": 2.5, "U": 1.4, "sound": 45},
    "Concrete block": {"weight": 3.5, "U": 1.8, "sound": 50},
    "Timber frame": {"weight": 1.5, "U": 0.35, "sound": 40},
    "Insulated panel": {"weight": 0.8, "U": 0.25, "sound": 35},
}

FINISHES = {
    "Plaster (internal)": 0.3,
    "Paint": 0.05,
    "Ceramic tiles": 0.4,
    "Carpet": 0.1,
    "Screed": 0.5,
}

# ======================
# UNIT CONVERSION HELPERS
# ======================
def to_metric(value, unit_type):
    """Convert from imperial to metric if needed (not used directly, kept for compatibility)."""
    # The main conversion is handled in streamlit_app.py, but we keep a placeholder
    return value

def to_imperial(value, unit_type):
    """Convert from metric to imperial if needed."""
    return value

# ======================
# STRUCTURAL CALCULATIONS
# ======================
def check_rc_beam(b_mm, h_mm, d_mm, fck_mpa, M_ed_kNm, V_ed_kN, span_m):
    """
    Simplified RC beam design check (EC2).
    b_mm: width (mm)
    h_mm: total depth (mm)
    d_mm: effective depth (mm)
    fck_mpa: characteristic cylinder strength (MPa)
    M_ed_kNm: design moment (kNm)
    V_ed_kN: design shear (kN)
    span_m: span (m)
    Returns dict with pass/fail and required steel area.
    """
    fck = fck_mpa
    fcd = fck / 1.5
    fyd = 500 / 1.15  # assuming B500 steel
    # Calculate lever arm
    z = min(0.95 * d_mm, d_mm - 50)
    # Required steel area (simplified)
    M_ed_Nmm = M_ed_kNm * 1e6
    As_req = M_ed_Nmm / (fyd * z)
    As_min = 0.26 * (2.2 / fck) * b_mm * d_mm if fck > 0 else 0
    As_req = max(As_req, As_min)
    # Shear check (simplified)
    v_ed = V_ed_kN * 1000 / (b_mm * d_mm)  # N/mm²
    v_rdc = 0.12 * (1 + math.sqrt(200 / d_mm)) * (100 * 0.01 * fck) ** (1/3) if d_mm > 0 else 0
    pass_shear = v_ed <= v_rdc
    # Deflection check (simplified)
    deflection_limit = span_m * 1000 / 250
    # Assume simply supported with udl: δ = 5wL^4/(384EI)
    # We ignore exact deflection for simplicity but assume OK if span/depth ratio reasonable
    span_depth_ratio = span_m * 1000 / d_mm
    pass_deflection = span_depth_ratio < 20

    return {
        "pass": pass_shear and pass_deflection,
        "As_req": As_req,
        "shear_stress": v_ed,
        "shear_capacity": v_rdc,
        "span_depth_ratio": span_depth_ratio,
    }

def check_steel_beam(section, M_ed_kNm, V_ed_kN, span_m, steel_grade_dict):
    """
    Simplified steel beam check.
    section: str e.g. "IPE 160", "IPE 220", "IPE 300"
    Returns dict with utilization and deflection.
    """
    # Simplified section properties (I in mm^4, Wpl in mm^3)
    sections = {
        "IPE 160": {"I": 8.69e6, "Wpl": 1.09e5, "A": 2010},
        "IPE 220": {"I": 2.77e7, "Wpl": 2.52e5, "A": 3340},
        "IPE 300": {"I": 8.36e7, "Wpl": 6.28e5, "A": 5380},
    }
    if section not in sections:
        return {"pass": False, "error": "Unknown section"}
    props = sections[section]
    fy = steel_grade_dict["fy"]
    E = steel_grade_dict["E"]
    # Moment resistance
    M_pl_Rd = props["Wpl"] * fy / 1.0 / 1e6  # kNm
    utilization_m = M_ed_kNm / M_pl_Rd
    # Shear resistance (simplified)
    Av = props["A"] * 0.6
    V_pl_Rd = Av * fy / (math.sqrt(3) * 1.0) / 1000  # kN
    utilization_v = V_ed_kN / V_pl_Rd
    # Deflection (simplified, assume udl)
    w = 8 * M_ed_kNm / (span_m ** 2)  # equivalent udl in kN/m
    delta = 5 * w * (span_m*1000)**4 / (384 * E * props["I"])  # mm
    pass_deflection = delta < (span_m*1000)/250
    pass_overall = utilization_m <= 1.0 and utilization_v <= 1.0 and pass_deflection
    return {
        "pass": pass_overall,
        "utilization": max(utilization_m, utilization_v),
        "moment_utilization": utilization_m,
        "shear_utilization": utilization_v,
        "deflection_mm": delta,
        "deflection_limit": span_m*1000/250,
    }

def check_rc_column(N_ed_kN, M_ed_kNm, b_mm, h_mm, fck_mpa, l0_m):
    """
    Simplified RC column check (axial + moment using interaction approximation).
    """
    fck = fck_mpa
    fcd = fck / 1.5
    fyd = 500 / 1.15
    Ac = b_mm * h_mm
    # Assume 1% reinforcement
    As = 0.01 * Ac
    # Pure axial capacity (simplified)
    N_rd = 0.567 * fcd * Ac + 0.87 * fyd * As  # N
    N_rd_kN = N_rd / 1000
    # Moment capacity (simplified as 0.1*fcd*b*d^2)
    d = h_mm - 50
    M_rd = 0.167 * fcd * b_mm * d**2 / 1e6  # kNm
    # Check slenderness
    i = h_mm / math.sqrt(12)
    lambda_ = l0_m * 1000 / i
    lambda_limit = 20
    pass_slender = lambda_ <= lambda_limit
    # Interaction check (simplified linear)
    if N_ed_kN > N_rd_kN or M_ed_kNm > M_rd:
        pass_interaction = False
    else:
        # Basic check
        pass_interaction = (N_ed_kN/N_rd_kN + M_ed_kNm/M_rd) <= 1.0
    return {
        "pass": pass_interaction and pass_slender,
        "N_rd": N_rd_kN,
        "M_rd": M_rd,
        "lambda": lambda_,
    }

def slab_thickness_estimate(span_m, support_type):
    """Return recommended slab thickness in meters."""
    if support_type == "simply_supported":
        return span_m / 20
    else:  # continuous
        return span_m / 28

def foundation_size(allowable_bearing_kpa, load_kN, factor_of_safety=3.0):
    """
    Simplified pad footing sizing.
    Returns dict with side length in m and area in m².
    """
    q_all = allowable_bearing_kpa * factor_of_safety  # ultimate bearing pressure? simplified
    area_req = load_kN / q_all
    side = math.sqrt(area_req)
    return {"side_m": side, "area_m2": area_req}

def calculate_total_area(plan):
    """Calculate total floor area from plan (list of rooms with x,y,w,h in mm)."""
    total = 0
    for room in plan:
        total += room["w"] * room["h"] / 1e6  # convert mm² to m²
    return total

def compute_floor_loads(plan, live_load_kN_per_m2, slab_thickness_m, additional_dead_load_kN_per_m2):
    """Calculate total design load on floor (simplified)."""
    area = calculate_total_area(plan)
    concrete_density = 25  # kN/m³
    dead = slab_thickness_m * concrete_density + additional_dead_load_kN_per_m2
    total_load = (dead + live_load_kN_per_m2) * area
    return total_load

def check_structural_integrity(plan):
    """
    Check overall building plan for maximum span and suggest beam type.
    Returns dict with pass bool and max_span_m.
    """
    # Find max room dimension
    max_span_mm = 0
    for room in plan:
        span = max(room["w"], room["h"])
        if span > max_span_mm:
            max_span_mm = span
    max_span_m = max_span_mm / 1000
    # Suggested beam based on span
    if max_span_m <= 4:
        beam = "IPE 160"
    elif max_span_m <= 6:
        beam = "IPE 220"
    elif max_span_m <= 8:
        beam = "IPE 300"
    else:
        beam = "RC beam or truss"
    pass_flag = max_span_m <= 8
    return {"pass": pass_flag, "max_span_m": max_span_m, "suggested_beam": beam}

def calculate_energy_score(plan, glazing_ratio=0.2, orientation="south"):
    """Very simplified energy score (0-100)."""
    # Based on area and glazing
    area = calculate_total_area(plan)
    score = max(0, 100 - area*0.5 - glazing_ratio*50)
    return score

def estimate_cost(plan):
    """
    Estimate construction cost based on area and materials.
    Returns dict with costs in USD.
    """
    area = calculate_total_area(plan)
    # Rough rates per m²
    concrete_rate = 150
    steel_rate = 80
    glass_rate = 120
    labor_rate = 100
    concrete_cost = area * concrete_rate
    steel_cost = area * steel_rate
    glass_cost = area * glass_rate * 0.2  # assume 20% glazing
    labor_cost = area * labor_rate
    total = concrete_cost + steel_cost + glass_cost + labor_cost
    return {
        "concrete": concrete_cost,
        "steel": steel_cost,
        "glass": glass_cost,
        "labor": labor_cost,
        "total": total,
    }

def pile_capacity(diameter_m, length_m, soil_type, N_value, factor_of_safety=2.5):
    """
    Simplified pile capacity (bored/driven) based on SPT N.
    Returns dict with capacities in kN.
    """
    # Simplified empirical formulas
    if soil_type == "sand":
        # Ultimate shaft friction: 2*N kPa, base: 40*N kPa
        shaft_stress = 2 * N_value  # kPa
        base_stress = 40 * N_value  # kPa
    else:  # clay
        shaft_stress = 5 * N_value
        base_stress = 9 * N_value
    perimeter = math.pi * diameter_m
    shaft_area = perimeter * length_m
    base_area = math.pi * (diameter_m/2)**2
    shaft_capacity = shaft_stress * shaft_area  # kN
    base_capacity = base_stress * base_area  # kN
    Q_ult = shaft_capacity + base_capacity
    Q_all = Q_ult / factor_of_safety
    return {
        "Q_ult_kN": Q_ult,
        "Q_all_kN": Q_all,
        "shaft_kN": shaft_capacity,
        "base_kN": base_capacity,
    }

def check_prestressed_beam(M_ext_kNm, P_kN, e_m, A_m2, I_m4, y_top_m, y_bot_m, fck_mpa):
    """
    Check prestressed concrete beam stresses.
    Returns dict with stress values and pass/fail.
    """
    # Convert to N and mm
    P = P_kN * 1000
    M_ext = M_ext_kNm * 1e6  # Nmm
    # Stress due to prestress
    sigma_p_top = P/A_m2*1e-6 - P*e_m*y_top_m/(I_m4*1e12)  # MPa
    sigma_p_bot = P/A_m2*1e-6 + P*e_m*y_bot_m/(I_m4*1e12)
    # Stress due to external moment (assuming sagging positive)
    sigma_m_top = -M_ext*y_top_m/(I_m4*1e12)  # MPa
    sigma_m_bot = M_ext*y_bot_m/(I_m4*1e12)
    # Total stresses
    sigma_top = sigma_p_top + sigma_m_top
    sigma_bot = sigma_p_bot + sigma_m_bot
    # Allowable stresses
    sigma_c_allow = 0.6 * fck_mpa
    sigma_t_allow = -0.5 * math.sqrt(fck_mpa) if fck_mpa > 0 else 0
    pass_top = sigma_top <= sigma_c_allow and sigma_top >= sigma_t_allow
    pass_bot = sigma_bot <= sigma_c_allow and sigma_bot >= sigma_t_allow
    return {
        "pass": pass_top and pass_bot,
        "sigma_top_MPa": sigma_top,
        "sigma_bot_MPa": sigma_bot,
        "sigma_c_allow": sigma_c_allow,
        "sigma_t_allow": sigma_t_allow,
    }

def retaining_wall_stability(H_m, gamma_kN_m3, phi_deg, c_kpa, surcharge_kpa, base_friction_coeff):
    """
    Simplified cantilever retaining wall stability check.
    Returns dict with active thrust and factors of safety.
    """
    # Active earth pressure coefficient (Rankine)
    phi = math.radians(phi_deg)
    Ka = (1 - math.sin(phi)) / (1 + math.sin(phi))
    # Active thrust (kN per m length)
    Pa = 0.5 * Ka * gamma_kN_m3 * H_m**2 + Ka * surcharge_kpa * H_m
    # Weight of wall (assume concrete, thickness ~0.3H)
    wall_thickness = 0.3 * H_m
    W = 25 * wall_thickness * H_m  # kN/m
    # Overturning moment (act at H/3)
    M_overt = Pa * H_m / 3
    # Resisting moment
    M_resist = W * wall_thickness / 2
    F_overt = M_resist / M_overt if M_overt > 0 else 999
    # Sliding
    F_sliding = (W * base_friction_coeff) / Pa if Pa > 0 else 999
    pass_flag = F_overt > 1.5 and F_sliding > 1.5
    return {
        "pass": pass_flag,
        "Pa_kN": Pa,
        "F_overt": F_overt,
        "F_sliding": F_sliding,
    }

def truss_method_of_joints(nodes, elements, loads, supports):
    """Placeholder for method of joints (use truss_analysis instead)."""
    return {"info": "Use truss_analysis for full stiffness method solution."}

def generate_analysis_report(data_dict, filename=None):
    """
    Generate a simple text/PDF report and return (filename, error).
    For simplicity, this writes a text file with the data.
    You can replace with reportlab or fpdf if needed.
    """
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{timestamp}.txt"
    try:
        with open(filename, "w") as f:
            f.write("DRUM Studio Analysis Report\n")
            f.write("="*30 + "\n")
            for key, value in data_dict.items():
                f.write(f"{key}: {value}\n")
        return filename, None
    except Exception as e:
        return None, str(e)

# ======================
# NEW FUNCTIONS (TRUSS, LOAD COMBOS, SEISMIC, CONNECTIONS)
# ======================
def truss_analysis(nodes, elements, loads, supports):
    """
    Full 2D truss analysis using the stiffness method.
    nodes: dict node_id -> (x, y) in mm
    elements: list of (node1_id, node2_id, E, A)   E in MPa, A in mm²
    loads: dict node_id -> (Fx, Fy) in kN
    supports: dict node_id -> [True, True] for fixed x,y (or [True, False] for roller)
    Returns dict with displacements, forces, reactions.
    """
    n_nodes = len(nodes)
    dof = 2 * n_nodes
    K = np.zeros((dof, dof))
    node_indices = {nid: i for i, nid in enumerate(nodes.keys())}

    for idx, (n1, n2, E, A) in enumerate(elements):
        x1, y1 = nodes[n1]
        x2, y2 = nodes[n2]
        L = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        if L == 0:
            continue
        c = (x2 - x1) / L
        s = (y2 - y1) / L
        k = (E * A) / L
        k_local = k * np.array([
            [ c*c,  c*s, -c*c, -c*s],
            [ c*s,  s*s, -c*s, -s*s],
            [-c*c, -c*s,  c*c,  c*s],
            [-c*s, -s*s,  c*s,  s*s]
        ])
        i1, i2 = node_indices[n1], node_indices[n2]
        dofs = [2*i1, 2*i1+1, 2*i2, 2*i2+1]
        for a in range(4):
            for b in range(4):
                K[dofs[a], dofs[b]] += k_local[a, b]

    # Identify free and fixed DOFs
    free_dofs = []
    fixed_dofs = []
    for nid, (sx, sy) in supports.items():
        i = node_indices[nid]
        if sx:
            fixed_dofs.append(2*i)
        else:
            free_dofs.append(2*i)
        if sy:
            fixed_dofs.append(2*i+1)
        else:
            free_dofs.append(2*i+1)
    # All remaining DOFs are free
    all_dofs = set(range(dof))
    for d in fixed_dofs:
        all_dofs.discard(d)
    for d in free_dofs:
        all_dofs.add(d)
    free_dofs = sorted(list(all_dofs))

    # Force vector (convert kN to N)
    F = np.zeros(dof)
    for nid, (fx, fy) in loads.items():
        i = node_indices[nid]
        F[2*i] = fx * 1000
        F[2*i+1] = fy * 1000

    # Solve for displacements
    if free_dofs:
        K_ff = K[np.ix_(free_dofs, free_dofs)]
        F_f = F[free_dofs]
        try:
            U_f = np.linalg.solve(K_ff, F_f)
        except np.linalg.LinAlgError:
            return {"error": "Stiffness matrix is singular – structure is unstable."}
    else:
        U_f = np.array([])

    U = np.zeros(dof)
    if free_dofs:
        U[free_dofs] = U_f

    # Reactions
    reactions = {}
    for nid, (sx, sy) in supports.items():
        i = node_indices[nid]
        Rx = np.dot(K[2*i, :], U) - F[2*i]
        Ry = np.dot(K[2*i+1, :], U) - F[2*i+1]
        reactions[nid] = (Rx/1000, Ry/1000)  # kN

    # Element forces
    forces = []
    for idx, (n1, n2, E, A) in enumerate(elements):
        x1, y1 = nodes[n1]
        x2, y2 = nodes[n2]
        L = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        if L == 0:
            forces.append(0.0)
            continue
        c = (x2 - x1) / L
        s = (y2 - y1) / L
        i1, i2 = node_indices[n1], node_indices[n2]
        u1 = U[2*i1]; v1 = U[2*i1+1]
        u2 = U[2*i2]; v2 = U[2*i2+1]
        delta = (u2 - u1)*c + (v2 - v1)*s
        N = (E * A / L) * delta
        forces.append(N/1000)  # kN

    # Displacements in mm
    disp = {nid: (U[2*i], U[2*i+1]) for nid, i in node_indices.items()}
    return {
        "displacements": disp,
        "forces": forces,
        "reactions": reactions
    }

def load_combinations(design_loads, code="eurocode"):
    """Generate load combinations per Eurocode or ASCE."""
    combos = []
    if code.lower() == "eurocode":
        dead = design_loads.get("dead", 0)
        live = design_loads.get("live", 0)
        wind = design_loads.get("wind", 0)
        snow = design_loads.get("snow", 0)
        seismic = design_loads.get("seismic", 0)
        combos.append(("1.35G + 1.5Q", 1.35*dead + 1.5*live))
        combos.append(("1.35G + 1.5W", 1.35*dead + 1.5*wind))
        combos.append(("1.35G + 1.5S", 1.35*dead + 1.5*snow))
        if seismic:
            combos.append(("1.0G + 1.0E", 1.0*dead + 1.0*seismic))
        combos.append(("1.0G + 1.5Q + 0.9W", 1.0*dead + 1.5*live + 0.9*wind))
    elif code.lower() == "asce":
        dead = design_loads.get("dead", 0)
        live = design_loads.get("live", 0)
        wind = design_loads.get("wind", 0)
        snow = design_loads.get("snow", 0)
        seismic = design_loads.get("seismic", 0)
        combos.append(("1.4D", 1.4*dead))
        combos.append(("1.2D + 1.6L + 0.5Lr", 1.2*dead + 1.6*live + 0.5*snow))
        combos.append(("1.2D + 1.0W + 1.0L", 1.2*dead + 1.0*wind + 1.0*live))
        combos.append(("1.2D + 1.0E + 1.0L", 1.2*dead + 1.0*seismic + 1.0*live))
        combos.append(("0.9D + 1.0W", 0.9*dead + 1.0*wind))
        combos.append(("0.9D + 1.0E", 0.9*dead + 1.0*seismic))
    return combos

def seismic_base_shear(Ss, S1, site_class, R, Ie, T):
    """Simplified ASCE 7-10 base shear calculation."""
    Fa_table = {
        "A": (0.8, 0.8, 0.8, 0.8, 0.8),
        "B": (1.0, 1.0, 1.0, 1.0, 1.0),
        "C": (1.2, 1.2, 1.1, 1.0, 1.0),
        "D": (1.6, 1.4, 1.2, 1.1, 1.0),
        "E": (2.5, 1.7, 1.2, 0.9, 0.9),
    }
    Fv_table = {
        "A": (0.8, 0.8, 0.8, 0.8, 0.8),
        "B": (1.0, 1.0, 1.0, 1.0, 1.0),
        "C": (1.7, 1.6, 1.5, 1.4, 1.3),
        "D": (2.4, 2.0, 1.8, 1.6, 1.5),
        "E": (3.5, 3.2, 2.8, 2.4, 2.4),
    }
    idx = 2
    Fa = Fa_table[site_class][idx]
    Fv = Fv_table[site_class][idx]
    Sds = (2/3) * Fa * Ss
    Sd1 = (2/3) * Fv * S1
    Cs_short = Sds / (R / Ie)
    Cs_1s = Sd1 / (T * (R / Ie)) if T > 0 else 0
    Cs_min = 0.044 * Sds * Ie
    if S1 >= 0.6:
        Cs_min = 0.5 * S1 / (R / Ie)
    Cs = max(min(Cs_short, Cs_1s), Cs_min)
    return {
        "Sds": Sds,
        "Sd1": Sd1,
        "Cs": Cs,
        "note": "Base shear V = Cs * W (W = seismic weight)"
    }

def steel_connection_check(connection_type, bolt_dia, bolt_grade, num_bolts, plate_thickness, weld_size, load):
    """Simplified steel connection design check."""
    if connection_type == "bolted":
        fub = {"4.6": 400, "8.8": 800, "10.9": 1000}.get(bolt_grade, 800)
        As = (3.14159 * bolt_dia**2) / 4
        shear_capacity = 0.6 * fub * As / 1000
        total_shear = shear_capacity * num_bolts
        fu_plate = 360
        bearing_capacity = 2.5 * fu_plate * plate_thickness * bolt_dia / 1000
        total_bearing = bearing_capacity * num_bolts
        capacity = min(total_shear, total_bearing)
        return {
            "shear_capacity_per_bolt": shear_capacity,
            "total_shear_capacity": total_shear,
            "bearing_capacity_per_bolt": bearing_capacity,
            "total_bearing_capacity": total_bearing,
            "design_capacity": capacity,
            "status": "OK" if load <= capacity else "FAIL",
            "utilization": load / capacity if capacity > 0 else 0
        }
    elif connection_type == "welded":
        fu_weld = 360
        throat = 0.7 * weld_size
        weld_length = 400  # assume total length
        capacity_per_mm = 0.6 * fu_weld * throat
        total_capacity = capacity_per_mm * weld_length / 1000
        return {
            "capacity_per_mm": capacity_per_mm / 1000,
            "total_capacity": total_capacity,
            "status": "OK" if load <= total_capacity else "FAIL",
            "utilization": load / total_capacity if total_capacity > 0 else 0
        }
    else:
        return {"error": "Invalid connection type"}