# eurocodes/en1990.py
def eurocode_uls_combinations(dead, live, wind=0, snow=0, seismic=0, psi0_live=0.7, psi0_wind=0.6, psi0_snow=0.5):
    combos = []
    combos.append(("6.10a: 1.35G + 1.5ψ0Q", 1.35*dead + 1.5*psi0_live*live, 1.35, 1.5))
    combos.append(("6.10a: 1.35G + 1.5ψ0W", 1.35*dead + 1.5*psi0_wind*wind, 1.35, 1.5))
    if snow:
        combos.append(("6.10a: 1.35G + 1.5ψ0S", 1.35*dead + 1.5*psi0_snow*snow, 1.35, 1.5))
    combos.append(("6.10b: 1.25G + 1.5Q + 0.9W", 1.25*dead + 1.5*live + 0.9*wind, 1.25, 1.5))
    combos.append(("6.10b: 1.25G + 1.5W + 1.05Q", 1.25*dead + 1.5*wind + 1.05*live, 1.25, 1.5))
    if snow:
        combos.append(("6.10b: 1.25G + 1.5S + 1.05Q", 1.25*dead + 1.5*snow + 1.05*live, 1.25, 1.5))
    if seismic:
        combos.append(("Seismic: 1.0G + 1.0E + 0.3Q", 1.0*dead + 1.0*seismic + 0.3*live, 1.0, 1.0))
    return combos

def eurocode_sls_combinations(dead, live, wind=0, snow=0):
    combos = []
    combos.append(("Characteristic: G + Q", dead + live))
    combos.append(("Frequent: G + ψ1Q", dead + 0.5*live))
    combos.append(("Quasi-permanent: G + ψ2Q", dead + 0.3*live))
    if wind:
        combos.append(("Characteristic: G + W", dead + wind))
        combos.append(("Frequent: G + ψ1W", dead + 0.2*wind))
    if snow:
        combos.append(("Characteristic: G + S", dead + snow))
        combos.append(("Frequent: G + ψ1S", dead + 0.2*snow))
    return combos