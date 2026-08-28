# engineering/foundations.py
import math

def foundation_size(allowable_bearing_kpa, load_kN, factor_of_safety=3.0):
    if allowable_bearing_kpa <= 0:
        return {"error": "Allowable bearing pressure must be positive."}
    if load_kN <= 0:
        return {"error": "Load must be positive."}
    if factor_of_safety <= 0:
        return {"error": "Factor of safety must be positive."}
    q_all = allowable_bearing_kpa * factor_of_safety
    area_req = load_kN / q_all
    side = math.sqrt(area_req)
    return {"side_m": side, "area_m2": area_req}