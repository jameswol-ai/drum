# eurocodes/en1997.py
import math

def en1997_shallow_foundation(load_kN, bearing_capacity_kPa, safety_factor=3.0):
    if load_kN <= 0 or bearing_capacity_kPa <= 0:
        return {"pass": False, "error": "Inputs must be positive"}
    area_req = load_kN / (bearing_capacity_kPa * safety_factor)
    side = math.sqrt(area_req)
    return {"side_m": side, "area_m2": area_req}

def en1997_pile_capacity(diameter_m, length_m, soil_type, N_value, safety_factor=2.5):
    if diameter_m <= 0 or length_m <= 0:
        return {"pass": False, "error": "Dimensions must be positive"}
    if soil_type == "sand":
        shaft_stress = 2 * N_value
        base_stress = 40 * N_value
    elif soil_type == "clay":
        shaft_stress = 5 * N_value
        base_stress = 9 * N_value
    else:
        return {"pass": False, "error": "Unknown soil type"}
    perimeter = math.pi * diameter_m
    shaft_area = perimeter * length_m
    base_area = math.pi * (diameter_m/2)**2
    shaft_capacity = shaft_stress * shaft_area
    base_capacity = base_stress * base_area
    Q_ult = shaft_capacity + base_capacity
    Q_all = Q_ult / safety_factor
    return {
        "Q_ult_kN": Q_ult,
        "Q_all_kN": Q_all,
        "shaft_kN": shaft_capacity,
        "base_kN": base_capacity,
    }