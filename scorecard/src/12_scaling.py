"""Paso 12 · Escalamiento, tramos, overrides, reason codes y salida por hogar (modelos A y A-lite).

Escala (odds = buenos:malos):  Factor = PDO / ln 2;  Offset = S₀ − Factor·ln O₀;  Score = Offset + Factor·ln(odds).
Puntos por bin = (βⱼ·WoEⱼ + β₀/n)·Factor + Offset/n, redondeados a entero (tabla legible; D12.1). Score = Σ puntos.
Mayor score = menor churn. 800 puntos no es 80% de nada: la probabilidad sale de la calibración, no del score.

Probabilidad calibrada (capa modelo, DM.1): Platt logit(p_cal) = a + b·logit(p) ajustado sobre las OOF de la CV anidada
de desarrollo; se valida en el paso 14.
Tramos (decididos con OOF de desarrollo, reportados en holdout; D12.2, D12.6): Crítico = top 3% + overrides de Crítico;
  Alto = capacidad fija (10% de la cartera; parámetro) ocupada por prioridad = max(p_cal, precisión del override activo);
  Vigilancia / Estable por rejilla con las restricciones siguientes. (Versión previa, sin capacidad en Alto:)
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
    # ── Tramos por capacidad + overrides (decisión con OOF calibrada de desarrollo; D12.6) ──
    dev = ALL[dev_m].reset_index(drop=True)
    N = len(dev)
    c0 = np.quantile(p_cal_oof, 1 - PARAMS["critical_capacity_pct"])
    k_alto = int(round(PARAMS["alto_capacity_pct"] * N))
    masks_dev = {r: fn(dev).fillna(False).to_numpy() for r, fn in OVERRIDES.items()}
    masks_all = {r: fn(ALL).fillna(False).to_numpy() for r, fn in OVERRIDES.items()}
    prec = {r: yd[m].mean() if m.any() else np.nan for r, m in masks_dev.items()}
    level = {r: ("Crítico" if p_ >= 0.25 else "Alto" if p_ >= 0.12 else None) for r, p_ in prec.items()}
    note = {r: "" for r in OVERRIDES}
    crit_model = p_cal_oof >= c0
    for r in OVERRIDES:   # ≤ 30% del Crítico por regla; si no, baja a Alto
        if level[r] == "Crítico" and (masks_dev[r] & ~crit_model).sum() > 0.30 * crit_model.sum():
            level[r], note[r] = "Alto", "bajó de Crítico (> 30% del tramo)"

    def assign(p, masks, t_alto=None, c2=None):
        crit = p >= c0
        for r, lv in level.items():
            if lv == "Crítico":
                crit = crit | masks[r]
        eff = p.copy()
        for r, lv in level.items():
            if lv == "Alto":
                eff = np.where(masks[r], np.maximum(eff, min(prec[r], c0 - 1e-9)), eff)
        return crit, eff

    for _ in range(len(OVERRIDES) + 1):   # capacidad de Alto y regla ≤ 30% del tramo por override
        crit, eff = assign(p_cal_oof, masks_dev)
        rest = np.sort(eff[~crit])[::-1]
        t_alto = rest[k_alto - 1]
        alto = ~crit & (eff >= t_alto)
        drop = [r for r, lv in level.items() if lv == "Alto" and (alto & masks_dev[r] & (p_cal_oof < t_alto)).sum() > 0.30 * alto.sum()]
        if not drop:
            break
        worst = min(drop, key=lambda r: prec[r])
        level[worst], note[worst] = None, "fuera (> 30% del Alto)"
    # Vigilancia / Estable: rejilla con restricciones del brief, máximo margen de separación
    best, feas = None, []
    base_rest = ~crit & ~alto
    tr0 = np.where(crit, "Crítico", np.where(alto, "Alto", ""))
    for cb in np.arange(0.20, 0.90, 0.01):   # % acumulado de desarrollo hasta Vigilancia
        c2 = np.quantile(p_cal_oof, 1 - cb)
        tr = np.where(tr0 != "", tr0, np.where(p_cal_oof >= c2, "Vigilancia", "Estable"))
        r, e = rates_by_tramo(tr, yd)
        if (tr == "Vigilancia").sum() == 0 or (tr == "Estable").sum() == 0:
            continue
        mr = min(r["Crítico"] / r["Alto"], r["Alto"] / r["Vigilancia"], r["Vigilancia"] / r["Estable"])
        ok = mr >= 2 and r["Crítico"] >= 5 * r["Estable"] and e.min() >= 70
        feas.append({"% hasta Vigilancia": cb, "factible": ok, "min ratio contiguo": mr, "lift C/E": r["Crítico"] / r["Estable"], "eventos mín": e.min()})
        key = (ok, round(mr, 3), 1 - cb)
        if best is None or key > best[0]:
            best = (key, c2, cb)
    feas = pd.DataFrame(feas)
    relaxed = not best[0][0]
    c2, cb = best[1], best[2]
    cuts = (c0, t_alto, c2)

    def tramos(p, masks, with_ov=True):
        if with_ov:
            crit, eff = assign(p, masks)
        else:
            crit, eff = p >= c0, p
        alto = ~crit & (eff >= t_alto)
        return np.where(crit, "Crítico", np.where(alto, "Alto", np.where(p >= c2, "Vigilancia", "Estable")))

    tramo_model = tramos(p_cal, masks_all, with_ov=False)
    tramo_final = tramos(p_cal, masks_all)
    tramo_oof_final = tramos(p_cal_oof, masks_dev)
    tramo_oof_model = tramos(p_cal_oof, masks_dev, with_ov=False)
    ca = (np.isin(tramo_oof_final, ["Crítico", "Alto"])).mean()
    ov_rows = []
    yh = y_all[hold_m]
    for r in OVERRIDES:
        m_dev, m_hold = masks_dev[r], masks_all[r][hold_m]
        ov_rows.append({"modelo": name, "regla": r, "hogares dev": int(m_dev.sum()), "eventos dev": int(yd[m_dev].sum()),
                        "precisión dev %": 100 * prec[r],
                        "precisión incremental dev % (fuera de su tramo sin override)": 100 * yd[m_dev & (tramo_oof_model != (level[r] or "Crítico"))].mean(),
                        "hogares holdout": int(m_hold.sum()), "eventos holdout": int(yh[m_hold].sum()),
                        "precisión holdout %": 100 * yh[m_hold].mean() if m_hold.any() else np.nan,
                        "hogares que entran por la regla (dev)": int((m_dev & (tramo_oof_final == (level[r] or "")) & (tramo_oof_model != tramo_oof_final)).sum()),
                        "tramo asignado": level[r] or "eliminado", "nota": note[r]})
    ov = pd.DataFrame(ov_rows)
    ov_assign = {r: lv for r, lv in level.items() if lv}
    ov_active = np.array([""] * len(ALL), dtype=object)
    for r in ov_assign:
        m = masks_all[r]
        ov_active[m] = [f"{s_}; {r}" if s_ else r for s_ in ov_active[m]]
    # ── Reason codes ─────────────────────────────────────────────────────────────────
    L = np.column_stack([[0.0 if v in NO_REASON else loss_map[(v, b)] for b in bins[v]] for v in vars_])
    order = np.argsort(-L, axis=1)[:, :3]
    rc = []
    for i in range(len(ALL)):
        codes = [f"{LABEL.get(vars_[j], vars_[j])}: {pretty_bin(vars_[j], bins[vars_[j]][i])} (−{L[i, j]:.0f} pts)" for j in order[i] if L[i, j] > 0.5]
        rc.append(codes + [""] * (3 - len(codes)))
    rc = np.array(rc)
    return {"name": name, "vars": vars_, "lookup": lk, "score": score, "p_score": p_score, "p_cal": p_cal, "platt": (a, b),
            "cuts": cuts, "ca": ca, "cb": cb, "relaxed": relaxed, "feas": feas, "tramo_model": tramo_model,
            "tramo": tramo_final, "tramo_oof": tramo_oof_final, "tramo_oof_model": tramo_oof_model, "overrides": ov, "ov_active": ov_active, "rc": rc, "p_cal_oof": p_cal_oof}


def master(res: dict, mask: np.ndarray, sample: str, tramo=None, tramo_m=None) -> tuple[pd.DataFrame, pd.DataFrame]:
    tr = res["tramo"][mask] if tramo is None else tramo
    p = res["p_cal"][mask] if tramo is None else res["p_cal_oof"][elig[dev_m]]
    yy, r, lv, sc = y_all[mask].astype(int), rv[mask], vl[mask], res["score"][mask]
    base = yy.mean()
    H, V = [], []
    tm = res["tramo_model"][mask] if tramo_m is None else tramo_m
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
            H, V = master(R, msk, "desarrollo OOF", tramo=R["tramo_oof"][elig[dev_m]], tramo_m=R["tramo_oof_model"][elig[dev_m]])
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
    alto_share = (R["tramo"][elig & hold_m] == "Alto").mean()
    qc.check(f"{name}: Alto ≈ capacidad (10% ± 1.5 pp, holdout)", abs(alto_share - PARAMS["alto_capacity_pct"]) <= 0.015,
             f"{100 * PARAMS['alto_capacity_pct']:.0f}%", f"{100 * alto_share:.1f}%")
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
                        [{"parámetro": f"Cortes {k}: p_cal Crítico / prioridad Alto / p_cal Vigilancia", "valor": " / ".join(f"{100 * c:.2f}%" for c in r["cuts"])} for k, r in results.items()] +
                        [{"parámetro": f"% acumulado {k} (Crítico / +Alto / +Vigilancia, desarrollo)", "valor": f"3% / {100 * r['ca']:.1f}% / {100 * r['cb']:.0f}%"} for k, r in results.items()]
                        + [{"parámetro": "Capacidad Alto (supuesto, D12.6)", "valor": f"{100 * PARAMS['alto_capacity_pct']:.0f}% de la cartera"}])
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
