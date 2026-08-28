# engineering/seismic.py

def seismic_base_shear(Ss, S1, site_class, R, Ie, T):
    Fa_table = {
        "A": (0.8, 0.8, 0.8, 0.8, 0.8),
        "B": (1.0, 1.0, 1.0, 1.0, 1.0),
        "C": (1.2, 1.2, 1.1, 1.0, 1.0),
        "D": (1.6, 1.4, 1.2, 1.1, 1.0),
        "E": (2.5, 1.7, 1.2, 0.9, 0.9),
    }
    Fv_table = {
        "A": (0.8, 0.8, 0.8, 0.8, 0.8),
        "B": (1.0, 1.0, 1.0, 1.0, 1.0),
        "C": (1.7, 1.6, 1.5, 1.4, 1.3),
        "D": (2.4, 2.0, 1.8, 1.6, 1.5),
        "E": (3.5, 3.2, 2.8, 2.4, 2.4),
    }
    idx = 2
    Fa = Fa_table[site_class][idx]
    Fv = Fv_table[site_class][idx]
    Sds = (2/3) * Fa * Ss
    Sd1 = (2/3) * Fv * S1
    Cs_short = Sds / (R / Ie)
    Cs_1s = Sd1 / (T * (R / Ie)) if T > 0 else 0
    Cs_min = 0.044 * Sds * Ie
    if S1 >= 0.6:
        Cs_min = 0.5 * S1 / (R / Ie)
    Cs = max(min(Cs_short, Cs_1s), Cs_min)
    return {
        "Sds": Sds,
        "Sd1": Sd1,
        "Cs": Cs,
        "note": "Base shear V = Cs * W (W = seismic weight)"
    }