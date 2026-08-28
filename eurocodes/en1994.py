# eurocodes/en1994.py
import math

def en1994_composite_beam_design(section, slab_thickness_mm, slab_width_mm, fck_mpa, fy_mpa, M_ed_kNm, V_ed_kN, span_m):
    sections = {
        "IPE 160": {"I": 8.69e6, "A": 2010, "h": 160},
        "IPE 220": {"I": 2.77e7, "A": 3340, "h": 220},
        "IPE 300": {"I": 8.36e7, "A": 5380, "h": 300},
    }
    if section not in sections:
        return {"pass": False, "error": "Unknown section"}
    props = sections[section]
    fcd = fck_mpa / 1.5
    Fc = 0.85 * fcd * slab_width_mm * slab_thickness_mm / 1000
    Fs = fy_mpa * props["A"] / 1000
    total_depth = props["h"] + slab_thickness_mm
    if Fc >= Fs:
        depth_na = Fs / (0.85 * fcd * slab_width_mm)
        lever_arm = total_depth - depth_na/2 - props["h"]/2
    else:
        lever_arm = total_depth / 2
    M_pl_Rd = Fs * lever_arm / 1000
    utilization_moment = M_ed_kNm / M_pl_Rd if M_pl_Rd > 0 else 999
    V_pl_Rd = props["A"] * fy_mpa / (math.sqrt(3) * 1000)
    utilization_shear = V_ed_kN / V_pl_Rd if V_pl_Rd > 0 else 999
    E = 210e3
    I_eff = props["I"] * 2
    w = 8 * M_ed_kNm / (span_m ** 2)
    delta = 5 * w * (span_m*1000)**4 / (384 * E * I_eff)
    utilization_deflection = delta / (span_m*1000/250)
    pass_overall = utilization_moment <= 1.0 and utilization_shear <= 1.0 and utilization_deflection <= 1.0
    return {
        "pass": pass_overall,
        "moment_capacity_knm": M_pl_Rd,
        "shear_capacity_kn": V_pl_Rd,
        "utilization_moment": utilization_moment,
        "utilization_shear": utilization_shear,
        "utilization_deflection": utilization_deflection,
        "deflection_mm": delta,
    }