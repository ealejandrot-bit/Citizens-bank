"""Paso 7 · Complaints & voice of client (variables 14, 15, 33, 36).

* Quejas de 12 meses con taxonomía de nivel 2: frecuencia y categoría ligadas a z_service y
  z_neglect; ruido independiente del riesgo (fraude, errores de estado de cuenta); queja por demora
  del ACATS entre quienes se mudan (propensión). Cada queja: apertura, resolución, SLA, escalamiento
  (gerencia / ombudsman / regulador / legal) y reapertura.
* Assistant (#36): solo hogares del piloto (sin historia para el resto → NULL). Estado real de
  insatisfacción → conversación → clasificador (TPR / FPR) → revisión humana.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import special

from .seeds import SeedManager

H = 365


def simulate_complaints(base, truth, cfg, seeds: SeedManager, exit_ev) -> dict:
    s7 = cfg["step7"]
    n = len(base)
    z_s, z_n = truth["z_service"].to_numpy(), truth["z_neglect"].to_numpy()
    cats = list(s7["categories"])
    r = seeds.rng("s7.complaints")
    lam = s7["complaint_base_rate_12m"] * np.exp(s7["complaint_service_loading"] * z_s + s7["complaint_neglect_loading"] * z_n)
    cnt = r.poisson(lam)
    hh = np.repeat(np.arange(n), cnt)
    # Categoría: la base se inclina hacia banker_attention con z_neglect y hacia rendimiento / proceso con z_service.
    w = np.tile(np.array(list(s7["categories"].values())), (len(hh), 1))
    w[:, cats.index("banker_attention")] *= np.exp(0.6 * z_n[hh])
    w[:, cats.index("process_delay")] *= np.exp(0.3 * z_s[hh])
    w[:, cats.index("investment_performance")] *= np.exp(0.3 * z_s[hh])
    w /= w.sum(axis=1, keepdims=True)
    u = r.random(len(hh))[:, None]
    cat = np.array(cats)[(u > np.cumsum(w, axis=1)).sum(axis=1)]
    src = np.full(len(hh), "service")
    # Ruido: fraude / errores de estado de cuenta, independientes del riesgo.
    rn = seeds.rng("s7.noise")
    cn = rn.poisson(s7["noise_complaints_12m"], n)
    hn = np.repeat(np.arange(n), cn)
    catn = rn.choice(s7["noise_categories"], len(hn))
    # Demora del ACATS entre quienes se mudan.
    ra = seeds.rng("s7.acats")
    ac = exit_ev["aum_transfer"].to_numpy() & (ra.random(n) < s7["acats_complaint_p"])
    ha = np.nonzero(ac)[0]
    hh = np.concatenate([hh, hn, ha])
    cat = np.concatenate([cat, catn, np.full(len(ha), "transfers_wires")])
    src = np.concatenate([src, np.full(len(hn), "noise"), np.full(len(ha), "acats_delay")])
    m = len(hh)
    rr = seeds.rng("s7.lifecycle")
    open_day = np.floor(rr.uniform(-H, 0, m)) + 1
    acats_day = exit_ev["acats_day"].to_numpy()
    open_day = np.where(src == "acats_delay", np.minimum(np.nan_to_num(acats_day[hh], nan=0) + 10, 0), open_day)
    res_days = rr.lognormal(np.log(s7["resolution_median_days"]) + s7["resolution_service_loading"] * np.where(src == "noise", 0, z_s[hh]),
                            s7["resolution_sigma"], m)
    close_day = open_day + np.ceil(res_days)
    is_open = close_day > 0
    sla = pd.Series(cat).map(s7["sla_days"]).to_numpy()
    elapsed = np.where(is_open, -open_day, close_day - open_day)
    out_sla = elapsed > sla
    zs_eff = np.where(src == "noise", 0.0, z_s[hh])
    p_esc = special.expit(s7["escalation_intercept"] + s7["escalation_service_slope"] * zs_eff + s7["escalation_out_of_sla_add"] * out_sla)
    esc = rr.random(m) < p_esc
    lv = list(s7["escalation_levels"])
    level = np.where(esc, rr.choice(lv, m, p=np.array(list(s7["escalation_levels"].values()))), "none")
    reopen = ~is_open & (rr.random(m) < special.expit(s7["reopen_intercept"] + s7["reopen_service_slope"] * zs_eff))
    comp = pd.DataFrame({"hh": hh, "category": cat, "source": src, "open_day": open_day,
                         "close_day": np.where(is_open, np.nan, close_day), "status": np.where(is_open, "open", "closed"),
                         "sla_days": sla, "out_of_sla": out_sla, "escalation_level": level, "reopened": reopen})
    comp = comp[comp["open_day"] > -H].sort_values(["hh", "open_day"], kind="stable").reset_index(drop=True)

    # --- Assistant ---------------------------------------------------------------------
    ra = seeds.rng("s7.assistant")
    pilot = ra.random(n) < s7["assistant_pilot_p"]
    moving = exit_ev["move"].to_numpy()
    p_d = special.expit(s7["dissatisfaction_intercept"] + s7["dissatisfaction_service_slope"] * z_s
                        + s7["dissatisfaction_neglect_slope"] * z_n + s7["dissatisfaction_move_add"] * moving)
    dissat = ra.random(n) < p_d
    talked = ra.random(n) < s7["assistant_usage_30d_p"]
    detect = talked & np.where(dissat, ra.random(n) < s7["classifier_tpr"], ra.random(n) < s7["classifier_fpr"])
    confirm = detect & np.where(dissat, ra.random(n) < s7["human_confirm_tp"], ra.random(n) < s7["human_confirm_fp"])
    ev = pd.DataFrame({"household_id": base["household_id"].to_numpy(), "assistant_pilot": pilot, "p_dissatisfied": p_d,
                       "dissatisfied_true": dissat, "talked_30d": talked, "classifier_flag": detect,
                       "human_confirmed": confirm, "acats_complaint": ac})
    return {"complaints": comp, "events": ev}


def compute_variables(sim7, base, cfg) -> pd.DataFrame:
    n = len(base)
    c, ev = sim7["complaints"], sim7["events"]
    out = pd.DataFrame({"household_id": base["household_id"].to_numpy()})
    esc = c[c["escalation_level"] != "none"].groupby("hh").size().reindex(range(n), fill_value=0).to_numpy()
    out["complaint_escalated_flag"] = (esc > 0).astype(int)
    op = c[c["status"] == "open"]
    oldest = op.groupby("hh")["open_day"].min().reindex(range(n))
    out["open_complaint_flag"] = oldest.notna().astype(int).to_numpy()
    out["complaint_age_days"] = np.where(oldest.notna(), -oldest.fillna(0), 0).astype(int)
    out["complaint_out_of_sla_flag"] = op.groupby("hh")["out_of_sla"].any().reindex(range(n), fill_value=False).astype(int).to_numpy()
    same_cat = c.groupby(["hh", "category"]).size().groupby(level=0).max().reindex(range(n), fill_value=0).to_numpy()
    reop = c.groupby("hh")["reopened"].any().reindex(range(n), fill_value=False).to_numpy()
    out["repeat_complaint_flag"] = ((same_cat >= 2) | reop).astype(int)
    out["complaints_12m"] = c.groupby("hh").size().reindex(range(n), fill_value=0).to_numpy()
    out["relationship_dissatisfaction_flag"] = pd.array(np.where(ev["assistant_pilot"], ev["human_confirmed"].astype(int), pd.NA),
                                                        dtype="Int8")
    return out


def build_step7(base, truth, cfg, seeds, exit_ev):
    sim7 = simulate_complaints(base, truth, cfg, seeds, exit_ev)
    return compute_variables(sim7, base, cfg), sim7
