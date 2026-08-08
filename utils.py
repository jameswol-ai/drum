# utils.py
import streamlit as st
import json

def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, .stApp {
        font-family: 'Inter', sans-serif;
        background: #0F172A; color: #E2E8F0;
    }
    h1, h2, h3 { color: #F8FAFC; font-weight: 600; }
    .sidebar .sidebar-content { background: #1E293B; }
    .stButton>button {
        background: linear-gradient(135deg, #3B82F6, #2563EB);
        color: white; border: none; border-radius: 8px;
        padding: 0.5rem 1.5rem; font-weight: 600; transition: 0.2s;
    }
    .stButton>button:hover { transform: scale(1.02); }
    .metric-card {
        background: #1E293B; border-radius: 12px; padding: 1rem;
        border: 1px solid #334155;
    }
    .stNumberInput>div>div>input {
        background: #1E293B; color: #F8FAFC; border: 1px solid #475569;
    }
    .stSelectbox>div>div>select {
        background: #1E293B; color: #F8FAFC;
    }
    </style>
    """, unsafe_allow_html=True)

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
    """Simple plan without grid (used in archives)."""
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" style="width:100%; background:#0F172A;">'
    for item in plan:
        x, y, w, h = item["x"], item["y"], item["w"], item["h"]
        color = item.get("color", "#4f46e5")
        name = item["name"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        svg += f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{color}" fill-opacity="0.4" stroke="#94a3b8" stroke-width="2"/>'
        svg += f'<text x="{x+w/2}" y="{y+h/2}" font-size="12" fill="white" text-anchor="middle" dominant-baseline="middle">{name}</text>'
    svg += '</svg>'
    return svg

def render_svg_plan_with_grid(plan, width=800, height=500,
                              show_grid=False, grid_spacing_mm=1000,
                              show_north=False, orientation="north"):
    """Plan with optional grid and north arrow."""
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" style="width:100%; background:#0F172A;">'

    if show_grid and grid_spacing_mm > 0:
        # Vertical lines
        x = 0
        while x <= width:
            svg += f'<line x1="{x}" y1="0" x2="{x}" y2="{height}" stroke="#334155" stroke-width="0.5" stroke-dasharray="4,4"/>'
            x += grid_spacing_mm
        # Horizontal lines
        y = 0
        while y <= height:
            svg += f'<line x1="0" y1="{y}" x2="{width}" y2="{y}" stroke="#334155" stroke-width="0.5" stroke-dasharray="4,4"/>'
            y += grid_spacing_mm

    for item in plan:
        x, y, w, h = item["x"], item["y"], item["w"], item["h"]
        color = item.get("color", "#4f46e5")
        name = item["name"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        svg += f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{color}" fill-opacity="0.4" stroke="#94a3b8" stroke-width="2"/>'
        svg += f'<text x="{x+w/2}" y="{y+h/2}" font-size="12" fill="white" text-anchor="middle" dominant-baseline="middle">{name}</text>'

    if show_north:
        arrow_x = width - 60
        arrow_y = 30
        # Rotate if orientation is not north (simple example: rotate 90° for east, etc.)
        rotation_map = {"north": 0, "east": 90, "south": 180, "west": 270}
        angle = rotation_map.get(orientation, 0)
        svg += f'''
        <g transform="translate({arrow_x},{arrow_y}) rotate({angle})">
            <line x1="0" y1="20" x2="0" y2="0" stroke="#FBBF24" stroke-width="3"/>
            <polygon points="-6,8 0,0 6,8" fill="#FBBF24"/>
            <text x="0" y="30" text-anchor="middle" font-size="14" fill="#FBBF24" font-weight="bold">N</text>
        </g>
        '''

    svg += '</svg>'
    return svg

def generate_3d_html(plan):
    if not plan:
        return "<p>No plan data.</p>"
    rooms_js = ""
    for room in plan:
        x = room["x"] / 1000
        z = room["y"] / 1000
        w = room["w"] / 1000
        d = room["h"] / 1000
        h = 3.0
        color = room.get("color", "#4f46e5")
        rooms_js += f"""
            geometry = new THREE.BoxGeometry({json.dumps(w)}, {json.dumps(h)}, {json.dumps(d)});
            material = new THREE.MeshPhongMaterial({{color: {json.dumps(color)}, opacity: 0.7, transparent: true}});
            cube = new THREE.Mesh(geometry, material);
            cube.position.set({json.dumps(x + w/2)}, {json.dumps(h/2)}, {json.dumps(z + d/2)});
            scene.add(cube);
        """
    html = f"""
    <html>
    <head>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
    </head>
    <body style="margin:0; overflow:hidden;">
        <script>
            var scene = new THREE.Scene();
            scene.background = new THREE.Color(0x0f172a);
            var camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 100);
            camera.position.set(8, 6, 10);
            var renderer = new THREE.WebGLRenderer();
            renderer.setSize(window.innerWidth, window.innerHeight);
            document.body.appendChild(renderer.domElement);
            var controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.target.set(4, 1.5, 2.5);
            controls.update();
            var light = new THREE.DirectionalLight(0xffffff, 1);
            light.position.set(5, 10, 7);
            scene.add(light);
            var ambient = new THREE.AmbientLight(0x404040);
            scene.add(ambient);
            var geometry, material, cube;
            {rooms_js}
            function animate() {{
                requestAnimationFrame(animate);
                controls.update();
                renderer.render(scene, camera);
            }}
            animate();
        </script>
    </body>
    </html>
    """
    return html