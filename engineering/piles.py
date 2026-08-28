# engineering/piles.py
import math

def pile_capacity(diameter_m, length_m, soil_type, N_value, factor_of_safety=2.5):
    if soil_type == "sand":
        shaft_stress = 2 * N_value
        base_stress = 40 * N_value
    else:
        shaft_stress = 5 * N_value
        base_stress = 9 * N_value
    perimeter = math.pi * diameter_m
    shaft_area = perimeter * length_m
    base_area = math.pi * (diameter_m/2)**2
    shaft_capacity = shaft_stress * shaft_area
    base_capacity = base_stress * base_area
    Q_ult = shaft_capacity + base_capacity
    Q_all = Q_ult / factor_of_safety
    return {
        "Q_ult_kN": Q_ult,
        "Q_all_kN": Q_all,
        "shaft_kN": shaft_capacity,
        "base_kN": base_capacity,
    }