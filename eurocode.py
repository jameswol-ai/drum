# eurocodes.py
# Eurocode-specific structural analysis functions
import math
import numpy as np

# ======================
# EN 1990 - LOAD COMBINATIONS
# ======================
def eurocode_uls_combinations(dead, live, wind=0, snow=0, seismic=0, psi0_live=0.7, psi0_wind=0.6, psi0_snow=0.5):
    combos = []
    combos.append(("6.10a: 1.35G + 1.5ψ0Q", 1.35*dead + 1.5*psi0_live*live, 1.35, 1.5))
    combos.append(("6.10a: 1.35G + 1.5ψ0W", 1.35*dead + 1.5*psi0_wind*wind, 1.35, 1.5))
    if snow:
        combos.append(("6.10a: 1.35G + 1.5ψ0S", 1.35*dead + 1.5*psi0_snow*snow, 1.35, 1.5))
    combos.append(("6.10b: 1.25G + 1.5Q + 0.9W", 1.25*dead + 1.5*live + 0.9*wind, 1.25, 1.5))
    combos.append(("6.10b: 1.25G + 1.5W + 1.05Q", 1.25*dead + 1.5*wind + 1.05*live, 1.25, 1.5))
    if snow:
        combos.append(("6.10b: 1.25G + 1.5S + 1.05Q", 1.25*dead + 1.5*snow + 1.05*live, 1.25, 1.5))
    if seismic:
        combos.append(("Seismic: 1.0G + 1.0E + 0.3Q", 1.0*dead + 1.0*seismic + 0.3*live, 1.0, 1.0))
    return combos

def eurocode_sls_combinations(dead, live, wind=0, snow=0, psi1_live=0.5, psi1_wind=0.2, psi1_snow=0.2, psi2_live=0.3, psi2_wind=0.0, psi2_snow=0.0):
    combos = []
    combos.append(("Characteristic: G + Q", dead + live))
    combos.append(("Frequent: G + ψ1Q", dead + psi1_live*live))
    combos.append(("Quasi-permanent: G + ψ2Q", dead + psi2_live*live))
    if wind:
        combos.append(("Characteristic: G + W", dead + wind))
        combos.append(("Frequent: G + ψ1W", dead + psi1_wind*wind))
    if snow:
        combos.append(("Characteristic: G + S", dead + snow))
        combos.append(("Frequent: G + ψ1S", dead + psi1_snow*snow))
    return combos


# ======================
# EN 1992-1-1 - RC BEAM DESIGN
# ======================
def en1992_rc_beam_design(b_mm, h_mm, d_mm, fck_mpa, fyk_mpa, M_ed_kNm, V_ed_kN, span_m, exposure_class="XC3", bar_dia=20):
    fck = fck_mpa
    fyk = fyk_mpa
    gamma_c = 1.5
    gamma_s = 1.15
    fcd = fck / gamma_c
    fyd = fyk / gamma_s
    
    cover = 25 + 10
    d_actual = h_mm - cover - bar_dia/2
    if d_mm is None or d_mm <= 0:
        d_mm = d_actual
    
    if d_mm <= 0 or d_mm >= h_mm:
        return {"pass": False, "error": "Invalid effective depth"}
    
    z = min(0.95 * d_mm, d_mm - 50)
    if z <= 0:
        return {"pass": False, "error": "Lever arm too small"}
    
    M_ed_Nmm = M_ed_kNm * 1e6
    As_req = M_ed_Nmm / (fyd * z)
    
    As_min = max(0.26 * (2.2/fck) * b_mm * d_mm, 0.0013 * b_mm * d_mm)
    As_max = 0.04 * b_mm * h_mm
    As_req = max(As_req, As_min)
    
    if As_req > As_max:
        return {"pass": False, "error": "Required steel exceeds maximum allowed"}
    
    v_ed = V_ed_kN * 1000 / (b_mm * d_mm)
    v_rdc = 0.12 * (1 + math.sqrt(200/d_mm)) * (100 * 0.01 * fck)**(1/3)
    utilization_shear = v_ed / v_rdc if v_rdc > 0 else 999
    
    span_depth_ratio = span_m * 1000 / d_mm
    allowed_ratio = 20
    utilization_deflection = span_depth_ratio / allowed_ratio
    
    pass_overall = utilization_shear <= 1.0 and utilization_deflection <= 1.0
    
    return {
        "pass": pass_overall,
        "As_required_mm2": As_req,
        "As_min_mm2": As_min,
        "As_max_mm2": As_max,
        "lever_arm_mm": z,
        "shear_stress_MPa": v_ed,
        "shear_capacity_MPa": v_rdc,
        "utilization_shear": utilization_shear,
        "span_depth_ratio": span_depth_ratio,
        "allowed_span_depth_ratio": allowed_ratio,
        "utilization_deflection": utilization_deflection,
    }


# ======================
# EN 1993-1-1 - STEEL BEAM DESIGN
# ======================
def en1993_steel_beam_design(section, fy_mpa, M_ed_kNm, V_ed_kN, span_m, buckling_check=True):
    sections = {
        "IPE 160": {"I_y": 8.69e6, "W_pl_y": 1.09e5, "W_el_y": 0.97e5, "A": 2010, "h": 160, "b": 82, "t_f": 7.4, "t_w": 5.0},
        "IPE 220": {"I_y": 2.77e7, "W_pl_y": 2.52e5, "W_el_y": 2.25e5, "A": 3340, "h": 220, "b": 110, "t_f": 9.2, "t_w": 5.9},
        "IPE 300": {"I_y": 8.36e7, "W_pl_y": 6.28e5, "W_el_y": 5.57e5, "A": 5380, "h": 300, "b": 150, "t_f": 10.7, "t_w": 7.1},
    }
    if section not in sections:
        return {"pass": False, "error": "Unknown section"}
    if span_m <= 0:
        return {"pass": False, "error": "Span must be positive"}
    
    props = sections[section]
    fy = fy_mpa
    E = 210e3
    gamma_m0 = 1.0
    
    M_pl_Rd = props["W_pl_y"] * fy / gamma_m0 / 1e6
    utilization_moment = M_ed_kNm / M_pl_Rd if M_pl_Rd > 0 else 999
    
    Av = props["A"] - 2*props["b"]*props["t_f"] + (props["t_w"] + 2*10)*props["t_f"]
    V_pl_Rd = Av * fy / (math.sqrt(3) * gamma_m0) / 1000
    utilization_shear = V_ed_kN / V_pl_Rd if V_pl_Rd > 0 else 999
    
    if buckling_check:
        I_z = props["b"]**3 * props["t_f"] / 6 + (props["h"] - props["t_f"]) * props["t_w"]**3 / 12
        G = 81000
        L = span_m * 1000
        Mcr = (math.pi/L) * math.sqrt(E * I_z * G * props["I_y"] / (L**2)) / 1e6
        lambda_lt = math.sqrt(props["W_pl_y"] * fy / Mcr)
        if lambda_lt > 0.4:
            phi_lt = 0.5 * (1 + 0.49 * (lambda_lt - 0.4) + 0.75 * lambda_lt**2)
            chi_lt = min(1.0 / (phi_lt + math.sqrt(phi_lt**2 - lambda_lt**2)), 1.0)
        else:
            chi_lt = 1.0
        M_b_Rd = chi_lt * M_pl_Rd
        utilization_ltb = M_ed_kNm / M_b_Rd if M_b_Rd > 0 else 999
    else:
        M_b_Rd = M_pl_Rd
        utilization_ltb = utilization_moment
        chi_lt = 1.0
    
    w = 8 * M_ed_kNm / (span_m ** 2)
    delta = 5 * w * (span_m*1000)**4 / (384 * E * props["I_y"])
    utilization_deflection = delta / (span_m*1000/250)
    
    pass_overall = utilization_moment <= 1.0 and utilization_shear <= 1.0 and utilization_deflection <= 1.0 and utilization_ltb <= 1.0
    
    return {
        "pass": pass_overall,
        "moment_capacity_knm": M_pl_Rd,
        "shear_capacity_kn": V_pl_Rd,
        "buckling_moment_knm": M_b_Rd,
        "utilization_moment": utilization_moment,
        "utilization_shear": utilization_shear,
        "utilization_deflection": utilization_deflection,
        "utilization_ltb": utilization_ltb,
        "chi_lt": chi_lt,
        "deflection_mm": delta,
    }


# ======================
# EN 1995-1-1 - TIMBER BEAM DESIGN
# ======================
def en1995_timber_beam_design(timber_class, b_mm, h_mm, M_ed_kNm, V_ed_kN, span_m, service_class=2, load_duration_class="medium"):
    timber_classes = {
        "C14": {"fm_k": 14.0, "fv_k": 2.0, "E0_mean": 7e3},
        "C16": {"fm_k": 16.0, "fv_k": 2.0, "E0_mean": 8e3},
        "C24": {"fm_k": 24.0, "fv_k": 2.5, "E0_mean": 11e3},
        "GL24h": {"fm_k": 24.0, "fv_k": 2.7, "E0_mean": 11.5e3},
    }
    if timber_class not in timber_classes:
        return {"pass": False, "error": "Unknown timber class"}
    
    props = timber_classes[timber_class]
    
    kmod_table = {
        1: {"short": 0.9, "medium": 0.8, "long": 0.7},
        2: {"short": 0.9, "medium": 0.8, "long": 0.7},
        3: {"short": 0.7, "medium": 0.65, "long": 0.55},
    }
    kmod = kmod_table.get(service_class, {}).get(load_duration_class, 0.8)
    gamma_m = 1.3
    
    fm_d = kmod * props["fm_k"] / gamma_m
    fv_d = kmod * props["fv_k"] / gamma_m
    
    W = b_mm * h_mm**2 / 6
    A = b_mm * h_mm
    I = b_mm * h_mm**3 / 12
    
    sigma_m = M_ed_kNm * 1e6 / W
    utilization_moment = sigma_m / fm_d
    
    tau = 1.5 * V_ed_kN * 1000 / A
    utilization_shear = tau / fv_d
    
    k_def = {1: 0.6, 2: 0.8, 3: 2.0}.get(service_class, 0.8)
    E_fin = props["E0_mean"] / (1 + k_def)
    w = 8 * M_ed_kNm / (span_m ** 2)
    delta_inst = 5 * w * (span_m*1000)**4 / (384 * props["E0_mean"] * I)
    delta_fin = 5 * w * (span_m*1000)**4 / (384 * E_fin * I)
    utilization_deflection = delta_fin / (span_m*1000/250)
    
    pass_overall = utilization_moment <= 1.0 and utilization_shear <= 1.0 and utilization_deflection <= 1.0
    
    return {
        "pass": pass_overall,
        "bending_stress_mpa": sigma_m,
        "bending_strength_mpa": fm_d,
        "shear_stress_mpa": tau,
        "shear_strength_mpa": fv_d,
        "utilization_moment": utilization_moment,
        "utilization_shear": utilization_shear,
        "utilization_deflection": utilization_deflection,
        "deflection_instantaneous_mm": delta_inst,
        "deflection_final_mm": delta_fin,
    }


# ======================
# EN 1992-1-1 - COLUMN DESIGN
# ======================
def en1992_rc_column_design(N_ed_kN, M_ed_kNm, b_mm, h_mm, fck_mpa, fyk_mpa, l0_m):
    fck = fck_mpa
    fyk = fyk_mpa
    gamma_c = 1.5
    gamma_s = 1.15
    fcd = fck / gamma_c
    fyd = fyk / gamma_s
    
    Ac = b_mm * h_mm
    As = 0.01 * Ac
    
    N_rd = (0.567 * fcd * Ac + 0.87 * fyd * As) / 1000
    
    d = h_mm - 50
    M_rd = 0.167 * fcd * b_mm * d**2 / 1e6
    
    i = h_mm / math.sqrt(12)
    lambda_ = l0_m * 1000 / i
    lambda_limit = 20 * 0.7 * 1.1 / math.sqrt(N_ed_kN / (fcd * Ac) + 1e-6)
    
    if lambda_ > lambda_limit:
        e0 = M_ed_kNm / N_ed_kN if N_ed_kN > 0 else 0
        e2 = (lambda_**2) * (l0_m * 1000) / 10 * 0.001
        M_ed_eff = N_ed_kN * (e0 + e2)
    else:
        M_ed_eff = M_ed_kNm
    
    utilization_axial = N_ed_kN / N_rd if N_rd > 0 else 999
    utilization_moment = M_ed_eff / M_rd if M_rd > 0 else 999
    utilization_combined = utilization_axial + utilization_moment
    
    pass_overall = utilization_combined <= 1.0 and lambda_ <= lambda_limit * 1.5
    
    return {
        "pass": pass_overall,
        "N_rd_kn": N_rd,
        "M_rd_knm": M_rd,
        "lambda": lambda_,
        "lambda_limit": lambda_limit,
        "M_ed_effective_knm": M_ed_eff,
        "utilization_axial": utilization_axial,
        "utilization_moment": utilization_moment,
        "utilization_combined": utilization_combined,
    }