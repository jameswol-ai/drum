import numpy as np

# ======================
# TRUSS SOLVER (2D Stiffness Method)
# ======================
def truss_analysis(nodes, elements, loads, supports):
    """
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
    all_dofs = set(range(dof))
    for d in fixed_dofs:
        all_dofs.discard(d)
    for d in free_dofs:
        all_dofs.add(d)
    free_dofs = sorted(list(all_dofs))

    F = np.zeros(dof)
    for nid, (fx, fy) in loads.items():
        i = node_indices[nid]
        F[2*i] = fx * 1000
        F[2*i+1] = fy * 1000

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

    reactions = {}
    for nid, (sx, sy) in supports.items():
        i = node_indices[nid]
        Rx = np.dot(K[2*i, :], U) - F[2*i]
        Ry = np.dot(K[2*i+1, :], U) - F[2*i+1]
        reactions[nid] = (Rx/1000, Ry/1000)

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
        forces.append(N/1000)

    disp = {nid: (U[2*i], U[2*i+1]) for nid, i in node_indices.items()}
    return {
        "displacements": disp,
        "forces": forces,
        "reactions": reactions
    }

# ======================
# LOAD COMBINATIONS
# ======================
def load_combinations(design_loads, code="eurocode"):
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

# ======================
# SEISMIC BASE SHEAR
# ======================
def seismic_base_shear(Ss, S1, site_class, R, Ie, T):
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
    idx = 2  # mid-range
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

# ======================
# STEEL CONNECTION CHECK
# ======================
def steel_connection_check(connection_type, bolt_dia, bolt_grade, num_bolts, plate_thickness, weld_size, load):
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
        weld_length = 400
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