# engineering/connections.py

def steel_connection_check(connection_type, bolt_dia, bolt_grade, num_bolts, plate_thickness, weld_size, load):
    if connection_type == "bolted":
        fub = {"4.6": 400, "8.8": 800, "10.9": 1000}.get(bolt_grade, 800)
        As = (3.14159 * bolt_dia**2) / 4
        shear_capacity = 0.6 * fub * As / 1000
        total_shear = shear_capacity * num_bolts
        fu_plate = 360
        bearing_capacity = 2.5 * fu_plate * plate_thickness * bolt_dia / 1000
        total_bearing = bearing_capacity * num_bolts
        capacity = min(total_shear, total_bearing)
        return {
            "shear_capacity_per_bolt": shear_capacity,
            "total_shear_capacity": total_shear,
            "bearing_capacity_per_bolt": bearing_capacity,
            "total_bearing_capacity": total_bearing,
            "design_capacity": capacity,
            "status": "OK" if load <= capacity else "FAIL",
            "utilization": load / capacity if capacity > 0 else 0
        }
    elif connection_type == "welded":
        fu_weld = 360
        throat = 0.7 * weld_size
        weld_length = 400
        capacity_per_mm = 0.6 * fu_weld * throat
        total_capacity = capacity_per_mm * weld_length / 1000
        return {
            "capacity_per_mm": capacity_per_mm / 1000,
            "total_capacity": total_capacity,
            "status": "OK" if load <= total_capacity else "FAIL",
            "utilization": load / total_capacity if total_capacity > 0 else 0
        }
    else:
        return {"error": "Invalid connection type"}