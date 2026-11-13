# Calculate PI-based horizontal alignments using entry spirals, arcs, and exit spirals.
import sys, numpy as np
sys.path.insert(0, '/home/claude/v2')
import geom
from geom import corner_speed, T_ONSET

def spiral_params(R, Ls):
    p = Ls**2 / (24 * R)                       # Shift of the arc from the tangent.
    k = Ls / 2 - Ls**3 / (240 * R**2)          # Distance from TS to the shifted PC.
    return p, k

def tangent_length(R, Ls, D):
    p, k = spiral_params(R, Ls)
    return (R + p) * np.tan(D / 2) + k

def analyse(PIS, verbose=True):
    n = len(PIS)
    P = np.array([[p[1], p[2]] for p in PIS], float)
    rows = []
    for i in range(n):
        a, b, c = P[i - 1], P[i], P[(i + 1) % n]
        u, w = b - a, c - b
        h_in, h_out = np.arctan2(u[1], u[0]), np.arctan2(w[1], w[0])
        d = (h_in - h_out + np.pi) % (2 * np.pi) - np.pi  # Positive is a clockwise turn.
        name, R, bank = PIS[i][0], PIS[i][3], PIS[i][4]
        v = corner_speed(R, bank)
        Ls = max(15.0, v * T_ONSET)
        D = abs(d)
        if D * R - Ls < 5:  # Reduce spiral length when the turn is too tight.
            Ls = 0.5 * D * R
        Ts = tangent_length(R, Ls, D)
        rows.append(dict(name=name, R=R, bank=bank, dfl=np.degrees(d), Ls=Ls, Ts=Ts))
    ok = True
    straights = []
    for i in range(n):
        j = (i + 1) % n
        dist = np.hypot(*(P[j] - P[i]))
        L = dist - rows[i]['Ts'] - rows[j]['Ts']
        straights.append(L)
        if L < 20:
            ok = False
            if verbose: print(f"  !! straight {rows[i]['name']} -> {rows[j]['name']} = {L:.0f} m (needs >= 20)")
    tot = sum(r['dfl'] for r in rows)
    if verbose:
        print(f"sum of deflections {tot:+.1f} deg (+360 = clockwise)")
    return rows, straights, ok

def to_layout(PIS, rows, straights, grades, labels):
    lay = []
    n = len(PIS)
    # Start at the corner before the pit straight so the straight is element 0.
    for i in range(n):
        lay.append(('S', straights[i - 1], grades[i - 1], labels[i - 1]))  # Straight leading into corner i.
        r = rows[i]
        lay.append(('C', r['name'], r['dfl'], r['R'], r['bank']))
    return lay
