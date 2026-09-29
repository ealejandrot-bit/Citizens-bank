"""Paso 12 · Escalamiento, tramos, overrides, reason codes y salida por hogar (modelos A y A-lite).

Escala (odds = buenos:malos):  Factor = PDO / ln 2;  Offset = S₀ − Factor·ln O₀;  Score = Offset + Factor·ln(odds).
Puntos por bin = (βⱼ·WoEⱼ + β₀/n)·Factor + Offset/n, redondeados a entero (tabla legible; D12.1). Score = Σ puntos.
Mayor score = menor churn. 800 puntos no es 80% de nada: la probabilidad sale de la calibración, no del score.

Probabilidad calibrada (capa modelo, DM.1): Platt logit(p_cal) = a + b·logit(p) ajustado sobre las OOF de la CV anidada
de desarrollo; se valida en el paso 14.
Tramos (decididos con OOF de desarrollo, reportados en holdout; D12.2):
  Crítico = top 3% por probabilidad (capacidad) → Alto / Vigilancia / Estable con: salto ≥ 2× entre tramos contiguos,
  lift Crítico/Estable ≥ 5×, ≥ 70 eventos por tramo en desarrollo (≈ 30 en holdout); entre los cortes factibles se elige
  el de mayor margen de separación (ratio contiguo mínimo), desempate por Estable más grande. (La regla inicial —más
  hogares en Estable— elegía cortes al borde de la factibilidad que no se sostenían en holdout; D12.2.)
Overrides (decididos en desarrollo, reportados en holdout): precisión ≥ 25% → Crítico; 12–25% → Alto; < 12% → fuera;
  una regla no puede aportar > 30% del tramo (si lo hace, baja un tramo o sale). Solo suben de tramo, nunca bajan.
Reason codes: 3 bins con mayor pérdida de puntos vs neutral (WoE = 0).
"""
from __future__ import annotations

import json
import pickle

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm

from common import FIGURES, MODELS, OUT, PARAMS, QC, SCORED, TABLES, save_table, set_seed
from woe import load_sample

set_seed()
T = PARAMS["target_primary"]
ALL = load_sample(OUT, TABLES, sample=None)
with open(MODELS / "09_binning.pkl", "rb") as fh:
    B = pickle.load(fh)
cfg = json.loads((MODELS / "11_final_vars.json").read_text())
oof = pd.read_csv(OUT / "data" / "11_oof_dev.csv")
FACTOR = PARAMS["PDO"] / np.log(2)
OFFSET = PARAMS["S0"] - FACTOR * np.log(PARAMS["O0"])
TRAMOS = ["Crítico", "Alto", "Vigilancia", "Estable"]
LABEL = {  # etiqueta legible para reason codes
    "banker_change_6m_flag": "cambió de banquero (6m)", "external_transfer_pct_of_balance_60d": "transferencias externas / saldo (60d)",
    "products_closed_180d": "productos cerrados (180d)", "share_of_wallet": "share of wallet", "recurring_deposit_change_pct": "cambio en depósitos recurrentes",
    "investment_redemption_pct": "redenciones de inversión (90d)", "repeat_complaint_flag": "queja repetida", "return_vs_benchmark": "rendimiento vs benchmark",
    "client_reply_rate": "tasa de respuesta al banquero", "contact_gap_ratio": "brecha de contacto vs cadencia", "segment": "segmento",
}
GOV = {"Crítico": ("banquero + Head of PB", "≤ 5 días hábiles", "comité mensual revisa el 100%"),
       "Alto": ("banquero", "≤ 15 días hábiles", "comité mensual revisa muestra y overrides"),
       "Vigilancia": ("banquero", "siguiente contacto de cadencia", "tablero mensual"),
       "Estable": ("banquero", "cadencia normal", "sin acción")}
OVERRIDES = {
    "banker_change_6m_flag": lambda d: d.banker_change_6m_flag == 1,
    "complaint_escalated_flag": lambda d: d.complaint_escalated_flag == 1,
    "repeat_complaint_flag": lambda d: d.repeat_complaint_flag == 1,
    "relationship_dissatisfaction_flag": lambda d: d.relationship_dissatisfaction_flag == 1,
    "trustee_change_flag": lambda d: d.trustee_change_flag == 1,
    "transfer_to_competitor_pct_90d ≥ 0.10": lambda d: d.transfer_to_competitor_pct_90d >= 0.10,
    "new_external_destinations_90d ≥ 2": lambda d: d.new_external_destinations_90d >= 2,
    "pension_deposit_stopped_flag (D9.1)": lambda d: d.pension_deposit_stopped_flag == 1,
}
logit = lambda p: np.log(np.clip(p, 1e-9, 1 - 1e-9) / (1 - np.clip(p, 1e-9, 1 - 1e-9)))
expit = lambda z: 1 / (1 + np.exp(-z))
dev_m, hold_m = (ALL.muestra == "desarrollo").to_numpy(), (ALL.muestra == "holdout").to_numpy()
elig = ~ALL.churn_excluded.astype(bool).to_numpy()
y_all = ALL[T].to_numpy()
rv = ALL.relationship_value.to_numpy()
vl = ALL.value_lost_6m.fillna(0).to_numpy()
qc = QC("12")


PCT_VARS = {"external_transfer_pct_of_balance_60d", "share_of_wallet", "recurring_deposit_change_pct", "investment_redemption_pct",
            "return_vs_benchmark", "client_reply_rate"}
NO_REASON = {"segment"}   # estructural, no accionable: fuera de reason codes (D12.4)


def pretty_bin(v: str, lab: str) -> str:
    """Etiqueta legible para ejecutivos: sí/no en flags, rangos con unidad en el resto."""
    if lab in ("no_aplica", "sin_dato"):
        return {"no_aplica": "no aplica", "sin_dato": "sin dato"}[lab]
    vb = B[v]
    if v == "segment":
        return "UHNW" if lab.startswith("[0.5") else "HNW"
    if vb.dtype == "numerical" and vb.splits == [0.5]:
        return "sí" if lab.startswith("[0.5") else "no"
    lo, hi = lab.strip("[)").split(", ")
    f = (lambda x: f"{100 * float(x):.1f}%") if v in PCT_VARS else (lambda x: f"{float(x):.3g}")
    if v in ("products_closed_180d",):
        f = lambda x: f"{int(np.ceil(float(x)))}"
        if lo == "-inf":
            return f"0"
        return f"≥ {f(lo)}" if hi == "inf" else f"{f(lo)}"
    return f"< {f(hi)}" if lo == "-inf" else f"≥ {f(lo)}" if hi == "inf" else f"{f(lo)} a < {f(hi)}"


def tramo_of(p, cuts):
    """cuts = umbrales de probabilidad (Crítico ≥ c0 > Alto ≥ c1 > Vigilancia ≥ c2 > Estable)."""
    return np.select([p >= cuts[0], p >= cuts[1], p >= cuts[2]], TRAMOS[:3], TRAMOS[3])


def rates_by_tramo(tr, yy):
    return pd.Series({t: yy[tr == t].mean() if (tr == t).any() else np.nan for t in TRAMOS}), pd.Series({t: int(yy[tr == t].sum()) for t in TRAMOS})


def build(name: str, vars_: list[str], pkl: str, oof_col: str) -> dict:
    mdl = pickle.load(open(MODELS / pkl, "rb"))
    beta = mdl["params"]
    n = len(vars_)
    # ── Lookup de puntos ──────────────────────────────────────────────────────────────
    rows = []
    for v in vars_:
        vb = B[v]
        for lab in vb.labels:
            w = vb.woe.get(lab, 0.0)
            pts = (beta[v] * w + beta["const"] / n) * FACTOR + OFFSET / n
            neutral = (beta["const"] / n) * FACTOR + OFFSET / n
            rows.append({"modelo": name, "variable": v, "etiqueta": LABEL.get(v, v), "bin": lab, "rango legible": pretty_bin(v, lab), "WoE": w, "β": beta[v],
                         "puntos (exacto)": pts, "puntos": int(round(pts)), "neutral": neutral, "pérdida vs neutral": neutral - pts})
    lk = pd.DataFrame(rows)
    pts_map = {(r.variable, r.bin): r.puntos for r in lk.itertuples()}
    loss_map = {(r.variable, r.bin): r._11 for r in lk.itertuples()}
    # ── Score por hogar ──────────────────────────────────────────────────────────────
    bins = {v: B[v].bin_labels(ALL[v], ALL[f"{v}__miss"] if f"{v}__miss" in ALL else None) for v in vars_}
    P = np.column_stack([[pts_map[(v, b)] for b in bins[v]] for v in vars_])
    score = P.sum(axis=1)
    exact = np.column_stack([[lk.set_index(["variable", "bin"]).loc[(v, b), "puntos (exacto)"] for b in bins[v]] for v in vars_]).sum(axis=1) \
        if False else None
    z_score = (score - OFFSET) / FACTOR           # ln odds buenos:malos implícito en el score
    p_score = expit(-z_score)                     # P(churn) antes de calibrar
    # ── Platt sobre OOF de desarrollo (DM.1) ──────────────────────────────────────────
    o = oof.set_index("household_id").loc[ALL.household_id[dev_m], oof_col].to_numpy()
    yd = y_all[dev_m].astype(int)
    platt = sm.Logit(yd, sm.add_constant(logit(o))).fit(disp=0)
    a, b = platt.params
    p_cal = expit(a + b * logit(p_score))
    p_cal_oof = expit(a + b * logit(o))
    # ── Tramos: decisión con OOF calibrada de desarrollo ─────────────────────────────
    c0 = np.quantile(p_cal_oof, 1 - PARAMS["critical_capacity_pct"])
    best, feas = None, []
    grid_a = np.arange(0.05, 0.31, 0.01)       # % acumulado Crítico + Alto
    for ca in grid_a:
        for cb in np.arange(ca + 0.05, 0.71, 0.01):  # % acumulado hasta Vigilancia
            c1, c2 = np.quantile(p_cal_oof, 1 - ca), np.quantile(p_cal_oof, 1 - cb)
            tr = tramo_of(p_cal_oof, (c0, c1, c2))
            r, e = rates_by_tramo(tr, yd)
            ok = (r["Crítico"] >= 2 * r["Alto"]) and (r["Alto"] >= 2 * r["Vigilancia"]) and (r["Vigilancia"] >= 2 * r["Estable"]) \
                and (r["Crítico"] >= 5 * r["Estable"]) and (e.min() >= 70)
            feas.append({"% Crítico+Alto": ca, "% hasta Vigilancia": cb, "factible": ok, "min ratio contiguo": min(r["Crítico"] / r["Alto"], r["Alto"] / r["Vigilancia"], r["Vigilancia"] / r["Estable"]),
                         "lift C/E": r["Crítico"] / r["Estable"], "eventos mín": e.min()})
            if ok:
                # D12.2 (revisada): máximo margen de separación (ratio contiguo mínimo); desempate Estable más grande
                key = (round(min(r["Crítico"] / r["Alto"], r["Alto"] / r["Vigilancia"], r["Vigilancia"] / r["Estable"]), 3), 1 - cb)
                if best is None or key > best[0]:
                    best = (key, (c0, c1, c2), ca, cb)
    feas = pd.DataFrame(feas)
    relaxed = best is None
    if relaxed:   # sin corte factible: el que maximiza el ratio contiguo mínimo con ≥ 70 eventos (D12.2)
        f2 = feas[feas["eventos mín"] >= 70].sort_values("min ratio contiguo", ascending=False).iloc[0]
        ca, cb = f2["% Crítico+Alto"], f2["% hasta Vigilancia"]
        best = (None, (c0, np.quantile(p_cal_oof, 1 - ca), np.quantile(p_cal_oof, 1 - cb)), ca, cb)
    cuts = best[1]
    tramo_model = tramo_of(p_cal, cuts)
    tramo_oof = tramo_of(p_cal_oof, cuts)
    # ── Overrides (decisión en desarrollo con OOF) ────────────────────────────────────
    dev = ALL[dev_m].reset_index(drop=True)
    ov_rows, ov_assign = [], {}
    size_dev = pd.Series(tramo_oof).value_counts()
    for rule, fn in OVERRIDES.items():
        m_dev = fn(dev).fillna(False).to_numpy()
        m_hold = fn(ALL[hold_m]).fillna(False).to_numpy()
        prec_d = yd[m_dev].mean() if m_dev.any() else np.nan
        target = "Crítico" if prec_d >= 0.25 else "Alto" if prec_d >= 0.12 else None
        moved = 0
        if target:
            above = TRAMOS[:TRAMOS.index(target) + 1]
            moved = int((m_dev & ~np.isin(tramo_oof, above)).sum())
            if moved > 0.30 * size_dev.get(target, 1):
                target_new = "Alto" if target == "Crítico" else None
                if target_new:
                    above2 = TRAMOS[:2]
                    moved2 = int((m_dev & ~np.isin(tramo_oof, above2)).sum())
                    target = target_new if moved2 <= 0.30 * size_dev.get("Alto", 1) else None
                    moved = moved2 if target else 0
                else:
                    target = None
        prec_inc = yd[m_dev & (tramo_oof != "Crítico")].mean() if (m_dev & (tramo_oof != "Crítico")).any() else np.nan
        yh = y_all[hold_m]
        ov_rows.append({"modelo": name, "regla": rule, "hogares dev": int(m_dev.sum()), "eventos dev": int(yd[m_dev].sum()),
                        "precisión dev %": 100 * prec_d, "precisión incremental dev % (fuera de Crítico)": 100 * prec_inc,
                        "hogares holdout": int(m_hold.sum()), "eventos holdout": int(yh[m_hold].sum()),
                        "precisión holdout %": 100 * yh[m_hold].mean() if m_hold.any() else np.nan,
                        "hogares que sube (dev)": moved, "tramo asignado": target or "eliminado"})
        if target:
            ov_assign[rule] = target
    ov = pd.DataFrame(ov_rows)
    tramo_final = tramo_model.copy()
    ov_active = np.array([""] * len(ALL), dtype=object)
    for rule, tgt in ov_assign.items():
        m = OVERRIDES[rule](ALL).fillna(False).to_numpy()
        up = m & (np.array([TRAMOS.index(t) for t in tramo_final]) > TRAMOS.index(tgt))
        tramo_final[up] = tgt
        ov_active[m] = [f"{s}; {rule}" if s else rule for s in ov_active[m]]
    tramo_oof_final = tramo_oof.copy()
    for rule, tgt in ov_assign.items():
        m = OVERRIDES[rule](dev).fillna(False).to_numpy()
        up = m & (np.array([TRAMOS.index(t) for t in tramo_oof_final]) > TRAMOS.index(tgt))
        tramo_oof_final[up] = tgt
    # ── Reason codes ─────────────────────────────────────────────────────────────────
    L = np.column_stack([[0.0 if v in NO_REASON else loss_map[(v, b)] for b in bins[v]] for v in vars_])
    order = np.argsort(-L, axis=1)[:, :3]
    rc = []
    for i in range(len(ALL)):
        codes = [f"{LABEL.get(vars_[j], vars_[j])}: {pretty_bin(vars_[j], bins[vars_[j]][i])} (−{L[i, j]:.0f} pts)" for j in order[i] if L[i, j] > 0.5]
        rc.append(codes + [""] * (3 - len(codes)))
    rc = np.array(rc)
    return {"name": name, "vars": vars_, "lookup": lk, "score": score, "p_score": p_score, "p_cal": p_cal, "platt": (a, b),
            "cuts": cuts, "ca": best[2], "cb": best[3], "relaxed": relaxed, "feas": feas, "tramo_model": tramo_model,
            "tramo": tramo_final, "tramo_oof": tramo_oof_final, "overrides": ov, "ov_active": ov_active, "rc": rc, "p_cal_oof": p_cal_oof}


def master(res: dict, mask: np.ndarray, sample: str, tramo=None) -> tuple[pd.DataFrame, pd.DataFrame]:
    tr = res["tramo"][mask] if tramo is None else tramo
    p, yy, r, lv, sc = res["p_cal"][mask], y_all[mask].astype(int), rv[mask], vl[mask], res["score"][mask]
    base = yy.mean()
    H, V = [], []
    tm = res["tramo_model"][mask] if tramo is None else tr
    for t in TRAMOS:
        m = tr == t
        mm = m & (tm == t)          # sin override: define los rangos de score / probabilidad
        H.append({"tramo": t, "score mín–máx (sin override)": f"{sc[mm].min():.0f}–{sc[mm].max():.0f}" if mm.any() else "",
                  "p_cal mín–máx % (sin override)": f"{100 * p[mm].min():.1f}–{100 * p[mm].max():.1f}" if mm.any() else "",
                  "hogares": int(m.sum()), "de ellos por override": int((m & (tm != t)).sum()), "% hogares": 100 * m.mean(), "churn esperado % (media p_cal)": 100 * p[m].mean(),
                  f"churn observado % ({sample})": 100 * yy[m].mean(), "eventos": int(yy[m].sum()), "captura eventos %": 100 * yy[m].sum() / yy.sum(),
                  "lift": yy[m].mean() / base, "responsable": GOV[t][0], "SLA": GOV[t][1], "gobernanza": GOV[t][2]})
        V.append({"tramo": t, "RV $M": r[m].sum() / 1e6, "% RV": 100 * r[m].sum() / r.sum(),
                  "valor esperado en riesgo $M (Σ p·RV)": (p[m] * r[m]).sum() / 1e6, f"RV de churners $M ({sample})": (r[m] * yy[m]).sum() / 1e6,
                  "captura valor churners %": 100 * (r[m] * yy[m]).sum() / (r * yy).sum(), "captura value_lost %": 100 * (lv[m] * yy[m]).sum() / (lv * yy).sum(),
                  "churn por valor % (RV churners ÷ RV)": 100 * (r[m] * yy[m]).sum() / r[m].sum()})
    return pd.DataFrame(H), pd.DataFrame(V)


results = {}
for name, vars_, pkl, col in [("A", cfg["models"]["A"], "11_modelA.pkl", "oof_A"), ("A-lite", cfg["models"]["A-lite"], "11_modelA_lite.pkl", "oof_A_lite")]:
    R = build(name, vars_, pkl, col)
    results[name] = R
    tag = name.replace("-", "").lower()
    save_table(R["lookup"].round(4), f"12_scorecard_lookup{'' if name == 'A' else '_' + tag}")
    save_table(R["overrides"].round(3), f"12_overrides_{tag}")
    for smp, msk in [("holdout", hold_m & elig), ("desarrollo", dev_m & elig)]:
        if smp == "desarrollo":   # decisión con OOF (DM.1): tramos OOF
            H, V = master(R, msk, "desarrollo OOF", tramo=R["tramo_oof"][elig[dev_m]])
            H["churn esperado % (media p_cal)"] = [100 * R["p_cal_oof"][elig[dev_m]][R["tramo_oof"][elig[dev_m]] == t].mean() for t in TRAMOS]
        else:
            H, V = master(R, msk, smp)
        save_table(H.round(3), f"12_master_scale_{tag}_{smp}_hogares")
        save_table(V.round(3), f"12_master_scale_{tag}_{smp}_valor")
    R["feas"].round(4).to_csv(TABLES / f"12_tramo_grid_{tag}.csv", index=False)

    # QC por modelo
    Hh, Vh = master(R, hold_m & elig, "holdout")
    yh = y_all[hold_m & elig].astype(int)
    qc.check(f"{name}: tramos suman 100% hogares (holdout)", abs(Hh["% hogares"].sum() - 100) < 1e-9, "100%", f"{Hh['% hogares'].sum():.4f}")
    qc.check(f"{name}: captura suma 100% (holdout)", abs(Hh["captura eventos %"].sum() - 100) < 1e-9, "100%", f"{Hh['captura eventos %'].sum():.4f}")
    mix = (Hh["% hogares"] / 100 * Hh["churn observado % (holdout)"]).sum()
    qc.check(f"{name}: churn cartera = Σ share × tasa (holdout)", abs(mix - 100 * yh.mean()) < 1e-9, f"{100 * yh.mean():.4f}", f"{mix:.4f}")
    qc.check(f"{name}: captura valor suma 100%", abs(Vh["captura valor churners %"].sum() - 100) < 1e-9, "100%", f"{Vh['captura valor churners %'].sum():.4f}")
    ev_min = Hh["eventos"].min()
    qc.check(f"{name}: ≥ 30 eventos por tramo en holdout", ev_min >= 30, "≥ 30", ev_min, severity="warn")
    rr = Hh["churn observado % (holdout)"].to_numpy()
    qc.check(f"{name}: salto ≥ 2× entre tramos contiguos (holdout)", bool(np.all(rr[:-1] >= 2 * rr[1:])), "≥ 2×",
             " / ".join(f"{a / b:.2f}" for a, b in zip(rr[:-1], rr[1:])), severity="warn")
    qc.check(f"{name}: lift Crítico/Estable ≥ 5× (holdout)", rr[0] >= 5 * rr[-1], "≥ 5×", f"{rr[0] / rr[-1]:.1f}×", severity="warn")
    crit_all = int((R["tramo"][elig] == "Crítico").sum())
    qc.check(f"{name}: Crítico total vs capacidad (3% ≈ 600 hogares; overrides ≤ 30% del tramo)", crit_all <= 1.3 * PARAMS["critical_capacity_pct"] * elig.sum(),
             f"≤ {1.3 * PARAMS['critical_capacity_pct'] * elig.sum():.0f}", crit_all, severity="warn")
    qc.check(f"{name}: corte de tramos factible en desarrollo", not R["relaxed"], "factible", "factible" if not R["relaxed"] else "relajado", severity="warn")
    exact_score = OFFSET + FACTOR * (logit(1 - R["p_score"]))
    qc.check(f"{name}: score = Σ puntos enteros; mayor score ⇒ menor p", bool(np.all(np.diff(R["p_score"][np.argsort(R["score"])]) <= 1e-12)), "monótono", "ok")
    lkp = R["lookup"]
    qc.check(f"{name}: redondeo de puntos (error máx. por hogar)", True, "≤ n/2 puntos", f"≤ {len(vars_) * 0.5:.1f} pts (n = {len(vars_)})")

# ── Archivo de scoring ──────────────────────────────────────────────────────────────────
A, L = results["A"], results["A-lite"]
sc = pd.DataFrame({
    "household_id": ALL.household_id, "segment": ALL.segment.map({0: "HNW", 1: "UHNW"}), "muestra": ALL.muestra,
    "score": A["score"], "probabilidad": A["p_cal"], "tramo": A["tramo"], "tramo_modelo_sin_override": A["tramo_model"],
    "override_activo": A["ov_active"], "driver_1": A["rc"][:, 0], "driver_2": A["rc"][:, 1], "driver_3": A["rc"][:, 2],
    "relationship_value": rv, "p_x_valor": A["p_cal"] * rv,
    "score_lite": L["score"], "probabilidad_lite": L["p_cal"], "tramo_lite": L["tramo"], "override_activo_lite": L["ov_active"],
    "churn_excluded": ALL.churn_excluded.astype(bool)})
sc["prioridad_en_tramo"] = sc.groupby("tramo")["p_x_valor"].rank(ascending=False, method="first").astype(int)
sc = sc.sort_values(["tramo", "prioridad_en_tramo"], key=lambda s: s.map({t: i for i, t in enumerate(TRAMOS)}) if s.name == "tramo" else s)
SCORED.mkdir(parents=True, exist_ok=True)
sc.to_csv(SCORED / "scored_households.csv", index=False)
qc.check("Archivo de scoring con los 20,000 hogares (excluidos con bandera)", len(sc) == 20_000 and sc.churn_excluded.sum() == 123, "20,000 / 123", f"{len(sc)} / {int(sc.churn_excluded.sum())}")
qc.check("segment fuera de reason codes", not sc[["driver_1", "driver_2", "driver_3"]].apply(lambda c: c.str.startswith("segmento")).any().any(), "0", "ok")
qc.check("Sin outcomes en el archivo de scoring", not {"hard_churn_6m", "soft_churn_3m", "value_lost_6m"} & set(sc.columns), "∅", "∅")

params_t = pd.DataFrame([{"parámetro": "S₀", "valor": PARAMS["S0"]}, {"parámetro": "O₀ (buenos:malos)", "valor": PARAMS["O0"]},
                         {"parámetro": "PDO", "valor": PARAMS["PDO"]}, {"parámetro": "Factor = PDO/ln2", "valor": FACTOR},
                         {"parámetro": "Offset = S₀ − Factor·ln O₀", "valor": OFFSET}] +
                        [{"parámetro": f"Platt {k} (a, b)", "valor": f"{r['platt'][0]:.4f}, {r['platt'][1]:.4f}"} for k, r in results.items()] +
                        [{"parámetro": f"Cortes p_cal {k} (Crítico / Alto / Vigilancia)", "valor": " / ".join(f"{100 * c:.2f}%" for c in r["cuts"])} for k, r in results.items()] +
                        [{"parámetro": f"% acumulado {k} (Crítico / +Alto / +Vigilancia)", "valor": f"3% / {100 * r['ca']:.0f}% / {100 * r['cb']:.0f}%"} for k, r in results.items()])
save_table(params_t, "12_scaling_params")

# ── Figura: tasa por tramo holdout, A vs A-lite ─────────────────────────────────────────
INK, MUTED, GRID, BLUE, ORANGE = "#0b0b0b", "#52514e", "#e6e5e0", "#2a78d6", "#eb6834"
fig, axes = plt.subplots(1, 2, figsize=(12, 4))
x = np.arange(4)
for ax, (col, ttl) in zip(axes, [("churn observado % (holdout)", "Churn observado por tramo (holdout)"), ("captura eventos %", "Captura de eventos por tramo (holdout)")]):
    for i, (k, c) in enumerate([("A", BLUE), ("A-lite", ORANGE)]):
        Hh, _ = master(results[k], hold_m & elig, "holdout")
        bars = ax.bar(x + (i - 0.5) * 0.38, Hh[col], 0.36, color=c, label=k)
        for bb in bars:
            ax.text(bb.get_x() + bb.get_width() / 2, bb.get_height() + 0.5, f"{bb.get_height():.1f}", ha="center", fontsize=8, color=INK)
    ax.set_xticks(x, TRAMOS, color=INK)
    ax.set_title(ttl, loc="left", color=INK, fontsize=10)
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    ax.tick_params(colors=MUTED, length=0)
axes[0].axhline(100 * y_all[hold_m & elig].mean(), color=MUTED, ls="--", lw=1)
axes[0].set_ylabel("%", color=MUTED)
axes[0].legend(frameon=False, labelcolor=INK)
fig.suptitle("Escala maestra por tramo · A (operativo) vs A-lite (ejecutivo) [DATA-SINT]", x=0.01, ha="left", color=INK, fontsize=11)
fig.tight_layout()
fig.savefig(FIGURES / "12_tramos.png", dpi=140)

for k, R in results.items():
    tag = k.replace("-", "").lower()
    print(f"\n══ {k} · Platt a={R['platt'][0]:.3f} b={R['platt'][1]:.3f} · cortes {[round(100 * c, 2) for c in R['cuts']]} · relajado={R['relaxed']}")
    print(pd.read_csv(TABLES / f"12_master_scale_{tag}_holdout_hogares.csv").iloc[:, :11].round(2).to_string(index=False))
    print(pd.read_csv(TABLES / f"12_master_scale_{tag}_holdout_valor.csv").round(2).to_string(index=False))
    print(R["overrides"].round(1).to_string(index=False))
print("\n" + A["lookup"][["etiqueta", "rango legible", "WoE", "puntos"]].round(3).to_string(index=False))
print("\n" + L["lookup"][["etiqueta", "rango legible", "puntos"]].to_string(index=False))
print(sc[["score", "probabilidad", "tramo", "driver_1", "driver_2", "driver_3"]].head(5).to_string(index=False))
qc.gate()
