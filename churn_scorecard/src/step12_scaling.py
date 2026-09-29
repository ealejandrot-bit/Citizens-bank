"""Paso 12 · Escalamiento PDO, tramos, bandas, escala maestra, overrides y salida por household.

- Score = Offset + Factor · ln(odds buenos) = base + Σ puntos_j; base = Offset + Factor·β₀ (corregido);
  puntos_j = Factor·β_j·WoE_j, redondeados a entero; score = base redondeada + Σ puntos redondeados (assert por fila).
  El lookup incluye además la forma del SPEC con la base repartida: (β_j·WoE_j + β₀/n)·Factor + Offset/n.
- Probabilidad: la del modelo con intercepto corregido (pre-Platt); se recalibra sobre validación en el paso 14 (D12.1).
- Tramos (tabla H-3) diseñados en dev: capacidad sin dato (I-2) ⟹ se buscan cortes por percentil de score (grilla 1%)
  que cumplan: tasa observada con salto ≥ 2x entre tramos contiguos (≥ 1.5x admisible en Vigilancia/Estable), lift
  Crítico/Estable ≥ 5x, ≥ 70 eventos por tramo en dev (≈ 30 en validación con la razón dev/val 1,871/803; D12.2).
  Entre los factibles se elige el de mayor IV de tramo (más información conservada); desempate: Crítico más grande.
- Bandas AAA…CCC/D anidadas en los tramos (Estable → AAA/AA/A, Vigilancia → BBB/BB, Alto → B, Crítico → CCC/D).
- Overrides (disponibles en el archivo): banker_change_6m_flag, complaint_escalated_flag, transfer_to_competitor_pct_90d
  ≥ 10%, trustee_change_flag. Precisión (tasa B) de los hogares que el override mueve, en dev: ≥ 25% → Crítico,
  12–25% → Alto, < 12% se elimina; si los movidos superan 30% del tramo destino se prueba el tramo inferior, si no se
  elimina (D12.3). Validación de precisión en el paso 13.
- Salida: outputs/scores/household_scores.csv para los 20,000 hogares (banderas de población).
"""
from __future__ import annotations

import itertools
import pickle

import numpy as np
import pandas as pd

from common import FACTOR, MODEL, OFFSET, PROC, REPORTS, SCORES, load_raw, md_table, save_table, set_seed
from woe import woe_iv

set_seed()
CH = pickle.load(open(MODEL / "step11A_champion.pkl", "rb"))
V, BIN, beta, b0 = CH["vars"], CH["binning"], CH["params"].iloc[1:], CH["b0_corr"]
F = pd.read_parquet(PROC / "features.parquet")
F["segment_uhnw"] = (F.segment == "UHNW").astype(int)
F = F.merge(pd.read_parquet(PROC / "step07_clusters.parquet"), on="household_id")
pop = pd.read_parquet(PROC / "step01_population.parquet")[["household_id", "excl_reason", "in_pop_B", "y_B", "y_B_indet"]]
part = pd.concat([pd.read_parquet(PROC / f"{p}.parquet", columns=["household_id"]).assign(partición=p) for p in ("dev", "val")])
F = F.merge(pop, on="household_id").merge(part, on="household_id", how="left")
F["partición"] = F["partición"].fillna("fuera de desarrollo")

# ── Lookup y score ───────────────────────────────────────────────────────────────────────────────────────────
n = len(V)
BASE = int(round(OFFSET + FACTOR * b0))
look = []
for c in V:
    vb = BIN[c]
    for lab in vb.labels:
        w = vb.woe.get(lab, 0.0)
        look.append({"variable": c, "bin": lab, "WoE": w, "β": beta[c], "puntos": int(round(FACTOR * beta[c] * w)),
                     "puntos (SPEC, base repartida)": (beta[c] * w + b0 / n) * FACTOR + OFFSET / n, "neutral": lab in vb.neutral})
LABS = {}
for c in V:                                                 # bins no observados en dev (solo hogares fuera de población): neutral (D12.5)
    r = F[f"{c}__miss"] if f"{c}__miss" in F else None
    LABS[c] = BIN[c].bin_labels(F[c], r)
    for lab in sorted(set(LABS[c]) - set(BIN[c].labels)):
        look.append({"variable": c, "bin": lab, "WoE": 0.0, "β": beta[c], "puntos": 0, "puntos (SPEC, base repartida)": b0 / n * FACTOR + OFFSET / n,
                     "neutral": True, "no observado en dev": True, "hogares": int((LABS[c] == lab).sum())})
look = pd.DataFrame(look)
look["no observado en dev"] = look["no observado en dev"].fillna(False).astype(bool)
save_table(look, "step12_lookup")
PTS = {}
for c in V:
    m = look[look.variable == c].set_index("bin")["puntos"]
    PTS[c] = pd.Series(LABS[c]).map(m).to_numpy()
    assert not np.isnan(PTS[c].astype(float)).any()
P = pd.DataFrame(PTS)
F["score"] = BASE + P.sum(axis=1).to_numpy()
assert (F.score == BASE + P.sum(axis=1)).all()
F["probabilidad"] = 1 / (1 + np.exp((F.score - OFFSET) / FACTOR))          # p de churn implícita en el score redondeado
MAXP = look.groupby("variable").puntos.max()
LOSS = MAXP[V].to_numpy() - P.to_numpy()                                    # puntos perdidos vs mejor bin
order = np.argsort(-LOSS, axis=1)
for i in range(3):
    F[f"driver_{i + 1}"] = [V[j] if LOSS[r, j] > 0 else "" for r, j in enumerate(order[:, i])]
    F[f"driver_{i + 1}_puntos_perdidos"] = [int(LOSS[r, j]) if LOSS[r, j] > 0 else 0 for r, j in enumerate(order[:, i])]

# ── Tramos (dev) ─────────────────────────────────────────────────────────────────────────────────────────────
dv = F[(F["partición"] == "dev") & F.in_pop_B].reset_index(drop=True)
yd = dv.y_B.astype(int).to_numpy()
q = dv.score.rank(pct=True, method="first").to_numpy()                      # 0 = peor score (más riesgo)
ratio = 1871 / 803
MIN_EV_DEV = int(np.ceil(30 * ratio))


def evaluate(c1, c2, c3):
    g = np.select([q <= c1, q <= c2, q <= c3], [0, 1, 2], 3)
    n_ = np.bincount(g, minlength=4)
    e_ = np.bincount(g, weights=yd, minlength=4)
    r_ = e_ / n_
    ok = (e_ >= MIN_EV_DEV).all() and r_[0] >= 2 * r_[1] and r_[1] >= 2 * r_[2] and r_[2] >= 1.5 * r_[3] and r_[0] >= 5 * r_[3]
    iv = woe_iv(n_ - e_, e_)[1].sum()
    return ok, iv, n_, e_, r_


cand = []
for a, b, c in itertools.product(range(1, 16), range(5, 51), range(15, 81)):
    if a < b < c:
        ok, iv, n_, e_, r_ = evaluate(a / 100, b / 100, c / 100)
        if ok:
            cand.append((iv, a, b, c))
assert cand, "sin cortes factibles"
cand.sort(key=lambda t: (round(t[0], 6), t[1]), reverse=True)
_, A_, B_, C_ = cand[0]
cuts_q = [A_ / 100, B_ / 100, C_ / 100]
sd = np.sort(dv.score.to_numpy())
CUT = [float(sd[int(np.ceil(cq * len(sd))) - 1]) for cq in cuts_q]            # score ≤ corte ⟹ tramo más riesgoso
TR = ["Crítico", "Alto", "Vigilancia", "Estable"]


def tramo(s):
    return np.select([s <= CUT[0], s <= CUT[1], s <= CUT[2]], TR[:3], TR[3])


F["tramo_modelo"] = tramo(F.score)
# Bandas anidadas
BANDS = {"Estable": ["A", "AA", "AAA"], "Vigilancia": ["BB", "BBB"], "Alto": ["B"], "Crítico": ["CCC/D"]}
F["banda"] = ""
band_cuts, BAND_USED = {}, {}
dv_t = tramo(dv.score)
for t, bl in BANDS.items():
    m = F.tramo_modelo == t
    sel_ = dv_t == t
    s_dev, e_dev = dv.score[sel_].to_numpy(), yd[sel_]
    k = int(max(1, min(len(bl), e_dev.sum() // MIN_EV_DEV)))
    names = bl[-k:]                                              # se conserva la mejor banda del tramo (D12.4)
    while True:                                                  # cortes por eventos acumulados; se reduce k si un corte deja < MIN_EV
        o = np.argsort(s_dev)
        ce = np.cumsum(e_dev[o])
        qs = np.unique([s_dev[o][np.searchsorted(ce, e_dev.sum() * j / k)] for j in range(1, k)]) if k > 1 else np.array([])
        lab = np.searchsorted(qs, s_dev, side="left")
        ev_b = np.bincount(lab, weights=e_dev, minlength=k)
        if k == 1 or (len(qs) == k - 1 and ev_b.min() >= MIN_EV_DEV):
            break
        k -= 1
        names = bl[-k:]
    band_cuts[t], BAND_USED[t] = qs, names
    F.loc[m, "banda"] = np.array(names)[np.searchsorted(qs, F.loc[m, "score"].to_numpy(), side="left")]

# ── Overrides (diseño en dev) ────────────────────────────────────────────────────────────────────────────────
RULES = {"banker_change_6m_flag = 1": F.banker_change_6m_flag == 1, "complaint_escalated_flag = 1": F.complaint_escalated_flag == 1,
         "transfer_to_competitor_pct_90d ≥ 10%": F.transfer_to_competitor_pct_90d >= 0.10, "trustee_change_flag = 1": F.trustee_change_flag == 1}
RANK = {t: i for i, t in enumerate(TR)}
isdev = (F["partición"] == "dev") & F.in_pop_B
ov_rows, ACTIVE = [], {}
for name, m in RULES.items():
    m = m.fillna(False).to_numpy()
    for dest in ("Crítico", "Alto"):
        moved = m & (F.tramo_modelo.map(RANK).to_numpy() > RANK[dest])
        md = moved & isdev.to_numpy()
        prec = float(F.y_B[md].mean()) if md.sum() else np.nan
        size_dest = int(((F.tramo_modelo == dest) & isdev).sum())
        share = md.sum() / size_dest
        need = 0.25 if dest == "Crítico" else 0.12
        cap_ok = share <= 0.30
        row = {"regla": name, "destino probado": dest, "hogares activos dev": int((m & isdev.to_numpy()).sum()), "movidos dev": int(md.sum()),
               "precisión movidos %": 100 * prec, "movidos / tramo destino %": 100 * share, "umbral precisión %": 100 * need,
               "cumple precisión": prec >= need, "cumple ≤ 30%": cap_ok}
        ov_rows.append(row)
        if prec >= need and cap_ok and name not in ACTIVE:
            ACTIVE[name] = dest
    decision = ACTIVE.get(name, "eliminada")
    for r_ in ov_rows:
        if r_["regla"] == name:
            r_["decisión"] = decision
ov = pd.DataFrame(ov_rows)
_any = np.zeros(len(F), bool)
for name, dest in ACTIVE.items():
    _any |= RULES[name].fillna(False).to_numpy() & (F.tramo_modelo.map(RANK).to_numpy() > RANK[dest])
COMB = {"movidos dev (unión de reglas activas)": int((_any & isdev.to_numpy()).sum()),
        "tramo Alto (modelo) dev": int(((F.tramo_modelo == "Alto") & isdev).sum())}
COMB["% del tramo destino"] = 100 * COMB["movidos dev (unión de reglas activas)"] / COMB["tramo Alto (modelo) dev"]
COMB["precisión movidos %"] = 100 * float(F.y_B[_any & isdev.to_numpy()].mean())
save_table(ov, "step12_overrides")
F["overrides"] = ""
F["tramo"] = F.tramo_modelo
for name, dest in ACTIVE.items():
    act = RULES[name].fillna(False)
    F.loc[act, "overrides"] = (F.loc[act, "overrides"] + "; " + name).str.strip("; ")
    F.loc[act & (F.tramo.map(RANK) > RANK[dest]), "tramo"] = dest

# ── Escala maestra (dev, tramo final) ────────────────────────────────────────────────────────────────────────
def master(df, weight=None):
    rows = []
    tot_n, tot_e = len(df), df.y_B.sum()
    rv = df.relationship_value
    for t in TR:
        g = df[df.tramo == t]
        rows.append({"tramo": t, "score mín": int(g.score.min()), "score máx": int(g.score.max()), "hogares": len(g), "% hogares": 100 * len(g) / tot_n,
                     "% RV": 100 * g.relationship_value.sum() / rv.sum(), "p media %": 100 * g.probabilidad.mean(),
                     "churn esperado (Σp)": g.probabilidad.sum(), "eventos observados": int(g.y_B.sum()), "tasa observada %": 100 * g.y_B.mean(),
                     "captura eventos %": 100 * g.y_B.sum() / tot_e,
                     "captura RV de eventos %": 100 * (g.relationship_value * g.y_B).sum() / (rv * df.y_B).sum(),
                     "lift": g.y_B.mean() / df.y_B.mean()})
    return pd.DataFrame(rows)


dvf = F[isdev].reset_index(drop=True)
ms = master(dvf)
GOV = {"Crítico": "banquero + líder de equipo, contacto ≤ 5 días hábiles", "Alto": "banquero, contacto ≤ 15 días hábiles",
       "Vigilancia": "seguimiento en revisión mensual", "Estable": "gestión normal"}
ms["gobernanza [DEF-default paso 16]"] = ms.tramo.map(GOV)
save_table(ms, "step12_master_scale")
ms_model = master(dvf.assign(tramo=dvf.tramo_modelo))
save_table(ms_model, "step12_master_scale_pre_override")
msrv = ms[["tramo", "% RV", "captura RV de eventos %"]].copy()
msrv["RV total $M"] = [dvf.loc[dvf.tramo == t, "relationship_value"].sum() / 1e6 for t in TR]
msrv["RV de eventos $M"] = [(dvf.relationship_value * dvf.y_B)[dvf.tramo == t].sum() / 1e6 for t in TR]
msrv["RV esperado en riesgo $M (Σ p·RV)"] = [(dvf.probabilidad * dvf.relationship_value)[dvf.tramo == t].sum() / 1e6 for t in TR]
save_table(msrv, "step12_master_scale_rv")
ORDER = [b for t in ("Crítico", "Alto", "Vigilancia", "Estable") for b in BAND_USED[t]]
bands = dvf.groupby("banda").agg(hogares=("y_B", "size"), eventos=("y_B", "sum"), tasa=("y_B", "mean"), score_mín=("score", "min"),
                                 score_máx=("score", "max")).reindex(ORDER).reset_index()
bands["tramo"] = bands.banda.map({b: t for t, bl in BANDS.items() for b in bl})
bands["tasa"] *= 100
save_table(bands, "step12_bands")

# Caseload (todos los hogares puntuables en producción: 20,000)
cl = []
for t in ("Crítico", "Alto"):
    nt = int((F.tramo == t).sum())
    cl.append({"tramo": t, "hogares (20,000 puntuados)": nt, **{f"por banquero ({k})": nt / k for k in (40, 100, 200)}})
cl = pd.DataFrame(cl)
save_table(cl, "step12_caseload")

# ── Salida por household ─────────────────────────────────────────────────────────────────────────────────────
F["prioridad_intra_tramo"] = F.probabilidad * F.relationship_value
F["población"] = np.select([F.excl_reason == "tenure_lt_1", F.excl_reason == "churn_excluded", F.y_B_indet.astype(bool)],
                           ["fuera de población de desarrollo (antigüedad < 1, G1-2)", "excluido (churn_excluded, I-4)", "indeterminado B"], "desarrollo")
out = F[["household_id", "segment", "cluster", "score", "probabilidad", "tramo", "tramo_modelo", "banda", "driver_1", "driver_1_puntos_perdidos",
         "driver_2", "driver_2_puntos_perdidos", "driver_3", "driver_3_puntos_perdidos", "overrides", "prioridad_intra_tramo", "población", "partición"]]
out = out.rename(columns={"segment": "segmento", "probabilidad": "probabilidad_pre_calibración"})
SCORES.mkdir(parents=True, exist_ok=True)
out.to_csv(SCORES / "household_scores.csv", index=False)
F[["household_id", "score", "probabilidad", "tramo", "tramo_modelo", "banda", "overrides"]].to_parquet(PROC / "step12_scores.parquet", index=False)
with open(MODEL / "step12_scaling.pkl", "wb") as fh:
    pickle.dump({"bands_used": BAND_USED, "base": BASE, "cuts": CUT, "cuts_pct": cuts_q, "band_cuts": band_cuts, "overrides": ACTIVE, "min_ev_dev": MIN_EV_DEV}, fh)
cut_t = pd.DataFrame({"corte": ["Crítico / Alto", "Alto / Vigilancia", "Vigilancia / Estable"], "percentil dev (peor score)": [100 * c for c in cuts_q],
                      "score ≤": CUT})
save_table(cut_t, "step12_cuts")
save_table(pd.DataFrame(cand[:10], columns=["IV tramo", "Crítico %", "Crítico+Alto %", "Crítico+Alto+Vigilancia %"]), "step12_cut_candidates")

# ── Reporte ──────────────────────────────────────────────────────────────────────────────────────────────────
ex = dvf.iloc[0]
ex_pts = {c: int(PTS[c][F.index[F.household_id == ex.household_id][0]]) for c in V}
ex_t = pd.DataFrame({"componente": ["base"] + V, "puntos": [BASE] + [ex_pts[c] for c in V]})
rep = f"""# Paso 12 · Escalamiento, tramos, salida por household

## Objetivo
- Pasar el campeón a puntos (escala PDO), definir tramos y bandas con reglas previas a ver resultados, y entregar el score
  por household con drivers y overrides.

## Método
- Escala: S₀ = 600 @ 20:1, PDO = 40 ⟹ Factor {FACTOR:.2f}, Offset {OFFSET:.2f} [DEF-default I-6]. Score = base + Σ puntos;
  base = Offset + Factor·β₀ = {BASE} [DATA]; puntos_j = Factor·β_j·WoE_j (enteros). Score alto = menos churn.
- Probabilidad = la del score (intercepto corregido, pre-Platt); se recalibra en el paso 14 (D12.1).
- Tramos (H-3) en dev: grilla de percentiles 1%; saltos ≥ 2x (Crítico/Alto, Alto/Vigilancia), ≥ 1.5x
  (Vigilancia/Estable), lift Crítico/Estable ≥ 5x, ≥ {MIN_EV_DEV} eventos por tramo en dev (≈ 30 en validación; D12.2);
  entre factibles, mayor IV de tramo ({len(cand):,} configuraciones factibles [DATA]).
- Overrides: precisión de los hogares movidos en dev (≥ 25% Crítico, 12–25% Alto, < 12% fuera; ≤ 30% del tramo destino; D12.3).
- Drivers: variables con más puntos perdidos frente a su mejor bin.
- Bins no observados en dev ("sin dato" en hogares con antigüedad < 1): 0 puntos, neutral, marcados en el lookup (D12.5):
  {', '.join(f"`{r.variable}` {int(r.hogares)}" for r in look[look['no observado en dev']].itertuples())} hogares [DATA].

## Código
- `src/step12_scaling.py` · `tests/test_step12.py` · `step12_*.csv`, `outputs/scores/household_scores.csv`.

## Resultados

### Cortes de tramo [DATA]
{md_table(cut_t, floatfmt=",.1f")}

### Escala maestra · households (dev, tramo final con overrides) [DATA]
{md_table(ms.drop(columns=["% RV", "captura RV de eventos %"]), floatfmt=",.2f")}

- Verificación: % hogares suma {ms['% hogares'].sum():.1f}%; captura suma {ms['captura eventos %'].sum():.1f}%; churn de cartera
  Σ share × tasa = {(ms['% hogares'] * ms['tasa observada %']).sum() / 100:.2f}% = tasa dev {100 * dvf.y_B.mean():.2f}% [DATA].
- Saltos de tasa [DATA]: Crítico/Alto {ms['tasa observada %'][0] / ms['tasa observada %'][1]:.2f}x · Alto/Vigilancia {ms['tasa observada %'][1] / ms['tasa observada %'][2]:.2f}x ·
  Vigilancia/Estable {ms['tasa observada %'][2] / ms['tasa observada %'][3]:.2f}x · lift Crítico/Estable {ms['tasa observada %'][0] / ms['tasa observada %'][3]:.2f}x.

### Escala maestra · RV (dev) [DATA]
{md_table(msrv, floatfmt=",.1f")}

- Verificación: % RV suma {msrv['% RV'].sum():.1f}%; captura RV de eventos suma {msrv['captura RV de eventos %'].sum():.1f}% [DATA].

### Escala antes de overrides (dev) [DATA]
{md_table(ms_model[['tramo', 'hogares', '% hogares', 'eventos observados', 'tasa observada %', 'lift']], floatfmt=",.2f")}

### Bandas (dev) [DATA]
{md_table(bands, floatfmt=",.1f")}

- Verificación: hogares suman {int(bands.hogares.sum()):,} = {len(dvf):,}; eventos {int(bands.eventos.sum()):,} = {int(dvf.y_B.sum()):,} [DATA].

### Overrides (diseño en dev) [DATA]
{md_table(ov, floatfmt=",.1f")}

- Activos: {', '.join(f'{k} → {v}' for k, v in ACTIVE.items()) or 'ninguno'} [DATA].
- Unión de reglas activas: {COMB['movidos dev (unión de reglas activas)']:,} hogares movidos = {COMB['% del tramo destino']:.1f}% del tramo Alto del modelo,
  precisión {COMB['precisión movidos %']:.1f}% [DATA]. Cada regla cumple ≤ 30%; la unión no (D12.3, pregunta G3). Sin datos de fallecimiento ni liquidity event en el archivo.

### Caseload (20,000 hogares puntuados) [DATA]
{md_table(cl, floatfmt=",.1f")}

### Ejemplo: Σ puntos + base = score (hogar {ex.household_id}) [DATA]
{md_table(ex_t)}

- Verificación: {BASE} + {sum(ex_pts.values())} = {BASE + sum(ex_pts.values())} = score {int(ex.score)} [DATA]; el test lo verifica en los 20,000 hogares.

### Lookup (puntos por bin) [DATA]
{md_table(look[['variable', 'bin', 'WoE', 'puntos', 'puntos (SPEC, base repartida)']], floatfmt=",.3f")}

## Tests
- `tests/test_step12.py` (ver pytest).

## Decisiones y preguntas abiertas
- D12.1–D12.4 en `reports/decision_log.md`.
"""
(REPORTS / "step12.md").write_text(rep, encoding="utf-8")
print(cut_t.to_string(index=False)); print(ms.round(2).to_string(index=False)); print(bands.round(1).to_string(index=False)); print(ov.round(1).to_string(index=False)); print(cl.round(1).to_string(index=False)); print(len(cand))
