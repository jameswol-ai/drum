# eurocodes/en1991.py
def en1991_imposed_loads(building_type="residential"):
    loads = {
        "residential": 2.0,
        "office": 3.0,
        "assembly": 5.0,
        "retail": 4.0,
        "storage": 7.5,
        "industrial": 5.0,
    }
    return loads.get(building_type, 2.0)

def en1991_snow_load(region="UK", altitude_m=0):
    base_snow = 0.5
    altitude_factor = altitude_m / 1000
    return base_snow + altitude_factor

def en1991_wind_load(basic_wind_speed, terrain_category="II", height_m=10):
    terrain_factors = {"0": 1.2, "I": 1.0, "II": 0.8, "III": 0.6, "IV": 0.5}
    k = terrain_factors.get(terrain_category, 0.8)
    q_p = 0.613 * (basic_wind_speed * k)**2 / 1000  # kPa
    return q_p