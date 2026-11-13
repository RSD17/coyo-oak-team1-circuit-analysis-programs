# Build both circuits with terrain profiles and lap simulations.
import sys; sys.path.insert(0, '/home/claude/v3')
import numpy as np, circuit as C, layouts, base as B
NAMES = {'W': ['Rise', 'Bench', 'Skyline', 'The Nose', 'Bengalla', 'Sump', 'Northgate', 'Boundary', 'Dragline', 'Boom',
               'Seam', 'Haul Road', 'Stockpile', 'Boxcut', 'Basin'],
         'E': ['Saddle', 'The Drop', 'Gully', 'Culvert', 'Shelf', 'Crest', 'Pocket', 'Mangoola', 'Step', 'Rim',
               'Overlook', 'Lakeside', 'Wetland', 'Conveyor']}
TITLE = {'W': 'Ridge Circuit (West)', 'E': 'Lakeside Circuit (East)'}
SF = 250.0                                   # Start/finish position along the start straight, in metres.
def build():
    out = {}
    for k in 'WE':
        pis = [[f"{p[0]} {NAMES[k][i]}"] + p[1:] for i, p in enumerate(getattr(layouts, k))]
        c = C.Circuit(k, pis)
        if k == 'W':
            # Keep the track at least 6.5 m above the low ground between T6 and T7.
            t6, t7 = c.corners[5], c.corners[6]
            m = (c.s > t6['s1']) & (c.s < t7['s0'])
            zg = B.ground(c.x[m], c.y[m]); i = np.argmin(zg); s_u = c.s[m][i]; lev = float(zg[i]) + 6.5
            c.drape(z_flat=226.0, z_min=[(s_u, lev, 12.0)]); c.underpass = dict(s=float(s_u), ground=float(zg[i]), level=lev)
        else:
            c.drape()
        c.earthworks()
        c.res = {n: c.simulate(car) for n, car in C.CARS.items()}
        c.title = TITLE[k]
        out[k] = c
    return out
if __name__ == '__main__':
    cs = build()
    for k, c in cs.items():
        print(f"{c.title}: {c.LAP:.1f} m, {len(c.corners)} corners, z {c.z.min():.1f}-{c.z.max():.1f}, level straight at {c.z_flat:.1f}, "
              f"grade {c.grade.min()*100:+.1f}/{c.grade.max()*100:+.1f}%, cut {c.cut/1e3:.0f}k fill {c.fill/1e3:.0f}k, closure {c.gap*1000:.0f} mm")
        for n, r in c.res.items():
            print(f"   Car {n}: {int(r['lap']//60)}:{r['lap']%60:05.2f}  avg {c.LAP/r['lap']*3.6:.1f} km/h  vmax {r['v'].max()*3.6:.0f}")
        if k == 'W': print('   underpass', c.underpass)
