# engineering/beams.py
import math

def check_rc_beam(b_mm, h_mm, d_mm, fck_mpa, M_ed_kNm, V_ed_kN, span_m):
    if b_mm <= 0 or h_mm <= 0 or d_mm <= 0 or fck_mpa <= 0:
        return {"pass": False, "error": "Invalid input dimensions."}
    fck = fck_mpa
    fcd = fck / 1.5
    fyd = 500 / 1.15
    z = min(0.95 * d_mm, d_mm - 50)
    if z <= 0:
        return {"pass": False, "error": "Effective depth too small."}
    M_ed_Nmm = M_ed_kNm * 1e6
    As_req = M_ed_Nmm / (fyd * z)
    As_min = 0.26 * (2.2 / fck) * b_mm * d_mm
    As_req = max(As_req, As_min)
    v_ed = V_ed_kN * 1000 / (b_mm * d_mm)
    v_rdc = 0.12 * (1 + math.sqrt(200 / d_mm)) * (100 * 0.01 * fck) ** (1/3)
    utilization_shear = v_ed / v_rdc if v_rdc > 0 else 999
    span_depth_ratio = span_m * 1000 / d_mm
    utilization_deflection = span_depth_ratio / 20
    pass_overall = utilization_shear <= 1.0 and utilization_deflection <= 1.0
    return {
        "pass": pass_overall,
        "As_req": As_req,
        "shear_stress": v_ed,
        "shear_capacity": v_rdc,
        "utilization_shear": utilization_shear,
        "span_depth_ratio": span_depth_ratio,
        "utilization_deflection": utilization_deflection,
    }

def check_steel_beam(section, M_ed_kNm, V_ed_kN, span_m, steel_grade_dict):
    sections = {
        "IPE 160": {"I": 8.69e6, "Wpl": 1.09e5, "A": 2010},
        "IPE 220": {"I": 2.77e7, "Wpl": 2.52e5, "A": 3340},
        "IPE 300": {"I": 8.36e7, "Wpl": 6.28e5, "A": 5380},
        "IPE 400": {"I": 2.31e8, "Wpl": 1.31e6, "A": 8450},
        "IPE 500": {"I": 4.82e8, "Wpl": 2.19e6, "A": 11600},
    }
    if section not in sections:
        return {"pass": False, "error": "Unknown section"}
    if span_m <= 0:
        return {"pass": False, "error": "Span must be positive."}
    props = sections[section]
    fy = steel_grade_dict["fy"]
    E = steel_grade_dict["E"]
    M_pl_Rd = props["Wpl"] * fy / 1.0 / 1e6
    utilization_m = M_ed_kNm / M_pl_Rd
    Av = props["A"] * 0.6
    V_pl_Rd = Av * fy / (math.sqrt(3) * 1.0) / 1000
    utilization_v = V_ed_kN / V_pl_Rd
    w = 8 * M_ed_kNm / (span_m ** 2)
    delta = 5 * w * (span_m*1000)**4 / (384 * E * props["I"])
    utilization_deflection = delta / (span_m*1000/250)
    pass_overall = utilization_m <= 1.0 and utilization_v <= 1.0 and utilization_deflection <= 1.0
    return {
        "pass": pass_overall,
        "moment_capacity": M_pl_Rd,
        "shear_capacity": V_pl_Rd,
        "utilization_moment": utilization_m,
        "utilization_shear": utilization_v,
        "utilization_deflection": utilization_deflection,
        "deflection_mm": delta,
        "deflection_limit": span_m*1000/250,
    }

def check_timber_beam(timber_class, b_mm, h_mm, M_ed_kNm, V_ed_kN, span_m, load_duration="medium"):
    from .materials import TIMBER_CLASSES
    if timber_class not in TIMBER_CLASSES:
        return {"pass": False, "error": "Unknown timber class"}
    props = TIMBER_CLASSES[timber_class]
    fm_k = props["fm_k"]
    fv_k = props["fv_k"]
    E0_mean = props["E0_mean"]
    kmod = {"short": 0.9, "medium": 0.8, "long": 0.7}.get(load_duration, 0.8)
    gamma_m = 1.3
    fm_d = kmod * fm_k / gamma_m
    fv_d = kmod * fv_k / gamma_m
    W = b_mm * h_mm**2 / 6
    A = b_mm * h_mm
    I = b_mm * h_mm**3 / 12
    sigma_m = M_ed_kNm * 1e6 / W
    utilization_m = sigma_m / fm_d
    tau = 1.5 * V_ed_kN * 1000 / A
    utilization_v = tau / fv_d
    w = 8 * M_ed_kNm / (span_m ** 2)
    delta = 5 * w * (span_m*1000)**4 / (384 * E0_mean * I)
    utilization_deflection = delta / (span_m*1000/250)
    pass_overall = utilization_m <= 1.0 and utilization_v <= 1.0 and utilization_deflection <= 1.0
    return {
        "pass": pass_overall,
        "bending_stress": sigma_m,
        "bending_strength": fm_d,
        "shear_stress": tau,
        "shear_strength": fv_d,
        "utilization_moment": utilization_m,
        "utilization_shear": utilization_v,
        "utilization_deflection": utilization_deflection,
        "deflection_mm": delta,
        "deflection_limit": span_m*1000/250,
    }

def check_composite_beam(section, slab_thickness_mm, slab_width_mm, fck_mpa, M_ed_kNm, V_ed_kN, span_m, steel_grade_dict):
    sections = {
        "IPE 160": {"I": 8.69e6, "Wpl": 1.09e5, "A": 2010, "h": 160},
        "IPE 220": {"I": 2.77e7, "Wpl": 2.52e5, "A": 3340, "h": 220},
        "IPE 300": {"I": 8.36e7, "Wpl": 6.28e5, "A": 5380, "h": 300},
    }
    if section not in sections:
        return {"pass": False, "error": "Unknown section"}
    props = sections[section]
    fy = steel_grade_dict["fy"]
    E = steel_grade_dict["E"]
    fck = fck_mpa
    fcd = fck / 1.5
    Fc = 0.85 * fcd * slab_width_mm * slab_thickness_mm / 1000
    Fs = fy * props["A"] / 1000
    total_depth = props["h"] + slab_thickness_mm
    if Fc >= Fs:
        depth_na = Fs / (0.85 * fcd * slab_width_mm)
        lever_arm = total_depth - depth_na/2 - props["h"]/2
    else:
        lever_arm = total_depth / 2
    lever_arm_m = lever_arm / 1000
    M_pl_Rd = Fs * lever_arm_m
    Av = props["A"] * 0.6
    V_pl_Rd = Av * fy / (math.sqrt(3) * 1.0) / 1000
    utilization_m = M_ed_kNm / M_pl_Rd if M_pl_Rd > 0 else 999
    utilization_v = V_ed_kN / V_pl_Rd if V_pl_Rd > 0 else 999
    I_eff = props["I"] * 2
    w = 8 * M_ed_kNm / (span_m ** 2)
    delta = 5 * w * (span_m*1000)**4 / (384 * E * I_eff)
    utilization_deflection = delta / (span_m*1000/250)
    pass_overall = utilization_m <= 1.0 and utilization_v <= 1.0 and utilization_deflection <= 1.0
    return {
        "pass": pass_overall,
        "moment_capacity": M_pl_Rd,
        "shear_capacity": V_pl_Rd,
        "utilization_moment": utilization_m,
        "utilization_shear": utilization_v,
        "utilization_deflection": utilization_deflection,
        "deflection_mm": delta,
        "lever_arm_mm": lever_arm,
    }