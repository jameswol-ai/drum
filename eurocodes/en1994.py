# eurocodes/en1994.py
import math

def en1994_composite_beam_design(section, slab_thickness_mm, slab_width_mm, fck_mpa, fy_mpa, M_ed_kNm, V_ed_kN, span_m):
    sections = {
        "IPE 160": {"I": 8.69e6, "A": 2010, "h": 160},
        "IPE 220": {"I": 2.77e7, "A": 3340, "h": 220},
        "IPE 300": {"I": 8.36e7, "A": 5380, "