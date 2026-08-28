# engineering/visualization.py
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def plot_beam_diagrams(beam_type, span_m, load_type, load_value, point_load_pos=None):
    x = [i/100 for i in range(int(span_m*100)+1)]
    V = [0]*len(x)
    M = [0]*len(x)
    L = span_m

    if beam_type == 'simply_supported':
        if load_type == 'udl':
            w = load_value
            R1 = R2 = w * L / 2
        elif load_type == 'point':
            P = load_value
            a = point_load_pos if point_load_pos else L/2
            b = L - a
            R1 = P * b / L
            R2 = P * a / L
        else:
            R1 = R2 = 0
        for i, xi in enumerate(x):
            V[i] = R1
            if load_type == 'udl':
                V[i] -= w * xi
            elif load_type == 'point':
                if xi >= a:
                    V[i] -= P
            M[i] = R1 * xi
            if load_type == 'udl':
                M[i] -= w * xi**2 / 2
            elif load_type == 'point' and xi >= a:
                M[i] -= P * (xi - a)

    elif beam_type == 'cantilever':
        if load_type == 'udl':
            w = load_value
            for i, xi in enumerate(x):
                V[i] = w * xi
                M[i] = -w * xi**2 / 2
        elif load_type == 'point':
            P = load_value
            a = point_load_pos if point_load_pos else L
            for i, xi in enumerate(x):
                if xi >= a:
                    V[i] = -P
                    M[i] = -P * (xi - a)
                else:
                    V[i] = 0
                    M[i] = 0
        else:
            V = [0]*len(x)
            M = [0]*len(x)
    else:
        return None

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6))
    ax1.plot(x, V, 'b-', linewidth=2)
    ax1.set_title("Shear Force Diagram")
    ax1.set_xlabel("Position (m)")
    ax1.set_ylabel("Shear (kN)")
    ax1.grid(True)

    ax2.plot(x, M, 'r-', linewidth=2)
    ax2.set_title("Bending Moment Diagram")
    ax2.set_xlabel("Position (m)")
    ax2.set_ylabel("Moment (kNm)")
    ax2.grid(True)
    plt.tight_layout()
    return fig

def plot_truss_deformed(nodes, elements, displacements, scale_factor=50):
    fig, ax = plt.subplots(figsize=(8,6))
    for nid, (x,y) in nodes.items():
        ax.plot(x, y, 'ko', markersize=5)
        ax.text(x, y, f' {nid}', fontsize=9)
    for (n1,n2,_,_) in elements:
        x1,y1 = nodes[n1]
        x2,y2 = nodes[n2]
        ax.plot([x1,x2], [y1,y2], 'b-', linewidth=1.5, label='Original' if n1==1 and n2==2 else "")
    for nid, (x,y) in nodes.items():
        ux,uy = displacements.get(nid, (0,0))
        xd = x + ux * scale_factor
        yd = y + uy * scale_factor
        ax.plot(xd, yd, 'ro', markersize=5)
    for (n1,n2,_,_) in elements:
        x1,y1 = nodes[n1]
        x2,y2 = nodes[n2]
        ux1,uy1 = displacements.get(n1, (0,0))
        ux2,uy2 = displacements.get(n2, (0,0))
        xd1 = x1 + ux1 * scale_factor
        yd1 = y1 + uy1 * scale_factor
        xd2 = x2 + ux2 * scale_factor
        yd2 = y2 + uy2 * scale_factor
        ax.plot([xd1,xd2], [yd1,yd2], 'r--', linewidth=1.5, label='Deformed' if n1==1 and n2==2 else "")
    ax.set_aspect('equal', adjustable='box')
    ax.grid(True)
    ax.set_xlabel('X (mm)')
    ax.set_ylabel('Y (mm)')
    ax.set_title('Truss Deformation (exaggerated)')
    ax.legend()
    return fig