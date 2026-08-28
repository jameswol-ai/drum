# ======================
# TRUSS SOLVER (2D Stiffness Method)
# ======================
import numpy as np

def truss_analysis(nodes, elements, loads, supports):
    """
    nodes: dict of node_id -> (x, y)
    elements: list of (node1_id, node2_id, E, A)   (E in MPa, A in mm²)
    loads: dict of node_id -> (Fx, Fy)             (forces in kN)
    supports: dict of node_id -> [True, True] for fixed x,y (or [True, False] for roller)

    Returns:
        displacements: dict node_id -> (ux, uy) in mm
        forces: dict element_index -> axial force in kN (tension positive)
        reactions: dict node_id -> (Rx, Ry) in kN
    """
    # Build global stiffness matrix
    n_nodes = len(nodes)
    dof = 2 * n_nodes
    K = np.zeros((dof, dof))
    node_indices = {nid: i for i, nid in enumerate(nodes.keys())}

    for idx, (n1, n2, E, A) in enumerate(elements):
        x1, y1 = nodes[n1]
        x2, y2 = nodes[n2]
        L = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)  # mm
        if L == 0:
            continue
        c = (x2 - x1) / L
        s = (y2 - y1) / L
        k = (E * A) / L  # N/mm
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

    # Apply boundary conditions
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
    # All other dofs are free
    all_dofs = set(range(dof))
    for d in fixed_dofs:
        all_dofs.discard(d)
    for d in free_dofs:
        all_dofs.add(d)  # they are already free, just ensure not removed
    free_dofs = sorted(list(all_dofs))

    # Force vector
    F = np.zeros(dof)
    for nid, (fx, fy) in loads.items():
        i = node_indices[nid]
        F[2*i] = fx * 1000  # convert kN to N
        F[2*i+1] = fy * 1000

    # Solve for displacements
    K_ff = K[np.ix_(free_dofs, free_dofs)]
    F_f = F[free_dofs]
    if K_ff.size > 0:
        try:
            U_f = np.linalg.solve(K_ff, F_f)
        except np.linalg.LinAlgError:
            return {"error": "Stiffness matrix is singular – structure is unstable."}
    else:
        U_f = np.array([])

    U = np.zeros(dof)
    U[free_dofs] = U_f

    # Calculate reactions and element forces
    reactions = {}
    for nid, (sx, sy) in supports.items():
        i = node_indices[nid]
        Rx = np.dot(K[2*i, :], U) - F[2*i]
        Ry = np.dot(K[2*i+1, :], U) - F[2*i+1]
        reactions[nid] = (Rx/1000, Ry/1000)  # kN

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
        # Axial deformation in local coordinates
        delta = (u2 - u1)*c + (v2 - v1)*s
        N = (E * A / L) * delta  # N
        forces.append(N/1000)  # kN

    # Convert displacements to mm (already in mm)
    disp = {nid: (U[2*i], U[2*i+1]) for nid, i in node_indices.items()}
    return {
        "displacements": disp,
        "forces": forces,
        "reactions": reactions
    }


# ======================
# LOAD COMBINATIONS (Eurocode / ASCE)
# ======================
def load_combinations(design_loads, code="eurocode"):
    """
    design_loads: dict with keys as load types (e.g., "dead", "live", "wind", "snow", "seismic")
                  each value is the characteristic load effect (e.g., bending moment or axial force)
    code: "eurocode" or "asce"
    Returns list of tuples (combination_name, combined_value)
    """
    combos = []
    if code.lower() == "eurocode":
        # Simplified Eurocode 0 (EN 1990) fundamental combinations
        # 1.35G + 1.5Q (or 1.35G + 1.5ψQ with ψ=0.7 for live)
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
        # Simplified ASCE 7-10 LRFD combinations
        dead = design_loads.get("dead", 0)
        live = design_loads.get("live", 0)
        wind = design_loads.get("wind", 0)
        snow = design_loads.get("snow", 0)
        seismic = design_loads.get("seismic", 0)

        combos.append(("1.4D", 1.4*dead))
        combos.append(("1.2D + 1.6L + 0.5Lr", 1.2*dead + 1.6*live + 0.5*(snow if snow else 0)))
        combos.append(("1.2D + 1.0W + 1.0L", 1.2*dead + 1.0*wind + 1.0*live))
        combos.append(("1.2D + 1.0E + 1.0L", 1.2*dead + 1.0*seismic + 1.0*live))
        combos.append(("0.9D + 1.0W", 0.9*dead + 1.0*wind))
        combos.append(("0.9D + 1.0E", 0.9*dead + 1.0*seismic))
    return combos


# ======================
# SEISMIC BASE SHEAR (Simplified ASCE 7-10)
# ======================
def seismic_base_shear(Ss, S1, site_class, R, Ie, T, TL=8, Sds=None, Sd1=None):
    """
    Simplified ASCE 7-10 equivalent lateral force procedure.
    Ss, S1: spectral accelerations at short and 1s period (g)
    site_class: "A" to "E"
    R: response modification factor
    Ie: importance factor
    T: fundamental period (sec)
    Returns dict with Cs, base shear coefficient, and note.
    """
    # Site coefficients (simplified)
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
    # Select coefficients based on Ss and S1 ranges (simplified index)
    # For simplicity, choose mid-range values (index 2)
    idx = 2
    Fa = Fa_table[site_class][idx]
    Fv = Fv_table[site_class][idx]
    if Sds is None:
        Sds = (2/3) * Fa * Ss
    if Sd1 is None:
        Sd1 = (2/3) * Fv * S1
    # Calculate Cs
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


# ======================
# STEEL CONNECTION DESIGN (Simplified)
# ======================
def steel_connection_check(connection_type, bolt_dia, bolt_grade, num_bolts, plate_thickness, weld_size, load):
    """
    Simplified checks for bolted and welded connections.
    connection_type: "bolted" or "welded"
    bolt_dia: mm
    bolt_grade: "4.6", "8.8", "10.9"
    num_bolts: int
    plate_thickness: mm (for bearing check)
    weld_size: mm (leg size for fillet weld)
    load: applied force in kN
    Returns dict with results.
    """
    if connection_type == "bolted":
        # Bolt shear capacity (simplified, assuming single shear)
        fub = {"4.6": 400, "8.8": 800, "10.9": 1000}.get(bolt_grade, 800)  # MPa
        As = (3.14159 * bolt_dia**2) / 4  # mm² (tensile stress area approx.)
        shear_capacity = 0.6 * fub * As / 1000  # kN per bolt
        total_shear = shear_capacity * num_bolts
        # Bearing capacity (plate)
        fu_plate = 360  # assume S235 plate, MPa
        bearing_capacity = 2.5 * fu_plate * plate_thickness * bolt_dia / 1000  # kN per bolt
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
        # Fillet weld capacity (simplified)
        fu_weld = 360  # MPa, for E43 electrodes
        throat = 0.7 * weld_size
        # Assume weld length = 4 sides of a square plate (simplify as 100 mm each side)
        weld_length = 400  # mm total
        capacity_per_mm = 0.6 * fu_weld * throat  # N/mm
        total_capacity = capacity_per_mm * weld_length / 1000  # kN
        return {
            "capacity_per_mm": capacity_per_mm / 1000,  # kN/mm
            "total_capacity": total_capacity,
            "status": "OK" if load <= total_capacity else "FAIL",
            "utilization": load / total_capacity if total_capacity > 0 else 0
        }
    else:
        return {"error": "Invalid connection type"}