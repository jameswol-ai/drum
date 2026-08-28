# eurocodes/en1999.py

def en1999_aluminium_beam_design(alloy_class, section_modulus_mm3, M_ed_kNm, V_ed_kN, span_m):
    """
    Simplified aluminium beam design per EN 1999.
    """
    alloys = {
        "6082-T6": {"fy": 250, "E": 70e3},
        "6061-T6": {"fy": 240, "E": 69e3},
        "7075-T6": {"fy": 470, "E": 71e3},
    }
    if alloy_class not in alloys:
        return {"pass": False, "error": "Unknown alloy"}
    props = alloys[alloy_class]
    fy = props["fy"]
    E = props["E"]
    gamma_m0 = 1.1
    M_pl_Rd = section_modulus_mm3 * fy / gamma_m0 / 1e6
    utilization_moment = M_ed_kNm / M_pl_Rd if M_pl_Rd > 0 else 999
    w = 8 * M_ed_kNm / (span_m ** 2)
    delta = 5 * w * (span_m*1000)**4 / (384 * E * section_modulus_mm3 * 10)
    utilization_deflection = delta / (span_m*1000/250)
    pass_overall = utilization_moment <= 1.0 and utilization_deflection <= 1.0
    return {
        "pass": pass_overall,
        "moment_capacity_knm": M_pl_Rd,
        "utilization_moment": utilization_moment,
        "utilization_deflection": utilization_deflection,
        "deflection_mm": delta,
    }