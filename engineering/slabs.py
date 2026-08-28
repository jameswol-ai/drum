# engineering/slabs.py

def slab_thickness_estimate(span_m, support_type):
    if support_type == "simply_supported":
        return span_m / 20
    else:
        return span_m / 28