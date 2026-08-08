# utils.py (append after existing functions)

def render_svg_plan_with_grid(plan, width=800, height=500,
                              show_grid=False, grid_spacing_mm=1000,
                              show_north=False, orientation="north"):
    """
    Render plan as SVG with optional grid and north arrow.
    grid_spacing_mm: distance between grid lines in the plan's unit (mm).
    """
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" style="width:100%; background:#0F172A;">'

    # ---- Grid lines ----
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

    # ---- Rooms ----
    for item in plan:
        x, y, w, h = item["x"], item["y"], item["w"], item["h"]
        color = item.get("color", "#4f46e5")
        name = item["name"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        svg += f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{color}" fill-opacity="0.4" stroke="#94a3b8" stroke-width="2"/>'
        svg += f'<text x="{x+w/2}" y="{y+h/2}" font-size="12" fill="white" text-anchor="middle" dominant-baseline="middle">{name}</text>'

    # ---- North arrow ----
    if show_north:
        # Draw a simple arrow at top-right corner
        arrow_x = width - 60
        arrow_y = 30
        svg += f'''
        <g transform="translate({arrow_x},{arrow_y})">
            <!-- Arrow shaft -->
            <line x1="0" y1="20" x2="0" y2="0" stroke="#FBBF24" stroke-width="3"/>
            <!-- Arrow head -->
            <polygon points="-6,8 0,0 6,8" fill="#FBBF24"/>
            <!-- N label -->
            <text x="0" y="30" text-anchor="middle" font-size="14" fill="#FBBF24" font-weight="bold">N</text>
        </g>
        '''
        # Optionally rotate the whole arrow according to orientation.
        # If orientation != "north", we could rotate, but for simplicity
        # we just show a static north arrow for reference.
        # You could add a rotation transform if needed.

    svg += '</svg>'
    return svg