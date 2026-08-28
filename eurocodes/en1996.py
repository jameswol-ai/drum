# eurocodes/en1996.py

def en1996_masonry_wall_design(wall_thickness_mm, wall_height_m, fk_mpa, N_ed_kN_per_m, M_ed_kNm_per_m=0):
    """
    Simplified masonry wall design per EN 1996.
    """
    t = wall_thickness_mm / 1000
    if t <= 0:
        return {"pass": False, "error": "Wall thickness must be positive"}
    gamma_m = 2.0
    fd = fk_mpa / gamma_m
    N_rd = fd * t * 1000  # kN per meter
    utilization = N_ed_kN_per_m / N_rd if N_rd > 0 else 999
    slenderness = wall_height_m / t
    slenderness_limit = 27
    pass_slender = slenderness <= slenderness_limit
    return {
        "pass": utilization <= 1.0 and pass_slender,
        "N_rd_kn_per_m": N_rd,
        "utilization": utilization,
        "slenderness": slenderness,
        "slenderness_limit": slenderness_limit,
    }