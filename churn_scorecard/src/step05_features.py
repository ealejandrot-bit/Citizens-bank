"""Paso 5 · Ingeniería de señales transversales.

Derivadas (SPEC G.5): log_rv, aum_share, deposit_share, streams_stopped_count (+ n_streams_eligible),
n_products_held, outflow_x_contact_gap, competitor_x_new_destinations, indicadores de missing, peer-relative por celda
segment × banda de RV (quintiles de RV calculados en dev por segmento; medianas de dev; celdas ≥ 100 hogares).
Razón de missing por variable (`<var>__miss` ∈ ok / no_aplica / sin_dato): "no aplica" = gatillo estructural en False;
"sin dato" = resto (historia corta, < 3 contactos, piloto, patrón no detectado). Recodificación: los 134 valores de
`pension_deposit_stopped_flag` sin `has_pension_stream` pasan a "no aplica" (excepción estructural del paso 3).
Excluidas por G1-3 [DEF-default]: age_primary, bureau_new_mortgage_elsewhere (quedan en el archivo solo para sensibilidad).
Salida: data/processed/features.parquet (20,000 filas: modelado + indeterminados + excluidos para scoring).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from common import COMPOSITES, PROC, REPORTS, STRUCTURAL, load_raw, md_table, save_table, set_seed

set_seed()
df = load_raw()
pop = pd.read_parquet(PROC / "step01_population.parquet")
dev_ids = set(pd.read_parquet(PROC / "dev.parquet", columns=["household_id"]).household_id)
dic = pd.read_csv(__import__("common").TABLES / "step02_dictionary.csv").set_index("columna")
F = df.copy()

# Recodificación estructural de pensión (paso 3: 134 excepciones)
n_recode = int((F.pension_deposit_stopped_flag.notna() & ~F.has_pension_stream).sum())
F.loc[~F.has_pension_stream, "pension_deposit_stopped_flag"] = np.nan

# Razón de missing
TRIG = {c: t for t, cs in STRUCTURAL.items() for c in cs}
REASONS = {}
for c in df.columns:
    if F[c].isna().any() and dic.loc[c, "uso"] == "predictor":
        r = pd.Series("ok", index=F.index)
        na = F[c].isna()
        if c in TRIG:
            r[na & ~F[TRIG[c]].astype(bool)] = "no_aplica"
            r[na & F[TRIG[c]].astype(bool)] = "sin_dato"
        else:
            r[na] = "sin_dato"
        F[f"{c}__miss"] = r
        REASONS[c] = r

# Derivadas
rv = F.relationship_value
F["log_rv"] = np.log10(rv)
F["aum_share"] = F.aum.fillna(0) / rv
F["deposit_share"] = F.deposit_balance / rv
STREAMS = {"salary_deposit_stopped_flag": "has_payroll_stream", "pension_deposit_stopped_flag": "has_pension_stream",
           "business_payroll_stopped_flag": "has_linked_business"}
F["streams_stopped_count"] = F[list(STREAMS) + ["recurring_deposit_stopped_flag"]].fillna(0).sum(axis=1)
F["n_streams_eligible"] = F[list(STREAMS.values())].astype(int).sum(axis=1)
HAS = [c for c in df.columns if c.startswith("has_")]
F["n_products_held"] = F[HAS].astype(int).sum(axis=1)
aum_out0 = F.aum_outflow_pct_90d.where(F.has_investments, 0.0)   # sin inversiones: no hay AUM que sacar
F["outflow_x_contact_gap"] = aum_out0 * F.contact_gap_ratio
F["competitor_x_new_destinations"] = F.transfer_to_competitor_pct_90d * F.new_external_destinations_90d
F["competitor_x_new_destinations__miss"] = F["new_external_destinations_90d__miss"]   # hereda la razón del factor con missing
for c in ["client_reply_rate", "meetings_cancelled_by_client", "relationship_dissatisfaction_flag", "fixed_income_maturity_not_reinvested"]:
    F[f"ind_sin_dato_{c}"] = F[c].isna().astype(int)

# Peer-relative: celda segment × quintil de RV (cortes de dev por segmento); mediana de dev por celda
isdev = F.household_id.isin(dev_ids)
F["rv_band"] = ""
cuts = {}
for s_ in ("HNW", "UHNW"):
    q = F.loc[isdev & (F.segment == s_), "relationship_value"].quantile([0.2, 0.4, 0.6, 0.8]).to_numpy()
    cuts[s_] = q
    m = F.segment == s_
    F.loc[m, "rv_band"] = s_ + "_Q" + (np.searchsorted(q, F.loc[m, "relationship_value"], side="right") + 1).astype(str)
PEER = ["aum_outflow_pct_90d", "net_deposit_flow_pct_90d", "contact_gap_ratio"]
cell = F[isdev].groupby("rv_band")
cell_n = cell.size()
peer_rows = []
for c in PEER:
    med = cell[c].median()
    F[f"{c}_peer"] = F[c] - F.rv_band.map(med)
    if f"{c}__miss" in F:
        F[f"{c}_peer__miss"] = F[f"{c}__miss"]
    for b in med.index:
        peer_rows.append({"variable": c, "celda": b, "hogares dev": int(cell_n[b]), "mediana dev": med[b]})
peer = pd.DataFrame(peer_rows)
save_table(peer, "step05_peer_cells")
F.drop(columns="rv_band").to_parquet(PROC / "features.parquet", index=False)

DER = [
    ("log_rv", "log10(relationship_value)", "patrimonial", "?", "derivada"),
    ("aum_share", "aum / RV (0 sin inversiones)", "patrimonial", "?", "derivada"),
    ("deposit_share", "deposit_balance / RV", "patrimonial", "?", "derivada"),
    ("streams_stopped_count", "suma de flags de streams detenidos (salario, pensión, nómina de negocio, recurrente); no aplica = 0", "transaccional", "+", "derivada"),
    ("n_streams_eligible", "streams con gatillo (nómina, pensión, negocio): elegibilidad del conteo", "producto", "−", "derivada"),
    ("n_products_held", "suma de has_* (8)", "producto", "−", "derivada"),
    ("outflow_x_contact_gap", "aum_outflow_pct_90d (0 sin inversiones) × contact_gap_ratio", "transaccional", "+", "derivada"),
    ("competitor_x_new_destinations", "transfer_to_competitor_pct_90d × new_external_destinations_90d", "transaccional", "+", "derivada"),
    ("ind_sin_dato_client_reply_rate", "1 si < 3 contactos del banquero en 90d (client_reply_rate sin dato)", "relación", "+", "derivada"),
    ("ind_sin_dato_meetings_cancelled_by_client", "1 si el banquero no registra reuniones", "relación", "?", "derivada"),
    ("ind_sin_dato_relationship_dissatisfaction_flag", "1 si fuera del piloto del Assistant", "servicio", "?", "derivada"),
    ("ind_sin_dato_fixed_income_maturity_not_reinvested", "1 si sin vencimientos de renta fija", "transaccional", "?", "derivada"),
    ("aum_outflow_pct_90d_peer", "aum_outflow_pct_90d − mediana de su celda segment × quintil de RV (dev)", "transaccional", "+", "derivada"),
    ("net_deposit_flow_pct_90d_peer", "net_deposit_flow_pct_90d − mediana de su celda (dev)", "transaccional", "−", "derivada"),
    ("contact_gap_ratio_peer", "contact_gap_ratio − mediana de su celda (dev)", "relación", "+", "derivada"),
    ("<var>__miss", "razón de missing: ok / no_aplica / sin_dato", "—", "—", "auxiliar (bins del campeón)"),
]
prov = dic[dic.uso == "predictor"].reset_index()[["columna", "significado de negocio", "bloque", "dirección esperada"]]
prov = prov[~prov.columna.isin(["age_primary", "bureau_new_mortgage_elsewhere"])]
prov["columna"] = prov.columna.replace({"segment": "segment_uhnw"})
prov.columns = ["variable", "definición", "dimensión", "signo esperado"]
prov["origen"] = "proveedor"
feat = pd.concat([prov, pd.DataFrame(DER, columns=["variable", "definición", "dimensión", "signo esperado", "origen"])], ignore_index=True)
save_table(feat, "step05_features")
dims = pd.DataFrame({"dimensión": ["transaccional", "patrimonial", "relación", "producto", "servicio", "economía", "digital", "vida"]})
dims["variables de proveedor"] = [int((prov.dimensión == d_).sum()) for d_ in dims["dimensión"]]
dims["estado"] = np.where(dims["variables de proveedor"] > 0, "presente", "AUSENTE (L6)")
save_table(dims, "step05_dimensions")

rep = f"""# Paso 5 · Ingeniería de señales (transversal)

## Objetivo
- Agregar solo derivadas transversales permitidas y dejar explícito el tratamiento del missing.

## Método
- Derivadas del SPEC; peer-relative con celdas `segment` × quintil de RV (cortes y medianas de dev).
- Razón de missing `<var>__miss` (ok / no_aplica / sin_dato); {n_recode} valores de pensión sin gatillo recodificados a
  "no aplica" [DATA]. Sin imputación por media o mediana (el peer-relative resta la mediana de la celda; no imputa).
- Excluidas de los modelos por G1-3 [DEF-default]: `age_primary`, `bureau_new_mortgage_elsewhere`. Compuestos: solo
  challenger [DEF-default I-3].

## Código
- `src/step05_features.py` · `tests/test_step05.py` · `data/processed/features.parquet`.

## Resultados

### Variables [DATA]
{md_table(feat)}

### Dimensiones [DATA]
{md_table(dims)}

### Celdas peer-relative [DATA]
{md_table(peer[peer.variable == PEER[0]][['celda', 'hogares dev']])}

- Todas las celdas con ≥ 100 hogares de dev: mínimo {int(cell_n.min())} [DATA].

## Tests
- `tests/test_step05.py` (ver pytest).

## Decisiones y preguntas abiertas
- D5.1 en `reports/decision_log.md`.
"""
(REPORTS / "step05.md").write_text(rep, encoding="utf-8")
print(dims.to_string(index=False)); print(cell_n.to_string()); print(len(REASONS), "variables con razón de missing")
