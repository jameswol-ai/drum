# engineering/load_combinations.py

def load_combinations(design_loads, code="eurocode"):
    combos = []
    if code.lower() == "eurocode":
        dead = design_loads.get("dead", 0)
        live = design_loads.get("live", 0)
        wind = design_loads.get("wind", 0)
        snow = design_loads.get("snow", 0)
        seismic = design_loads.get("seismic", 0)
        combos.append(("1.35G + 1.5Q", 1.35*dead + 1.5*live))
        combos.append(("1.35G + 1.5W", 1.35*dead + 1.5*wind))
        combos.append(("1.35G + 1.5S", 1.35*dead + 1.5*snow))
        if seismic:
            combos.append(("1.0G + 1.0E", 1.0*dead + 1.0*seismic))
        combos.append(("1.0G + 1.5Q + 0.9W", 1.0*dead + 1.5*live + 0.9*wind))
    elif code.lower() == "asce":
        dead = design_loads.get("dead", 0)
        live = design_loads.get("live", 0)
        wind = design_loads.get("wind", 0)
        snow = design_loads.get("snow", 0)
        seismic = design_loads.get("seismic", 0)
        combos.append(("1.4D", 1.4*dead))
        combos.append(("1.2D + 1.6L + 0.5Lr", 1.2*dead + 1.6*live + 0.5*snow))
        combos.append(("1.2D + 1.0W + 1.0L", 1.2*dead + 1.0*wind + 1.0*live))
        combos.append(("1.2D + 1.0E + 1.0L", 1.2*dead + 1.0*seismic + 1.0*live))
        combos.append(("0.9D + 1.0W", 0.9*dead + 1.0*wind))
        combos.append(("0.9D + 1.0E", 0.9*dead + 1.0*seismic))
    return combos