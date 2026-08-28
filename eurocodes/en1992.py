# eurocodes/en1992.py
import math

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

def en1992_slab_design(span_m, support_type, fck_mpa, fyk_mpa, live_load_kpa, finishes_kpa=1.5):
    fck = fck_mpa
    gamma_c = 1.5
    gamma_s = 1.15
    fcd = fck / gamma_c
    fyd = fyk / gamma_s
    thickness = span_m / 20 if support_type == "simply_supported" else span_m / 28
    thickness = max(thickness, 0.15)  # minimum 150mm
    self_weight = thickness * 25
    total_load = self_weight + finishes_kpa + live_load_kpa
    M_ed = total_load * span_m**2 / 8
    d = thickness - 25 - 5
    z = min(0.95 * d, d - 25)
    As_req = M_ed * 1e6 / (fyd * z * 1000)  # per meter width
    As_min = max(0.26 * (2.2/fck) * 1000 * d, 0.0013 * 1000 * d)
    As_req = max(As_req, As_min)
    return {
        "thickness_mm": thickness * 1000,
        "design_load_kPa": total_load,
        "M_ed_kNm": M_ed,
        "As_required_mm2_per_m": As_req,
        "As_min_mm2_per_m": As_min,
    }