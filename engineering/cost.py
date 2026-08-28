# engineering/cost.py

def calculate_total_area(plan):
    total = 0
    for room in plan:
        total += room["w"] * room["h"] / 1e6
    return total

def compute_floor_loads(plan, live_load_kN_per_m2, slab_thickness_m, additional_dead_load_kN_per_m2):
    area = calculate_total_area(plan)
    concrete_density = 25
    dead = slab_thickness_m * concrete_density + additional_dead_load_kN_per_m2
    total_load = (dead + live_load_kN_per_m2) * area
    return total_load

def check_structural_integrity(plan):
    max_span_mm = 0
    for room in plan:
        span = max(room["w"], room["h"])
        if span > max_span_mm:
            max_span_mm = span
    max_span_m = max_span_mm / 1000
    if max_span_m <= 4:
        beam = "IPE 160"
    elif max_span_m <= 6:
        beam = "IPE 220"
    elif max_span_m <= 8:
        beam = "IPE 300"
    else:
        beam = "RC beam or truss"
    pass_flag = max_span_m <= 8
    return {"pass": pass_flag, "max_span_m": max_span_m, "suggested_beam": beam}

def calculate_energy_score(plan, glazing_ratio=0.2, orientation="south"):
    area = calculate_total_area(plan)
    score = max(0, 100 - area*0.5 - glazing_ratio*50)
    return score

def estimate_cost(plan):
    area = calculate_total_area(plan)
    concrete_rate = 150
    steel_rate = 80
    glass_rate = 120
    labor_rate = 100
    concrete_cost = area * concrete_rate
    steel_cost = area * steel_rate
    glass_cost = area * glass_rate * 0.2
    labor_cost = area * labor_rate
    total = concrete_cost + steel_cost + glass_cost + labor_cost
    return {
        "concrete": concrete_cost,
        "steel": steel_cost,
        "glass": glass_cost,
        "labor": labor_cost,
        "total": total,
    }