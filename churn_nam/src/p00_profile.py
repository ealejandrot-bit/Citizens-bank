"""Fase 0 · Perfil: tabla esperado vs observado para cada hecho de SPEC §2, con discrepancias marcadas.

Salidas: outputs/p00/facts.csv (hecho, esperado, observado, coincide, base, nota), outputs/p00/_meta.json;
reporte reports/p00.md (src/report.py). El split heredado se lee de ../churn_scorecard (solo lectura).
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from config import P, get, set_seed
from report import render

set_seed()
df = pd.read_excel(P.raw, sheet_name=get("paths.sheet"))
el = ~df.churn_excluded.astype(bool)
E = df[el]
hard, soft = df.hard_churn_6m == 1, df.soft_churn_3m == 1
rows = []


def fact(n, hecho, esperado, observado, ok, base, nota=""):
    rows.append({"#": n, "hecho": hecho, "esperado (SPEC §2)": esperado, "observado": observado, "coincide": bool(ok), "base": base, "nota": nota})


import openpyxl  # noqa: E402

sheets = openpyxl.load_workbook(P.raw, read_only=True).sheetnames
fact(1, "Hoja / filas / columnas", "client_pulse_synthetic / 20,000 / 62", f"{', '.join(sheets)} / {len(df):,} / {df.shape[1]}",
     sheets == ["client_pulse_synthetic"] and df.shape == (20000, 62), "archivo")
snap = sorted(df.snapshot_date.astype(str).str[:10].unique())
fact(2, "Unidad y snapshot", "household_id único; 2025-12-31", f"{df.household_id.nunique():,} únicos; {', '.join(snap)}",
     df.household_id.is_unique and snap == ["2025-12-31"], "20,000")
seg = df.segment.value_counts()
fact(3, "Segmento", "HNW 18,897 · UHNW 1,103", f"HNW {seg.get('HNW', 0):,} · UHNW {seg.get('UHNW', 0):,}", (seg.get("HNW"), seg.get("UHNW")) == (18897, 1103), "20,000")
fact(4, "churn_excluded / elegibles", "123 / 19,877", f"{int((~el).sum())} / {int(el.sum()):,}", (int((~el).sum()), int(el.sum())) == (123, 19877), "20,000")
lr = df.value_lost_6m / df.relationship_value
nh = int((hard & el).sum())
fact(5, "hard_churn_6m", "1,200 = 6.04%; pérdida 100% del RV", f"{nh:,} = {100 * nh / el.sum():.2f}%; pérdida mín–máx {lr[hard].min():.3f}–{lr[hard].max():.3f}",
     nh == 1200 and round(100 * nh / el.sum(), 2) == 6.04 and np.allclose(lr[hard], 1.0), "elegibles")
ns, ov = int((soft & el).sum()), int((hard & soft).sum())
fact(6, "soft_churn_3m", "1,756 = 8.83%; disjunto de hard", f"{ns:,} = {100 * ns / el.sum():.2f}%; solapes con hard {ov}", ns == 1756 and round(100 * ns / el.sum(), 2) == 8.83 and ov == 0, "elegibles")
pos = df.value_lost_6m.fillna(0) > 0
fact(7, "value_lost_6m > 0 ⟺ hard ∪ soft", "exacto (2,956)", f"{int(pos.sum()):,}; coincide con hard ∪ soft: {bool((pos == (hard | soft)).all())}",
     int(pos.sum()) == 2956 and (pos == (hard | soft)).all(), "20,000")
diff = (df.relationship_value - df.aum.fillna(0) - df.deposit_balance).abs()
fact(8, "RV = AUM (0 sin inversiones) + depósitos", "dif. máx. $0.01", f"dif. máx. ${diff.max():.10f}", (diff.round(6) <= 0.01).all(), "20,000",
     "dif. máx. > 0.01 solo por ruido de flotante en magnitudes 10⁸–10⁹; redondeada a 6 decimales ≤ 0.01 (M1 D0.6)")
noinv = E.has_investments.astype(bool)
struct_ok = E.loc[~noinv, "aum"].isna().all() and E.loc[noinv, "aum"].notna().all()
fact(9, "aum falta ⟺ has_investments = False", "exacto; 2,847 sin inversiones", f"{'exacto' if struct_ok else 'no exacto'}; {int((~noinv).sum()):,} sin inversiones",
     struct_ok and int((~noinv).sum()) == 2847, "elegibles")
miss = {c: 100 * E[c].isna().mean() for c in ["client_reply_rate", "meetings_cancelled_by_client", "relationship_dissatisfaction_flag", "fixed_income_maturity_not_reinvested"]}
exp10 = {"client_reply_rate": 48.0, "meetings_cancelled_by_client": 60.7, "relationship_dissatisfaction_flag": 70.4, "fixed_income_maturity_not_reinvested": 73.9}
fact(10, "Missing no estructural (%)", " · ".join(f"{k} {v}" for k, v in exp10.items()), " · ".join(f"{k} {v:.1f}" for k, v in miss.items()),
     all(round(miss[k], 1) == v for k, v in exp10.items()), "elegibles")
t1, h24 = int((E.tenure_years < 1).sum()), int((E.history_months < 24).sum())
fact(11, "tenure < 1 / history < 24", "404 / 1,417", f"{t1} / {h24:,}", (t1, h24) == (404, 1417), "elegibles")
flags = [c for c in df.columns if c.endswith("_flag") and c != "multi_signal_flag"] + ["bureau_new_mortgage_elsewhere"]
eq = bool((df.multi_signal_flag.astype(bool) == (df.multi_signal_count >= 3)).all())
rho = float(np.corrcoef(E.multi_signal_count, E[flags].fillna(0).astype(float).sum(axis=1))[0, 1])
fact(12, "Compuestos", "flag ≡ count ≥ 3; ρ Pearson count vs Σ flags visibles 0.59", f"flag ≡ count ≥ 3: {eq}; ρ = {rho:.2f} ({len(flags)} señales)", eq and round(rho, 2) == 0.59, "elegibles",
     "Σ de 9 *_flag + bureau_new_mortgage_elsewhere (definición de M1 D0.3)")
from sklearn.metrics import roc_auc_score  # noqa: E402
yh = E.hard_churn_6m.astype(int)
aucs = {}
for c in df.columns:
    if c in ("household_id", "snapshot_date", "segment", "hard_churn_6m", "soft_churn_3m", "value_lost_6m", "churn_excluded"):
        continue
    x = pd.to_numeric(E[c], errors="coerce")
    if x.notna().sum() > 100 and x.nunique() > 1:
        x = x.fillna(x.median())
        a = roc_auc_score(yh, x)
        aucs[c] = max(a, 1 - a)
top = sorted(aucs.items(), key=lambda t: -t[1])[:3]
fact(13, "Ninguna señal con AUC > 0.70 vs hard", "máx. < 0.70", ", ".join(f"{k} {v:.3f}" for k, v in top), top[0][1] <= 0.70, "elegibles",
     "AUC univariada orientada (máx(AUC, 1−AUC)); missing → mediana solo para este cribado")
m1 = P.m1 / "data" / "processed"
dv, vl = pd.read_parquet(m1 / "dev.parquet"), pd.read_parquet(m1 / "val.parquet")
dB, vB = dv[dv.in_pop_B], vl[vl.in_pop_B]
fact(14, "Split heredado de M1/M2", "dev 13,631 / val 5,842; B eventos 1,871 / 803", f"dev {len(dv):,} / val {len(vl):,}; B eventos {int(dB.y_B.sum()):,} / {int(vB.y_B.sum()):,}",
     (len(dv), len(vl), int(dB.y_B.sum()), int(vB.y_B.sum())) == (13631, 5842, 1871, 803), "población M1")

T = pd.DataFrame(rows)
out = P.out(0)
T.to_csv(out / "facts.csv", index=False)
json.dump({"hechos": len(T), "coinciden": int(T.coincide.sum()), "discrepancias": T.loc[~T.coincide, "#"].tolist()}, open(out / "summary.json", "w"), ensure_ascii=False)
json.dump({"title": "Fase 0 · Perfil (esperado vs observado, SPEC §2)", "order": ["summary.json", "facts.csv"],
           "notes": {"facts.csv": "coincide = False marca una discrepancia; ver nota y explicación en el resumen de fase."}}, open(out / "_meta.json", "w"), ensure_ascii=False)
print(render(0)); print(T[["#", "hecho", "observado", "coincide"]].to_string(index=False))
