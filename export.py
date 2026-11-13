import sys, json, csv, os; sys.path.insert(0, '/home/claude/v3')
import numpy as np, model, base as B
from pyproj import Transformer
OUT = '/mnt/user-data/outputs/v3'; cs = model.build(); T = Transformer.from_crs(32756, 4326, always_xy=True)
feats = []; kml = ['<?xml version="1.0" encoding="UTF-8"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>Muswellbrook twin circuits - centrelines</name>']
dxf = ['0', 'SECTION', '2', 'ENTITIES']
for k, c in cs.items():
    name = 'ridge' if k == 'W' else 'lakeside'
    si = np.arange(0, c.LAP, 1.0); f = lambda a: np.interp(si, c.s, a)
    x, y, z, zg, g, kap = f(c.x), f(c.y), f(c.z), f(c.zg), f(c.grade), f(c.kap)
    lon, lat = T.transform(x, y)
    def elem(s_):
        for n, e in enumerate(c.corners):
            if e['s0'] <= s_ <= e['s1']: return e['label']
        return 'start straight' if s_ <= 900 else 'straight'
    with open(f'{OUT}/centreline_{name}_1m.csv', 'w', newline='') as fh:
        w = csv.writer(fh); w.writerow(['chainage_m', 'easting_m', 'northing_m', 'design_level_m', 'ground_level_m', 'cut(-)/fill(+)_m', 'grade_pct', 'radius_m(+R/-L, 0=straight)', 'element', 'lat_wgs84', 'lon_wgs84'])
        for i in range(len(si)):
            R = 0 if abs(kap[i]) < 1e-5 else round(1/kap[i], 1)
            w.writerow([f'{si[i]:.0f}', f'{x[i]:.2f}', f'{y[i]:.2f}', f'{z[i]:.2f}', f'{zg[i]:.2f}', f'{z[i]-zg[i]:.2f}', f'{g[i]*100:.2f}', R, elem(si[i]), f'{lat[i]:.7f}', f'{lon[i]:.7f}'])
    # Close the GIS/CAD line using points sampled every 2 m.
    j = np.r_[np.arange(0, len(si), 2), 0]
    feats.append(dict(type='Feature', properties=dict(name=c.title, length_m=round(c.LAP, 1), corners=len(c.corners), direction='anticlockwise', width_m=12, start_e=B.STARTS[k]['e'], start_n=B.STARTS[k]['n'], bearing=B.STARTS[k]['brg']),
                      geometry=dict(type='LineString', coordinates=[[round(lon[i], 7), round(lat[i], 7), round(z[i], 2)] for i in j])))
    kml.append(f'<Placemark><name>{c.title}</name><Style><LineStyle><color>{"ff1f45c8" if k=="W" else "ffa85f1f"}</color><width>4</width></LineStyle></Style><LineString><tessellate>1</tessellate><coordinates>'
               + ' '.join(f'{lon[i]:.7f},{lat[i]:.7f},{z[i]:.1f}' for i in j) + '</coordinates></LineString></Placemark>')
    dxf += ['0', 'POLYLINE', '8', f'CL_{name.upper()}', '66', '1', '70', '9', '10', '0', '20', '0', '30', '0']
    for i in j[:-1]: dxf += ['0', 'VERTEX', '8', f'CL_{name.upper()}', '10', f'{x[i]:.3f}', '20', f'{y[i]:.3f}', '30', f'{z[i]:.3f}', '70', '32']
    dxf += ['0', 'SEQEND']
    print(name, len(si), 'rows; first', x[0], y[0], 'at 900', x[900], y[900], 'brg', np.degrees(np.arctan2(x[900]-x[0], y[900]-y[0])) % 360, 'lat/lon', lat[0], lon[0])
px, py = B.PARCEL.exterior.xy
dxf += ['0', 'POLYLINE', '8', 'PARCEL', '66', '1', '70', '1']
for a_, b_ in list(zip(px, py))[:-1]: dxf += ['0', 'VERTEX', '8', 'PARCEL', '10', f'{a_:.1f}', '20', f'{b_:.1f}', '30', '0']
dxf += ['0', 'SEQEND', '0', 'ENDSEC', '0', 'EOF']; kml.append('</Document></kml>')
json.dump(dict(type='FeatureCollection', features=feats), open(f'{OUT}/centrelines_wgs84.geojson', 'w'))
open(f'{OUT}/centrelines.kml', 'w').write('\n'.join(kml)); open(f'{OUT}/centrelines_utm56s_3d.dxf', 'w').write('\n'.join(dxf) + '\n')
print(sorted(os.listdir(OUT)))
