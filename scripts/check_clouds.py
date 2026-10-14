"""Print the cloud effect against the albedo at the sites and globally (check, not a figure).

    uv run python scripts/check_clouds.py
"""

import numpy as np

from nbs.animations import SITES, site_cell, site_key, typical_alpha_q_product, typical_cloud_product
from nbs.cloud_grid import TIER_NAMES, cloud_provenance_grid, delta_cloud_native
from nbs.grid import grid_lats
from nbs.landscape import plantable_area_m2

A = 5.0  # m2 per tree
LAT1, LON1 = np.arange(89.5, -90, -1.0), np.arange(-179.5, 180, 1.0)

alb, cld = typical_alpha_q_product(), typical_cloud_product()
for s in SITES:
    c, k = site_cell(s), site_key(s)
    i, j = int(np.argmin(abs(LAT1 - s.lat))), int(np.argmin(abs(LON1 - s.lon)))
    print(f"{s.label:14s} {k:14s} Δf je Monat: {np.round(delta_cloud_native(k)[:, i, j], 3)}")
    print(f"{'':14s} Albedo {-alb[c] * A:6.1f} W  Wolken {-cld[c] * A:6.1f} W  netto {-(alb[c] + cld[c]) * A:6.1f} W"
          f"  Anteil {cld[c] / -alb[c]:6.1%}  Wolken-Stufe {TIER_NAMES[int(cloud_provenance_grid(k)[c])]}")

w = plantable_area_m2()
ok = np.isfinite(alb) & np.isfinite(cld) & (w > 0)
ga, gc = np.average(alb[ok], weights=w[ok]), np.average(cld[ok], weights=w[ok])
print(f"\nglobal (flächengewichtet, wiederbewaldbar): Albedo {ga:.2f}  Wolken {gc:.2f} W/m²  Anteil {gc / -ga:.1%}")
print("\nBreitenprofil (W/m², positiv = heller):")
lat = grid_lats()
for lo in range(-40, 70, 5):
    m = ok & ((lat >= lo) & (lat < lo + 5))[:, None]
    if m.any():
        print(f"{lo:4d}..{lo + 5:<4d} Wolken {np.average(cld[m], weights=w[m]):6.2f}  "
              f"Albedo {np.average(alb[m], weights=w[m]):6.2f}")
