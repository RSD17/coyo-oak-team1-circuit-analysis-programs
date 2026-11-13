import sys, pickle, json; sys.path.insert(0, '/home/claude/v3')
import numpy as np, model, base as B, circuit as C
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LightSource, LinearSegmentedColormap
from matplotlib.collections import LineCollection
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
import os
OUT = '/mnt/user-data/outputs/v3'; os.makedirs(OUT, exist_ok=True)
cs = model.build(); sh = pickle.load(open('shapes.pkl', 'rb')); res = json.load(open('results.json'))
INK = '#1d2428'; COL = {'W': '#c8451f', 'E': '#1f5fa8'}
terr = LinearSegmentedColormap.from_list('t', ['#9fb8a0', '#c9d3ae', '#e9e2c3', '#d9c39c', '#b99a78'])
Z = np.where(B.MASK, B.Z, np.nan); ext = [B.E.min()-5, B.E.max()+5, B.N.min()-5, B.N.max()+5]
north_up = B.N[0] > B.N[-1]
def terrain(ax, alpha=1.0):
    Zf = np.where(np.isnan(Z), np.nanmean(Z), Z)
    hs = LightSource(315, 45).shade(Zf, cmap=terr, vert_exag=3, dx=10, dy=10, blend_mode='soft', vmin=190, vmax=300)
    hs[..., 3] = np.where(np.isnan(Z), 0, alpha)
    ax.imshow(hs, extent=ext, origin='upper' if north_up else 'lower', zorder=0)
    cl = ax.contour(B.E, B.N, Z, levels=np.arange(190, 300, 10), colors='#6b5a45', linewidths=0.35, alpha=0.6, zorder=1)
    ax.clabel(cl, fmt='%d', fontsize=5.5, colors='#6b5a45')
def fill(ax, g, **kw):
    if g.is_empty: return
    for p in getattr(g, 'geoms', [g]):
        if p.geom_type != 'Polygon': continue
        ax.fill(*p.exterior.xy, **kw)
        for h in p.interiors: ax.fill(*h.xy, color='#e3dcc0', zorder=kw.get('zorder', 2))
def furniture(ax, k, labels=True, fs=7):
    c = cs[k]; s_ = sh[k]
    fill(ax, s_['grav'], color='#e6c97a', alpha=0.9, zorder=3, lw=0)
    fill(ax, s_['asph'], color='#8d9399', alpha=0.95, zorder=3, lw=0)
    fill(ax, s_['paddock'], color='#b9bcc0', zorder=3, lw=0); fill(ax, s_['bldg'], color='#3b4a57', zorder=4, lw=0)
    fill(ax, s_['terrace'], color='#7b4fa3', zorder=4, lw=0); fill(ax, s_['pit'], color='#55595e', zorder=4, lw=0)
    fill(ax, s_['track'], color=INK, zorder=5, lw=0)
    ax.plot(c.x, c.y, color=COL[k], lw=0.9, zorder=6)
    i = np.searchsorted(c.s, model.SF)
    ax.plot([c.x[i]-c.nx[i]*9, c.x[i]+c.nx[i]*9], [c.y[i]-c.ny[i]*9, c.y[i]+c.ny[i]*9], color='w', lw=2.2, zorder=7)
    for sa in np.arange(120, c.LAP, 420):  # Add direction arrows around the circuit.
        j = np.searchsorted(c.s, sa); ax.annotate('', (c.x[j+8], c.y[j+8]), (c.x[j], c.y[j]), arrowprops=dict(arrowstyle='-|>', color='w', lw=0, mutation_scale=9), zorder=8)
    if labels:
        for n, e in enumerate(c.corners):
            j = np.searchsorted(c.s, e['s_apex']); sd = -e['sgn']  # Place labels on the inside of each corner.
            ax.text(c.x[j]-sd*c.nx[j]*-38, c.y[j]-sd*c.ny[j]*-38, str(n+1), fontsize=fs, ha='center', va='center', color='w', weight='bold', zorder=9,
                    bbox=dict(boxstyle='circle,pad=0.18', fc=COL[k], ec='w', lw=0.5))
def site_layers(ax):
    S = sh['site']
    fill(ax, S['wet_e'], color='#6fb3c9', alpha=0.75, zorder=2, lw=0); fill(ax, S['wet_nw'], color='#6fb3c9', alpha=0.75, zorder=2, lw=0); fill(ax, S['wet_basin'], color='#6fb3c9', alpha=0.75, zorder=2, lw=0)
    fill(ax, S['road_e'], color='#fafafa', zorder=4, lw=0); fill(ax, S['road_w'], color='#fafafa', zorder=4, lw=0)
    ax.plot(*B.PARCEL.exterior.xy, color=INK, lw=1.4, zorder=9)
    ax.fill(*B.ENTRY.exterior.xy, fc='none', ec='#7a3b00', hatch='///', lw=0.8, zorder=2, alpha=0.7)
def scale_north(ax, x0, y0):
    ax.plot([x0, x0+500], [y0, y0], color=INK, lw=3, solid_capstyle='butt', zorder=10); ax.plot([x0+250, x0+500], [y0, y0], color='w', lw=1.6, solid_capstyle='butt', zorder=11)
    ax.text(x0, y0+22, '0', fontsize=7, ha='center'); ax.text(x0+500, y0+22, '500 m', fontsize=7, ha='center')
    ax.annotate('N', (x0+640, y0+120), (x0+640, y0-20), ha='center', fontsize=10, weight='bold', arrowprops=dict(arrowstyle='-|>', color=INK, lw=1.6))
# Draw the master plan.
fig, ax = plt.subplots(figsize=(12.5, 15.2), dpi=170); terrain(ax); site_layers(ax)
for k in 'WE': furniture(ax, k)
habitat = [(303150, 6419700, 'North-east hill\nwoodland restoration'), (301520, 6418420, 'South-west hill\nwoodland restoration'), (302620, 6418020, 'Southern slopes\ngrassy woodland'),
           (303070, 6418150, 'Void wetland'), (301800, 6420000, 'NW swale'), (302330, 6419030, 'Central ridge\nhabitat corridor')]
for x_, y_, t in habitat: ax.text(x_, y_, t, fontsize=7.5, ha='center', va='center', style='italic', color='#1f4d2b', zorder=9, bbox=dict(fc='w', ec='none', alpha=0.55, pad=1.5))
ax.text(301890, 6420390, 'ENTRY / EXIT ZONE\nto Thomas Mitchell Drive', fontsize=8, ha='center', color='#7a3b00', weight='bold', zorder=9, rotation=-8)
ax.text(301800, 6418900, 'RIDGE CIRCUIT\n5.145 km · 15 corners', fontsize=10, weight='bold', color=COL['W'], ha='center', zorder=9, bbox=dict(fc='w', ec=COL['W'], alpha=0.9, pad=3))
ax.text(302790, 6419050, 'LAKESIDE CIRCUIT\n4.783 km · 14 corners', fontsize=10, weight='bold', color=COL['E'], ha='center', zorder=9, bbox=dict(fc='w', ec=COL['E'], alpha=0.9, pad=3))
for k in 'WE':
    st = B.STARTS[k]; ax.plot(st['e'], st['n'], 'o', ms=6, mfc='yellow', mec=INK, zorder=10)
    ax.annotate(f"Start {1 if k=='W' else 2}\nE{st['e']} N{st['n']}\nbearing {st['brg']}°", (st['e'], st['n']), (st['e']+(-330 if k=='W' else 200), st['n']+(-150 if k=='W' else 60)), fontsize=7, zorder=10,
                arrowprops=dict(arrowstyle='-', lw=0.6), bbox=dict(fc='w', ec=INK, lw=0.4, pad=2))
ax.legend(handles=[Patch(fc=INK, label='Track, 12 m'), Patch(fc='#55595e', label='Pit lane'), Patch(fc='#3b4a57', label='Modular pit / paddock buildings'), Patch(fc='#b9bcc0', label='Paddock apron'),
                   Patch(fc='#7b4fa3', label='Modular spectator terrace'), Patch(fc='#e6c97a', label='Gravel run-off'), Patch(fc='#8d9399', label='Asphalt run-off / escape road'),
                   Patch(fc='#6fb3c9', label='Wetland / detention (biodiversity)'), Patch(fc='#fafafa', ec='#999', label='Public access road'), Patch(fc='none', ec='#7a3b00', hatch='///', label='Reserved entry / exit zone'),
                   Line2D([], [], color=INK, lw=1.4, label='Parcel boundary (521.6 ha)'), Line2D([], [], color='w', lw=2.2, label='Start / finish line')],
          loc='lower left', fontsize=7.5, framealpha=0.95, facecolor='w', edgecolor=INK, title='Muswellbrook twin circuits', title_fontsize=9)
scale_north(ax, 302650, 6420560)
ax.set_xlim(300990, 303840); ax.set_ylim(6417560, 6420760); ax.set_aspect('equal'); ax.tick_params(labelsize=6.5); ax.ticklabel_format(style='plain', useOffset=False)
ax.set_xlabel('Easting (m), MGA / UTM zone 56S', fontsize=8); ax.set_ylabel('Northing (m)', fontsize=8)
ax.set_title('Master plan — Ridge Circuit (west) and Lakeside Circuit (east) on the surveyed terrain, 10 m contours', fontsize=11, weight='bold', loc='left')
fig.savefig(f'{OUT}/01_master_plan.png', bbox_inches='tight', facecolor='w'); plt.close(fig)
# Draw a plan, speed profile, and elevation profile for each circuit.
for num, k in ((2, 'W'), (3, 'E')):
    c = cs[k]; r = c.res[5]; o = res[k]
    fig = plt.figure(figsize=(9.6, 18.5), dpi=160); gs = fig.add_gridspec(3, 1, height_ratios=[4.6, 1, 1], hspace=0.13)
    ax = fig.add_subplot(gs[0]); terrain(ax, 0.75); site_layers(ax); s_ = sh[k]
    fill(ax, s_['grav'], color='#e6c97a', alpha=0.9, zorder=3, lw=0); fill(ax, s_['asph'], color='#8d9399', zorder=3, lw=0); fill(ax, s_['paddock'], color='#b9bcc0', zorder=3, lw=0)
    fill(ax, s_['bldg'], color='#3b4a57', zorder=4, lw=0); fill(ax, s_['terrace'], color='#7b4fa3', zorder=4, lw=0); fill(ax, s_['pit'], color='#55595e', zorder=4, lw=0)
    pts = np.c_[c.x, c.y].reshape(-1, 1, 2)[::2]; seg = np.concatenate([pts[:-1], pts[1:]], axis=1)
    ax.add_collection(LineCollection(seg, colors=INK, linewidths=6.2, zorder=5, capstyle='round'))
    lc = LineCollection(seg, cmap='turbo', linewidths=4.2, zorder=6, capstyle='round'); lc.set_array(r['v'][::2][:-1]*3.6); lc.set_clim(60, 280); ax.add_collection(lc)
    cb = fig.colorbar(lc, ax=ax, fraction=0.025, pad=0.01); cb.set_label('Car 5 speed (km/h)', fontsize=8); cb.ax.tick_params(labelsize=7)
    for n, e in enumerate(c.corners):
        j = np.searchsorted(c.s, e['s_apex']); sd = e['sgn']
        ax.text(c.x[j]+sd*c.nx[j]*-34, c.y[j]+sd*c.ny[j]*-34, f"T{n+1} · {o['corners'][n]['v5']:.0f}", fontsize=6.3, ha='center', va='center', zorder=9, bbox=dict(fc='w', ec=COL[k], lw=0.5, alpha=0.9, pad=1.2))
    i = np.searchsorted(c.s, model.SF); ax.plot([c.x[i]-c.nx[i]*14, c.x[i]+c.nx[i]*14], [c.y[i]-c.ny[i]*14, c.y[i]+c.ny[i]*14], color='w', lw=3, zorder=8)
    for sa in np.arange(0, c.LAP, 500):
        j = min(np.searchsorted(c.s, sa), len(c.s)-1); ax.text(c.x[j]+c.nx[j]*22, c.y[j]+c.ny[j]*22, f'{sa/1000:.1f}', fontsize=5.5, color='#333', ha='center', va='center', zorder=9)
    pad = 170; ax.set_xlim(c.x.min()-pad, c.x.max()+pad); ax.set_ylim(c.y.min()-pad, c.y.max()+pad); ax.set_aspect('equal'); ax.tick_params(labelsize=6.5); ax.ticklabel_format(style='plain', useOffset=False)
    scale_north(ax, c.x.min()-pad+40, c.y.max()+pad-70)
    lap5 = c.res[5]['lap']
    ax.set_title(f"{c.title} — {c.LAP/1000:.3f} km, {len(c.corners)} corners, anticlockwise.  Car 5 {int(lap5//60)}:{lap5%60:05.2f}", fontsize=9.5, weight='bold', loc='left')
    a2 = fig.add_subplot(gs[1]); a2.plot(c.s, r['v']*3.6, color=COL[k], lw=1.4, label='Car 5 Grip Specialist, simulated')
    for n, e in enumerate(c.corners): a2.axvspan(e['s0'], e['s1'], color='#000', alpha=0.06); a2.text(e['s_apex'], 12, str(n+1), fontsize=6.5, ha='center')
    a2.set_ylabel('Speed (km/h)', fontsize=8); a2.set_xlim(0, c.LAP); a2.set_ylim(0, 300); a2.grid(alpha=0.25); a2.legend(fontsize=7, loc='upper right', ncol=2); a2.tick_params(labelsize=7)
    a3 = fig.add_subplot(gs[2]); a3.fill_between(c.s, c.zg, c.z, where=c.z < c.zg, color='#c9773a', alpha=0.7, label='Cut'); a3.fill_between(c.s, c.zg, c.z, where=c.z >= c.zg, color='#4f8f5b', alpha=0.7, label='Fill')
    a3.plot(c.s, c.zg, color='#6b5a45', lw=0.8, label='Existing ground (DEM)'); a3.plot(c.s, c.z, color=INK, lw=1.5, label='Design level')
    a3.axvspan(0, 900, color='gold', alpha=0.25); a3.text(450, c.z.max()+3, f'900 m level start straight\n{c.z_flat:.1f} m', fontsize=7, ha='center', va='bottom')
    for n, e in enumerate(c.corners): a3.text(e['s_apex'], c.z.min()-7, str(n+1), fontsize=6.5, ha='center')
    a3.set_ylim(c.z.min()-10, c.z.max()+14); a3.set_xlim(0, c.LAP); a3.set_xlabel('Chainage from start point (m)', fontsize=8); a3.set_ylabel('Elevation (m AHD)', fontsize=8); a3.grid(alpha=0.25); a3.legend(fontsize=7, ncol=4, loc='lower right'); a3.tick_params(labelsize=7)
    a3.set_title(f"Long section (vertical exaggeration ≈ 15×): cut {c.cut/1000:.0f}k m³, fill {c.fill/1000:.0f}k m³, grades {c.grade.min()*100:+.1f}% to {c.grade.max()*100:+.1f}%", fontsize=8.5, loc='left')
    fig.savefig(f"{OUT}/0{num}_{'ridge' if k=='W' else 'lakeside'}_circuit.png", bbox_inches='tight', facecolor='w'); plt.close(fig)
print(os.listdir(OUT))
