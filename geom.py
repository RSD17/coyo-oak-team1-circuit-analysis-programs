# Build circuit centrelines from straights and clothoid-arc-clothoid corners.
import numpy as np
from scipy.optimize import least_squares

DS = 1.0          # Integration step in metres.
T_ONSET = 0.5     # Steering onset time in seconds.
G = 9.8
MU_DESIGN = 1.00  # Car 5 grip used to size spirals.

# Corner entries contain name, deflection, radius, and banking.
# Straight entries contain type, length, grade, and label.
LAYOUT = [
    ('S', 820, -1.5, 'Pit Straight'),
    ('C', 'T1 Hunter',      +95,  38, 0.0),
    ('S', 130, -1.0, ''),
    ('C', 'T2 Bengalla',    -30, 160, 0.0),
    ('S', 230, -2.0, ''),
    ('C', 'T3 Dragline',    +40, 120, 0.0),
    ('S', 760, -4.0, 'Voidside'),
    ('C', 'T4 The Sweep',   +75, 320, 0.0),
    ('S', 200, -1.0, ''),
    ('C', 'T5 Wetland',     -55,  85, 0.0),
    ('S',  70,  0.0, ''),
    ('C', 'T6 Reedbed',     +50,  60, 0.0),
    ('S',  70,  0.0, ''),
    ('C', 'T7 Seam',        -80,  42, 0.0),
    ('S',  60,  0.0, ''),
    ('C', 'T8 Boxcut',     +120,  35, 0.0),
    ('S', 200,  0.0, ''),
    ('C', 'T9 Raidillon',   -25, 260, 0.0),
    ('S',  40,  4.0, ''),
    ('C', 'T10 Crest',      +35, 220, 0.0),
    ('S', 500,  7.0, 'Spoil Rise'),
    ('C', 'T11 Emplacement',+45, 180, 0.0),
    ('S',  30,  2.0, ''),
    ('C', 'T12 Plateau',    -55, 140, 0.0),
    ('S',  30,  1.0, ''),
    ('C', 'T13 Skyline',    +65, 120, 0.0),
    ('S', 350,  0.0, ''),
    ('C', 'T14 Conveyor',   -40, 130, 0.0),
    ('S', 150, -1.0, ''),
    ('C', 'T15 Mangoola',   +45,  55, 0.0),
    ('S', 120, -1.0, ''),
    ('C', 'T16 Panorama',   None, 110, 5.7),   # Solve the deflection to close the heading.
]


def corner_speed(R, bank_deg, mu=MU_DESIGN):
    t = np.tan(np.radians(bank_deg))
    return np.sqrt(G * R * (mu + t) / (1 - mu * t))


def resolve_layout(layout):
    out = [list(x) for x in layout]
    tot = sum(x[2] for x in out if x[0] == 'C' and x[2] is not None)
    for x in out:
        if x[0] == 'C' and x[2] is None:
            x[2] = 360.0 - tot
    return out


def build(layout, straights):
    # Step along the centreline and return geometry arrays and element metadata.
    xs, ys, ths, ks, tags = [0.0], [0.0], [0.0], [0.0], [-1]
    x = y = th = 0.0
    elems, si = [], 0

    def step(k, tag, ds=DS):
        nonlocal x, y, th
        th_mid = th - 0.5 * k * ds  # Right turns decrease the heading.
        x += ds * np.cos(th_mid); y += ds * np.sin(th_mid)
        th -= k * ds
        xs.append(x); ys.append(y); ths.append(th); ks.append(k); tags.append(tag)

    for idx, e in enumerate(layout):
        s0 = len(xs) - 1
        if e[0] == 'S':
            L = straights[si]; si += 1
            n = max(1, int(np.ceil(L / DS))); d = L / n
            for _ in range(n): step(0.0, idx, d)
            elems.append(dict(kind='S', idx=idx, label=e[3], grade=e[2], L=L, i0=s0, i1=len(xs) - 1))
        else:
            _, name, dfl, R, bank = e
            sgn = 1.0 if dfl > 0 else -1.0
            v = corner_speed(R, bank)
            Ls = max(15.0, v * T_ONSET)
            D = np.radians(abs(dfl))
            # Each spiral uses Ls/(2R) of the turn; the arc uses the remainder.
            arc = D * R - Ls
            if arc < 5.0:  # Shrink the spirals when the turn is too tight.
                Ls = 0.5 * D * R; arc = D * R - Ls
            kap = sgn / R
            n_s, n_a = max(1, int(np.ceil(Ls / DS))), max(1, int(np.ceil(arc / DS)))
            ds_s, ds_a = Ls / n_s, arc / n_a
            for i in range(n_s): step(kap * (i + 0.5) / n_s, idx, ds_s)
            for i in range(n_a): step(kap, idx, ds_a)
            for i in range(n_s): step(kap * (1 - (i + 0.5) / n_s), idx, ds_s)
            elems.append(dict(kind='C', idx=idx, label=name, dfl=dfl, R=R, bank=bank, Ls=Ls,
                              arc=arc, L=2 * Ls + arc, i0=s0, i1=len(xs) - 1, sgn=sgn))
    return (np.array(xs), np.array(ys), np.array(ths), np.array(ks), np.array(tags), elems)


def solve(layout=LAYOUT, target=5350.0, verbose=True):
    lay = resolve_layout(layout)
    base = np.array([e[1] for e in lay if e[0] == 'S'], float)
    labels = [e[3] for e in lay if e[0] == 'S']
    keep = np.array([3.0 if lab else 0.6 for lab in labels])

    def resid(sc):
        L = np.maximum(base * sc, 20.0)
        X, Y, TH, K, T, E = build(lay, L)
        lap = sum(e['L'] for e in E)
        return np.concatenate([[X[-1] * 50, Y[-1] * 50, (lap - target) / 4.0], keep * (sc - 1) * 60])

    sol = least_squares(resid, np.ones(len(base)), bounds=(0.35, 2.5), diff_step=1e-3)
    L = np.maximum(base * sol.x, 20.0)
    X, Y, TH, K, T, E = build(lay, L)
    if verbose:
        print(f"T16 deflection solved: {[e for e in lay if e[0]=='C'][-1][2]:+.1f} deg")
        print(f"closure: dx={X[-1]:.2f} dy={Y[-1]:.2f} m, heading {np.degrees(TH[-1]):+.2f} deg")
        print(f"lap = {sum(e['L'] for e in E):.1f} m")
    return lay, L, X, Y, TH, K, T, E


if __name__ == '__main__':
    lay, L, X, Y, TH, K, T, E = solve()
    for e in E:
        if e['kind'] == 'S':
            print(f"  S {e['L']:7.0f} m  {e['grade']:+.1f}%  {e['label']}")
        else:
            print(f"  C {e['label']:<17} {e['dfl']:+6.1f} deg  R={e['R']:<4} spiral {e['Ls']:4.0f}  arc {e['arc']:5.0f}")
    np.savez('centreline.npz', X=X, Y=Y, TH=TH, K=K, T=T)
