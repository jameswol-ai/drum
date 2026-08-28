# engineering/prestressed.py
import math

def check_prestressed_beam(M_ext_kNm, P_kN, e_m, A_m2, I_m4, y_top_m, y_bot_m, fck_mpa):
    P = P_kN * 1000
    M_ext = M_ext_kNm * 1e6
    sigma_p_top = P/A_m2*1e-6 - P*e_m*y_top_m/(I_m4*1e12)
    sigma_p_bot = P/A_m2*1e-6 + P*e_m*y_bot_m/(I_m4*1e12)
    sigma_m_top = -M_ext*y_top_m/(I_m4*1e12)
    sigma_m_bot = M_ext*y_bot_m/(I_m4*1e12)
    sigma_top = sigma_p_top + sigma_m_top
    sigma_bot = sigma_p_bot + sigma_m_bot
    sigma_c_allow = 0.6 * fck_mpa
    sigma_t_allow = -0.5 * math.sqrt(fck_mpa) if fck_mpa > 0 else 0
    pass_top = sigma_top <= sigma_c_allow and sigma_top >= sigma_t_allow
    pass_bot = sigma_bot <= sigma_c_allow and sigma_bot >= sigma_t_allow
    return {
        "pass": pass_top and pass_bot,
        "sigma_top_MPa": sigma_top,
        "sigma_bot_MPa": sigma_bot,
        "sigma_c_allow": sigma_c_allow,
        "sigma_t_allow": sigma_t_allow,
    }