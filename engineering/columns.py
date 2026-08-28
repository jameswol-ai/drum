# engineering/columns.py
import math

def check_rc_column(N_ed_kN, M_ed_kNm, b_mm, h_mm, fck_mpa, l0_m):
    fck = fck_mpa
    fcd = fck / 1.5
    fyd = 500 / 1.15
    Ac = b_mm * h_mm
    As = 0.01 * Ac
    N_rd = 0.567 * fcd * Ac + 0.87 * fyd * As
    N_rd_kN = N_rd / 1000
    d = h_mm - 50
    M_rd = 0.167 * fcd * b_mm * d**2 / 1e6
    i = h_mm / math.sqrt(12)
    lambda_ = l0_m * 1000 / i
    pass_slender = lambda_ <= 20
    if N_ed_kN > N_rd_kN or M_ed_kNm > M_rd:
        pass_interaction = False
    else:
        pass_interaction = (N_ed_kN/N_rd_kN + M_ed_kNm/M_rd) <= 1.0
    return {
        "pass": pass_interaction and pass_slender,
        "N_rd": N_rd_kN,
        "M_rd": M_rd,
        "lambda": lambda_,
    }