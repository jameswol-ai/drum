# eurocodes/en1998.py

def en1998_base_shear(seismic_weight_kN, ag_g, soil_class="C", q_factor=2.0, T_period=0.5):
    """
    Simplified base shear calculation per EN 1998.
    """
    soil_factors = {"A": 1.0, "B": 1.2, "C": 1.15, "D": 1.35, "E": 1.4}
    S = soil_factors.get(soil_class, 1.15)
    Sd = ag_g * S / q_factor
    if T_period <= 0.5:
        Cs = Sd
    else:
        Cs = Sd * 0.5 / T_period
    V_base = Cs * seismic_weight_kN
    return {
        "S": S,
        "Sd": Sd,
        "Cs": Cs,
        "V_base_kN": V_base,
    }