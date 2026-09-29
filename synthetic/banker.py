"""Paso 6 · Banker (variables 11, 12, 13, 35).

* Carteras: libros de ~60 hogares HNW / ~25 UHNW armados por calidad (índice de riesgo + ruido).
  La salida del banker se decide POR BANKER y es más probable en libros deteriorados; todo el libro
  cambia de banker. Otros cambios: pedido del cliente (z_service), rebalanceo (ruido); la cobertura
  temporal (< 30 días) se excluye.
* Bitácora de 12 meses: contactos del banker (llamada / email / mensaje) a una tasa que depende de la
  cadencia, la diligencia del banker y z_neglect; respuestas del cliente (z_neglect; quien se está
  mudando deja de contestar); llamada de bienvenida tras un cambio; envíos masivos (excluidos);
  reuniones y cancelaciones del cliente ("cancelado por" solo lo registra una parte de los bankers).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import special

from .seeds import SeedManager

H = 365


def simulate_banker(base, truth, cfg, seeds: SeedManager, exit_ev) -> dict:
    s6 = cfg["step6"]
    n = len(base)
    seg = base["segment"].to_numpy()
    risk = truth["risk_index"].to_numpy()
    z_neg, z_srv = truth["z_neglect"].to_numpy(), truth["z_service"].to_numpy()

    # --- Carteras ---------------------------------------------------------------------
    key = risk + s6["book_sort_noise"] * seeds.rng("s6.book_sort").standard_normal(n)
    banker = np.empty(n, int)
    next_id = 0
    for sg, size in s6["book_size"].items():
        idx = np.nonzero(seg == sg)[0]
        order = idx[np.argsort(key[idx])]
        k = max(1, int(round(len(idx) / size)))
        for chunk in np.array_split(order, k):
            banker[chunk] = next_id
            next_id += 1
    nb = next_id
    book_risk = pd.Series(risk).groupby(banker).mean().reindex(range(nb)).to_numpy()
    book_z = (book_risk - book_risk.mean()) / book_risk.std()
    p_dep = special.expit(s6["departure_intercept"] + s6["departure_slope"] * book_z)
    departs = seeds.rng("s6.departure").random(nb) < p_dep
    dep_day = np.floor(seeds.rng("s6.departure_day").uniform(-180, 0, nb))
    diligence = np.exp(s6["banker_diligence_sigma"] * seeds.rng("s6.diligence").standard_normal(nb))

    # --- Cambios de banker del hogar ------------------------------------------------------------
    p_req = special.expit(s6["client_request_intercept"] + s6["client_request_slope"] * z_srv)
    req = seeds.rng("s6.client_request").random(n) < p_req
    req_day = np.floor(seeds.rng("s6.client_request_day").uniform(-180, 0, n))
    reb = seeds.rng("s6.rebalance").random(n) < s6["rebalance_p_6m"]
    reb_day = np.floor(seeds.rng("s6.rebalance_day").uniform(-180, 0, n))
    tmp = seeds.rng("s6.temporary").random(n) < s6["temporary_coverage_p_6m"]
    dep_hh = departs[banker]
    change_day = np.full(n, np.nan)
    reason = np.full(n, None, dtype=object)
    for mask, day, why in [(dep_hh, dep_day[banker], "banker_departure"), (req, req_day, "client_request"),
                           (reb, reb_day, "book_rebalancing")]:
        new = mask & np.isnan(change_day)
        change_day[new] = day[new]
        reason[new] = why

    # --- Bitácora de interacción ----------------------------------------------------------------
    cad = pd.Series(seg).map(s6["cadence_days"]).to_numpy().astype(float)
    lam = s6["outreach_per_cadence"] / cad * diligence[banker] * np.exp(-s6["contact_neglect_loading"] * z_neg)
    r = seeds.rng("s6.outreach")
    cnt = r.poisson(lam * H)
    hh = np.repeat(np.arange(n), cnt)
    day = np.floor(r.uniform(-H, 0, len(hh))) + 1
    ch = list(s6["channel_mix"])
    channel = r.choice(ch, len(hh), p=np.array(list(s6["channel_mix"].values())))
    move_day = exit_ev["move_day"].to_numpy()
    moving = exit_ev["move"].to_numpy()
    p_rep = special.expit(s6["reply_intercept"] - s6["reply_neglect_slope"] * z_neg)
    after_move = moving[hh] & (day > move_day[hh])
    p_i = p_rep[hh] * np.where(after_move, s6["reply_after_move_factor"], 1.0)
    replied = r.random(len(hh)) < p_i
    reply_lag = np.floor(r.uniform(0, 10, len(hh)))
    reply_ok = replied & (reply_lag <= 7) & (day + reply_lag <= 0)
    minutes = np.where((channel == "call") & replied, r.lognormal(np.log(s6["call_minutes_median"]), s6["call_minutes_sigma"], len(hh)), 0.0)
    log = pd.DataFrame({"hh": hh, "day": day, "kind": channel, "replied_7d": reply_ok, "minutes": minutes.round(1)})
    # Llamada de bienvenida tras un cambio de banker.
    w = seeds.rng("s6.welcome")
    wel = ~np.isnan(change_day) & (w.random(n) < s6["welcome_call_p"])
    wday = change_day + np.floor(w.uniform(0, 14, n))
    wi = np.nonzero(wel & (wday <= 0))[0]
    log = pd.concat([log, pd.DataFrame({"hh": wi, "day": wday[wi], "kind": "call", "replied_7d": True,
                                        "minutes": np.round(w.lognormal(np.log(20), 0.4, len(wi)), 1)})])
    # Envíos masivos (excluidos).
    mm = seeds.rng("s6.mass")
    cnt_m = mm.poisson(s6["mass_mailings_per_90d"] * H / 90, n)
    hm = np.repeat(np.arange(n), cnt_m)
    log = pd.concat([log, pd.DataFrame({"hh": hm, "day": np.floor(mm.uniform(-H, 0, len(hm))) + 1, "kind": "mass_mailing",
                                        "replied_7d": False, "minutes": 0.0})])
    # Reuniones y cancelaciones del cliente.
    rm = seeds.rng("s6.meetings")
    mt = pd.Series(seg).map(s6["meetings_per_6m"]).to_numpy() * 2
    cnt_mt = rm.poisson(mt * diligence[banker])
    hmt = np.repeat(np.arange(n), cnt_mt)
    dmt = np.floor(rm.uniform(-H, 0, len(hmt))) + 1
    lg = s6["cancel_intercept"] + s6["cancel_neglect_slope"] * z_neg[hmt] + \
        np.where(moving[hmt] & (dmt > move_day[hmt]), s6["cancel_after_move_add"], 0.0)
    cancelled = rm.random(len(hmt)) < special.expit(lg)
    log = pd.concat([log, pd.DataFrame({"hh": hmt, "day": dmt, "kind": np.where(cancelled, "meeting_cancelled_by_client", "meeting"),
                                        "replied_7d": ~cancelled, "minutes": np.where(cancelled, 0.0, 45.0)})], ignore_index=True)
    captured = seeds.rng("s6.cancelled_by_captured").random(nb) < s6["cancelled_by_captured_p"]

    ev = pd.DataFrame({"household_id": base["household_id"].to_numpy(), "banker_id": banker, "book_risk_z": book_z[banker],
                       "banker_departed": dep_hh, "client_request": req, "book_rebalancing": reb,
                       "temporary_coverage": tmp, "change_day": change_day, "change_reason": reason,
                       "cadence_days": cad, "p_reply": p_rep, "cancelled_by_captured": captured[banker],
                       "welcome_call": wel & (wday <= 0)})
    return {"log": log.sort_values(["hh", "day"], kind="stable").reset_index(drop=True), "events": ev,
            "bankers": pd.DataFrame({"banker_id": range(nb), "book_risk_z": book_z, "p_departure": p_dep,
                                     "departed": departs, "departure_day": np.where(departs, dep_day, np.nan),
                                     "diligence": diligence, "cancelled_by_captured": captured})}


def compute_variables(sim6, base, cfg) -> pd.DataFrame:
    n = len(base)
    log, ev = sim6["log"], sim6["events"]
    hist = base["history_months"].to_numpy()
    out = pd.DataFrame({"household_id": base["household_id"].to_numpy()})
    changed = ev["change_day"].notna().to_numpy()
    out["banker_change_6m_flag"] = pd.array(np.where(hist >= 6, changed.astype(int), pd.NA), dtype="Int8")
    out["banker_change_reason"] = np.where(changed, ev["change_reason"], None)

    meaningful = (((log["kind"] == "call") & (log["minutes"] >= 5)) | log["kind"].isin(["meeting"]) |
                  (log["kind"].isin(["email", "message"]) & log["replied_7d"]))
    last = log[meaningful].groupby("hh")["day"].max().reindex(range(n))
    days_since = np.where(last.notna(), -last.fillna(0), H)  # sin contacto en 12 meses → 365 (censurado)
    out["days_since_meaningful_contact"] = days_since
    out["contact_gap_ratio"] = days_since / ev["cadence_days"].to_numpy()

    o90 = log[(log["day"] > -90) & log["kind"].isin(["call", "email", "message"])]
    tot = o90.groupby("hh").size().reindex(range(n), fill_value=0).to_numpy()
    rep = o90.groupby("hh")["replied_7d"].sum().reindex(range(n), fill_value=0).to_numpy()
    out["client_reply_rate"] = np.where(tot >= 3, rep / np.maximum(tot, 1), np.nan)

    m6 = log[(log["day"] > -180) & log["kind"].isin(["meeting", "meeting_cancelled_by_client"])]
    sched = m6.groupby("hh").size().reindex(range(n), fill_value=0).to_numpy()
    canc = (m6["kind"] == "meeting_cancelled_by_client").groupby(m6["hh"]).sum().reindex(range(n), fill_value=0).to_numpy()
    cap = ev["cancelled_by_captured"].to_numpy()
    out["meetings_cancelled_by_client"] = pd.array(np.where(cap, canc, pd.NA), dtype="Int16")
    out["meetings_cancelled_pct"] = np.where(cap & (sched > 0), canc / np.maximum(sched, 1), np.nan)
    return out


def build_step6(base, truth, cfg, seeds, exit_ev):
    sim6 = simulate_banker(base, truth, cfg, seeds, exit_ev)
    return compute_variables(sim6, base, cfg), sim6
