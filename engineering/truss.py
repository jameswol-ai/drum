# engineering/truss.py
import numpy as np

def truss_analysis(nodes, elements, loads, supports):
    n_nodes = len(nodes)
    dof = 2 * n_nodes
    K = np.zeros((dof, dof))
    node_indices = {nid: i for i, nid in enumerate(nodes.keys())}

    for idx, (n1, n2, E, A) in enumerate(elements):
        x1, y1 = nodes[n1]
        x2, y2 = nodes[n2]
        L = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        if L == 0:
            continue
        c = (x2 - x1) / L
        s = (y2 - y1) / L
        k = (E * A) / L
        k_local = k * np.array([
            [ c*c,  c*s, -c*c, -c*s],
            [ c*s,  s*s, -c*s, -s*s],
            [-c*c, -c*s,  c*c,  c*s],
            [-c*s, -s*s,  c*s,  s*s]
        ])
        i1, i2 = node_indices[n1], node_indices[n2]
        dofs = [2*i1, 2*i1+1, 2*i2, 2*i2+1]
        for a in range(4):
            for b in range(4):
                K[dofs[a], dofs[b]] += k_local[a, b]

    free_dofs = []
    fixed_dofs = []
    for nid, (sx, sy) in supports.items():
        i = node_indices[nid]
        if sx:
            fixed_dofs.append(2*i)
        else:
            free_dofs.append(2*i)
        if sy:
            fixed_dofs.append(2*i+1)
        else:
            free_dofs.append(2*i+1)
    all_dofs = set(range(dof))
    for d in fixed_dofs:
        all_dofs.discard(d)
    for d in free_dofs:
        all_dofs.add(d)
    free_dofs = sorted(list(all_dofs))

    F = np.zeros(dof)
    for nid, (fx, fy) in loads.items():
        i = node_indices[nid]
        F[2*i] = fx * 1000
        F[2*i+1] = fy * 1000

    if free_dofs:
        K_ff = K[np.ix_(free_dofs, free_dofs)]
        F_f = F[free_dofs]
        try:
            U_f = np.linalg.solve(K_ff, F_f)
        except np.linalg.LinAlgError:
            return {"error": "Stiffness matrix is singular – structure is unstable."}
    else:
        U_f = np.array([])

    U = np.zeros(dof)
    if free_dofs:
        U[free_dofs] = U_f

    reactions = {}
    for nid, (sx, sy) in supports.items():
        i = node_indices[nid]
        Rx = np.dot(K[2*i, :], U) - F[2*i]
        Ry = np.dot(K[2*i+1, :], U) - F[2*i+1]
        reactions[nid] = (Rx/1000, Ry/1000)

    forces = []
    for idx, (n1, n2, E, A) in enumerate(elements):
        x1, y1 = nodes[n1]
        x2, y2 = nodes[n2]
        L = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        if L == 0:
            forces.append(0.0)
            continue
        c = (x2 - x1) / L
        s = (y2 - y1) / L
        i1, i2 = node_indices[n1], node_indices[n2]
        u1 = U[2*i1]; v1 = U[2*i1+1]
        u2 = U[2*i2]; v2 = U[2*i2+1]
        delta = (u2 - u1)*c + (v2 - v1)*s
        N = (E * A / L) * delta
        forces.append(N/1000)

    disp = {nid: (U[2*i], U[2*i+1]) for nid, i in node_indices.items()}
    return {
        "displacements": disp,
        "forces": forces,
        "reactions": reactions
    }