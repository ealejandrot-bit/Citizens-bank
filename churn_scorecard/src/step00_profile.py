"""Paso 0 · Verificación de la ficha y definición del problema (termina en G0).

Salidas (outputs/tables/): step00_ficha.csv (hecho, esperado, observado, coincide), step00_target_options.csv,
step00_churn_rates.csv, step00_missing_map.csv, step00_leakage_screen.csv, step00_prohibited.csv,
step00_pairs.csv; reports/step00.md. Los asserts viven en tests/test_step00.py.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from common import (COMPOSITES, FACTOR, ID, OFFSET, O0, OUTCOMES, PDO, PROHIBITED, REPORTS, S0, SHEET, STRUCTURAL,
                    THETA_B, eligible, load_raw, loss_ratio, md_table, save_table, set_seed, targets)

set_seed()
df = load_raw()
el = eligible(df)
d = df[el]
T = targets(df)
hard, soft = df.hard_churn_6m == 1, df.soft_churn_3m == 1
r = loss_ratio(df)
rv = df.relationship_value


def pct(x):
    return 100 * x


# ── Ficha: observado vs esperado ────────────────────────────────────────────────────────
F = []
def fact(hecho, esperado, observado, ok, nota=""):
    F.append({"hecho": hecho, "esperado (ficha)": esperado, "observado [DATA]": observado, "coincide": bool(ok), "nota": nota})

import openpyxl
sheets = openpyxl.load_workbook(__import__("common").RAW, read_only=True).sheetnames
fact("Hoja / filas / columnas", "client_pulse_synthetic / 20,000 / 62", f"{sheets[0]} / {len(df):,} / {df.shape[1]}",
     sheets == [SHEET] and df.shape == (20_000, 62))
fact("household_id único", "sí", f"{df[ID].nunique():,} únicos", df[ID].is_unique)
snap = df.snapshot_date.astype(str).str[:10].unique()
fact("Un solo snapshot", "2025-12-31", ", ".join(snap), list(snap) == ["2025-12-31"])
seg = df.segment.value_counts()
fact("Segmento", "HNW 18,897 · UHNW 1,103", f"HNW {seg['HNW']:,} · UHNW {seg['UHNW']:,}", seg["HNW"] == 18_897 and seg["UHNW"] == 1_103)
ex = df[~el]
fact("churn_excluded", "123; targets NaN; history 13–24; tenure ≥ 1.14",
     f"{len(ex)}; targets NaN = {bool(ex[['hard_churn_6m', 'soft_churn_3m', 'value_lost_6m']].isna().all().all())}; "
     f"history {ex.history_months.min()}–{ex.history_months.max()}; tenure ≥ {ex.tenure_years.min():.2f}",
     len(ex) == 123 and ex[["hard_churn_6m", "soft_churn_3m", "value_lost_6m"]].isna().all().all()
     and ex.history_months.between(13, 24).all() and ex.tenure_years.min() >= 1.14)
fact("Elegibles", "19,877", f"{el.sum():,}", el.sum() == 19_877)
fact("hard_churn_6m", "1,200 = 6.04%; pérdida = 1.000", f"{int(hard.sum()):,} = {pct(hard[el].mean()):.2f}%; pérdida {r[hard].min():.3f}–{r[hard].max():.3f}",
     hard.sum() == 1_200 and np.allclose(r[hard], 1.0))
fact("soft_churn_3m", "1,756 = 8.83%; pérdida 0.20–0.60, mediana 0.40; disjunto",
     f"{int(soft.sum()):,} = {pct(soft[el].mean()):.2f}%; pérdida {r[soft].min():.4f}–{r[soft].max():.4f}, mediana {r[soft].median():.4f}; solapes {int((hard & soft).sum())}",
     soft.sum() == 1_756 and r[soft].between(0.20, 0.60).all() and abs(r[soft].median() - 0.40) < 0.005 and (hard & soft).sum() == 0)
vl_pos = df.value_lost_6m > 0
fact("value_lost_6m > 0 ⟺ hard ∪ soft", "2,956", f"{int(vl_pos.sum()):,}; ⟺ {bool((vl_pos == (hard | soft)).all())}", vl_pos.sum() == 2_956 and (vl_pos == (hard | soft)).all())
fact("Churn por valor (elegibles)", "6.46% bruto; 10.32% económico",
     f"{pct(d.relationship_value[d.hard_churn_6m == 1].sum() / d.relationship_value.sum()):.2f}%; {pct(d.value_lost_6m.sum() / d.relationship_value.sum()):.2f}%",
     round(pct(d.relationship_value[d.hard_churn_6m == 1].sum() / d.relationship_value.sum()), 2) == 6.46 and round(pct(d.value_lost_6m.sum() / d.relationship_value.sum()), 2) == 10.32)
rvs = d.relationship_value.sort_values(ascending=False)
top5, top1 = rvs.head(int(0.05 * len(rvs))).sum() / rvs.sum(), rvs.head(int(0.01 * len(rvs))).sum() / rvs.sum()
fact("Tamaño (elegibles)", "ΣRV 206.27 B; ΣAUM 135.09 B (17,030); top 5% 37.4%; top 1% 18.1%; mediana 4.84 M; p5 1.27; p95 31.8",
     f"ΣRV {d.relationship_value.sum() / 1e9:.2f} B; ΣAUM {d.aum.sum() / 1e9:.2f} B ({int(d.has_investments.sum()):,}); top 5% {pct(top5):.1f}%; top 1% {pct(top1):.1f}%; "
     f"mediana {d.relationship_value.median() / 1e6:.2f} M; p5 {d.relationship_value.quantile(.05) / 1e6:.2f}; p95 {d.relationship_value.quantile(.95) / 1e6:.1f}",
     round(d.relationship_value.sum() / 1e9, 2) == 206.27 and round(d.aum.sum() / 1e9, 2) == 135.09 and d.has_investments.sum() == 17_030
     and round(pct(top5), 1) == 37.4 and round(pct(top1), 1) == 18.1, "la ficha usa elegibles (19,877), no las 20,000 filas")
diff = (rv - df.aum.fillna(0) - df.deposit_balance).abs()
fact("relationship_value ≠ aum + deposit_balance ('RV es medida propia')", "Verdadero",
     f"RV = aum (0 si NaN) + deposit_balance con |dif| máx ${diff.max():.2f}; igualdad exacta de flotantes en {pct((diff == 0).mean()):.1f}% por redondeo a centavos",
     False, "DISCREPANCIA D0.2: RV sí es la suma (al centavo); solo difiere por redondeo de flotantes")
nf = (~d.has_investments).sum()
fact("Missing estructural has_investments", "faltan ⟺ has_investments = False (2,847)", f"{nf:,} elegibles sin inversiones", nf == 2_847)
nsm = {c: pct(df[c].isna().mean()) for c in ["client_reply_rate", "meetings_cancelled_by_client", "relationship_dissatisfaction_flag", "fixed_income_maturity_not_reinvested"]}
fact("Missing no estructural", "48.0 / 60.7 / 70.4 / 73.9 %", " / ".join(f"{v:.1f}" for v in nsm.values()) + " %",
     [round(v, 1) for v in nsm.values()] == [48.0, 60.7, 70.4, 73.9])
fact("Antigüedad / historia (elegibles)", "tenure < 1: 404; history < 24: 1,417", f"{int((d.tenure_years < 1).sum())}; {int((d.history_months < 24).sum()):,}",
     (d.tenure_years < 1).sum() == 404 and (d.history_months < 24).sum() == 1_417)
BIN = ["salary_deposit_stopped_flag", "recurring_deposit_stopped_flag", "banker_change_6m_flag", "complaint_escalated_flag",
       "pension_deposit_stopped_flag", "business_payroll_stopped_flag", "trustee_change_flag", "repeat_complaint_flag",
       "relationship_dissatisfaction_flag", "bureau_new_mortgage_elsewhere"]
rho = d[BIN].fillna(0).sum(axis=1).corr(d.multi_signal_count)
rc = d.groupby("multi_signal_count").hard_churn_6m.mean()
fact("Compuestos", "flag ≡ count ≥ 3; ρ = 0.59 con suma de flags; tasa hard 2.8% (0) → 44.8% (7)",
     f"≡ {bool((df.multi_signal_flag == (df.multi_signal_count >= 3)).all())}; ρ Pearson = {rho:.2f} (10 binarias visibles; Spearman {d[BIN].fillna(0).sum(axis=1).corr(d.multi_signal_count, method='spearman'):.2f}); "
     f"{pct(rc.loc[0]):.1f}% → {pct(rc.loc[7]):.1f}%",
     (df.multi_signal_flag == (df.multi_signal_count >= 3)).all() and round(rho, 2) == 0.59 and round(pct(rc.loc[0]), 1) == 2.8 and round(pct(rc.loc[7]), 1) == 44.8,
     "ρ = Pearson con las 9 *_flag + bureau (D0.3)")


def auc_uni(x, y):
    m = x.notna()
    if m.sum() < 50 or x[m].nunique() < 2 or y[m].nunique() < 2:
        return np.nan
    a = roc_auc_score(y[m], x[m])
    return max(a, 1 - a)


yA = d.hard_churn_6m.astype(int)
cands = [c for c in df.columns if c not in PROHIBITED and c != "segment" and pd.api.types.is_numeric_dtype(df[c])]
aucA = {c: auc_uni(d[c].astype(float).fillna(d[c].astype(float).median()), yA) for c in cands}
top = sorted(aucA.items(), key=lambda t: -t[1])[:4]
fact("Señal univariada (AUC vs hard, missing → mediana)", "máx ≤ 0.70: count 0.69, banker 0.64, SOW 0.64",
     "; ".join(f"{k} {v:.3f}" for k, v in top), max(aucA.values()) <= 0.70 and round(aucA["multi_signal_count"], 2) == 0.69
     and round(aucA["banker_change_6m_flag"], 2) == 0.64 and round(aucA["share_of_wallet"], 2) == 0.64,
     "la ficha no lista multi_signal_flag (0.648), segundo en el ranking")
dec = pd.qcut(d.relationship_value.rank(method="first"), 10, labels=False)
rd = d.groupby(dec).hard_churn_6m.mean()
fact("Gradiente por tamaño", "tasa hard por decil de RV 5.2%–7.1%", f"{pct(rd.min()):.1f}%–{pct(rd.max()):.1f}%", round(pct(rd.min()), 1) == 5.2 and round(pct(rd.max()), 1) == 7.1)
PAIRS = [("aum_outflow_pct_90d", "aum_outflow_90d", 0.98), ("relationship_value", "aum", 0.97), ("net_deposit_flow_pct_90d", "deposit_balance_vs_6m_avg_pct", 0.91),
         ("deposit_balance_change_pct_90d", "deposit_balance_vs_6m_avg_pct", 0.88), ("transfer_to_competitor_pct_90d", "transfer_to_competitor_bank_amount_90d", 0.82),
         ("deposit_balance_change_pct_90d", "net_deposit_flow_pct_90d", 0.80), ("aum_outflow_pct_90d", "aum_vs_baseline_pct", 0.77),
         ("salary_deposit_stopped_flag", "recurring_deposit_stopped_flag", 0.76), ("multi_signal_flag", "multi_signal_count", 0.76),
         ("net_deposit_flow_pct_90d", "net_external_flow_pct_90d", 0.76)]
pr = []
for a, b, e in PAIRS:
    s = d[[a, b]].astype(float).corr(method="spearman").iloc[0, 1]
    pr.append({"var A": a, "var B": b, "|ρ| ficha": e, "|ρ| observado [DATA]": round(abs(s), 3), "coincide (±0.015)": abs(abs(s) - e) <= 0.015})
pairs = pd.DataFrame(pr)
fact("Pares redundantes |Spearman| > 0.75", "10 pares (ver step00_pairs.csv)", f"{int(pairs['coincide (±0.015)'].sum())} de 10 coinciden (±0.015)", pairs["coincide (±0.015)"].all())
imp = {"saldos < 0": int((df[["relationship_value", "deposit_balance", "aum"]] < 0).sum().sum()),
       "share_of_wallet ∉ (0, 1]": int((~df.share_of_wallet.between(1e-12, 1)).sum()), "tenure < 0": int((df.tenure_years < 0).sum())}
fact("Valores imposibles", "ninguno", "; ".join(f"{k}: {v}" for k, v in imp.items()), sum(imp.values()) == 0)
ficha = pd.DataFrame(F)
save_table(ficha, "step00_ficha")
save_table(pairs, "step00_pairs")

# ── Mapa de missing estructural ─────────────────────────────────────────────────────────
mm = []
for trig, cols in STRUCTURAL.items():
    g = d[trig].astype(bool)
    for c in cols:
        na = d[c].isna()
        mm.append({"variable": c, "gatillo": trig, "elegibles sin gatillo": int((~g).sum()), "NaN sin gatillo": int((na & ~g).sum()),
                   "valor sin gatillo (excepción)": int((~na & ~g).sum()), "NaN con gatillo (excepción)": int((na & g).sum()),
                   "% excepciones": pct(((~na & ~g) | (na & g)).mean())})
mmap = pd.DataFrame(mm)
save_table(mmap, "step00_missing_map")

# ── Opciones de target ──────────────────────────────────────────────────────────────────
nb = int(T.y_B.notna().sum())
opts = pd.DataFrame([
    {"opción": "A", "definición": "hard_churn_6m = pérdida total a 6M", "eventos": int(T.y_A.sum()), "base": int(T.y_A.notna().sum()), "indeterminados": 0,
     "comentario": "cierre total, no fuga parcial; horizonte 6M"},
    {"opción": "B", "definición": f"hard ∪ (soft con value_lost/RV ≥ {THETA_B:.2f}) = pérdida ≥ 25% en 6M", "eventos": int(T.y_B.sum()), "base": nb,
     "indeterminados": int(T.y_B_indet.sum()), "comentario": "definición económica (θ = 25%); soft 0.20–0.25 fuera de entrenamiento, dentro de scoring; mezcla 3M/6M"},
    {"opción": "C", "definición": "hard ∪ soft", "eventos": int(T.y_C.sum()), "base": int(T.y_C.notna().sum()), "indeterminados": 0, "comentario": "θ implícito = 20%"},
    {"opción": "D", "definición": "soft sólo", "eventos": int(T.y_D.sum()), "base": int(T.y_D.notna().sum()), "indeterminados": 0, "comentario": "solo fuga parcial a 3M"},
])
opts["tasa %"] = 100 * opts.eventos / opts.base
save_table(opts, "step00_target_options")

# ── Churn rate por households y por RV (A y B), total y por segmento ────────────────────
cr = []
for tname, y, extra in (("A", T.y_A, None), ("B", T.y_B, None)):
    for s_ in ("Total", "HNW", "UHNW"):
        m = y.notna() & ((df.segment == s_) if s_ != "Total" else True)
        yy = y[m]
        rvm, vlm = rv[m], df.value_lost_6m[m]
        cr.append({"target": tname, "segmento": s_, "base": int(m.sum()), "eventos": int(yy.sum()),
                   "churn hogares %": pct(yy.mean()),
                   "churn RV bruto % (Σ RV eventos / Σ RV)": pct((rvm * yy).sum() / rvm.sum()),
                   "churn económico % (Σ value_lost eventos / Σ RV)": pct((vlm * yy).sum() / rvm.sum())})
crt = pd.DataFrame(cr)
save_table(crt, "step00_churn_rates")

# ── Anti-leakage: prohibidas y cribado AUC / IV ─────────────────────────────────────────
proh = pd.DataFrame([{"columna": c, "motivo": ("resultado post-T0" if c in OUTCOMES else "identificador / fecha de corte")} for c in PROHIBITED] +
                    [{"columna": c, "motivo": "compuesto del proveedor sin regla documentada: solo challenger / análisis (I-3)"} for c in COMPOSITES])
save_table(proh, "step00_prohibited")


def iv_quick(x, y, bins=10):
    x = pd.Series(x).astype(float)
    g = pd.qcut(x.rank(method="first"), bins, labels=False) if x.notna().sum() > bins else pd.Series(0, index=x.index)
    g = g.astype("float").fillna(-1)
    t = pd.DataFrame({"g": g, "y": y}).groupby("g").y.agg(["sum", "size"])
    b, gd = t["sum"] + 0.5, (t["size"] - t["sum"]) + 0.5
    pb, pg = b / b.sum(), gd / gd.sum()
    return float(((pg - pb) * np.log(pg / pb)).sum())


yB_m = T.y_B.notna()
dB = df[yB_m]
yB = T.y_B[yB_m].astype(int)
ls = []
for c in cands:
    xa = d[c].astype(float)
    xb = dB[c].astype(float)
    ls.append({"variable": c, "compuesto": c in COMPOSITES, "% missing": pct(d[c].isna().mean()),
               "AUC A": auc_uni(xa.fillna(xa.median()), yA), "IV A": iv_quick(xa, yA.values),
               "AUC B": auc_uni(xb.fillna(xb.median()), yB), "IV B": iv_quick(xb, yB.values)})
lk = pd.DataFrame(ls)
lk["sospecha de fuga (AUC > 0.85 o IV > 0.50)"] = (lk[["AUC A", "AUC B"]].max(axis=1) > 0.85) | (lk[["IV A", "IV B"]].max(axis=1) > 0.50)
lk = lk.sort_values("AUC A", ascending=False)
save_table(lk, "step00_leakage_screen")
# control: las columnas de resultado sí filtrarían (muestra que el cribado detecta fuga)
ctrl = pd.DataFrame([{"columna de resultado": c, "AUC vs A": auc_uni(d[c].astype(float).fillna(0), yA)} for c in ["value_lost_6m", "soft_churn_3m"]])
save_table(ctrl, "step00_leakage_control")

# ── Reporte ─────────────────────────────────────────────────────────────────────────────
f2 = ficha.copy()
f2["coincide"] = f2.coincide.map({True: "sí", False: "**NO**"})
rep = f"""# Paso 0 · Verificación y definición del problema

## Objetivo
- Verificar la ficha del dataset (SPEC §C) contra `data/raw/client_pulse_synthetic.xlsx` y dejar calculadas las
  opciones de target, el churn rate y el cribado anti-fuga para decidir en G0.

## Método
- Carga de la hoja `{SHEET}`; hechos de la ficha recalculados por código; elegibles = `churn_excluded` = False.
- Target B: hard ∪ (soft con `value_lost_6m / relationship_value` ≥ θ = {THETA_B} [DEF propuesta]); soft con pérdida
  < θ = indeterminado (fuera de entrenamiento, dentro de scoring).
- Churn por hogares = eventos / base; por RV bruto = Σ RV de eventos / Σ RV; económico = Σ value_lost de eventos / Σ RV.
- Cribado anti-fuga: AUC univariada (missing → mediana solo para el cribado) e IV preliminar (10 cuantiles + bin de
  missing) contra A y B; sospecha si AUC > 0.85 o IV > 0.50.

## Código
- `src/step00_profile.py` · `tests/test_step00.py` · bootstrap único del archivo: `src/bootstrap_raw.py` (D0.1).

## Resultados

### Ficha del dataset [DATA]
{md_table(f2)}

- {int(ficha.coincide.sum())} de {len(ficha)} hechos coinciden. Las cifras de tamaño, historia y missing de la ficha
  están calculadas sobre los 19,877 elegibles, no sobre las 20,000 filas (D0.4).
- **Discrepancia D0.2**: la ficha afirma que RV ≠ AUM + depósitos ("medida propia"). En el archivo RV = AUM (0 si no
  hay inversiones) + depósitos con diferencia máxima de $0.01 [DATA]; la desigualdad solo aparece al comparar flotantes
  exactos (redondeo a centavos). Pregunta al usuario en G0.

### Pares redundantes [DATA]
{md_table(pairs)}

### Mapa de missing estructural (elegibles) [DATA]
{md_table(mmap, floatfmt=",.2f")}

- Regla verificada: sin gatillo ⟹ NaN, con 0 violaciones salvo `pension_deposit_stopped_flag`
  ({int(mmap.loc[mmap.variable == 'pension_deposit_stopped_flag', 'valor sin gatillo (excepción)'].iloc[0])} con valor sin
  `has_pension_stream`). Los NaN con gatillo presente son las excepciones de 1–3% (historia corta o patrón no detectado).

### Opciones de target [DATA]
{md_table(opts, floatfmt=",.2f")}

- Propuesta (SPEC): **B** principal, **A** sensibilidad obligatoria. Decide el usuario (I-1).
- Verificación: A = 1,200 y C = hard + soft = {int(T.y_A.sum()):,} + {int(T.y_D.sum()):,} = {int(T.y_C.sum()):,} [DATA];
  B = C − indeterminados = {int(T.y_C.sum()):,} − {int(T.y_B_indet.sum())} = {int(T.y_B.sum()):,} [DATA]; base B = 19,877 − {int(T.y_B_indet.sum())} = {nb:,} [DATA].

### Churn rate: hogares, RV bruto y económico [DATA]
{md_table(crt, floatfmt=",.2f")}

- Verificación: churn de cartera = Σ share × tasa por segmento (A hogares:
  {100 * (crt.query("target=='A' and segmento!='Total'").base / crt.query("target=='A' and segmento=='Total'").base.iloc[0] * crt.query("target=='A' and segmento!='Total'")['churn hogares %']).sum():.4f}%
  = {crt.query("target=='A' and segmento=='Total'")['churn hogares %'].iloc[0]:.4f}% [DATA]).
- Churn rate (tasa de la cartera), score (puntos de la escala PDO: S₀ = {S0} @ {O0:.0f}:1, PDO = {PDO} ⟹ Factor
  {FACTOR:.2f}, Offset {OFFSET:.2f} [DEF]) y probabilidad calibrada (por hogar) son tres magnitudes distintas.

### Anti-fuga [DATA]
- Prohibidas como predictor: {', '.join(f'`{c}`' for c in PROHIBITED)}. Compuestos (`multi_signal_count`,
  `multi_signal_flag`): solo challenger / análisis hasta I-3.
- Placebo temporal: imposible (un solo snapshot, sin timestamps) → limitación L1/L2.
- Cribado: {int(lk['sospecha de fuga (AUC > 0.85 o IV > 0.50)'].sum())} variables sospechosas. Máximos: AUC A
  {lk['AUC A'].max():.3f} (`{lk.sort_values('AUC A', ascending=False).variable.iloc[0]}`), AUC B {lk['AUC B'].max():.3f}
  (`{lk.sort_values('AUC B', ascending=False).variable.iloc[0]}`), IV A {lk['IV A'].max():.3f}
  (`{lk.sort_values('IV A', ascending=False).variable.iloc[0]}`), IV B {lk['IV B'].max():.3f}
  (`{lk.sort_values('IV B', ascending=False).variable.iloc[0]}`).
- Control del cribado: `value_lost_6m` tendría AUC vs A = {ctrl.iloc[0, 1]:.3f} [DATA] (el cribado sí detecta una columna
  de resultado).

Top 10 por AUC vs A:
{md_table(lk.head(10)[['variable', 'compuesto', '% missing', 'AUC A', 'IV A', 'AUC B', 'IV B']], floatfmt=",.3f")}

- Tabla completa: `outputs/tables/step00_leakage_screen.csv`.

### Horizonte, unidad y T0
- Horizonte 6M (A y B) fijado por el dato; ventana de observación = la de las señales del proveedor (60/90/180 días,
  6M, baseline); `history_months` ≤ 24 [DATA]. Unidad: household. T0 = 2025-12-31 (único). Sin cohortes ni OOT (L1).

## Tests
- `tests/test_step00.py`: ver salida de pytest en `reports/gate_0.md`.

## Decisiones y preguntas abiertas
- D0.1 bootstrap del xlsx · D0.2 discrepancia RV · D0.3 definición de ρ en compuestos · D0.4 base de la ficha =
  elegibles. Preguntas I-1 a I-10 en `reports/gate_0.md`.
"""
(REPORTS / "step00.md").write_text(rep, encoding="utf-8")
print(f2[["hecho", "coincide"]].to_string(index=False))
print(opts.to_string(index=False))
print(crt.round(2).to_string(index=False))
print(lk.head(8).round(3).to_string(index=False))
