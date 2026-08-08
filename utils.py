import streamlit as st

# ---------- CSS ----------
def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, .stApp { font-family: 'Inter', sans-serif; background: #0F172A; color: #E2E8F0; }
    h1, h2, h3 { color: #F8FAFC; font-weight: 600; }
    .sidebar .sidebar-content { background: #1E293B; }
    .stButton>button {
        background: linear-gradient(135deg, #3B82F6, #2563EB);
        color: white; border: none; border-radius: 8px;
        padding: 0.5rem 1.5rem; font-weight: 600; transition: 0.2s;
    }
    .stButton>button:hover { transform: scale(1.02); }
    .metric-card {
        background: #1E293B; border-radius: 12px; padding: 1rem; border: 1px solid #334155;
    }
    .stNumberInput>div>div>input { background: #1E293B; color: #F8FAFC; border: 1px solid #475569; }
    .stSelectbox>div>div>select { background: #1E293B; color: #F8FAFC; }
    </style>
    """, unsafe_allow_html=True)

# ---------- Unit Helpers ----------
def input_metric(value, unit_type):
    if st.session_state.unit_system == "imperial":
        conversions = {
            "length": 0.3048, "length_mm": 0.0254, "area": 0.092903,
            "force": 4.44822, "pressure": 6.89476, "moment": 1.35582,
            "weight_density": 0.157087
        }
        if unit_type in conversions:
            return value * conversions[unit_type]
    return value

def output_metric(value, unit_type):
    if st.session_state.unit_system == "imperial":
        conversions = {
            "length": 3.28084, "length_mm": 39.3701, "area": 10.7639,
            "force": 0.224809, "pressure": 0.145038, "moment": 0.737562,
            "weight_density": 6.36588, "stress": 0.145038
        }
        if unit_type in conversions:
            return value * conversions[unit_type]
    return value

def unit_label(unit_type):
    labels = {
        "length": "m" if st.session_state.unit_system == "metric" else "ft",
        "length_mm": "mm" if st.session_state.unit_system == "metric" else "in",
        "area": "m²" if st.session_state.unit_system == "metric" else "ft²",
        "force": "kN" if st.session_state.unit_system == "metric" else "kip",
        "pressure": "kPa" if st.session_state.unit_system == "metric" else "psi",
        "moment": "kNm" if st.session_state.unit_system == "metric" else "kip-ft",
        "weight_density": "kN/m³" if st.session_state.unit_system == "metric" else "pcf",
        "stress": "MPa" if st.session_state.unit_system == "metric" else "ksi",
    }
    return labels.get(unit_type, "")

def render_svg_plan(plan, width=800, height=500):
    # ... same as before ...
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" style="width:100%; background:#0F172A;">'
    for item in plan:
        x, y, w, h = item["x"], item["y"], item["w"], item["h"]
        color = item.get("color", "#4f46e5")
        svg += f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{color}" fill-opacity="0.4" stroke="#94a3b8" stroke-width="2"/>'
        svg += f'<text x="{x+w/2}" y="{y+h/2}" font-size="12" fill="white" text-anchor="middle" dominant-baseline="middle">{item["name"]}</text>'
    svg += '</svg>'
    return svg

def generate_3d_html(plan):
    # ... entire Three.js builder, safely injecting values ...
    pass