# eurocodes/en1993.py
import math

def en1993_steel_beam_design(section, fy_mpa, M_ed_kNm, V_ed_kN, span_m, buckling_check=True):
    sections = {
        "IPE 160": {"I_y": 8.69e6, "W_pl_y": 1.09e5, "A": 2010, "h": 160, "b": 82, "t_f": 7.4, "t_w": 5.0},
        "IPE 220": {"I_y": 2.77e7, "W_pl_y": 2.52e5, "A": 3340, "h": 220, "b": 110, "t_f": 9.2, "t_w": 5.9},
        "IPE 300": {"I_y": 8.36e7, "W_pl_y": 6.28e5, "A": 5380, "h": 300, "b": 150, "t_f": 10.7, "t_w": 7.1},
        "IPE 400": {"I_y": 2.31e8, "W_pl_y": 1.31e6, "A": 8450, "h": 400, "b": 180, "t_f": 13.5, "t_w": 8.6},
        "IPE 500": {"I_y": 4.82e8, "W_pl_y": 2.19e6, "A": 11600, "h": 500, "b": 200, "t_f": 16.0, "t_w": 10.2},
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

def en1993_steel_column_design(section, fy_mpa, N_ed_kN, l0_m):
    sections = {
        "HEA 200": {"A": 5380, "i_y": 82.6, "i_z": 49.8, "h": 190, "b": 200, "t_f": 10.0, "t_w": 6.5},
        "HEA 240": {"A": 7680, "i_y": 101.0, "i_z": 60.3, "h": 230, "b": 240, "t_f": 12.0, "t_w": 7.5},
        "HEA 300": {"A": 11300, "i_y": 127.0, "i_z": 75.1, "h": 290, "b": 300, "t_f": 14.0, "t_w": 8.5},
    }
    if section not in sections:
        return {"pass": False, "error": "Unknown section"}
    props = sections[section]
    fy = fy_mpa
    E = 210e3
    N_pl_Rd = props["A"] * fy / 1000
    lambda_y = l0_m * 1000 / props["i_y"]
    lambda_z = l0_m * 1000 / props["i_z"]
    lambda_max = max(lambda_y, lambda_z)
    lambda_1 = 93.9 * math.sqrt(235/fy)
    lambda_bar = lambda_max / lambda_1
    if lambda_bar <= 0.2:
        chi = 1.0
    else:
        phi = 0.5 * (1 + 0.49 * (lambda_bar - 0.2) + lambda_bar**2)
        chi = 1.0 / (phi + math.sqrt(phi**2 - lambda_bar**2))
    N_b_Rd = chi * N_pl_Rd
    utilization = N_ed_kN / N_b_Rd if N_b_Rd > 0 else 999
    return {
        "pass": utilization <= 1.0,
        "N_pl_Rd_kn": N_pl_Rd,
        "N_b_Rd_kn": N_b_Rd,
        "lambda_bar": lambda_bar,
        "chi": chi,
        "utilization": utilization,
    }