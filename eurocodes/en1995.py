# eurocodes/en1995.py

def en1995_timber_beam_design(timber_class, b_mm, h_mm, M_ed_kNm, V_ed_kN, span_m, service_class=2, load_duration_class="medium"):
    timber_classes = {
        "C14": {"fm_k": 14.0, "fv_k": 2.0, "E0_mean": 7e3},
        "C16": {"fm_k": 16.0, "fv_k": 2.0, "E0_mean": 8e3},
        "C18": {"fm_k": 18.0, "fv_k": 2.2, "E0_mean": 9e3},
        "C24": {"fm_k": 24.0, "fv_k": 2.5, "E0_mean": 11e3},
        "C30": {"fm_k": 30.0, "fv_k": 3.0, "E0_mean": 12e3},
        "GL24h": {"fm_k": 24.0, "fv_k": 2.7, "E0_mean": 11.5e3},
        "GL28h": {"fm_k": 28.0, "fv_k": 3.2, "E0_mean": 12.6e3},
        "GL32h": {"fm_k": 32.0, "fv_k": 3.8, "E0_mean": 13.7e3},
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