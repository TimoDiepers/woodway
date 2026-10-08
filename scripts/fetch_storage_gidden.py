"""Download Gidden et al. (2025) storage data and derive the per-country table and basin mask.

Run: .venv/bin/python scripts/fetch_storage_gidden.py
"""

import json
import urllib.request

import numpy as np

from nbs.dac_storage import MASK, ROOT, TABLE, derive_mask, derive_table

RECORD = "https://zenodo.org/api/records/18343187/files/{}/content"
FILES = ("gidden_et_al_2025_supplemental_data.xlsx", "Figure_1a_EPSG4326_generalised_to_0_01degree.tif",
         "Read_Me_Figure1a.rtf")
RAW = ROOT / "data" / "raw" / "gidden"

RAW.mkdir(parents=True, exist_ok=True)
for name in FILES:
    if not (RAW / name).exists():
        urllib.request.urlretrieve(RECORD.format(name), RAW / name)
TABLE.write_text(json.dumps(derive_table(RAW / FILES[0]), indent=1, ensure_ascii=False))
np.savez_compressed(MASK, mask=derive_mask(RAW / FILES[1]))
print("ok", TABLE, MASK)
