# Build a terrain-fitted circuit and analyse its layout, earthworks, and lap performance.
import sys, numpy as np
sys.path.insert(0, '/home/claude/v3')
from scipy.interpolate import CubicSpline
from shapely.geometry import LineString, Polygon, Point
import base as B
import geom
from geom import corner_speed, T_ONSET
G = 9.8
CARS = {5: dict(name='Car 5 Grip Specialist', m=850, vmax=300/3.6, a0=7.0, b=38.0, mu=1.00),
        4: dict(name='Car 4 Traction+Braking', m=860, vmax=295/3.6, a0=7.8, b=42.0, mu=0.85)}
for c in CARS.values():
    c['k'] = c['m']*c['a0']/c['vmax']**2; c['CdA'] = 2*c['k']/1.2

def _ts(R, Ls, D):
    p = Ls**2/(24*R); k = Ls/2 - Ls**3/(240*R**2)
    return (R + p)*np.tan(D/2) + k

def _corner(R, bank, D):
    v = corner_speed(R, bank); Ls = max(15.0, v*T_ONSET)
    if D*R - Ls < 5: Ls = 0.5*D*R
    return Ls, _ts(R, Ls, D)

# Solve corner positions and straight lengths from PI data and the start-line definition.
# Each PI is [name, easting, northing, radius, bank].
# The first and last PIs are positioned to give the start straight its requested length and bearing.
def solve_pis(pis, start):
    br = np.radians(start['brg']); u = np.array([np.sin(br), np.cos(br)]); P0 = np.array([start['e'], start['n']])
    P = np.array([[p[1], p[2]] for p in pis], float)
    n = len(pis); ts_first = ts_last = 60.0
    for _ in range(25):
        P[0] = P0 + (start['L'] + ts_first)*u
        P[-1] = P0 - ts_last*u
        rows = []
        for i in range(n):
            a, b, c = P[i-1], P[i], P[(i+1) % n]
            h_in = np.arctan2(*(b - a)[::-1]); h_out = np.arctan2(*(c - b)[::-1])
            d = (h_in - h_out + np.pi) % (2*np.pi) - np.pi
            Ls, Ts = _corner(pis[i][3], pis[i][4], abs(d))
            rows.append(dict(name=pis[i][0], R=pis[i][3], bank=pis[i][4], dfl=np.degrees(d), Ls=Ls, Ts=Ts))
        if abs(rows[0]['Ts'] - ts_first) < 1e-6 and abs(rows[-1]['Ts'] - ts_last) < 1e-6: break
        ts_first, ts_last = rows[0]['Ts'], rows[-1]['Ts']
    L = [np.hypot(*(P[(i+1) % n] - P[i])) - rows[i]['Ts'] - rows[(i+1) % n]['Ts'] for i in range(n)]
    return P, rows, L  # L[i] is the straight after corner i; L[-1] is the start straight.

class Circuit:
    def __init__(self, key, pis, start=None, ds=1.0):
        self.key = key; self.start = start or B.STARTS[key]; self.pis_in = pis
        P, rows, L = solve_pis(pis, self.start)
        self.P, self.rows, self.Lstr = P, rows, L
        self.min_straight = min(L); self.sum_dfl = sum(r['dfl'] for r in rows)
        lay = [('S', L[-1], 0, 'Start straight')]
        for i, r in enumerate(rows):
            lay.append(('C', r['name'], r['dfl'], r['R'], r['bank']))
            if i < len(rows) - 1: lay.append(('S', max(L[i], 0.5), 0, ''))
        X, Y, TH, K, T, El = geom.build(lay, [max(e[1], 0.5) for e in lay if e[0] == 'S'])
        th0 = np.pi/2 - np.radians(self.start['brg'])
        c, s_ = np.cos(th0), np.sin(th0)
        Xe = self.start['e'] + X*c - Y*s_; Yn = self.start['n'] + X*s_ + Y*c
        S = np.concatenate([[0], np.cumsum(np.hypot(np.diff(Xe), np.diff(Yn)))])
        self.gap = float(np.hypot(Xe[-1] - Xe[0], Yn[-1] - Yn[0]))
        self.LAP = S[-1]; N = int(round(self.LAP/ds))
        self.s = np.linspace(0, self.LAP, N + 1)
        self.x = np.interp(self.s, S, Xe); self.y = np.interp(self.s, S, Yn)
        self.kap = np.interp(self.s, S[1:], K[1:])
        self.corners = [e for e in El if e['kind'] == 'C']; self.straights = [e for e in El if e['kind'] == 'S']
        for e in El:
            e['s0'], e['s1'] = S[e['i0']], S[e['i1']]; e['s_apex'] = 0.5*(e['s0'] + e['s1'])
        tx, ty = np.gradient(self.x), np.gradient(self.y); nn = np.hypot(tx, ty)
        self.nx, self.ny = -ty/nn, tx/nn  # Unit left normal.
        self.bank = np.zeros_like(self.s)
        for c_ in self.corners:
            if c_['bank'] > 0:
                m = (self.s >= c_['s0']) & (self.s <= c_['s1']); self.bank[m] = c_['bank']*np.abs(self.kap[m])*c_['R']
        self.line = LineString(np.c_[self.x, self.y])

    # Design the vertical profile.
    def drape(self, gmax=0.08, flat=(0.0, None), step=10.0, half_w=9.0, rv_sag=1200.0, rv_crest=1500.0, z_flat=None, w_bal=0.0, z_min=()):
        # Fit the design profile to ground while limiting grade and vertical curvature.
        # Minimise earthworks, and keep the start section level.
        import cvxpy as cp
        s, LAP = self.s, self.LAP
        offs = np.linspace(-half_w, half_w, 7)
        zg_x = np.array([B.ground(self.x + o*self.nx, self.y + o*self.ny) for o in offs])
        self.zg_cross, self.offs = zg_x, offs
        self.zg = zg_x.mean(axis=0)
        n = int(round(LAP/step)); h = LAP/n; sc = np.arange(n)*h
        zg_c = np.interp(sc, s, self.zg)
        f0, f1 = flat[0], (flat[1] if flat[1] is not None else self.start['L'])
        idx = np.where((sc >= f0 - 1e-6) & (sc <= f1 + 1e-6))[0]
        z = cp.Variable(n)
        d1 = cp.hstack([z[1:] - z[:-1], z[0:1] - z[n-1:n]])/h
        d2 = (cp.hstack([z[1:], z[0:1]]) - 2*z + cp.hstack([z[n-1:n], z[:-1]]))/h**2
        hh = z - zg_c
        obj = cp.sum(18*cp.abs(hh) + 2*cp.square(hh)) + 2e5*cp.sum_squares(d2*h) + w_bal*cp.square(cp.sum(hh))
        cons = [cp.abs(d1) <= gmax, d2 <= 1.0/rv_sag, d2 >= -1.0/rv_crest, z[idx[1:]] == z[idx[0]]]
        # Extend the level section beyond its ends so the vertical curve begins off the straight.
        if z_flat is not None: cons.append(z[idx[0]] == z_flat)
        for (s_c, lev, half) in z_min:
            ii = np.where(np.abs(sc - s_c) <= half)[0]
            cons.append(z[ii] >= lev)
        prob = cp.Problem(cp.Minimize(obj), cons); prob.solve(solver=cp.CLARABEL)
        if z.value is None: prob.solve(solver=cp.SCS)
        zv = np.asarray(z.value).ravel(); self.lam = prob.value
        sp = CubicSpline(np.r_[sc, LAP], np.r_[zv, zv[0]], bc_type='periodic')
        self.z = sp(s); self.grade = sp(s, 1); zpp = sp(s, 2)
        m = (s >= f0) & (s <= f1); self.z_flat = float(zv[idx[0]])
        self.z[m] = self.z_flat; self.grade[m] = 0.0; zpp[m] = 0.0
        self.kv = zpp/(1 + self.grade**2)**1.5
        return self

    def earthworks(self, batter=2.0):
        # Calculate cut and fill per metre across the formation and side batters.
        dw = self.offs[1] - self.offs[0]
        h = self.z[None, :] - self.zg_cross  # Positive is fill; negative is cut.
        fill = np.clip(h, 0, None); cut = np.clip(-h, 0, None)
        wts = np.ones(len(self.offs)); wts[0] = wts[-1] = 0.5
        a_fill = (fill*wts[:, None]).sum(0)*dw + 0.5*batter*(fill[0]**2 + fill[-1]**2)
        a_cut = (cut*wts[:, None]).sum(0)*dw + 0.5*batter*(cut[0]**2 + cut[-1]**2)
        ds = np.gradient(self.s)
        self.a_cut, self.a_fill = a_cut, a_fill
        self.cut, self.fill = float((a_cut*ds).sum()), float((a_fill*ds).sum())
        self.h_c = self.z - self.zg
        return self.cut, self.fill

    # Simulate a lap.
    def simulate(self, car, use_bank=True):
        s, kap, grade, kv = self.s, self.kap, self.grade, self.kv
        mu, b, vmax = car['mu'], car['b'], car['vmax']
        t = np.tan(np.radians(self.bank if use_bank else 0*self.bank)); ak = np.abs(kap)
        num = G*(mu + t); den = ak*(1 - mu*t) - mu*kv
        vlim = np.where(den > 1e-9, np.sqrt(np.maximum(num/np.maximum(den, 1e-9), 0)), vmax)
        vlim = np.minimum(vlim, vmax); n = len(s); h = np.diff(s); sin_g = grade/np.sqrt(1 + grade**2)
        amax = lambda v, i: mu*(G + v**2*kv[i]) + G*t[i]*(1 + mu*t[i])
        v = vlim.copy()
        for _ in range(3):
            for i in range(n - 1):
                vi = v[i]; f = np.sqrt(max(0.0, 1 - (vi**2*ak[i]/max(amax(vi, i), 1e-6))**2))
                a = car['a0']*(1 - (vi/vmax)**2)*f - G*sin_g[i]
                v[i+1] = min(v[i+1], np.sqrt(max(vi**2 + 2*a*h[i], 1.0)))
            v[0] = min(v[0], v[-1])
            for i in range(n - 1, 0, -1):
                vi = v[i]; f = np.sqrt(max(0.0, 1 - (vi**2*ak[i]/max(amax(vi, i), 1e-6))**2))
                d = b*f + G*sin_g[i]
                v[i-1] = min(v[i-1], np.sqrt(vi**2 + 2*max(d, 0.1)*h[i-1]))
            v[-1] = min(v[-1], v[0])
        dt = h/(0.5*(v[1:] + v[:-1])); tt = np.r_[0, np.cumsum(dt)]; acc = np.r_[0, np.diff(v)/dt]
        be = sum(car['m']*max(0, -a - G*sg)*hh for a, sg, hh in zip(acc[1:], sin_g[1:], h) if a < -1.0)/3.6e6
        return dict(v=v, t=tt, lap=tt[-1], acc=acc, vlim=vlim, brake_kWh=be)

    # Check track boundaries and clearances.
    def inside_margin(self, margin=25.0):
        # Return the track length outside the parcel after applying the margin.
        inner = B.PARCEL.buffer(-margin)
        out = self.line.difference(inner)
        return out.length

    def self_clearance(self, min_along=250.0, step=5):
        idx = np.arange(0, len(self.s), step); best = 1e9
        X, Y, S = self.x[idx], self.y[idx], self.s[idx]
        for a in range(len(idx)):
            d = np.hypot(X - X[a], Y - Y[a]); gap = np.abs(S - S[a]); gap = np.minimum(gap, self.LAP - gap)
            d[gap < min_along] = 1e9; best = min(best, d.min())
        return best
