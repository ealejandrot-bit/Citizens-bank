"""Bootstrap único de data/raw/client_pulse_synthetic.xlsx (D0.1 en reports/decision_log.md).

El archivo esperado por el SPEC no estaba en el repo; su contenido es la base del generador
(../data/synthetic/client_pulse_synthetic.csv). Se escribe una sola vez, hoja `client_pulse_synthetic`, y se verifica
que la relectura sea idéntica al CSV. No sobrescribe: data/raw es de solo lectura.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT.parent / "data" / "synthetic" / "client_pulse_synthetic.csv"
DST = ROOT / "data" / "raw" / "client_pulse_synthetic.xlsx"

if DST.exists():
    sys.exit(f"{DST} ya existe; data/raw es de solo lectura. No se sobrescribe.")
csv = pd.read_csv(SRC)
DST.parent.mkdir(parents=True, exist_ok=True)
csv.to_excel(DST, sheet_name="client_pulse_synthetic", index=False)
back = pd.read_excel(DST, sheet_name="client_pulse_synthetic")
assert back.shape == csv.shape and list(back.columns) == list(csv.columns)
for c in csv.columns:
    a, b = csv[c], back[c]
    if pd.api.types.is_numeric_dtype(a) and a.dtype != bool:
        assert np.allclose(a.to_numpy(float), b.to_numpy(float), equal_nan=True, rtol=0, atol=1e-9), c
    else:
        assert (a.astype(str) == b.astype(str)).all(), c
print("csv sha256 ", hashlib.sha256(SRC.read_bytes()).hexdigest())
print("xlsx sha256", hashlib.sha256(DST.read_bytes()).hexdigest())
print("OK: relectura idéntica al CSV", csv.shape)
