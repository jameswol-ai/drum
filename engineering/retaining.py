# engineering/retaining.py
import math

def retaining_wall_stability(H_m, gamma_kN_m3, phi_deg, c_kpa, surcharge_kpa, base_friction_coeff):
    phi = math.radians(phi_deg)
    Ka = (1 - math.sin(phi)) / (1 + math.sin(phi))
    Pa = 0.5 * Ka * gamma_kN_m3 * H_m**2 + Ka * surcharge_kpa * H_m
    wall_thickness = 0.3 * H_m
    W = 25 * wall_thickness * H_m
    M_overt = Pa * H_m / 3
    M_resist = W * wall_thickness / 2
    F_overt = M_resist / M_overt if M_overt > 0 else 999
    F_sliding = (W * base_friction_coeff) / Pa if Pa > 0 else 999
    pass_flag = F_overt > 1.5 and F_sliding > 1.5
    return {
        "pass": pass_flag,
        "Pa_kN": Pa,
        "F_overt": F_overt,
        "F_sliding": F_sliding,
    }