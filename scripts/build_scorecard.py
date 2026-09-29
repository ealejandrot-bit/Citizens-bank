"""UHNWI Churn Propensity Scorecard sobre la base sintética (modo SINT-BASE), pasos 0–17.

Uso: python scripts/build_scorecard.py
Salidas:
  docs/reports/scorecard_report.md       -> documento de modelo 0–17 (toda cifra [SINT-BASE])
  data/synthetic/scorecard_lookup.csv    -> lookup table: variable × bin → WoE, β, puntos
  data/synthetic/scorecard_clients.csv   -> salida por hogar: score, p, p calibrada, tramo, segmento,
                                            arquetipo, prioridad p × valor, top 3 drivers, overrides
"""
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import yaml
from scipy import special
from scipy.optimize import brentq
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import brier_score_loss, roc_auc_score
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from synthetic import scorecard as sc  # noqa: E402
from synthetic.outcome import construct_churn, simulate_outcome  # noqa: E402
from synthetic.pipeline import build  # noqa: E402
from synthetic.schema import COLUMNS, STEP1_COLUMNS  # noqa: E402

OUT = ROOT / "data" / "synthetic"
REPORT = ROOT / "docs" / "reports" / "scorecard_report.md"
TAG = "[SINT-BASE]"
TRANCHES = ["Crítico", "Alto", "Vigilancia", "Estable"]


def md(df, fmt=".3f", index=True):
    """Tabla markdown: columnas de conteo (enteros) con separador de miles, el resto con `fmt`."""
    df = df.copy()
    for c in df.columns:
        v = pd.to_numeric(df[c], errors="coerce")
        if v.notna().all() and len(v) and (v == v.round()).all() and (v.abs() >= 2).any() and df[c].dtype != object:
            df[c] = [f"{int(x):,}" for x in v]
    return df.to_markdown(floatfmt=fmt.replace(",", ""), index=index)


def pct(x, d=1):
    return f"{100 * x:.{d}f}%"


def usd_b(x):
    return f"${x / 1e9:,.2f} mil M"


def main() -> int:
    cfg = yaml.safe_load((ROOT / "config" / "params.yaml").read_text())
    o = build(cfg, upto=1)
    base = o["base"]
    sim_o = simulate_outcome(base, o["truth"], cfg, o["seeds"], o["sim1"])
    labels = construct_churn(sim_o, base, cfg)
    tg = sc.build_target(base, sim_o, labels)
    d = pd.read_csv(OUT / "client_pulse_synthetic.csv")
    assert (d["household_id"] == tg["household_id"]).all()
    d["log_relationship_value"] = np.log(d["relationship_value"])
    d["deposit_share"] = d["deposit_balance"] / d["relationship_value"]
    for c in ["has_investments", "has_trust", "has_linked_business", "has_payroll_stream", "has_pension_stream",
              "has_dividend_stream", "has_credit_anchor", "has_advisory"]:
        d[c] = d[c].astype(float)
    d = d.join(tg.drop(columns="household_id"))
    rng = o["seeds"].rng("scorecard.split")
    seed = int(o["seeds"].rng("scorecard.seed").integers(0, 2**31 - 1))
    L = []  # líneas del reporte

    # ------------------------------------------------------------------ 1 · Target
    N0 = len(d)
    excl = d["excluded"].to_numpy()
    short = d["short_tenure"].to_numpy() & ~excl
    pop = ~excl & ~d["short_tenure"].to_numpy()
    P = d[pop].copy()
    ind = P["indeterminate"].to_numpy()
    y_all = P["y"].to_numpy()
    V0 = P["V0"].sum()
    sens = []
    for u in sc.SENSITIVITY:
        econ_u = ~P["hard"] & (P["net_outflow_ex_mkt"] >= u)
        ind_u = ~P["hard"] & (P["net_outflow_ex_mkt"] >= sc.INDET_LOW) & (P["net_outflow_ex_mkt"] < u)
        ev = (P["hard"] | econ_u)
        sens.append({"umbral u": pct(u, 0), "hard": int(P["hard"].sum()), "económico": int(econ_u.sum()),
                     "eventos totales": int(ev.sum()), "churn rate relaciones": ev.mean(),
                     "indeterminados (10%–u)": int(ind_u.sum()),
                     "eventos entrenables (dev 70%)": int(round(0.7 * ev.sum())),
                     "eventos UHNW": int((ev & (P["segment"] == "UHNW")).sum())})
    sens = pd.DataFrame(sens).set_index("umbral u")
    lost_g, lost_n = P["lost_gross"].sum(), P["lost_net"].sum()
    rates = pd.DataFrame({
        "numerador": [f"{int(y_all.sum()):,} relaciones", f"{int(P['hard'].sum()):,} relaciones", usd_b(lost_g), usd_b(lost_n),
                      usd_b(P.loc[P['hard'], 'lost_gross'].sum())],
        "denominador": [f"{len(P):,}", f"{len(P):,}", usd_b(V0), usd_b(P['Vx0'].sum()), usd_b(V0)],
        "rate 6m": [y_all.mean(), P["hard"].mean(), lost_g / V0, lost_n / P["Vx0"].sum(), P.loc[P["hard"], "lost_gross"].sum() / V0]},
        index=["Churn por relaciones (hard ∪ económico)", "Churn por relaciones (solo hard)", "Churn por AUM bruto (con mercado)",
               "Churn por AUM neto de mercado (flujo)", "Churn por AUM, solo hard (bruto)"])
    by_seg = P.groupby("segment").apply(lambda g: pd.Series({
        "relaciones": len(g), "eventos": int(g["y"].sum()), "churn rate relaciones": g["y"].mean(),
        "AUM inicial ($M)": g["V0"].sum() / 1e6, "AUM perdido neto ($M)": g["lost_net"].sum() / 1e6,
        "churn rate AUM neto": g["lost_net"].sum() / g["Vx0"].sum()}), include_groups=False)

    # ------------------------------------------------------------------ 4 · Muestra
    strat = P["segment"].astype(str) + "|" + P["y"].astype(str) + "|" + P["indeterminate"].astype(str)
    test = np.zeros(len(P), bool)
    for _, idx in P.groupby(strat).indices.items():
        test[rng.choice(idx, int(round(0.3 * len(idx))), replace=False)] = True
    P["sample"] = np.where(test, "val", "dev")
    dev = P[(P["sample"] == "dev") & ~P["indeterminate"]]
    valm = P[(P["sample"] == "val") & ~P["indeterminate"]]     # validación de modelo (sin indeterminados)
    valo = P[P["sample"] == "val"]                             # validación operativa (indeterminados = no churn)
    y_dev, y_valm, y_valo = dev["y"].to_numpy(), valm["y"].to_numpy(), valo["y"].to_numpy()
    sample_tab = pd.DataFrame({
        "relaciones": [len(dev), int((P["sample"] == "dev").sum() - len(dev)), len(valm), int((P["sample"] == "val").sum() - len(valm))],
        "eventos": [int(y_dev.sum()), 0, int(y_valm.sum()), 0],
        "tasa": [y_dev.mean(), 0, y_valm.mean(), 0],
        "UHNW": [int((dev["segment"] == "UHNW").sum()), int(((P["sample"] == "dev") & P["indeterminate"] & (P["segment"] == "UHNW")).sum()),
                 int((valm["segment"] == "UHNW").sum()), int(((P["sample"] == "val") & P["indeterminate"] & (P["segment"] == "UHNW")).sum())]},
        index=["Desarrollo (entrena)", "Desarrollo · indeterminados (no entrenan)", "Validación (modelo)", "Validación · indeterminados (se scorean)"])

    # ------------------------------------------------------------------ 2/3 · Diccionario y calidad
    cand = [c for c in sc.VARS if c not in ("log_relationship_value", "has_trust", "has_linked_business")]
    dic = []
    col_desc = {**COLUMNS, **STEP1_COLUMNS}
    for c in sc.VARS:
        dim, sign, win, mean = sc.VARS[c]
        x = d[c] if c in d else pd.Series(np.nan, index=d.index)
        u = col_desc.get(c, ("", ""))[0] or ("0/1" if set(x.dropna().unique()) <= {0, 1} else "fracción" if x.abs().max() <= 5 else "valor")
        dic.append({"variable": c, "bloque": dim, "tipo": "binaria" if set(x.dropna().unique()) <= {0, 1} else "continua",
                    "fuente": "base sintética (37 vars Excel)" if dim not in ("Estructural",) else "atributo del hogar",
                    "frecuencia": "mensual (corte T0)", "ventana": win, "unidad": u, "% missing": x.isna().mean() * 100,
                    "significado": mean, "dirección esperada": sign})
    dic = pd.DataFrame(dic).set_index("variable")
    qual = sc.describe(d[pop], [c for c in sc.VARS])
    dup = int(d["household_id"].duplicated().sum())
    frac_cols = [c for c in cand if c.endswith("_pct") or c.endswith("pct_90d") or c.endswith("pct_60d") or c == "share_of_wallet"]
    impossible = {
        "share_of_wallet ∉ [0,1]": int(((d["share_of_wallet"] < 0) | (d["share_of_wallet"] > 1)).sum()),
        "client_reply_rate ∉ [0,1]": int(((d["client_reply_rate"] < 0) | (d["client_reply_rate"] > 1)).sum()),
        "flags ∉ {0,1}": int(sum(((~d[c].isin([0, 1])) & d[c].notna()).sum() for c in cand if c.endswith("_flag"))),
        "salidas/redenciones % < 0": int(sum((d[c] < 0).sum() for c in ["aum_outflow_pct_90d", "investment_redemption_pct", "positions_liquidated_pct"])),
        "salidas/redenciones % > 100%": int(sum((d[c] > 1).sum() for c in ["aum_outflow_pct_90d", "investment_redemption_pct", "positions_liquidated_pct"])),
        "caída de saldo < −100%": int(sum((d[c] < -1).sum() for c in ["deposit_balance_change_pct_90d", "deposit_balance_vs_6m_avg_pct", "aum_vs_baseline_pct"])),
        "montos negativos (valor, depósitos, AUM)": int(((d["relationship_value"] < 0) | (d["deposit_balance"] < 0) | (d["aum"] < 0)).sum()),
        "tenure < 0 o > edad − 18": int(((d["tenure_years"] < 0) | (d["tenure_years"] > d["age_primary"] - 18)).sum()),
        "history_months > 24 o > tenure": int(((d["history_months"] > 24) | (d["history_months"] > d["tenure_years"] * 12 + 1)).sum()),
        "IDs duplicados": dup}
    # Ilustración de outliers: transferencias externas ÷ saldo 60d
    xo = d.loc[pop, "external_transfer_pct_of_balance_60d"]
    p99 = xo.quantile(0.99)
    hi = d.loc[pop & (d["external_transfer_pct_of_balance_60d"] > p99)]
    out_cls = pd.Series({
        "error (∉ dominio: < 0)": int((xo < 0).sum()),
        "comportamiento real (> p99 y el saldo cae ≥ 20%)": int((hi["deposit_balance_change_pct_90d"] <= -0.20).sum()),
        "operación extraordinaria (> p99, saldo estable: p. ej. compra de inmueble / impuestos)": int((hi["deposit_balance_change_pct_90d"] > -0.20).sum())})

    # ------------------------------------------------------------------ 6 · Univariado
    uni = sc.univariate(dev, y_dev, cand)

    # ------------------------------------------------------------------ 7 · Pre-segmentación
    Zs = d.loc[pop, sc.STRUCTURAL].copy()
    Zs = ((Zs - Zs.mean()) / Zs.std(ddof=0)).to_numpy()
    kt, K, km = sc.kmeans_select(Zs, seed=seed % 10_000)
    P["cluster"] = km.labels_
    prof = P.groupby("cluster").agg(relaciones=("y", "size"), valor_mediano=("V0", "median"),
                                    tenure=("tenure_years", "median"), trust=("has_trust", "mean"),
                                    negocio=("has_linked_business", "mean"), nomina=("has_payroll_stream", "mean"),
                                    pension=("has_pension_stream", "mean"), dividendos=("has_dividend_stream", "mean"),
                                    inversiones=("has_investments", "mean"), uhnw=("segment", lambda s: (s == "UHNW").mean()),
                                    eventos=("y", "sum"), churn=("y", "mean"))

    def name_cluster(r):
        if r["uhnw"] > 0.25 or (r["trust"] > 0.6 and r["valor_mediano"] > 1.5e7):
            return "Family office / trust (UHNW)"
        if r["negocio"] > 0.6:
            return "Fundador / dueño de negocio"
        if r["pension"] > 0.5:
            return "Retirado (pensión)"
        if r["nomina"] > 0.6:
            return "Ejecutivo (nómina)"
        if r["inversiones"] < 0.3:
            return "Depositante (sin inversiones)"
        return "Inversionista patrimonial"
    prof["arquetipo estructural"] = [name_cluster(r) for _, r in prof.iterrows()]
    dup_names = prof["arquetipo estructural"].duplicated(keep=False)
    prof.loc[dup_names, "arquetipo estructural"] += " · " + prof.index[dup_names].astype(str)
    P["segmento_estructural"] = P["cluster"].map(prof["arquetipo estructural"])
    for s in ("dev", "valm", "valo"):
        pass
    dev = dev.join(P["segmento_estructural"])
    valm = valm.join(P["segmento_estructural"])
    valo = valo.join(P["segmento_estructural"])
    ev_train = dev.groupby("segmento_estructural")["y"].sum()

    # ------------------------------------------------------------------ 9 · Binning / WoE / IV
    binners, bin_rows = {}, []
    for c in cand:
        sign = sc.VARS[c][1]
        trend = {"+": "ascending", "−": "descending"}.get(sign, "auto_asc_desc")
        b_forced = sc.Binner(c, dev[c], y_dev, trend=trend)
        b_auto = sc.Binner(c, dev[c], y_dev, trend="auto_asc_desc")
        binners[c] = b_forced
        t = b_forced.table[b_forced.table["code"] >= 0]
        bin_rows.append({"variable": c, "dimensión": sc.VARS[c][0], "tendencia forzada": trend,
                         "bins": len(t), "IV (forzado)": b_forced.iv, "IV (auto)": b_auto.iv,
                         "missing": b_forced.missing_policy, "monótono val": "sí" if b_forced.is_monotone(valm[c], y_valm) else "no"})
    ivt = pd.DataFrame(bin_rows).set_index("variable").sort_values("IV (forzado)", ascending=False)
    ivt["clase IV"] = pd.cut(ivt["IV (forzado)"], [-1, 0.02, 0.10, 0.30, 0.50, 99],
                             labels=["fuera (< 0.02)", "débil", "medio", "fuerte", "sospechoso fuga (> 0.50)"])
    ivt["pérdida por monotonicidad"] = 1 - ivt["IV (forzado)"] / ivt["IV (auto)"].where(ivt["IV (auto)"] > 0)

    # ------------------------------------------------------------------ 10 · Selección
    elig = [c for c in ivt.index if c not in sc.PROHIBITED and ivt.loc[c, "IV (forzado)"] >= 0.02
            and ivt.loc[c, "IV (forzado)"] <= 0.50 and (ivt.loc[c, "pérdida por monotonicidad"] or 0) < 0.5]
    W_dev = pd.DataFrame({c: binners[c].woe(dev[c]) for c in elig}, index=dev.index)
    vc = sc.variable_clusters(W_dev, {c: ivt.loc[c, "IV (forzado)"] for c in elig})
    reps = vc.loc[vc["representante"], "variable"].tolist()
    good_dev = 1 - y_dev
    order = sc.l1_entry_order(W_dev[reps], good_dev)
    dim_of = {c: sc.VARS[c][0] for c in cand}
    chosen, sel_log = sc.forward_select(W_dev, good_dev, order, dim_of, seed)
    print("K estructural:", K, "| elegibles:", len(elig), "| representantes:", reps, "| elegidas:", chosen, flush=True)

    # ------------------------------------------------------------------ 8 · Correlación / PCA (diagnóstico)
    num = [c for c in cand if c not in ("age_primary",)]
    Mraw = dev[num].astype(float)
    Mimp = Mraw.fillna(Mraw.median())
    sp = Mimp.corr(method="spearman")
    pe = Mimp.corr(method="pearson")
    pairs = []
    for i, a in enumerate(num):
        for b in num[i + 1:]:
            if abs(sp.loc[a, b]) >= 0.6 or abs(pe.loc[a, b]) >= 0.6:
                inc = "—"
                if a in binners and b in binners:
                    ia, ib = binners[a].iv, binners[b].iv
                    keep = a if ia >= ib else b
                    inc = f"se prefiere {keep} (IV {max(ia, ib):.3f} vs {min(ia, ib):.3f})"
                pairs.append({"par": f"{a} ~ {b}", "Spearman": sp.loc[a, b], "Pearson": pe.loc[a, b], "decisión": inc})
    pairs = pd.DataFrame(pairs)
    vif_raw = sc.vif(Mimp).sort_values(ascending=False)
    pca_sum, kaiser, ev = sc.pca_diagnostic(Mimp)

    # ------------------------------------------------------------------ 11 · Estimación
    W_ch = W_dev[chosen]
    fit = sm.Logit(good_dev, sm.add_constant(W_ch)).fit(disp=0)
    beta = fit.params[chosen]
    b0_star = float(fit.params["const"])
    # Corrección de intercepto: el desarrollo excluye indeterminados (que en la población son "no churn").
    dev_all = P[P["sample"] == "dev"]
    odds_s = (1 - y_dev).sum() / y_dev.sum()
    odds_p = (1 - dev_all["y"]).sum() / dev_all["y"].sum()
    b0 = b0_star - np.log(odds_s) + np.log(odds_p)
    card = sc.Scorecard(binners, beta, b0)
    coef_tab = pd.DataFrame({"dimensión": [sc.VARS[c][0] for c in chosen], "β (WoE)": beta, "e.e.": fit.bse[chosen],
                             "z": fit.tvalues[chosen], "p-valor": fit.pvalues[chosen],
                             "IV": [binners[c].iv for c in chosen], "VIF": sc.vif(W_ch)})
    # Challenger: gradient boosting sobre todas las candidatas permitidas (crudas)
    gb_cols = [c for c in cand if c not in sc.PROHIBITED]
    gb = HistGradientBoostingClassifier(max_iter=400, learning_rate=0.05, max_leaf_nodes=31, min_samples_leaf=40,
                                        l2_regularization=1.0, early_stopping=True, validation_fraction=0.15,
                                        random_state=seed % 10_000).fit(dev[gb_cols], y_dev)
    p_gb_valm = gb.predict_proba(valm[gb_cols])[:, 1]
    p_dev = card.p_churn(dev)
    p_valm = card.p_churn(valm)
    p_valo = card.p_churn(valo)
    # Modelo logístico por segmento (misma forma, β re-estimados) vs. modelo único
    seg_cmp = []
    for s, g in valm.groupby("segmento_estructural"):
        gd = dev[dev["segmento_estructural"] == s]
        if gd["y"].sum() < 100:
            seg_cmp.append({"segmento": s, "eventos dev": int(gd["y"].sum()), "AUC único": roc_auc_score(g["y"], p_valm[valm.index.get_indexer(g.index)]),
                            "AUC propio": np.nan, "Δ": np.nan})
            continue
        Wg = pd.DataFrame({c: binners[c].woe(gd[c]) for c in chosen}, index=gd.index)
        var_cols = [c for c in chosen if Wg[c].std() > 0]   # en algunos segmentos una variable es constante (p. ej. sin inversiones)
        fg = LogisticRegression(C=1e4, max_iter=5000).fit(Wg[var_cols], gd["y"].to_numpy())
        Wv = pd.DataFrame({c: binners[c].woe(g[c]) for c in var_cols}, index=g.index)
        pg = fg.decision_function(Wv)
        a1 = roc_auc_score(g["y"], p_valm[valm.index.get_indexer(g.index)])
        a2 = roc_auc_score(g["y"], pg)
        seg_cmp.append({"segmento": s, "eventos dev": int(gd["y"].sum()), "AUC único": a1, "AUC propio": a2, "Δ": a2 - a1})
    seg_cmp = pd.DataFrame(seg_cmp).set_index("segmento")

    val_value_m = valm["V0"].to_numpy()
    champ = {"Dev · Modelo A (scorecard WoE)": sc.metrics(y_dev, p_dev, dev["V0"].to_numpy()),
             "Val · Modelo A (scorecard WoE)": sc.metrics(y_valm, p_valm, val_value_m),
             "Val · Modelo B (gradient boosting)": sc.metrics(y_valm, p_gb_valm, val_value_m)}
    p_gb_dev = gb.predict_proba(dev[gb_cols])[:, 1]
    champ["Dev · Modelo B (gradient boosting)"] = sc.metrics(y_dev, p_gb_dev, dev["V0"].to_numpy())
    cmp = pd.DataFrame(champ).T.loc[["Dev · Modelo A (scorecard WoE)", "Val · Modelo A (scorecard WoE)",
                                      "Dev · Modelo B (gradient boosting)", "Val · Modelo B (gradient boosting)"]]
    # Bootstrap pareado de la diferencia de AUC en validación
    brng = o["seeds"].rng("scorecard.bootstrap")
    diffs = []
    for _ in range(300):
        i = brng.integers(0, len(y_valm), len(y_valm))
        diffs.append(roc_auc_score(y_valm[i], p_gb_valm[i]) - roc_auc_score(y_valm[i], p_valm[i]))
    dlo, dhi = np.quantile(diffs, [0.025, 0.975])
    gb_cal = {"A": (p_valm.mean(), brier_score_loss(y_valm, p_valm)), "B": (p_gb_valm.mean(), brier_score_loss(y_valm, p_gb_valm))}

    # ------------------------------------------------------------------ 14 · Calibración (antes de fijar tramos)
    # Platt con validación cruzada en 2 mitades de la validación operativa (evita calibrar y medir sobre lo mismo).
    a_pl, b_pl = sc.platt(y_valo, p_valo)
    half = o["seeds"].rng("scorecard.platt").random(len(valo)) < 0.5
    a1, b1 = sc.platt(y_valo[half], p_valo[half])
    a2, b2 = sc.platt(y_valo[~half], p_valo[~half])
    pcal_cf = np.where(half, sc.apply_platt(p_valo, a2, b2), sc.apply_platt(p_valo, a1, b1))
    iso = IsotonicRegression(out_of_bounds="clip").fit(p_valo[~half], y_valo[~half])
    brier = {"sin calibrar": brier_score_loss(y_valo, p_valo), "Platt (cross-fit)": brier_score_loss(y_valo, pcal_cf),
             "Isotónica (mitad → mitad)": brier_score_loss(y_valo[half], iso.predict(p_valo[half]))}
    P["score"] = card.score(P)
    P["p_model"] = card.p_churn(P)
    P["p_platt"] = sc.apply_platt(P["p_model"].to_numpy(), a_pl, b_pl)
    # Capa segmento: el tamaño no está en el score (paso 10). Si la tasa observada de un segmento sale del
    # IC Wilson 90% de su esperado, se corrige con un desplazamiento de intercepto propio del segmento.
    seg_rows, seg_shift = [], {}
    for sgm, g in P.groupby("segment"):
        k_, n_ = int(g["y"].sum()), len(g)
        lo_, hi_ = sc.wilson(k_, n_)
        exp_ = g["p_platt"].mean()
        lp_ = special.logit(g["p_platt"].clip(1e-6, 1 - 1e-6))
        dl = 0.0 if lo_ <= exp_ <= hi_ else brentq(lambda z: special.expit(lp_ + z).mean() - k_ / n_, -3, 3)
        seg_shift[sgm] = dl
        seg_rows.append({"segmento": sgm, "N": n_, "eventos": k_, "esperado (Platt)": exp_, "observado": k_ / n_,
                         "Wilson 90% inf": lo_, "Wilson 90% sup": hi_, "¿dentro?": "sí" if lo_ <= exp_ <= hi_ else "NO",
                         "δ intercepto": dl, "esperado tras δ": special.expit(lp_ + dl).mean()})
    seg_tab = pd.DataFrame(seg_rows).set_index("segmento")
    P["p_cal"] = special.expit(special.logit(P["p_platt"].clip(1e-6, 1 - 1e-6)) + P["segment"].map(seg_shift))
    valo = valo.join(P[["score", "p_model", "p_cal"]])
    dec = sc.gains_table(y_valo, valo["p_cal"].to_numpy(), valo["V0"].to_numpy())
    cal_dec = pd.DataFrame({"p media sin calibrar": pd.Series(p_valo).groupby(pd.qcut(pd.Series(p_valo).rank(method="first"), 10, labels=range(1, 11))).mean().to_numpy(),
                            "p media calibrada": valo.groupby(pd.qcut(valo["p_cal"].rank(method="first"), 10, labels=range(1, 11)), observed=True)["p_cal"].mean().to_numpy(),
                            "churn observado": valo.groupby(pd.qcut(valo["p_cal"].rank(method="first"), 10, labels=range(1, 11)), observed=True)["y"].mean().to_numpy()},
                           index=pd.Index(range(1, 11), name="decil (1 = menor riesgo)"))

    # ------------------------------------------------------------------ 12 · Tramos
    n_bankers = math.ceil((d["segment"] == "HNW").sum() / sc.BANKS_PER_BANKER["HNW"]) + \
        math.ceil((d["segment"] == "UHNW").sum() / sc.BANKS_PER_BANKER["UHNW"])
    capacity = n_bankers * sc.CRITICAL_PER_BANKER_MONTH
    crit_share = capacity / len(P)
    pv = valo["p_cal"].to_numpy()
    yv = y_valo
    order_v = np.argsort(-pv)

    def tranche_stats(cuts):  # cuts = participaciones acumuladas (crit, alto, vig)
        n = len(pv)
        b = np.searchsorted(np.array(cuts) * n, np.arange(n), side="right")
        lab = np.empty(n, int)
        lab[order_v] = b
        r = [yv[lab == k].mean() for k in range(4)]
        e = [int(yv[lab == k].sum()) for k in range(4)]
        return lab, r, e

    best, grid = None, []
    for t2 in np.arange(crit_share + 0.02, 0.40, 0.01):
        for t3 in np.arange(t2 + 0.05, 0.85, 0.01):
            lab, r, e = tranche_stats([crit_share, t2, t3])
            ok_ratio = all(r[k] >= 2 * r[k + 1] for k in range(3))
            ok_ev = min(e) >= 30
            lift = r[0] / max(r[3], 1e-9)
            s = pd.Series(yv).groupby(lab).agg(["sum", "size"])
            g_ = (s["size"] - s["sum"]) / (s["size"] - s["sum"]).sum()
            b_ = (s["sum"] + 0.5) / (s["sum"] + 0.5).sum()
            ivx = float(((g_ - b_) * np.log(g_ / b_)).sum())
            grid.append((t2, t3, ok_ratio, ok_ev, lift, ivx, min(r[k] / max(r[k + 1], 1e-9) for k in range(3))))
            if ok_ratio and ok_ev and lift >= 5 and (best is None or ivx > best[5]):
                best = grid[-1]
    relaxed = False
    if best is None:  # relaja el salto Vigilancia/Estable: maximiza el salto mínimo
        relaxed = True
        best = max((g for g in grid if g[3]), key=lambda g: (g[6], g[5]))
    cuts_share = [crit_share, best[0], best[1]]
    thr = [np.quantile(pv, 1 - s_) for s_ in cuts_share]  # umbrales de p calibrada (fijos año 1)

    def tranche_of(p):
        return np.select([p >= thr[0], p >= thr[1], p >= thr[2]], TRANCHES[:3], TRANCHES[3])
    P["tramo_modelo"] = tranche_of(P["p_cal"].to_numpy())
    valo["tramo_modelo"] = P.loc[valo.index, "tramo_modelo"]
    # Cortes de score equivalentes por segmento (p calibrada es monótona decreciente en el score porque b > 0):
    # logit(t) = a + b·logit(p_model) + δ, logit(p_model) = −(score − Offset)/Factor
    # → score* = Offset + Factor·(a + δ − logit(t))/b
    def score_cut(t_, sgm):
        return sc.OFFSET + sc.FACTOR * (a_pl + seg_shift[sgm] - special.logit(t_)) / b_pl
    cuts_tab = pd.DataFrame({sgm: [score_cut(t_, sgm) for t_ in thr] for sgm in seg_shift},
                            index=["Crítico si score ≤", "Alto si score ≤", "Vigilancia si score ≤"])

    def score_range(t, sgm):
        c_ = [score_cut(t_, sgm) for t_ in thr]
        lo_ = {"Crítico": None, "Alto": c_[0], "Vigilancia": c_[1], "Estable": c_[2]}[t]
        hi_ = {"Crítico": c_[0], "Alto": c_[1], "Vigilancia": c_[2], "Estable": None}[t]
        return f"{'' if lo_ is None else f'> {lo_:.0f}'}{' y ' if lo_ is not None and hi_ is not None else ''}{'' if hi_ is None else f'≤ {hi_:.0f}'}"

    def master(df, weight=None):
        rows = []
        tot_ev = df["y"].sum() if weight is None else (df["y"] * df[weight]).sum()
        tot = len(df) if weight is None else df[weight].sum()
        rate_all = df["y"].mean() if weight is None else (df["y"] * df[weight]).sum() / df[weight].sum()
        for t in TRANCHES:
            g = df[df["tramo"] == t]
            if weight is None:
                share, rate, exp_, ev_ = len(g) / tot, g["y"].mean(), g["p_cal"].mean(), g["y"].sum()
            else:
                w = g[weight]
                share, rate = w.sum() / tot, (g["y"] * w).sum() / w.sum()
                exp_, ev_ = (g["p_cal"] * w).sum() / w.sum(), (g["y"] * w).sum()
            rows.append({"tramo": t, "score HNW": score_range(t, "HNW"), "score UHNW": score_range(t, "UHNW"),
                         "p calibrada (incl. overrides)": f"{g['p_cal'].min():.1%} – {g['p_cal'].max():.1%}",
                         "% relaciones" if weight is None else "% AUM": share, "churn esperado (p media)": exp_,
                         "churn observado": rate, "captura": ev_ / tot_ev, "lift": rate / rate_all,
                         "eventos": int(g["y"].sum()), "N": len(g)})
        t = pd.DataFrame(rows).set_index("tramo")
        return t, rate_all

    # ---- Overrides (precisión medida en validación, sobre casos que el modelo NO puso en Crítico)
    ovr_rules = {
        "Cambio de banquero (6m; proxy de salida ≤ 90 días)": valo["banker_change_6m_flag"] == 1,
        "Intención de salida / insatisfacción expresada": valo["relationship_dissatisfaction_flag"] == 1,
        "Queja formal escalada": valo["complaint_escalated_flag"] == 1,
        "Transferencia externa ≥ 10% del saldo (60d; proxy de un movimiento)": valo["external_transfer_pct_of_balance_60d"] >= 0.10,
        "Cambio de trustee (proxy sucesión / fallecimiento)": valo["trustee_change_flag"] == 1}
    not_crit = (valo["tramo_modelo"] != "Crítico").to_numpy()
    # Tope: los casos que entran por override no pueden ser > 30% del tramo final →
    # entran como máximo 0.30/0.70 × (casos del modelo en el tramo). Las reglas se admiten completas,
    # en orden de precisión; la que no cabe en Crítico baja a Alto, y la que no cabe en Alto queda
    # como alerta EWS sin cambio de tramo.
    n_model = valo["tramo_modelo"].value_counts()
    room = {t: int(np.floor(0.30 / 0.70 * n_model.get(t, 0))) for t in ("Crítico", "Alto")}
    used = {"Crítico": np.zeros(len(valo), bool), "Alto": np.zeros(len(valo), bool)}
    masks = {k: m.fillna(False).to_numpy() & not_crit for k, m in ovr_rules.items()}
    precs = {k: (yv[m].mean() if m.any() else np.nan) for k, m in masks.items()}
    ovr_rows, keep_rules = [], {}
    for k in sorted(masks, key=lambda k: -np.nan_to_num(precs[k])):
        m, prec = masks[k], precs[k]
        by_prec = "se queda en Crítico" if prec >= 0.25 else ("baja a Alto" if prec >= 0.12 else "se elimina")
        dec_ = by_prec
        if dec_ == "se queda en Crítico":
            new_c = m & ~used["Crítico"]
            if (used["Crítico"] | new_c).sum() <= room["Crítico"]:
                used["Crítico"] |= new_c
            else:
                dec_ = "baja a Alto (no cabe en el tope de Crítico)"
        if dec_.startswith("baja a Alto"):
            new_a = m & ~used["Crítico"] & ~used["Alto"] & (valo["tramo_modelo"] != "Alto").to_numpy()
            if (used["Alto"] | new_a).sum() <= room["Alto"]:
                used["Alto"] |= new_a
            else:
                dec_ = "solo alerta EWS (no cabe en el tope de Alto)"
        ovr_rows.append({"override": k, "casos (val, fuera de Crítico)": int(m.sum()), "precisión": prec,
                         "decisión por precisión": by_prec, "decisión final (con tope 30%)": dec_})
        keep_rules[k] = dec_
    ovr = pd.DataFrame(ovr_rows).set_index("override")
    rule_cols = {"Cambio de banquero (6m; proxy de salida ≤ 90 días)": lambda X: X["banker_change_6m_flag"] == 1,
                 "Intención de salida / insatisfacción expresada": lambda X: X["relationship_dissatisfaction_flag"] == 1,
                 "Queja formal escalada": lambda X: X["complaint_escalated_flag"] == 1,
                 "Transferencia externa ≥ 10% del saldo (60d; proxy de un movimiento)": lambda X: X["external_transfer_pct_of_balance_60d"] >= 0.10,
                 "Cambio de trustee (proxy sucesión / fallecimiento)": lambda X: X["trustee_change_flag"] == 1}

    def apply_overrides(X):
        t = X["tramo_modelo"].to_numpy().copy()
        why = np.full(len(X), "", dtype=object)
        rank = {k: i for i, k in enumerate(TRANCHES)}
        for k, f in rule_cols.items():
            dec_ = keep_rules[k]
            if dec_ == "se elimina" or dec_.startswith("solo alerta"):
                continue
            target = "Crítico" if dec_ == "se queda en Crítico" else "Alto"
            m = f(X).fillna(False).to_numpy() & (np.array([rank[v] for v in t]) > rank[target])
            t[m] = target
            why[m] = np.where(why[m] == "", k, why[m] + " | " + k)
        return t, why
    P["tramo"], P["override"] = apply_overrides(P)
    valo["tramo"], valo["override"] = apply_overrides(valo)
    ovr_share = valo.groupby("tramo").apply(lambda g: (g["override"] != "").mean(), include_groups=False).reindex(TRANCHES)
    ms_rel, r_rel = master(valo)
    ms_aum, r_aum = master(valo, weight="V0")
    ms_aum = ms_aum.rename(columns={"churn esperado (p media)": "churn esperado (Σp·AUM ÷ AUM)",
                                    "churn observado": "churn observado (AUM de churners ÷ AUM)",
                                    "captura": "captura de AUM de churners"})
    ms_model_rel, _ = master(valo.assign(tramo=valo["tramo_modelo"]))
    gov = pd.DataFrame({
        "quién actúa": ["Banquero + Head of PB (visto bueno); comité si valor ≥ p95 de la cartera",
                        "Banquero", "Banquero (cadencia reforzada)", "Banquero (cadencia normal)"],
        "SLA de contacto": ["≤ 5 días hábiles", "≤ 15 días hábiles", "próximo contacto de cadencia", "—"],
        "escalamiento": ["Head of PB revisa semanal; comité mensual", "Head of PB si no hay contacto en SLA",
                         "sube a Alto si sube 2 tramos en un trimestre", "—"]}, index=TRANCHES)

    # ------------------------------------------------------------------ 13 · Validación (continuación)
    gini_dev = 2 * roc_auc_score(y_dev, p_dev) - 1
    gini_val = 2 * roc_auc_score(y_valm, p_valm) - 1
    gini_drop = 1 - gini_val / gini_dev
    dev_tr = tranche_of(P.loc[dev.index, "p_cal"].to_numpy())
    psi_tr = sc.psi(dev_tr, valo["tramo_modelo"][~valo["indeterminate"]])
    mono = {}
    for nm, df_, yy in [("desarrollo", dev.assign(tr=dev_tr), y_dev), ("validación", valm.join(P["tramo_modelo"]).rename(columns={"tramo_modelo": "tr"}), y_valm)]:
        r = pd.Series(yy, index=df_.index).groupby(df_["tr"]).mean().reindex(TRANCHES)
        mono[nm] = r
    mono = pd.DataFrame(mono)
    mono_ok = all((mono[c].diff().dropna() < 0).all() for c in mono)
    bins_mono = pd.DataFrame({c: {"dev": "sí" if binners[c].is_monotone() else "no",
                                  "val": "sí" if binners[c].is_monotone(valm[c], y_valm) else "no"} for c in chosen}).T
    crit_alto = valo["tramo"].isin(["Crítico", "Alto"])
    fp = int((crit_alto & (valo["y"] == 0)).sum())
    tp = int((crit_alto & (valo["y"] == 1)).sum())
    top10 = valo["p_cal"].rank(ascending=False) <= 0.1 * len(valo)
    prio_rank = (valo["p_cal"] * valo["V0"]).rank(ascending=False) <= 0.1 * len(valo)
    aum_churn = (valo["y"] * valo["V0"])
    cap_top = aum_churn[top10].sum() / aum_churn.sum()
    cap_prio = aum_churn[prio_rank].sum() / aum_churn.sum()
    val_full = sc.metrics(y_valo, valo["p_cal"].to_numpy(), valo["V0"].to_numpy())

    # ------------------------------------------------------------------ 14 · Calibración por tramo, AUM, hazard
    trc = []
    for t in TRANCHES:
        g = valo[valo["tramo"] == t]
        k, n = int(g["y"].sum()), len(g)
        lo, hi = sc.wilson(k, n)
        pe_ = g["p_cal"].mean()
        shr = (k + 30 * pe_) / (n + 30)
        trc.append({"tramo": t, "N": n, "eventos": k, "esperado (p media)": pe_, "observado": k / n,
                    "Wilson 90% inf": lo, "Wilson 90% sup": hi, "¿esperado dentro del IC?": "sí" if lo <= pe_ <= hi else "NO",
                    "p shrinkage (m = 30)": shr})
    trc = pd.DataFrame(trc).set_index("tramo")
    haz = P[P["y"] == 1].groupby("event_month").size().reindex(range(1, 7), fill_value=0)
    haz = pd.DataFrame({"eventos": haz, "% acumulado del churn a 6m": haz.cumsum() / haz.sum()})
    haz.index.name = "mes"
    valo["banda AUM"] = pd.cut(valo["V0"], [0, 5e6, 1e7, 3e7, 1e8, np.inf],
                               labels=["$1–5M", "$5–10M", "$10–30M", "$30–100M", "> $100M"])
    aum_cal = valo.groupby("banda AUM", observed=True).apply(lambda g: pd.Series({
        "N": len(g), "eventos": int(g["y"].sum()), "p media": g["p_cal"].mean(), "churn obs.": g["y"].mean(),
        "Σ p·AUM ($M)": (g["p_cal"] * g["V0"]).sum() / 1e6, "AUM de churners obs. ($M)": (g["y"] * g["V0"]).sum() / 1e6,
        "outflow neto obs. ($M)": g["lost_net"].sum() / 1e6}), include_groups=False)
    aum_cal["ratio obs./esperado (AUM)"] = aum_cal["AUM de churners obs. ($M)"] / aum_cal["Σ p·AUM ($M)"]
    seg_cal = valo.groupby("segment").apply(lambda g: pd.Series({
        "N": len(g), "eventos": int(g["y"].sum()), "p media": g["p_cal"].mean(), "churn obs.": g["y"].mean(),
        "Σ p·AUM ($M)": (g["p_cal"] * g["V0"]).sum() / 1e6, "AUM de churners obs. ($M)": (g["y"] * g["V0"]).sum() / 1e6}), include_groups=False)
    seg_cal["ratio obs./esperado (AUM)"] = seg_cal["AUM de churners obs. ($M)"] / seg_cal["Σ p·AUM ($M)"]

    # ------------------------------------------------------------------ 15 · Estabilidad
    psi_score = sc.psi(pd.cut(card.score(dev), np.quantile(card.score(dev), np.linspace(0, 1, 11)), include_lowest=True).astype(str),
                       pd.cut(valo["score"], np.quantile(card.score(dev), np.linspace(0, 1, 11)), include_lowest=True).astype(str))
    psi_vars = pd.Series({c: sc.psi(binners[c].codes(dev[c]), binners[c].codes(valo[c])) for c in chosen}, name="PSI dev→val")
    psi_seg = pd.Series({c: sc.psi(binners[c].codes(P.loc[P["segment"] == "HNW", c]), binners[c].codes(P.loc[P["segment"] == "UHNW", c]))
                         for c in chosen}, name="PSI HNW→UHNW")
    valo["banda antigüedad"] = pd.cut(valo["tenure_years"], [1, 3, 7, 15, 99], labels=["1–3", "3–7", "7–15", "> 15"], include_lowest=True)

    def cut_view(col):
        g = valo.groupby(col, observed=True)
        return pd.DataFrame({"N": g.size(), "p media": g["p_cal"].mean(), "churn obs.": g["y"].mean(),
                             "AUC": g.apply(lambda x: roc_auc_score(x["y"], x["p_cal"]) if 0 < x["y"].sum() < len(x) else np.nan, include_groups=False),
                             "% en Crítico+Alto": g["tramo"].apply(lambda s: s.isin(["Crítico", "Alto"]).mean())})
    stab = {"segmento": cut_view("segment"), "segmento estructural": cut_view("segmento_estructural"),
            "banda de AUM": cut_view("banda AUM"), "antigüedad (años)": cut_view("banda antigüedad")}

    # ------------------------------------------------------------------ 16 · Arquetipos de churners
    arch_vars = [c for c in ["aum_vs_baseline_pct", "positions_liquidated_pct", "transfer_to_competitor_pct_90d",
                             "external_transfer_pct_of_balance_60d", "salary_deposit_stopped_flag", "share_of_wallet_change",
                             "complaint_escalated_flag", "relationship_dissatisfaction_flag", "return_vs_benchmark",
                             "banker_change_6m_flag", "client_reply_rate", "contact_gap_ratio", "trustee_change_flag"] if c in binners]
    ch = dev[dev["y"] == 1]
    R = pd.DataFrame({c: -binners[c].woe(ch[c]) for c in arch_vars}, index=ch.index)  # riesgo aportado (−WoE)
    Rz = ((R - R.mean()) / R.std(ddof=0).replace(0, 1)).to_numpy()
    at, Ka, kma = sc.kmeans_select(Rz, ks=range(3, 6), seed=seed % 10_000 + 1, min_share=0.10, sample=len(Rz))
    cent = pd.DataFrame(kma.cluster_centers_, columns=arch_vars)
    arch_names, arch_desc = {}, {}
    groups = {"Erosión silenciosa de wallet / salida de activos": ["aum_vs_baseline_pct", "positions_liquidated_pct", "share_of_wallet_change"],
              "Externalización / mudanza del banco principal": ["transfer_to_competitor_pct_90d", "external_transfer_pct_of_balance_60d", "salary_deposit_stopped_flag"],
              "Salida por servicio": ["complaint_escalated_flag", "relationship_dissatisfaction_flag", "return_vs_benchmark"],
              "Salida con el banquero / desatención": ["banker_change_6m_flag", "client_reply_rate", "contact_gap_ratio"],
              "Evento de vida / sucesión": ["trustee_change_flag"]}
    for k in range(Ka):
        sc_g = {g: cent.loc[k, [v for v in vs if v in arch_vars]].mean() for g, vs in groups.items()}
        ranked = sorted(sc_g, key=lambda g: -sc_g[g])
        # Sin ninguna dimensión ≥ 0.3 d.e. sobre el churner promedio: el churner no mostró señal previa.
        arch_names[k] = ranked[0] if sc_g[ranked[0]] >= 0.3 else "Salida sin señal previa (no anticipable)"
        arch_desc[k] = ", ".join(f"{v} ({cent.loc[k, v]:+.1f} d.e.)" for v in cent.columns[np.argsort(-cent.loc[k].to_numpy())[:3]])
    # desambiguar nombres repetidos con el segundo grupo
    names = pd.Series(arch_names)
    for k in names[names.duplicated(keep=False)].index:
        sc_g = {g: cent.loc[k, [v for v in vs if v in arch_vars]].mean() for g, vs in groups.items()}
        arch_names[k] = " + ".join(sorted(sc_g, key=lambda g: -sc_g[g])[:2])
    ch_lab = pd.Series(kma.labels_, index=ch.index).map(arch_names)
    arch_tab = pd.DataFrame({"churners dev": ch_lab.value_counts(), "% de churners": ch_lab.value_counts(normalize=True),
                             "valor mediano ($M)": ch.groupby(ch_lab)["V0"].median() / 1e6,
                             "% económico (vs hard)": ch.groupby(ch_lab)["econ"].mean()})
    arch_tab["señales dominantes (centroide, d.e.)"] = pd.Series({arch_names[k]: arch_desc[k] for k in range(Ka)})
    # Asignación de arquetipo a toda la cartera (centroide más cercano, sobre el perfil de riesgo)
    Rall = pd.DataFrame({c: -binners[c].woe(P[c]) for c in arch_vars}, index=P.index)
    Rall_z = ((Rall - R.mean()) / R.std(ddof=0).replace(0, 1)).to_numpy()
    P["arquetipo"] = pd.Series(kma.predict(Rall_z), index=P.index).map(arch_names)

    # ------------------------------------------------------------------ Salida por cliente
    rc = card.reason_codes(P)
    P = P.join(rc)
    P["prioridad_p_x_valor"] = P["p_cal"] * P["V0"]
    P["rank_intra_tramo"] = P.groupby("tramo")["prioridad_p_x_valor"].rank(ascending=False, method="first").astype(int)
    outc = P[["household_id", "segment", "segmento_estructural", "sample", "indeterminate", "V0", "score", "p_model", "p_cal",
              "tramo_modelo", "override", "tramo", "arquetipo", "prioridad_p_x_valor", "rank_intra_tramo",
              "driver_1", "driver_1_pts", "driver_2", "driver_2_pts", "driver_3", "driver_3_pts", "y"]].rename(
        columns={"V0": "relationship_value_t0", "y": "churn_observado_6m"})
    outc.to_csv(OUT / "scorecard_clients.csv", index=False, float_format="%.6f", lineterminator="\n")
    lk = card.lookup()
    lk.to_csv(OUT / "scorecard_lookup.csv", index=False, float_format="%.4f", lineterminator="\n")

    def jumps(ms):
        r = ms["churn observado"].to_numpy()
        return ", ".join(f"{TRANCHES[i]}/{TRANCHES[i + 1]} {r[i] / r[i + 1]:.2f}×" for i in range(3))

    # ================================================================== REPORTE
    uh = P["segment"] == "UHNW"
    L += [f"# UHNWI Churn Propensity Scorecard · documento de modelo (pasos 0–17)", "",
          f"> **Toda cifra de este documento es {TAG}:** se calcula sobre `data/synthetic/client_pulse_synthetic.csv` "
          "(idéntica al Excel adjunto), una base **sintética** generada con parámetros explícitos (`config/params.yaml`). "
          "Ningún número es resultado de Citizens ni benchmark de industria. Reproducible: `python scripts/build_scorecard.py`.", "",
          "## Modo, parámetros y supuestos", "",
          "| Parámetro | Valor usado | Origen |", "|---|---|---|",
          "| Modo | **SINT-BASE**: pipeline de modo REAL ejecutado sobre la base sintética | Instrucción del usuario («usa la base sintética») |",
          f"| Universo | {N0:,} hogares ({int((d['segment'] == 'UHNW').sum()):,} UHNW ≥ $30M; resto HNW) | Base |",
          f"| Universo de modelado | {len(P):,} hogares (sin excluidos ni antigüedad < 12m) · UHNW {int(uh.sum()):,} | Paso 1 |",
          f"| Unidad | Hogar / relación (`household_id`) | Paso 0 |",
          f"| T0 | 2025-12-31 (un solo corte) | Base |",
          f"| Observación / desempeño | 24 m / **6 m** (T0, T0+6m] | Base (no hay 12 m) |",
          f"| Target | hard ∪ económico: salida neta ex-mercado ≥ {pct(sc.ECON_THRESHOLD, 0)} al cierre de la ventana | Paso 1 |",
          f"| Indeterminados | salida neta ex-mercado entre {pct(sc.INDET_LOW, 0)} y {pct(sc.ECON_THRESHOLD, 0)}: fuera del entrenamiento, dentro del scoring | Prompt |",
          f"| Escala | S₀ = {sc.S0:.0f} a O₀ = {sc.O0:.0f}:1 (buenos:malos), PDO = {sc.PDO:.0f} → Factor = {sc.FACTOR:.4f}, Offset = {sc.OFFSET:.4f} | Prompt |",
          f"| Banqueros | {n_bankers} (libros de {sc.BANKS_PER_BANKER['HNW']} HNW / {sc.BANKS_PER_BANKER['UHNW']} UHNW de la base); capacidad {sc.CRITICAL_PER_BANKER_MONTH} críticos nuevos/banquero/mes = **{capacity} casos/mes** ({pct(crit_share)} de la cartera) | Prompt (2/mes) escalado a la base |",
          f"| Validación | 70/30 estratificado (segmento × target × indeterminado) + bootstrap. **Sin OOT** (un solo corte) | Paso 4 |", "",
          "**Supuestos tomados por defecto (las preguntas del Paso 0 quedaron sin respuesta; cada uno se puede cambiar en `synthetic/scorecard.py`):**", "",
          f"- Universo completo con el segmento como variable de calibración, no solo UHNW: el UHNW aislado tiene {int(P.loc[uh, 'y'].sum())} eventos "
          f"({int(round(0.7 * P.loc[uh, 'y'].sum()))} en desarrollo), por debajo de los 300 que exige WoE-logística. Toda métrica se reporta también para UHNW.",
          "- Horizonte de 6 m en lugar de 12 m: la base no tiene ventana de 12 m.",
          "- Umbral económico de 25% (el del prompt), no el 20% del deck; la sensibilidad está en el Paso 1.",
          "- Capacidad: los 2 casos críticos por banquero al mes del prompt, aplicados a los banqueros implícitos de la base.",
          "- Las horas de banquero por alerta no están dadas: los falsos positivos se reportan en alertas; la conversión a horas queda como parámetro H.", ""]

    # ---- 0
    L += ["## 0. Definición del problema", "",
          "**Objetivo.** Fijar qué es churn, con qué horizonte, en qué unidad y cuál es la regla anti-leakage.",
          "**Por qué.** En UHNW la fuga es parcial: un target de cierre total llega tarde y modela cierres administrativos.",
          "**Método.** Target jerárquico con severidad:",
          "- Nivel 1: hard (valor ≤ 5% y sin recuperación).",
          "- Nivel 2: económico (flujo neto ex-mercado ≥ u).",
          "- La pérdida de banco principal (nómina, pensión, transferencias, share of wallet) entra como **features y overrides**, no como target, para no hacer circular el modelo.",
          "- Unidad: hogar. La decisión de mover activos es familiar (trust, negocio vinculado), los traspasos entre cuentas del mismo hogar no son fuga y el banquero gestiona hogares.",
          "**Anti-leakage.**",
          "- Features con fecha ≤ T0 (ventanas de lookback 30/60/90/180d y 24m); target solo en (T0, T0+6m].",
          "- `value_lost_6m`, `hard_churn_6m` y `soft_churn_3m` son resultados: prohibidos como predictores.",
          "- `multi_signal_count` es una compuesta de las demás features: fuera del modelo.",
          "**Datos.** Base + simulación de la ventana de resultado (`synthetic/outcome.py`, misma semilla maestra).",
          "**Salida.** Ficha del target (tabla de parámetros arriba).",
          "**Control de calidad.**",
          "- Ninguna feature supera IV 0.50 (ver paso 9).",
          "- La etiqueta hard reconstruida coincide 100% con el evento del generador (`docs/reports/model_comparison.md`).",
          "**Decisiones.** Descartados: unidad cuenta (falsos positivos por traspasos internos); 12 m (no existe en la base); Cox (no hay tiempo al evento continuo, solo el mes).", ""]

    # ---- 1
    L += ["## 1. Target y churn rate", "",
          "**Objetivo.** Construir y medir el evento: cuántos hay, a qué umbral y qué pesan en AUM.",
          "**Por qué.** El número de eventos decide el método (paso 11). En UHNW el rate por AUM manda: un hogar grande pesa más que veinte pequeños.",
          "**Método y fórmulas.**",
          "- Churn rate por relaciones = eventos ÷ relaciones activas en T0.",
          "- Churn rate por AUM bruto = Σ (V₀ − V₆) de churners ÷ Σ V₀. Incluye mercado.",
          "- Churn rate por AUM neto = Σ (Vx₀ − Vx₆) de churners ÷ Σ Vx₀, con Vx = depósitos + AUM ÷ índice de retorno del propio portafolio (flujo, no valuación).",
          "**Datos.** Saldos mensuales simulados en (T0, T0+6m].", "",
          "### 1.1 Exclusiones", "",
          "| Exclusión | Volumen | Tratamiento |", "|---|---|---|",
          f"| Excluidos del generador (fallecimiento / reubicación gestionada) | {int(excl.sum())} | Fuera de desarrollo y de scoring |",
          f"| Antigüedad < 12 meses | {int(short.sum())} | Fuera de desarrollo; en producción se scorean con marca «fuera de política» |",
          "| Vehículos de evento único (SPV), fraude, empleados, en proceso formal de salida | 0 (no identificables en la base) | Pedir marcas al banco (modo REAL) |",
          f"| **Universo de modelado** | **{len(P):,}** | = {N0:,} − {int(excl.sum())} − {int(short.sum())} |", "",
          "### 1.2 Sensibilidad del número de eventos al umbral económico", "", md(sens, ".4f"), "",
          f"Cálculo con u = 25%: {int(P['hard'].sum()):,} hard + {int(P['econ'].sum()):,} económico = {int(y_all.sum()):,} eventos; "
          f"{int(y_all.sum()):,} ÷ {len(P):,} = {pct(y_all.mean(), 2)}.", "",
          "### 1.3 Churn rate de cartera (6 m)", "", md(rates, ".4f"), "",
          "### 1.4 Por segmento", "", md(by_seg, ",.4f"), "",
          f"Chequeo: churn de cartera = Σ share × tasa = " + " + ".join(
              f"{by_seg.loc[s, 'relaciones'] / len(P):.4f}×{by_seg.loc[s, 'churn rate relaciones']:.4f}" for s in by_seg.index) +
          f" = {sum(by_seg.loc[s, 'relaciones'] / len(P) * by_seg.loc[s, 'churn rate relaciones'] for s in by_seg.index):.4f} ✓", "",
          "**Censura.** Un solo corte y ventana simulada completa: no hay censura en la base. En modo REAL, las relaciones sin 6 m de desempeño no entran a la logística (quedan para la cohorte siguiente); en Cox serían censuradas.",
          f"**Control de calidad.** Los eventos de desarrollo ({int(y_dev.sum()):,}) superan 300 → WoE-logística. Los indeterminados son {pct(ind.mean())} del universo, dentro del rango 10–25% del prompt.",
          "**Decisiones.** u = 25% y rango indeterminado 10–25%. Descartado u = 50%: deja solo el 12% de los eventos como económicos y convierte el target en casi-hard.", ""]

    # ---- 2
    L += ["## 2. Diccionario de datos y proceso generador", "",
          "**Objetivo.** Inventariar variables con tipo, ventana, missing y dirección esperada. **Por qué.** El signo esperado se fija "
          "antes de ver datos: es la hipótesis que valida la monotonicidad del paso 9.",
          "**Método.** 37 variables del Excel (seis bloques) + atributos estructurales. Bloque digital: **no existe en la base** (0 variables) → "
          "en modo REAL pedir logins, sesiones y transacciones digitales. Eventos de vida: solo `trustee_change_flag` (proxy de sucesión).", "",
          md(dic, ".1f"), "",
          "**Proceso generador [SINT] (β verdaderos, `config/params.yaml`).**",
          "- Latentes: tres factores N(0,1) correlacionados (outflow, neglect, service; ρ = 0.35 / 0.25 / 0.30).",
          "- Índice de riesgo = 0.60·z_outflow + 0.45·z_neglect + 0.35·z_service − 0.15·ln(1 + antigüedad) − 0.20·crédito ancla + 0.10·UHNW + ε, con ε ~ N(0, 0.60²); luego se estandariza.",
          "- Hard: logit p = a + 1.6·índice (tasa 6%). Soft: logit p = a + 1.2·índice (tasa 9%).",
          "- Las features se generan desde los latentes con ruido propio, **nunca desde el target**.",
          "- Techo teórico (AUC de la probabilidad verdadera) ≈ 0.86 para hard.", ""]

    # ---- 3
    L += ["## 3. Calidad de datos", "",
          "**Objetivo.** Detectar errores antes de modelar. **Por qué.** En UHNW las colas son reales (hogares de $900M); eliminarlas borra justo lo que importa.",
          "**Método.** Perfil por variable, controles de dominio y clasificación de outliers (error / comportamiento real / operación extraordinaria). Capping solo para errores.", "",
          md(qual, ".4g"), "",
          "### 3.1 Controles (umbral: 0 casos)", "",
          md(pd.Series(impossible, name="casos").to_frame(), ".0f"), "",
          ("Resultado: todos los controles en 0." if all(v == 0 for v in impossible.values()) else
           "Resultado: " + "; ".join(f"{k} = {v}" for k, v in impossible.items() if v > 0) +
           ". **No es error de dominio**: el denominador es el AUM *promedio* de la ventana, que cae cuando el hogar se lleva el portafolio, "
           "así que una salida total puede superar 100%. Se conservan (son la señal) y el binning por cuantiles las absorbe en el bin extremo sin capping."),
          "- Duplicados, fechas inconsistentes, cambios de definición y quiebres estructurales no aplican o no se detectan: hay un solo corte y no hay fechas por registro.",
          "- Cuentas dormidas: `history_months` < 24 en " + f"{int((d['history_months'] < 24).sum())} hogares (historia incompleta, se conservan; las ventanas de 90d están completas).", "",
          f"### 3.2 Ilustración de outliers · `external_transfer_pct_of_balance_60d` (p99 = {p99:.3f})", "",
          md(out_cls.rename("hogares").to_frame(), ".0f"), "",
          "Ninguno es error: no se capa. Los casos «comportamiento real» son la señal que se quiere capturar.",
          "**Control de calidad.** Si un control da > 0, se corrige en la fuente; el capping al p99.5 aplica solo a errores confirmados. Missing estructural (p. ej. flags de pensión sin flujo de pensión) = «no aplica», nunca 0.", ""]

    # ---- 4
    L += ["## 4. Muestra", "",
          "**Objetivo.** Separar desarrollo y validación sin fuga. **Método.** 70/30 estratificado por segmento × target × indeterminado. "
          "Sin sobremuestreo: la tasa de eventos es suficiente, así que no hay pesos que guardar. La única corrección de intercepto es por excluir indeterminados (paso 11).", "",
          md(sample_tab, ".4f"), "",
          "**Control de calidad.** La tasa de desarrollo y la de validación difieren < 0.1 pp (por construcción).",
          "- **OOT: no es posible.** La base tiene un solo corte.",
          "- La aprobación del paso 13 queda **condicionada** a una validación OOT sobre la cohorte más reciente cuando exista el panel mensual (el código de modo REAL aplica el mismo pipeline por cohorte).",
          "**Decisiones.** Descartado el random split como única validación → se complementa con bootstrap y con estabilidad por subpoblación (paso 15).", ""]

    # ---- 5
    L += ["## 5. Ingeniería de señales", "",
          "**Objetivo.** Traducir comportamientos en señales con nivel, recencia, magnitud relativa, tendencia y cambio vs. baseline propio. "
          "**Por qué.** En UHNW el nivel absoluto no discrimina; el cambio vs. el propio cliente sí.",
          "**Método.** La base ya trae las señales construidas (ventanas en el diccionario del paso 2):", "",
          "| Tipo de señal | Variables en la base |", "|---|---|",
          "| Magnitud relativa al AUM/saldo | aum_outflow_pct_90d, investment_redemption_pct, positions_liquidated_pct, external_transfer_pct_of_balance_60d, transfer_to_competitor_pct_90d |",
          "| Tendencia (3M vs 3M previo) | deposit_balance_change_pct_90d, recurring_deposit_change_pct |",
          "| Cambio vs baseline propio | aum_vs_baseline_pct, deposit_balance_vs_6m_avg_pct, outflow_vs_baseline_pct (24m) |",
          "| Aceleración | external_transfer_acceleration |",
          "| Recencia / frecuencia | complaint_age_days, contact_gap_ratio, new_external_destinations_90d, meetings_cancelled_by_client |",
          "| Nivel / estado | share_of_wallet, client_reply_rate, flags de nómina / pensión / queja / banquero |",
          "| **No disponibles** | persistencia (meses consecutivos de deterioro), volatilidad, engagement digital → pedir el panel mensual |", "",
          "Las 9 dimensiones del prompt quedan cubiertas salvo **engagement digital** (0 variables); «crédito / saldos» solo con crédito ancla y buró (este último condicionado).", ""]

    # ---- 6
    L += ["## 6. Análisis univariado (desarrollo)", "",
          "**Objetivo.** Confirmar dirección y tamaño de efecto antes de modelar.",
          "**Método.** Mediana y rango intercuartil por grupo; effect size = Cliff δ = 2·AUC − 1 sobre no-missing; missing por grupo.",
          "**Criterio.** Candidata si |δ| ≥ 0.05 y la dirección es la esperada; «CONTRARIA» se investiga.", "",
          md(uni.sort_values("Cliff δ", key=abs, ascending=False), ".3f"), "",
          f"Candidatas (evidencia consistente): {int((uni['evidencia'] == 'consistente').sum())} de {len(uni)}; "
          f"contrarias: {', '.join(uni.index[uni['evidencia'] == 'CONTRARIA']) or 'ninguna'}.",
          "El missing es informativo en varias variables (p. ej. `client_reply_rate`: missing = sin interacciones registradas), por eso va como bin propio.", ""]

    # ---- 7
    L += ["## 7. Pre-segmentación", "",
          "**Objetivo.** Ver si la cartera tiene poblaciones estructuralmente distintas que justifiquen scorecards separados.",
          "**Método.** K-means sobre variables estructurales estandarizadas: ln(valor), antigüedad, % depósitos, tenencias, flujos recurrentes y crédito ancla. **Sin edad (ECOA).**",
          "K se elige por silhouette entre las opciones con tamaño mínimo ≥ 5% y estabilidad (ARI medio en 5 submuestras del 80%) ≥ 0.80.", "",
          md(kt, ".3f"), "", f"**K elegido = {K}.**", "",
          md(prof.rename(columns={"valor_mediano": "valor mediano ($)"}), ",.3f"), "",
          "Solo K = 2 es estable (ARI ≥ 0.80): la estructura la domina la tenencia de inversiones. Los arquetipos del prompt (fundadores, next-gen, ejecutivos, family offices) "
          "**no emergen de forma estable** con las variables estructurales de la base (K ≥ 3 da ARI < 0.80); no se fuerzan.",
          "Churn rate por segmento: descriptivo; **no implica causalidad** (el segmento correlaciona con antigüedad y crédito ancla, que están en el mecanismo).", "",
          "**Regla de decisión.**",
          "- Scorecard separado solo si cada segmento conserva ≥ 100 eventos **y** el modelo propio mejora en validación.",
          f"- Eventos de desarrollo por segmento: {', '.join(f'{k}: {int(v)}' for k, v in ev_train.items())}.", "",
          md(seg_cmp, ".3f"), "",
          f"**Decisión: un solo scorecard.** La ganancia máxima de AUC de un modelo propio es {seg_cmp['Δ'].max():+.3f}, que no compensa multiplicar por {K} la validación y el monitoreo. "
          "El segmento se usa en la calibración (paso 14) y en el monitoreo (paso 15).", ""]

    # ---- 8
    L += ["## 8. Correlación y diagnóstico de estructura", "",
          "**Objetivo.** Identificar variables que miden el mismo fenómeno. **Método.** Pearson y Spearman (missing imputado a la mediana solo para este diagnóstico) y VIF sobre crudas.",
          "PCA **solo diagnóstico**: no entra en la selección ni en el modelo.", "",
          f"### 8.1 Pares con |ρ| ≥ 0.6 ({len(pairs)})", "", md(pairs, ".3f", index=False) if len(pairs) else "Ninguno.", "",
          "### 8.2 VIF sobre variables crudas (top 10)", "", md(vif_raw.head(10).rename("VIF").to_frame(), ".2f"), "",
          f"### 8.3 PCA diagnóstico (autovalores > 1: {kaiser} de {len(ev)})", "", md(pca_sum, ".2f"), "",
          "**Lectura (desde los loadings, no por nombre):**",
          "- Los primeros componentes agrupan **salida de activos** (outflow / redención / liquidación / baseline) y **externalización** (transferencias externas, flujo neto): varias variables miden el mismo fenómeno.",
          "- La varianza está repartida (sin componente dominante): hay información en varias dimensiones, lo que respalda un scorecard con diversidad de dimensiones.", ""]

    # ---- 9
    L += ["## 9. Binning, WoE e IV", "",
          "**Objetivo.** Discretizar cada variable en 4–8 bins monótonos con sentido de negocio.",
          "**Método.** optbinning (programación con restricciones):",
          f"- Fine classing de 20 pre-bins → coarse de ≤ 8 bins.",
          f"- Cada bin con ≥ {pct(sc.MIN_BIN_SHARE, 0)} de la población y ≥ {sc.MIN_BIN_EVENTS} eventos.",
          "- **Tendencia monótona forzada a la dirección esperada.**",
          "- Missing como bin propio si cumple los mínimos; si no, se asigna al bin de tasa más cercana.",
          "**Fórmulas.** WoE = ln(%buenos / %malos); IV = Σ (%buenos − %malos)·WoE.",
          "**Criterio IV.** < 0.02 fuera · 0.02–0.10 débil · 0.10–0.30 medio · 0.30–0.50 fuerte · > 0.50 sospechoso de fuga.", "",
          md(ivt, ".3f"), "",
          "*pérdida por monotonicidad* = 1 − IV forzado ÷ IV con tendencia libre. Si es > 50%, la relación no sigue la lógica de negocio y la variable no pasa.",
          f"Además, bins contiguos deben diferir en tasa con p < {sc.MAX_PVALUE} (si no, se funden); por eso varias variables quedan con 2–4 bins en lugar de 4–8. Se prefiere menos bins estables a más bins con WoE de ruido.",
          "**Flags raros (IV ≈ 0 con 1 bin):** quejas repetidas, insatisfacción expresada, cambio de trustee, nómina o pensión detenida y buró. Su categoría «1» tiene menos del 5% de la población, así que no puede ser un bin propio. "
          "No se pierden: pasan a **overrides y reglas de EWS** (pasos 12 y 16), donde se mide su precisión directamente.", ""]
    top3 = [c for c in chosen if dev[c].nunique() > 2][:3]   # continuas: en una binaria los 4 esquemas coinciden
    bus_cuts = {"aum_vs_baseline_pct": [-0.20, -0.05], "client_reply_rate": [0.5, 0.75], "positions_liquidated_pct": [0.001, 0.10, 0.25],
                "transfer_to_competitor_pct_90d": [0.001, 0.05, 0.15], "banker_change_6m_flag": [0.5], "return_vs_benchmark": [-0.03, 0.0],
                "external_transfer_pct_of_balance_60d": [0.05, 0.15], "share_of_wallet": [0.3, 0.6], "cash_pct_of_portfolio_chg": [0.0, 0.05],
                "complaint_age_days": [1, 30], "contact_gap_ratio": [1.0, 2.0], "salary_deposit_stopped_flag": [0.5],
                "recurring_deposit_stopped_flag": [0.5], "products_closed_180d": [0.5], "share_of_wallet_change": [-0.10, 0.0],
                "outflow_vs_baseline_pct": [0.0, 0.5], "net_external_flow_pct_90d": [-0.15, 0.0], "deposit_balance_vs_6m_avg_pct": [-0.30, 0.0]}
    L += ["### 9.1 Comparación de esquemas de binning (3 variables del modelo final)", ""]
    for c in top3:
        L += [f"**{c}**", "", md(sc.bin_method_comparison(c, dev[c], y_dev, bus_cuts.get(c, [0.0])), ".3f"), ""]
    L += ["### 9.2 Tablas WoE/IV (desarrollo) y estabilidad del WoE dev → val", ""]
    for c in top3:
        t = binners[c].table.copy()
        tv = binners[c].table_on(valm[c], y_valm)
        t["tasa churn val"] = tv["tasa churn"].to_numpy()
        g_ = (tv["N"] - tv["malos"]) / (tv["N"] - tv["malos"]).sum()
        b_ = tv["malos"] / tv["malos"].sum()
        t["WoE val"] = np.log((g_ + 1e-9) / (b_ + 1e-9)).to_numpy()
        L += [f"**{c}** · IV = {binners[c].iv:.3f} · missing: {binners[c].missing_policy}", "",
              md(t[["bin", "N", "% pob", "malos", "tasa churn", "WoE", "IV bin", "tasa churn val", "WoE val"]], ".4f", index=False), ""]
    L += ["**Problemas a vigilar.**",
          "- Bins pequeños: el mínimo de 5% y 30 eventos evita WoE con ruido.",
          "- WoE inestable entre cohortes: no medible con un solo corte; dev → val es el proxy.",
          "- No monotonicidad: si aparece en validación, se funden bins contiguos (nunca se invierte el signo).",
          "- Missing con WoE alto: se revisa si el missing es informativo (sin interacciones) o un defecto de captura.", ""]

    # ---- 10
    L += ["## 10. Selección de variables", "",
          "**Objetivo.** 5–8 variables no redundantes, con diversidad de dimensiones y signo correcto.",
          "**Método (en orden).**",
          "1. Filtro de negocio y regulación: variables prohibidas o condicionadas fuera.",
          "2. IV entre 0.02 y 0.50, con monotonicidad que no destruye el IV.",
          "3. Clustering de variables sobre WoE: jerárquico, distancia 1 − |ρ Spearman|, corte en |ρ| = 0.6. El centroide de cada cluster es la media del WoE estandarizado, sin PCA. Representante = menor (1 − R² propio)/(1 − R² vecino); si hay empate (± 0.05), gana el mayor IV.",
          "4. Orden de entrada en el camino LASSO (logística L1) entre representantes.",
          "5. Forward selection en ese orden. Entra una variable si cumple a la vez:",
          "   - β > 0 sobre WoE;",
          "   - VIF < 5;",
          "   - p < 0.05;",
          "   - ΔAUC (CV 5-fold) ≥ 0.002 una vez alcanzado el mínimo de 5;",
          "   - máximo 2 variables por dimensión.", "",
          "### 10.1 Variables excluidas por regulación o diseño", "",
          md(pd.Series(sc.PROHIBITED, name="motivo").to_frame(), ".3f"), "",
          f"### 10.2 Clustering de variables ({vc['cluster'].nunique()} clusters, {len(reps)} representantes)", "",
          md(vc, ".3f", index=False), "",
          "### 10.3 Forward selection (orden LASSO)", "", md(sel_log, ".4f", index=False), "",
          f"**Variables finales ({len(chosen)}):** " + ", ".join(f"`{c}` ({sc.VARS[c][0]})" for c in chosen) + ".",
          f"Dimensiones cubiertas: {len(set(sc.VARS[c][0] for c in chosen))} de las 9 del prompt.", ""]

    # ---- 11
    L += ["## 11. Estimación", "",
          "**Tabla de decisión por eventos.** < 50 → híbrido experto calibrado · 50–300 → logística penalizada o Cox · > 300 → logística sobre WoE.",
          f"Con {int(y_dev.sum()):,} eventos de desarrollo corresponde **logística sobre WoE** (Modelo A).",
          "No se usa Cox: la base no tiene tiempo al evento continuo, y la curva de hazard mensual del paso 14 cubre la necesidad del playbook.", "",
          "**Modelo A (campeón).** ln(odds buenos) = β₀ + Σ βⱼ·WoEⱼ.", "", md(coef_tab, ".4f"), "",
          f"- **Todos los β > 0:** {'sí ✓' if (beta > 0).all() else 'NO ✗'}. **VIF máx:** {coef_tab['VIF'].max():.2f} (< 5 ✓).",
          f"- Corrección de intercepto por indeterminados: el desarrollo excluye {int((P['sample'] == 'dev').sum() - len(dev))} indeterminados, que en la población son «no churn».",
          f"  - β₀ = β₀* − ln(odds muestra) + ln(odds población) = {b0_star:.4f} − ln({odds_s:.4f}) + ln({odds_p:.4f}) = **{b0:.4f}**.", "",
          "**Modelo B (challenger): gradient boosting** (HistGradientBoosting, todas las candidatas permitidas, crudas).", "",
          md(cmp[["N", "eventos", "AUC", "Gini", "PR-AUC", "PR-AUC base (tasa)", "KS", "captura AUM top 10%"]], ".4f"), "",
          f"- Diferencia de AUC en validación (B − A), IC 95% bootstrap pareado: [{dlo:+.4f}, {dhi:+.4f}] → "
          f"{'**no significativa**' if dlo <= 0 <= dhi else ('B mejor' if dlo > 0 else 'A mejor')}.",
          f"- Calibración en validación (sin indeterminados): p media A = {gb_cal['A'][0]:.4f}, Brier {gb_cal['A'][1]:.4f} · "
          f"B = {gb_cal['B'][0]:.4f}, Brier {gb_cal['B'][1]:.4f} · observado {y_valm.mean():.4f}.", "",
          "| Criterio | Modelo A · scorecard | Modelo B · GBM |", "|---|---|---|",
          f"| AUC / PR-AUC / KS val | {cmp.iloc[1]['AUC']:.3f} / {cmp.iloc[1]['PR-AUC']:.3f} / {cmp.iloc[1]['KS']:.1f} | {cmp.iloc[3]['AUC']:.3f} / {cmp.iloc[3]['PR-AUC']:.3f} / {cmp.iloc[3]['KS']:.1f} |",
          f"| Caída de Gini dev → val | {1 - cmp.iloc[1]['Gini'] / cmp.iloc[0]['Gini']:.1%} | {1 - cmp.iloc[3]['Gini'] / cmp.iloc[2]['Gini']:.1%} |",
          f"| Variables | {len(chosen)} | {len(gb_cols)} |",
          "| Explicabilidad | Puntos por bin; reason codes exactos | Requiere SHAP; no hay puntos auditables |",
          "| Monotonicidad garantizada | Sí (binning forzado) | No (salvo restricciones explícitas) |",
          "| Implementación | Lookup table (SQL/CRM) | Servicio de scoring + versión del modelo |", "",
          "**Decisión: Modelo A campeón.**",
          "- La ventaja de B no es significativa, o es menor que el costo de explicabilidad.",
          "- B queda como challenger en el monitoreo: si supera a A en OOT de forma significativa en dos ciclos, se documenta el costo de explicabilidad y se reevalúa.", ""]

    # ---- 12
    L += ["## 12. Escalamiento, tramos y salida por cliente", "",
          "**Fórmulas.**",
          f"- Factor = PDO / ln 2 = {sc.PDO:.0f} / 0.6931 = **{sc.FACTOR:.4f}**.",
          f"- Offset = S₀ − Factor·ln(O₀) = {sc.S0:.0f} − {sc.FACTOR:.4f}·ln {sc.O0:.0f} = **{sc.OFFSET:.4f}**.",
          "- Score = Offset + Factor·ln(odds buenos).",
          f"- Puntos por bin = (βⱼ·WoEⱼ + β₀/n)·Factor + Offset/n, con n = {len(chosen)}.",
          "- Mayor score = menor churn. **El score son puntos, no una probabilidad**: 600 puntos equivale a odds 20:1, es decir p ≈ 4.8% *antes* de calibrar.", "",
          "### 12.1 Lookup table completa", "", md(lk, ".4f", index=False), "",
          f"Chequeo: score de un hogar con WoE = 0 en todo = Offset + β₀·Factor = {sc.OFFSET:.2f} + {b0:.4f}·{sc.FACTOR:.4f} = {sc.OFFSET + b0 * sc.FACTOR:.2f}. "
          f"Rango observado del score: {P['score'].min():.0f} – {P['score'].max():.0f}; mediana {P['score'].median():.0f}.", "",
          "### 12.2 Tramos (sobre probabilidad calibrada; cortes fijados en validación)", "",
          "**Criterios, en orden:**",
          f"1. **Capacidad.** Crítico = {capacity} casos = {pct(crit_share, 2)} de la cartera, trabajable en 30 días.",
          "2. **Salto ≥ 2×** entre tramos contiguos y **lift ≥ 5×** de Crítico vs. Estable.",
          "3. **≥ 30 eventos por tramo.**",
          "- Entre las particiones que cumplen, se elige la de mayor IV del tramo.",
          ("- **Aviso:** ninguna partición cumple todos los saltos ≥ 2×; se relajó al máximo salto mínimo alcanzable." if relaxed else "- Todas las condiciones se cumplen."),
          f"- Umbrales de p calibrada: Crítico ≥ {thr[0]:.2%} · Alto ≥ {thr[1]:.2%} · Vigilancia ≥ {thr[2]:.2%} · Estable < {thr[2]:.2%}.",
          "- Cortes equivalentes en puntos: difieren por segmento por el δ de calibración UHNW (paso 14). A igual score, un UHNW tiene más probabilidad.", "",
          md(cuts_tab, ".1f"), "",
          "### 12.3 Escala maestra · relaciones (validación, con overrides)", "", md(ms_rel, ".4f"), "",
          f"Chequeos:",
          f"- % relaciones suma {ms_rel['% relaciones'].sum():.4f}; captura suma {ms_rel['captura'].sum():.4f}.",
          f"- Churn de cartera = Σ share × tasa = " + " + ".join(f"{ms_rel.loc[t, '% relaciones']:.4f}×{ms_rel.loc[t, 'churn observado']:.4f}" for t in TRANCHES) +
          f" = {sum(ms_rel.loc[t, '% relaciones'] * ms_rel.loc[t, 'churn observado'] for t in TRANCHES):.4f} = tasa observada {r_rel:.4f} ✓.",
          f"- Lift Crítico/Estable = {ms_rel.loc['Crítico', 'churn observado'] / ms_rel.loc['Estable', 'churn observado']:.1f}×.",
          "- Saltos entre tramos contiguos:",
          f"  - sin overrides: {jumps(ms_model_rel)};",
          f"  - con overrides: {jumps(ms_rel)}.",
          "- Los overrides llevan a Alto casos de precisión 12–25%, por debajo de la tasa de Alto, así que diluyen el salto Alto/Vigilancia. Es el costo de la regla de negocio; se revisa trimestralmente (paso 14, capa 4).", "",
          "### 12.4 Escala maestra · AUM (validación)", "", md(ms_aum, ".4f"), "",
          f"Chequeos:",
          f"- % AUM suma {ms_aum['% AUM'].sum():.4f}; captura de AUM de churners suma {ms_aum['captura de AUM de churners'].sum():.4f}.",
          f"- Churn por AUM = " + " + ".join(f"{ms_aum.loc[t, '% AUM']:.4f}×{ms_aum.loc[t, 'churn observado (AUM de churners ÷ AUM)']:.4f}" for t in TRANCHES) +
          f" = {sum(ms_aum.loc[t, '% AUM'] * ms_aum.loc[t, 'churn observado (AUM de churners ÷ AUM)'] for t in TRANCHES):.4f} = {r_aum:.4f} ✓.",
          "- Aquí churn por AUM = valor de las relaciones que churnean ÷ valor del tramo. La salida neta efectiva (flujo) está en el paso 14 por banda de AUM.", "",
          "### 12.5 Matriz de gobernanza", "", md(gov, ".3f"), "",
          "Prioridad intra-tramo = p calibrada × valor de la relación (columna `rank_intra_tramo` de la salida).", "",
          "### 12.6 Overrides a Crítico (precisión en validación sobre casos que el modelo no puso en Crítico)", "",
          "Regla de permanencia: precisión ≥ 25% se queda en Crítico; 12–25% baja a Alto; < 12% se elimina. Tope: ningún override puede ser > 30% del tramo.", "",
          md(ovr, ".4f"), "",
          f"% de cada tramo que entra por override: {', '.join(f'{t} {ovr_share[t]:.1%}' for t in TRANCHES if pd.notna(ovr_share[t]))}.",
          f"Tope 30%: {'cumple ✓' if (ovr_share.fillna(0) <= 0.30).all() else 'NO cumple: reducir reglas'}.",
          f"Con overrides, Crítico tiene {int((P.tramo == 'Crítico').sum()):,} hogares en la cartera, frente a una capacidad de {capacity}/mes: "
          + ("el exceso se ordena por prioridad p × valor y lo que no entra en el mes pasa al SLA del mes siguiente." if (P.tramo == 'Crítico').sum() > capacity else "cabe en la capacidad."),
          "Sin datos en la base (se piden en modo REAL): liquidity event, fallecimiento del principal, salida del banquero con fecha exacta (≤ 90 días).", "",
          "### 12.7 Escala maestra sin overrides (efecto de los overrides)", "", md(ms_model_rel[["% relaciones", "churn observado", "captura", "lift", "eventos", "N"]], ".4f"), "",
          "### 12.8 Salida por cliente (ejemplos: los 5 de mayor prioridad en Crítico)", "",
          md(outc[outc["tramo"] == "Crítico"].sort_values("rank_intra_tramo").head(5)[
              ["household_id", "segment", "relationship_value_t0", "score", "p_cal", "tramo", "override", "arquetipo",
               "driver_1", "driver_1_pts", "driver_2", "driver_2_pts", "driver_3", "driver_3_pts"]], ",.3f", index=False), "",
          "Reason codes: bins con mayor pérdida de puntos vs. neutral (WoE = 0), pérdida = −βⱼ·WoEⱼ·Factor. Nunca se entrega un score sin sus tres drivers.",
          "Lectura de «Missing» para el banquero:",
          "- `aum_vs_baseline_pct` / `positions_liquidated_pct`: sin portafolio de inversión.",
          "- `client_reply_rate`: sin interacciones registradas.",
          "- `return_vs_benchmark`: sin cuenta advisory.",
          f"- Frecuencia del driver #1 en la cartera: {', '.join(f'{k} {v:,}' for k, v in P['driver_1'].str.split(' ').str[0].value_counts().items())}.",
          "Archivo completo: `data/synthetic/scorecard_clients.csv`.", ""]

    # ---- 13
    L += ["## 13. Validación", "",
          "**Métricas de referencia (validación de modelo, sin indeterminados).** Ver la tabla del paso 11.",
          f"**Validación operativa (población completa de validación, indeterminados = no churn):** AUC {val_full['AUC']:.3f}, "
          f"PR-AUC {val_full['PR-AUC']:.3f} (base {val_full['PR-AUC base (tasa)']:.3f}), KS {val_full['KS']:.1f}, Gini {val_full['Gini']:.3f}.", "",
          "### 13.1 Gains y lift por decil (validación operativa, p calibrada)", "", md(dec, ".4f"), "",
          "### 13.2 Métricas decisivas", "",
          f"- **Captura de AUM de churners en el decil top:** {cap_top:.1%} ordenando por p; {cap_prio:.1%} ordenando por prioridad p × valor.",
          f"- **Falsos positivos en Crítico + Alto:** {fp:,} alertas sin churn frente a {tp:,} con churn: {fp / max(tp, 1):.2f} alertas falsas por cada churner detectado.",
          f"  - Horas de banquero senior = FP × H, con H (horas por alerta) = **parámetro abierto**. Con la muestra de validación escalada a la cartera: ≈ {fp / 0.3:,.0f} alertas falsas × H.", "",
          "### 13.3 Criterios de aprobación", "",
          "| Criterio | Umbral | Resultado | Estado |", "|---|---|---|---|",
          f"| KS validación | ≥ 30 | {cmp.iloc[1]['KS']:.1f} | {'PASA' if cmp.iloc[1]['KS'] >= 30 else 'FALLA'} |",
          f"| PR-AUC > tasa base | > {y_valm.mean():.3f} | {cmp.iloc[1]['PR-AUC']:.3f} | {'PASA' if cmp.iloc[1]['PR-AUC'] > y_valm.mean() else 'FALLA'} |",
          f"| Caída de Gini dev → val | ≤ 15% relativo | {gini_drop:.1%} | {'PASA' if gini_drop <= 0.15 else 'FALLA'} |",
          f"| Monotonicidad de tasa por tramo (dev y val) | estrictamente decreciente | {'sí' if mono_ok else 'no'} | {'PASA' if mono_ok else 'FALLA'} |",
          f"| Monotonicidad por bin, variables finales (dev y val) | todas | {int((bins_mono == 'sí').all(axis=1).sum())}/{len(chosen)} | {'PASA' if (bins_mono == 'sí').all().all() else 'REVISAR'} |",
          f"| PSI por tramo dev → val | < 0.10 | {psi_tr:.4f} | {'PASA' if psi_tr < 0.10 else 'FALLA'} |",
          "| OOT (cohorte más reciente) | caída de Gini ≤ 15% | no disponible (un corte) | **PENDIENTE** |", "",
          md(mono, ".4f"), "",
          "**Dictamen:** aprobado para piloto en la base sintética; **la aprobación productiva queda condicionada al OOT** con datos del banco.", ""]

    # ---- 14
    L += ["## 14. Calibración (cuatro capas)", "",
          "**Capa 1 · Modelo.** Platt: logit(p_cal) = a + b·logit(p) sobre la validación operativa (incluye indeterminados).",
          f"- a = {a_pl:.4f}, b = {b_pl:.4f} → b {'dentro' if 0.8 <= b_pl <= 1.2 else 'FUERA'} de [0.8, 1.2].",
          f"- Cross-fit en mitades: (a, b) = ({a1:.3f}, {b1:.3f}) y ({a2:.3f}, {b2:.3f}).",
          f"- Brier: {', '.join(f'{k} {v:.4f}' for k, v in brier.items())}.",
          f"- Isotónica: la validación tiene {int(y_valo.sum())} eventos, suficiente, pero no mejora el Brier de forma material y rompe la suavidad → se queda Platt.",
          f"- **Tendencia central:** p calibrada media en la cartera = {P['p_cal'].mean():.4f} vs. churn observado de la cartera = {P['y'].mean():.4f}. Con un solo corte, la «tasa de largo plazo» es la del corte; en modo REAL es la media de las cohortes apiladas.", "",
          md(cal_dec, ".4f"), "",
          "**Capa 1b · Segmento.** El tamaño no está en el score.",
          "- Si la tasa observada de un segmento cae fuera del IC Wilson 90% de su esperado, se aplica un desplazamiento de intercepto δ propio del segmento: logit(p_cal) = a + b·logit(p) + δ_segmento.",
          "- Se estima sobre toda la cartera, porque la validación sola tiene pocos eventos UHNW.", "",
          md(seg_tab, ".4f"), "",
          f"Lectura: el generador tiene un efecto UHNW de +0.10 en el índice de riesgo (paso 2). El score no lo captura porque el tamaño se excluyó a propósito, así que **la capa de calibración lo recupera** (δ UHNW = {seg_shift.get('UHNW', 0):+.3f}). "
          "Los tramos se cortan sobre esta p calibrada final.", "",
          "**Capa 2 · Tramo.** Esperado vs. observado con IC de Wilson 90%; shrinkage beta-binomial p = (eventos + m·p_modelo)/(N + m), m = 30.", "",
          md(trc, ".4f"), "",
          ("Tramos fuera del IC: " + ", ".join(trc.index[trc["¿esperado dentro del IC?"] == "NO"]) +
           ". En la cola baja, Platt con b < 1 sobreestima el riesgo del tramo Estable, un error conservador. Para reportar se usa la p con shrinkage; "
           "los cortes no se tocan en el año 1." if (trc["¿esperado dentro del IC?"] == "NO").any() else "Todos los tramos dentro del IC."), "",
          "**Capa 3 · Cortes.**",
          "- Fijos el año 1.",
          "- Se recortan una vez al año si dos cohortes consecutivas caen fuera del IC.",
          "- Nunca se recalibran modelo y cortes en el mismo ciclo.",
          "**Capa 4 · Overrides.** Precisión por regla (paso 12.6), se re-mide cada trimestre.", "",
          "**Intervención vs. predicción.**",
          "- El playbook bajará el churn observado en Crítico; eso no es descalibración.",
          "- La calibración se mide sobre cohortes previas al lanzamiento.",
          "- La retención se mide por uplift, con un control aleatorio del 10–15% **solo en Alto**. En Crítico no hay control por razones éticas y comerciales.", "",
          "**Calibración parcial (hazard mensual del evento).** p(≤ h meses) ≈ p₆·H(h).", "", md(haz, ".4f"), "",
          "**Por segmento y por AUM.** Σ pᵢ·AUMᵢ esperado vs. AUM de los churners observados.", "",
          md(seg_cal, ",.4f"), "", md(aum_cal, ",.4f"), "",
          "Si la razón observado/esperado se aleja sistemáticamente de 1 en las bandas altas, se agrega la interacción tramo × banda de AUM en la calibración (no en el score).",
          "En las bandas > $30M hay pocos eventos: la razón es volátil, e ± 1 hogar grande la mueve.", ""]

    # ---- 15
    L += ["## 15. Estabilidad", "",
          "**Criterio PSI.** < 0.10 estable · 0.10–0.25 vigilar · > 0.25 inestable.",
          "- Por mes, trimestre y cohorte: **no medible** (un corte).",
          "- Se mide dev → val (muestreo) y HNW → UHNW (poblaciones distintas).",
          f"- **PSI del score (deciles de dev) dev → val:** {psi_score:.4f}.", "",
          md(pd.concat([psi_vars, psi_seg], axis=1), ".4f"), "",
          "El PSI HNW → UHNW **no es un fallo**: mide qué tan distinta es la población UHNW. Si es > 0.25, la calibración por segmento del paso 14 es obligatoria.", ""]
    for k, v in stab.items():
        L += [f"**Por {k} (validación operativa)**", "", md(v, ".4f"), ""]
    dep = stab["segmento estructural"]
    dep_row = dep.loc[[i for i in dep.index if i.startswith("Depositante")]].iloc[0] if any(i.startswith("Depositante") for i in dep.index) else None
    if dep_row is not None:
        L += ["**Hallazgo · hogares sin inversiones.**",
              f"- Discriminación baja: AUC {dep_row['AUC']:.2f}.",
              f"- Concentran alertas: {dep_row['% en Crítico+Alto']:.0%} de ellos queda en Crítico+Alto.",
              "- Por qué:",
              "  - su churn observado es alto porque el target económico se dispara con la volatilidad del saldo de depósitos (compras, impuestos), no solo con fuga;",
              "  - tres de las ocho variables quedan en «Missing» por no tener portafolio.",
              "- **No es un defecto de estabilidad sino de definición del target para este segmento.**",
              "- En modo REAL: medir la salida económica de depositantes con transferencias salientes netas (no con caída de saldo) y reevaluar un scorecard propio.", ""]

    # ---- 16
    L += ["## 16. Acción, arquetipos y EWS", "",
          "**Arquetipos.**",
          "- K-means solo sobre churners de desarrollo, usando su perfil de riesgo previo a T0 (−WoE de 13 señales, estandarizado).",
          "- K entre 3 y 5 por silhouette, con tamaño mínimo 10% y ARI ≥ 0.80.",
          "- Describen *cómo se ven* los churners antes de irse; **no son causas**.", "",
          md(at, ".3f"), "", f"**K = {Ka}.**", "", md(arch_tab, ".3f"), "",
          "- «Sin señal previa»: churners por debajo del churner promedio en todas las dimensiones. Es la parte del churn que ningún modelo con estas variables anticipa, y explica el techo de AUC.",
          "- Las señales de servicio y banquero no forman un cluster propio: aparecen mezcladas con la externalización (centroide con banquero +0.8 d.e.).",
          "- Los arquetipos se asignan a toda la cartera por centroide más cercano (columna `arquetipo`), para elegir la acción, no para puntuar.", "",
          "### 16.1 Playbook = tramo × arquetipo (el score predice; no decide la acción)", "",
          "| Arquetipo | Crítico (≤ 5 días hábiles) | Alto (≤ 15 días hábiles) | Vigilancia | Responsable |", "|---|---|---|---|---|",
          "| Erosión silenciosa de wallet / salida de activos | Reunión de revisión patrimonial: portafolio vs. objetivos, propuesta de consolidación | Llamada con revisión de desempeño y vencimientos | Alerta de vencimientos no reinvertidos | Banquero + especialista de inversiones |",
          "| Externalización / mudanza del banco principal | Visita del banquero senior; mapear a dónde van los flujos y por qué | Contacto sobre nómina y flujos recurrentes | Monitoreo de transferencias | Banquero + Head of PB |",
          "| Salida por servicio | Resolución de la queja con el Head of PB, compromiso de SLA | Seguimiento de caso y encuesta | Cierre de casos abiertos | Servicio + Head of PB |",
          "| Salida con el banquero / desatención | Presentación del nuevo banquero con el Head of PB; plan de cadencia | Recuperar la cadencia; welcome call | Cadencia | Head of PB |",
          "| Evento de vida / sucesión | Planeación sucesoria / Legacy con la next-gen | Contacto con trustee / familia | — | Banquero + Legacy |",
          "| Salida sin señal previa | No debería llegar a Crítico por score; si llega por override, contacto de diagnóstico | Revisión de relación en la próxima cadencia | Cadencia | Banquero |", "",
          "Filas sin arquetipo estadístico en esta base (servicio, banquero, evento de vida) se conservan en el playbook: las señales existen como drivers y overrides aunque no formen un cluster propio.", "",
          "Cadencia: Crítico semanal hasta volver a Vigilancia; Alto quincenal; Vigilancia según la cadencia del segmento (UHNW 30 días, HNW 90).", "",
          "### 16.2 EWS", "",
          "- **Disparadores:** entrada a Crítico/Alto; override activado; subida de dos tramos en un trimestre; `multi_signal_count` ≥ 3 (regla de alerta, no predictor).",
          "- **Integración CRM:** tarea con score, p calibrada, tramo, arquetipo, top 3 drivers y SLA; se cierra solo con el resultado del contacto registrado.",
          "- **Matriz de migración mensual** (tramo t−1 × tramo t) y **KPI de regreso Crítico → Vigilancia** tras la intervención: requieren el panel mensual; en esta base (un corte) no son medibles.",
          f"- **Distribución actual de la cartera por tramo:** {', '.join(f'{t} {(P.tramo == t).mean():.1%}' for t in TRANCHES)} (= {', '.join(str(int((P.tramo == t).sum())) for t in TRANCHES)} hogares).", ""]

    # ---- 17
    L += ["## 17. KPIs, monitoreo, gobernanza y limitaciones", "",
          "| KPI | Definición | Frecuencia | Umbral de acción |", "|---|---|---|---|",
          "| Churn rate por AUM (neto de mercado) | Σ flujo neto de salida de churners ÷ AUM inicial | Mensual (rolling 6m) | Tendencia al alza 2 trimestres |",
          "| NNM retenido en alertados | NNM de Crítico+Alto tratados vs. control (solo Alto) | Trimestral | Uplift ≤ 0 dos trimestres |",
          "| Precisión de alertas | churn observado en Crítico / Alto | Trimestral | Fuera del IC Wilson 90% |",
          "| Tiempo alerta → contacto | días hábiles | Semanal | > SLA en > 10% de casos |",
          "| PSI score y variables | vs. desarrollo | Mensual | > 0.10 vigilar; > 0.25 acción |",
          "| Calibración por tramo | esperado vs. observado | Trimestral | 2 ciclos fuera de rango |", "",
          "**Disparadores.**",
          "- **Recalibración:** b de Platt fuera de [0.8, 1.2] durante dos ciclos.",
          "- **Redesarrollo:** PSI > 0.25 sostenido o caída de Gini ≥ 15% relativo.",
          "- **Challenger:** el GBM supera al scorecard de forma significativa en OOT en dos ciclos.",
          "**Documento de modelo.** Este reporte cubre target, fuentes, ventanas, exclusiones, variables, transformaciones, binning, diagnóstico de estructura, "
          "segmentación, WoE/IV, campeón y challenger, escalamiento, calibración, validación, estabilidad y monitoreo. Código: `synthetic/scorecard.py`, `scripts/build_scorecard.py`.", "",
          "### Limitaciones", "",
          "- **Causalidad:** el modelo ordena por riesgo; no dice por qué se va nadie ni qué acción funciona (eso lo mide el uplift).",
          "- **Datos sintéticos:** el mecanismo es mayormente aditivo y conocido; en datos reales habrá interacciones, errores de captura y cambios de definición que aquí no existen.",
          "- **Un solo corte:** sin OOT, sin PSI temporal, sin matriz de migración, sin estacionalidad; cohortes apiladas no disponibles.",
          "- **Horizonte de 6 m**, no 12 m; la curva de hazard solo cubre (0, 6].",
          "- **Eventos no observados:** liquidity events, fallecimientos, divorcios, next-gen sin relación, digital: ausentes o con proxies.",
          "- **Cambios de régimen:** mercado, tasas y competencia cambian la relación señal–churn; el umbral ex-mercado depende de un índice de retorno bien medido.",
          "- **Efecto de la propia intervención:** una vez en producción, el churn observado en Crítico deja de medir la calidad predictiva.",
          "- **Cola UHNW:** pocos eventos en > $30M; la captura de AUM depende de unos pocos hogares. El tamaño se corrige en calibración (δ UHNW), no en el score.",
          "- **Depositantes sin inversiones:** baja discriminación y exceso de alertas (paso 15); el target económico es ruidoso para ellos.",
          "- **Churn sin señal previa:** más de la mitad de los churners de desarrollo no muestra señal distintiva antes de T0 (paso 16).", "",
          "## Cierre", "",
          "### (a) Qué cambiaría en modo REAL", "",
          "- Panel mensual con cohortes apiladas (≥ 3 años) → OOT real, PSI temporal, matriz de migración, cortes estables.",
          "- Ventana de desempeño de 12 m y flujo neto medido con transacciones (no inferido del índice de retorno).",
          "- Exclusiones con motivo (SPV, fraude, empleados, fallecidos, salida formal) y fecha del evento para Cox / curva de hazard real.",
          "- Bloque digital y eventos de vida; `banker_id` para capacidad real por banquero.",
          "- Validación independiente del binning y de los overrides sobre al menos dos cohortes.", "",
          "### (b) Preguntas abiertas para el equipo de datos", "",
          "1. ¿Existe un panel mensual de saldos y flujos por hogar, con al menos 36 meses?",
          "2. ¿Cómo se consolida el hogar (trusts, LLC, negocio vinculado) y con qué frecuencia cambia?",
          "3. ¿Hay flujo neto de inversión (aportes / retiros / ACATS) separado de la valuación?",
          "4. ¿Qué marcas existen para fallecimiento, fraude, empleados, SPV y proceso formal de salida?",
          "5. ¿Hay `banker_id` con historial de asignación y fecha de salida del banquero?",
          "6. ¿Qué datos digitales hay (logins, sesiones, uso del Assistant) y desde cuándo?",
          "7. ¿Hay dictamen legal para usar buró (FCRA) en revisión de cuenta?",
          "8. ¿Cuántas horas de banquero senior cuesta una alerta (parámetro H)?", "",
          "### (c) Limitaciones", "", "Ver la sección «Limitaciones» del paso 17.", ""]

    REPORT.write_text("\n".join(L) + "\n")
    print(f"Variables: {chosen}")
    print(cmp[["AUC", "PR-AUC", "KS", "Gini"]].round(4).to_string())
    print(ms_rel.round(4).to_string())
    print(f"Platt a={a_pl:.3f} b={b_pl:.3f} | relaxed={relaxed} | capacity={capacity}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
