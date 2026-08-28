# engineering/materials.py
CONCRETE_GRADES = {
    "C20/25": {"fck": 20.0, "fcm": 28.0, "Ecm": 30e3},
    "C25/30": {"fck": 25.0, "fcm": 33.0, "Ecm": 31e3},
    "C30/37": {"fck": 30.0, "fcm": 38.0, "Ecm": 33e3},
    "C35/45": {"fck": 35.0, "fcm": 43.0, "Ecm": 34e3},
    "C40/50": {"fck": 40.0, "fcm": 48.0, "Ecm": 35e3},
    "C45/55": {"fck": 45.0, "fcm": 53.0, "Ecm": 36e3},
    "C50/60": {"fck": 50.0, "fcm": 58.0, "Ecm": 37e3},
}

STEEL_GRADES = {
    "S235": {"fy": 235.0, "fu": 360.0, "E": 210e3},
    "S275": {"fy": 275.0, "fu": 430.0, "E": 210e3},
    "S355": {"fy": 355.0, "fu": 510.0, "E": 210e3},
    "S450": {"fy": 440.0, "fu": 550.0, "E": 210e3},
    "S460": {"fy": 460.0, "fu": 540.0, "E": 210e3},
}

TIMBER_CLASSES = {
    "C14": {"fm_k": 14.0, "fv_k": 2.0, "E0_mean": 7e3},
    "C16": {"fm_k": 16.0, "fv_k": 2.0, "E0_mean": 8e3},
    "C18": {"fm_k": 18.0, "fv_k": 2.2, "E0_mean": 9e3},
    "C24": {"fm_k": 24.0, "fv_k": 2.5, "E0_mean": 11e3},
    "C30": {"fm_k": 30.0, "fv_k": 3.0, "E0_mean": 12e3},
    "GL24h": {"fm_k": 24.0, "fv_k": 2.7, "E0_mean": 11.5e3},
    "GL28h": {"fm_k": 28.0, "fv_k": 3.2, "E0_mean": 12.6e3},
    "GL32h": {"fm_k": 32.0, "fv_k": 3.8, "E0_mean": 13.7e3},
}

WALL_TYPES = {
    "Brick cavity": {"weight": 2.5, "U": 1.4, "sound": 45},
    "Concrete block": {"weight": 3.5, "U": 1.8, "sound": 50},
    "Timber frame": {"weight": 1.5, "U": 0.35, "sound": 40},
    "Insulated panel": {"weight": 0.8, "U": 0.25, "sound": 35},
    "Solid brick": {"weight": 4.5, "U": 2.0, "sound": 55},
    "AAC block": {"weight": 2.0, "U": 0.8, "sound": 42},
}

FINISHES = {
    "Plaster (internal)": 0.3,
    "Paint": 0.05,
    "Ceramic tiles": 0.4,
    "Carpet": 0.1,
    "Screed": 0.5,
    "Timber flooring": 0.25,
    "Stone flooring": 0.6,
    "Suspended ceiling": 0.15,
}