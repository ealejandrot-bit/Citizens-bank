"""Paso 5 · Relationship & closures (variables 10, 29, 30, 31, 32).

* Tabla de cuentas por hogar (productos derivados de las banderas del Paso 0 + depósitos y tarjeta).
* Cierres con motivo y fecha:
    - SEÑAL propensión: quien se muda cierra productos 0–90 días después de la mudanza;
    - SEÑAL factor: un episodio de salida del Paso 1 cierra ahorro / money market;
    - RUIDO que cuenta: CD que vence sin renovar, cierre ocasional;
    - RUIDO excluido por el Excel: CD renovado, préstamo pagado a término, conversión, consolidación interna.
* Share of wallet: patrimonio total verdadero estable (SOW de hace 6 meses ligado a z_outflow), estimado
  con una fuente de calidad distinta; el valor en Citizens sale de las series del Paso 1.
* Cambio de trustee: mudanza, servicio (z_service) y ruido; la sucesión por muerte es exclusión.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import special

from .seeds import SeedManager

EXCLUDED_PRODUCT_REASONS = {"cd_renewed", "loan_paid_at_term", "conversion", "consolidation"}
EXCLUDED_ACCOUNT_REASONS = {"cd_renewed", "consolidation"}  # Excel #29: solo consolidaciones (el CD renovado no cierra)


def build_accounts(base, cfg, seeds: SeedManager) -> pd.DataFrame:
    s5 = cfg["step5"]
    n = len(base)
    held = {
        "checking": np.ones(n, bool),
        "savings": seeds.rng("s5.has_savings").random(n) < s5["p_savings"],
        "money_market": seeds.rng("s5.has_mm").random(n) < s5["p_money_market"],
        "cd": seeds.rng("s5.has_cd").random(n) < s5["p_cd"],
        "brokerage": base["has_investments"].to_numpy(),
        "advisory": base["has_advisory"].to_numpy(),
        "trust": base["has_trust"].to_numpy(),
        "credit_card": seeds.rng("s5.has_card").random(n) < s5["p_credit_card"],
        "business_account": base["has_linked_business"].to_numpy(),
    }
    credit = base["has_credit_anchor"].to_numpy()
    is_mort = seeds.rng("s5.mortgage_vs_line").random(n) < 0.6
    held["mortgage"], held["credit_line"] = credit & is_mort, credit & ~is_mort
    lam = np.where(base["segment"].to_numpy() == "UHNW", s5["extra_accounts_poisson"]["UHNW"],
                   s5["extra_accounts_poisson"]["HNW"])
    frames = []
    for prod, h in held.items():
        k = np.where(h, 1 + (seeds.rng(f"s5.extra_{prod}").poisson(lam) if prod not in ("mortgage", "credit_line", "trust") else 0), 0)
        hh = np.repeat(np.arange(n), k)
        frames.append(pd.DataFrame({"hh": hh, "product": prod}))
    acc = pd.concat(frames, ignore_index=True)
    acc["account_n"] = acc.groupby(["hh", "product"]).cumcount()
    acc["close_day"] = np.nan
    acc["close_reason"] = None
    return acc.reset_index(drop=True)


def simulate_relationship(base, truth, cfg, seeds: SeedManager, exit_ev, sim1) -> dict:
    s5 = cfg["step5"]
    n, M = len(base), cfg["step1"]["months"]
    acc = build_accounts(base, cfg, seeds)
    hh, prod = acc["hh"].to_numpy(), acc["product"].to_numpy()

    draws = {}

    def close(mask, day, reason):
        # Se guarda el sorteo (antes de censurar por cierres previos) para probar independencia.
        draws[reason] = draws.get(reason, np.zeros(n)) + np.bincount(hh[mask], minlength=n)
        free = mask & acc["close_day"].isna().to_numpy()
        acc.loc[free, "close_day"] = np.asarray(day)[free] if np.ndim(day) else day
        acc.loc[free, "close_reason"] = reason

    # --- Mudanza: cierre de productos (todas las cuentas del producto) ------------------
    move = exit_ev["move"].to_numpy()
    lag = np.floor(seeds.rng("s5.move_lag").uniform(*s5["move_close_lag_days"], n))
    mday = exit_ev["move_day"].fillna(0).to_numpy() + lag
    u = seeds.rng("s5.move_close").random((n, len(s5["move_close_p"])))
    for k, (p_name, p) in enumerate(s5["move_close_p"].items()):
        sel = move[hh] & (prod == p_name) & (u[hh, k] < p) & (mday[hh] <= 0)
        close(sel, mday[hh], "moved_relationship")
    # --- Episodio del Paso 1: cierra ahorro / money market ------------------------------
    t1 = sim1["truth"]
    ep = t1["s1_episode"].to_numpy() & (seeds.rng("s5.episode_close").random(n) < s5["episode_close_p"])
    ep_day = np.floor(-30.44 * t1["s1_episode_len"].to_numpy() * seeds.rng("s5.episode_close_day").random(n))
    close(ep[hh] & np.isin(prod, ["savings", "money_market"]) & (acc["account_n"].to_numpy() == 0), ep_day[hh], "client_request")
    # --- Ruido que cuenta (tasas por 90 días, simuladas sobre 180 días para no sesgar la ventana larga) ---
    r = seeds.rng("s5.noise")
    H = 180
    k90 = H / 90

    def when():
        return np.floor(r.uniform(-H, 0, len(acc)))

    cd_event = r.random(len(acc)) < s5["cd_maturity_p_90d"] * k90
    cd_day = when()
    renewed = r.random(len(acc)) < s5["cd_renewed_p"]
    close((prod == "cd") & cd_event & renewed, cd_day, "cd_renewed")
    close((prod == "cd") & cd_event & ~renewed, cd_day, "cd_matured_not_renewed")
    rnd = r.random(len(acc)) < s5["random_close_p_90d"] * k90 / np.maximum(acc.groupby("hh")["hh"].transform("size").to_numpy(), 1)
    close(rnd & ~np.isin(prod, ["mortgage", "credit_line", "trust"]), when(), "client_request")
    # --- Ruido excluido por el Excel -----------------------------------------------------------
    close(np.isin(prod, ["mortgage", "credit_line"]) & (r.random(len(acc)) < s5["loan_paid_at_term_p_90d"] * k90),
          when(), "loan_paid_at_term")
    close(np.isin(prod, ["checking", "savings", "money_market", "brokerage"]) & (r.random(len(acc)) < s5["conversion_p_90d"] * k90),
          when(), "conversion")
    multi = acc.groupby(["hh", "product"])["account_n"].transform("max").to_numpy() >= 1
    close(multi & (acc["account_n"].to_numpy() >= 1) & (r.random(len(acc)) < s5["consolidation_p_90d"] * k90),
          when(), "consolidation")

    # --- Share of wallet --------------------------------------------------------------------
    V_t = base["relationship_value"].to_numpy()
    hist = base["history_months"].to_numpy()
    V_6 = np.where(hist >= 7, sim1["deposit"][:, M - 7] + np.where(sim1["inv"], sim1["aum"][:, M - 7], 0.0), V_t)
    z_out = truth["z_outflow"].to_numpy()
    s0 = special.expit(s5["sow_logit_intercept"] - s5["sow_logit_zout"] * z_out
                       + s5["sow_logit_noise"] * seeds.rng("s5.sow_noise").standard_normal(n))
    W = V_6 / s0
    src = seeds.rng("s5.wealth_source").choice(list(s5["wealth_sources"]), n,
                                               p=np.array(list(s5["wealth_sources"].values())))
    sig = pd.Series(src).map(s5["wealth_noise_sigma"]).to_numpy()
    W_old = W * np.exp(sig * seeds.rng("s5.wealth_err_old").standard_normal(n))
    upd = seeds.rng("s5.wealth_updated").random(n) < s5["estimate_updated_6m_p"]
    W_new = np.where(upd, W * np.exp(sig * seeds.rng("s5.wealth_err_new").standard_normal(n)), W_old)

    # --- Trustee ------------------------------------------------------------------------------
    has_tr = base["has_trust"].to_numpy()
    tr_move = has_tr & move & (seeds.rng("s5.trustee_move").random(n) < s5["trustee_move_p"])
    p_srv = special.expit(s5["trustee_service_intercept"] + s5["trustee_service_slope"] * truth["z_service"].to_numpy())
    tr_srv = has_tr & (seeds.rng("s5.trustee_service").random(n) < p_srv)
    tr_noise = has_tr & (seeds.rng("s5.trustee_noise").random(n) < s5["trustee_noise_p_12m"])
    tr_death = has_tr & (base["churn_excluded"].to_numpy() |
                         (seeds.rng("s5.trustee_death").random(n) < s5["trustee_death_succession_p_12m"]))
    ev = pd.DataFrame({"household_id": base["household_id"].to_numpy(), "sow_true_6m_ago": s0,
                       "total_wealth_true": W, "wealth_estimate_source": src, "wealth_estimate_updated": upd,
                       "trustee_move": tr_move, "trustee_service": tr_srv, "trustee_noise": tr_noise,
                       "trustee_death_succession": tr_death, "p_trustee_service": p_srv})
    return {"accounts": acc, "events": ev, "draws": draws, "V_t": V_t, "V_6": V_6, "W_old": W_old, "W_new": W_new}


def compute_variables(sim5, base, cfg) -> pd.DataFrame:
    n = len(base)
    acc, ev = sim5["accounts"], sim5["events"]
    hist = base["history_months"].to_numpy()
    out = pd.DataFrame({"household_id": base["household_id"].to_numpy()})
    for W, lab in [(90, "90d"), (180, "180d")]:
        c = acc[acc["close_day"] > -W]
        prods = c[~c["close_reason"].isin(EXCLUDED_PRODUCT_REASONS)].groupby("hh")["product"].nunique()
        accs = c[~c["close_reason"].isin(EXCLUDED_ACCOUNT_REASONS)].groupby("hh").size()
        ok = hist >= W // 30
        out[f"products_closed_{lab}"] = pd.array(np.where(ok, prods.reindex(range(n), fill_value=0), pd.NA), dtype="Int16")
        out[f"accounts_closed_{lab}"] = pd.array(np.where(ok, accs.reindex(range(n), fill_value=0), pd.NA), dtype="Int16")
    sow_t = np.minimum(1.0, sim5["V_t"] / sim5["W_new"])
    sow_6 = np.minimum(1.0, sim5["V_6"] / sim5["W_old"])
    out["share_of_wallet"] = sow_t
    out["wealth_estimate_source"] = ev["wealth_estimate_source"].to_numpy()
    out["share_of_wallet_change"] = np.where(hist >= 7, sow_t - sow_6, np.nan)
    flag = (ev["trustee_move"] | ev["trustee_service"] | ev["trustee_noise"]).to_numpy()
    # Sucesión por muerte: exclusión (flag 0) salvo que además haya otro cambio.
    out["trustee_change_flag"] = pd.array(np.where(base["has_trust"].to_numpy(), flag.astype(int), pd.NA), dtype="Int8")
    return out


def build_step5(base, truth, cfg, seeds, exit_ev, sim1):
    sim5 = simulate_relationship(base, truth, cfg, seeds, exit_ev, sim1)
    return compute_variables(sim5, base, cfg), sim5
