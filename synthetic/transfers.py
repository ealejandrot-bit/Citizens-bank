"""Paso 3 · Transfers (variables 7, 8, 21, 22, 23, 24, 25).

Transferencias externas simuladas una por una (18 meses), coherentes con los pasos previos:
  * SALIDAS con origen en eventos ya simulados, con el monto exacto que movió la serie del Paso 1:
    - mudanza del banco principal (evento común): traslado de depósitos a un banco competidor
      nuevo y ACATS del AUM a un broker (o al brazo wealth del banco nuevo);
    - episodios de salida del Paso 1 (z_outflow): envíos mensuales a un banco competidor, un broker
      o un destino habitual; la parte de AUM sale por ACATS;
    - choques de liquidez del Paso 1: compra de casa (title/escrow) o pago al IRS (excluido);
  * SALIDAS de fondo a destinos habituales y destinos nuevos esporádicos (ruido);
  * PAGOS EXCLUIDOS por el Excel: billers, IRS estimado trimestral, donaciones recurrentes,
    préstamos con Citizens;
  * ENTRADAS externas: cierran la identidad contable mensual del saldo del Paso 1
        ΔD_m = ingresos recurrentes (Paso 2) + entradas externas − salidas desde depósitos − tarjeta.

Convención de meses (igual que las ventanas del Excel): el mes m ≤ 0 cubre los días
(30.44·(m−1), 30.44·m]; el mes 0 son los últimos 30 días.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .seeds import SeedManager

AVG_MONTH = 30.44
CATS = ["background", "one_off", "real_estate", "episode_deposit", "episode_acats", "move_deposit", "move_acats",
        "shock_aum", "incoming", "biller", "irs_tax", "donation", "loan_citizens", "irs_shock", "irs_shock_aum"]
EXTERNAL_OUT = {"background", "one_off", "real_estate", "episode_deposit", "episode_acats", "move_deposit",
                "move_acats", "shock_aum"}
EXCLUDED = {"biller", "irs_tax", "donation", "loan_citizens", "irs_shock", "irs_shock_aum"}
ACATS = {"episode_acats", "move_acats", "shock_aum"}  # salen de cuentas de inversión
FROM_DEPOSITS = {"background", "one_off", "real_estate", "episode_deposit", "move_deposit", "biller", "irs_tax",
                 "donation", "loan_citizens", "irs_shock"}


def month_of(day: np.ndarray) -> np.ndarray:
    return np.ceil(np.asarray(day, dtype=float) / AVG_MONTH).astype(int)


def aba_checksum(d8: np.ndarray) -> np.ndarray:
    """Dígito verificador ABA: 3·(d1+d4+d7) + 7·(d2+d5+d8) + (d3+d6) ≡ 0 (mod 10)."""
    w = np.array([3, 7, 1, 3, 7, 1, 3, 7])
    return (10 - (d8 @ w) % 10) % 10


def build_catalog(cfg: dict, seeds: SeedManager) -> tuple[pd.DataFrame, pd.DataFrame]:
    s3 = cfg["step3"]
    rng = seeds.rng("s3.catalog")
    rows = []
    for typ, k in s3["institutions"].items():
        for i in range(k):
            rows.append({"inst_type": typ, "inst_name": f"{typ.replace('_', ' ').title()} {i + 1:02d} (sintética)"})
    inst = pd.DataFrame(rows)
    inst.insert(0, "inst_id", np.arange(len(inst)))
    inst["competitor_bank"] = inst["inst_type"].isin(s3["competitor_types"])
    inst["broker_wealth"] = inst["inst_type"] == "broker_wealth"
    lo, hi = s3["aba_per_institution"]
    k_aba = rng.integers(lo, hi + 1, len(inst))
    inst_ids = np.repeat(inst["inst_id"].to_numpy(), k_aba)
    prefix = rng.choice(np.r_[1:13, 21:33], len(inst_ids))
    body = rng.integers(0, 10, (len(inst_ids), 6))
    d8 = np.column_stack([prefix // 10, prefix % 10, body])
    aba = np.array(["".join(map(str, r)) + str(c) for r, c in zip(d8, aba_checksum(d8))])
    abas = pd.DataFrame({"aba": aba, "inst_id": inst_ids}).drop_duplicates("aba").reset_index(drop=True)
    return inst, abas


class TxBuilder:
    def __init__(self):
        self.parts = []

    def add(self, hh, day, amount, cat, inst, dest):
        hh = np.asarray(hh)
        if len(hh) == 0:
            return
        self.parts.append(pd.DataFrame({"hh": hh, "day": np.asarray(day, float), "amount": np.asarray(amount, float),
                                        "category": cat, "inst_id": np.asarray(inst), "dest_id": np.asarray(dest)}))

    def frame(self) -> pd.DataFrame:
        return pd.concat(self.parts, ignore_index=True)


def simulate_transfers(base, truth, cfg, seeds: SeedManager, exit_ev, sim1, sim2) -> dict:
    s3 = cfg["step3"]
    n, H = len(base), s3["history_days"]
    M = cfg["step1"]["months"]
    D, A = sim1["deposit"], sim1["aum"]
    inst, abas = build_catalog(cfg, seeds)
    by_type = {t: g["inst_id"].to_numpy() for t, g in inst.groupby("inst_type")}
    open_day = np.where(base["history_months"].to_numpy() >= cfg["population"]["history_months_cap"], -H,
                        np.maximum(-H, -np.floor(base["history_months"].to_numpy() * AVG_MONTH)))
    active_months = -open_day / AVG_MONTH
    tx = TxBuilder()
    next_dest = [0]

    def new_dest(k):
        ids = np.arange(next_dest[0], next_dest[0] + k)
        next_dest[0] += k
        return ids

    def pick_inst(types_w: dict, k: int, rng) -> np.ndarray:
        t = rng.choice(list(types_w), k, p=np.array(list(types_w.values())) / sum(types_w.values()))
        out = np.empty(k, int)
        for typ in np.unique(t):
            m = t == typ
            out[m] = rng.choice(by_type[typ], m.sum())
        return out

    def day_in_month(m, rng):
        return np.floor(AVG_MONTH * (m - 1) + rng.uniform(0, 1, len(m)) * AVG_MONTH) + 1

    def dep_at(i, m):
        return D[i, M - 1 + m]

    # --- Destinos habituales ------------------------------------------------------
    rng = seeds.rng("s3.payees")
    K = np.minimum(1 + rng.poisson(s3["regular_payees_poisson"], n), 6)
    payee_inst = pick_inst(s3["regular_payee_types"], n * 6, rng).reshape(n, 6)
    payee_dest = new_dest(n * 6).reshape(n, 6)

    # --- Fondo: salidas a destinos habituales --------------------------------------
    rng = seeds.rng("s3.background")
    share = rng.lognormal(np.log(s3["background_monthly_share_median"]), s3["background_monthly_share_sigma"], n)
    cnt = rng.poisson(s3["background_transfers_per_month"] * active_months)
    hh = np.repeat(np.arange(n), cnt)
    day = np.floor(rng.uniform(open_day[hh], 0)) + 1
    day = np.minimum(day, 0)
    slot = np.floor(rng.uniform(0, 1, len(hh)) * K[hh]).astype(int)
    amt = share[hh] * dep_at(hh, month_of(day)) / s3["background_transfers_per_month"] * \
        rng.lognormal(0, s3["background_amount_sigma"], len(hh))
    tx.add(hh, day, amt, "background", payee_inst[hh, slot], payee_dest[hh, slot])

    # --- Ruido: destinos nuevos esporádicos -----------------------------------------
    rng = seeds.rng("s3.one_off")
    cnt = rng.poisson(s3["one_off_p_month"] * active_months)
    hh = np.repeat(np.arange(n), cnt)
    day = np.minimum(np.floor(rng.uniform(open_day[hh], 0)) + 1, 0)
    tx.add(hh, day, rng.lognormal(np.log(s3["one_off_amount_median"]), s3["one_off_amount_sigma"], len(hh)),
           "one_off", pick_inst(s3["one_off_types"], len(hh), rng), new_dest(len(hh)))

    # --- Choques de liquidez del Paso 1 ---------------------------------------------
    t1 = sim1["truth"]
    rng = seeds.rng("s3.shock")
    i = np.nonzero(t1["s1_shock"].to_numpy())[0]
    m = t1["s1_shock_month"].to_numpy()[i].astype(int)
    size = t1["s1_shock_size"].to_numpy()[i]
    real_estate = rng.random(len(i)) < s3["shock_real_estate_p"]
    day = day_in_month(m, rng)
    amt = dep_at(i, m) * size / (1 - size)  # exactamente lo que cayó el saldo ese mes
    tx.add(i[real_estate], day[real_estate], amt[real_estate], "real_estate",
           rng.choice(by_type["title_escrow"], real_estate.sum()), new_dest(real_estate.sum()))
    tx.add(i[~real_estate], day[~real_estate], amt[~real_estate], "irs_shock", -1, -1)
    # Parte del choque que salió de inversiones (en el Paso 1: retiro de size × AUM del mes previo).
    sa = sim1["shock_aum"][i]
    a_amt = A[i, M - 2 + m] * size
    for cat_mask, cat in [(sa & real_estate, "shock_aum"), (sa & ~real_estate, "irs_shock_aum")]:
        inst_ids = rng.choice(by_type["title_escrow"], cat_mask.sum()) if cat == "shock_aum" else -1
        dest_ids = new_dest(cat_mask.sum()) if cat == "shock_aum" else -1
        tx.add(i[cat_mask], day[cat_mask], a_amt[cat_mask], cat, inst_ids, dest_ids)

    # --- Episodios del Paso 1 --------------------------------------------------------
    rng = seeds.rng("s3.episode")
    ep = t1["s1_episode"].to_numpy()
    L = t1["s1_episode_len"].to_numpy()
    delta = t1["s1_episode_delta"].to_numpy()
    k_dep, k_aum = sim1["episode_k_dep"], sim1["episode_k_aum"]
    ed = s3["episode_destination"]
    choice = rng.choice(list(ed), n, p=np.array(list(ed.values())) / sum(ed.values()))
    spend = choice == "spending"
    ep_inst = np.where(choice == "competitor_bank", rng.choice(np.concatenate([by_type[t] for t in s3["competitor_types"]]), n),
                       np.where(choice == "broker", rng.choice(by_type["broker_wealth"], n), payee_inst[:, 0]))
    ep_dest = np.where(choice == "existing_payee", payee_dest[:, 0], new_dest(n))
    for mm in range(-5, 1):
        i = np.nonzero(ep & ~spend & (L >= 1 - mm))[0]  # meses −(L−1)..0; el gasto no es transferencia
        if len(i) == 0:
            continue
        mv = np.full(len(i), mm)
        dday = day_in_month(mv, rng)
        tx.add(i, dday, dep_at(i, mv) * (np.exp(delta[i] * k_dep[i]) - 1), "episode_deposit", ep_inst[i], ep_dest[i])
        inv_i = sim1["inv"][i]
        j = M - 1 + mm
        tx.add(i[inv_i], dday[inv_i], A[i[inv_i], j - 1] * (1 - np.exp(-delta[i[inv_i]] * k_aum[i[inv_i]])),
               "episode_acats", ep_inst[i[inv_i]], ep_dest[i[inv_i]])

    # --- Mudanza del banco principal (evento común) ----------------------------------
    rng = seeds.rng("s3.move")
    i = np.nonzero(exit_ev["deposit_transfer"].to_numpy())[0]
    comp = np.concatenate([by_type[t] for t in s3["competitor_types"]])
    new_bank = rng.choice(comp, n)
    new_bank_dest = new_dest(n)
    mday = exit_ev["move_day"].to_numpy()[i]
    sh = exit_ev["deposit_transfer_share"].to_numpy()[i]
    k = exit_ev["deposit_tranches"].to_numpy()[i]
    m0 = exit_ev["move_month"].to_numpy()[i]
    s_t = 1 - (1 - sh) ** (1 / k)  # fracción por tramo (igual que en el Paso 1)
    for t in range(int(k.max())):
        m_t = k > t
        mm = m0[m_t] + t
        dday = mday[m_t] if t == 0 else day_in_month(mm, rng)
        tx.add(i[m_t], dday, dep_at(i[m_t], mm) * s_t[m_t] / (1 - s_t[m_t]), "move_deposit",
               new_bank[i[m_t]], new_bank_dest[i[m_t]])
    i = np.nonzero(exit_ev["aum_transfer"].to_numpy())[0]
    aday = exit_ev["acats_day"].to_numpy()[i]
    ja = M - 1 + month_of(aday)
    to_broker = rng.random(len(i)) < s3["acats_to_broker_p"]
    tx.add(i, aday, A[i, ja - 1] * exit_ev["aum_transfer_share"].to_numpy()[i], "move_acats",
           np.where(to_broker, rng.choice(by_type["broker_wealth"], len(i)), new_bank[i]),
           np.where(to_broker, new_dest(len(i)), new_bank_dest[i]))

    # --- Pagos excluidos por el Excel ------------------------------------------------
    rng = seeds.rng("s3.excluded")
    cnt = rng.poisson(s3["billers_per_month"] * active_months)
    hh = np.repeat(np.arange(n), cnt)
    tx.add(hh, np.minimum(np.floor(rng.uniform(open_day[hh], 0)) + 1, 0),
           rng.lognormal(np.log(s3["biller_amount_median"]), s3["biller_amount_sigma"], len(hh)), "biller", -1, -1)
    annual_income = base["recurring_income_monthly"].to_numpy() * 12 + base["bonus_annual"].fillna(0).to_numpy()
    t0 = pd.Timestamp(cfg["snapshot_date"])
    for due in pd.to_datetime([f"{y}-{md}" for y in (t0.year - 1, t0.year) for md in ("01-15", "04-15", "06-15", "09-15")]):
        d = (due - t0).days
        if -H < d <= 0:
            hh = np.nonzero((open_day < d) & (annual_income > 0))[0]
            tx.add(hh, d, annual_income[hh] * s3["estimated_tax_rate"] / 4, "irs_tax", -1, -1)
    don = rng.random(n) < s3["donation_p"]
    don_amt = rng.lognormal(np.log(s3["donation_monthly_median"]), 0.6, n)
    loan_amt = rng.lognormal(np.log(s3["loan_payment_median"]), 0.6, n)
    for mm in range(month_of(-H + 1), 1):
        hh = np.nonzero(don & (open_day < AVG_MONTH * (mm - 1)))[0]
        tx.add(hh, np.full(len(hh), np.floor(AVG_MONTH * (mm - 1)) + 5), don_amt[hh], "donation", -1, -1)
        hh = np.nonzero(base["has_credit_anchor"].to_numpy() & (open_day < AVG_MONTH * (mm - 1)))[0]
        tx.add(hh, np.full(len(hh), np.floor(AVG_MONTH * (mm - 1)) + 1), loan_amt[hh], "loan_citizens", -1, -1)

    out_tx = tx.frame()
    out_tx = out_tx[(out_tx["day"] > -H) & (out_tx["day"] <= 0) & (out_tx["day"] >= open_day[out_tx["hh"]])]

    # --- Entradas externas: cierran la identidad del saldo mes a mes -------------------
    rng = seeds.rng("s3.incoming")
    months = np.arange(month_of(-H + 1), 1)
    out_tx = out_tx.assign(month=month_of(out_tx["day"]))
    dep_out = out_tx[out_tx["category"].isin(FROM_DEPOSITS)].groupby(["hh", "month"])["amount"].sum()
    inc = np.zeros((n, len(months)))
    for name in ["payroll", "bonus", "payroll_new", "pension", "pension_new", "business_distribution"]:
        s = sim2["streams"][name]
        d, a = s["dates"], s["amount_m"]
        mo = month_of(np.nan_to_num(d, nan=1e9))
        for k_m, mm in enumerate(months):
            inc[:, k_m] += np.nansum(np.where((mo == mm) & ~np.isnan(d), a, 0.0), axis=1)
    dep_out_m = np.zeros((n, len(months)))
    idx = dep_out.index
    dep_out_m[idx.get_level_values(0), idx.get_level_values(1) - months[0]] = dep_out.to_numpy()
    # Flujos internos AUM ↔ depósitos: retiros de AUM que no salieron por ACATS (ni choque externo)
    # se acreditan a depósitos; los aportes al AUM salen de depósitos.
    aum_ext = out_tx[out_tx["category"].isin({"episode_acats", "move_acats", "shock_aum", "irs_shock_aum"})]
    aum_ext_m = np.zeros((n, len(months)))
    g = aum_ext.groupby(["hh", "month"])["amount"].sum()
    aum_ext_m[g.index.get_level_values(0), g.index.get_level_values(1) - months[0]] = g.to_numpy()
    jj0 = M - 1 + months
    internal_in = np.maximum(sim1["withdraw"][:, jj0] - aum_ext_m, 0.0)
    internal_out = sim1["contrib"][:, jj0]
    card_share = rng.uniform(*s3["card_spending_share_of_income"], n)
    card = card_share[:, None] * inc.mean(axis=1, keepdims=True)
    jj = M - 1 + months
    dD = D[:, jj] - D[:, jj - 1]
    resid = dD - inc - internal_in + internal_out + dep_out_m + card
    incoming = np.maximum(resid, 0.0)
    other_debits = np.maximum(-resid, 0.0)
    valid = (AVG_MONTH * (months[None, :] - 1) >= open_day[:, None]) & sim1["avail"][:, jj] & sim1["avail"][:, jj - 1]
    incoming[~valid] = 0.0
    lo, hi = s3["incoming_transfers_per_month"]
    hh_i, m_i = np.nonzero(incoming > 0)
    k = rng.integers(lo, hi + 1, len(hh_i))
    rep = np.repeat(np.arange(len(hh_i)), k)
    w = rng.exponential(1.0, len(rep))
    w /= np.bincount(rep, w)[rep]
    hh = hh_i[rep]
    mm = months[m_i[rep]]
    slot = np.floor(rng.uniform(0, 1, len(rep)) * K[hh]).astype(int)
    tx_in = pd.DataFrame({"hh": hh, "day": day_in_month(mm, rng), "amount": incoming[hh_i, m_i][rep] * w,
                          "category": "incoming", "inst_id": payee_inst[hh, slot], "dest_id": payee_dest[hh, slot],
                          "month": mm})
    allt = pd.concat([out_tx, tx_in], ignore_index=True)
    allt = allt[allt["amount"] > 0.005]
    allt["amount"] = allt["amount"].round(2)
    # ABA de cada transacción: una de las ABA de la institución (varias por institución).
    k_aba = abas.groupby("inst_id").size().reindex(inst["inst_id"]).to_numpy()
    aba_mat = np.full((len(inst), k_aba.max()), None, dtype=object)
    for iid, g in abas.groupby("inst_id"):
        aba_mat[iid, :len(g)] = g["aba"].to_numpy()
    # La ABA es fija por cuenta destino (una cuenta tiene un solo routing number).
    rng = seeds.rng("s3.aba_pick")
    u_dest = rng.random(next_dest[0] + 1)
    ii = allt["inst_id"].to_numpy()
    has_inst = ii >= 0
    dest = np.maximum(allt["dest_id"].to_numpy(), 0)
    pick = np.floor(u_dest[dest] * k_aba[np.where(has_inst, ii, 0)]).astype(int)
    allt["aba"] = np.where(has_inst, aba_mat[np.where(has_inst, ii, 0), pick], None)
    cash_share = seeds.rng("s3.cash_share").beta(*s3["investment_cash_share_beta"], n)
    return {"tx": allt.sort_values(["hh", "day"], kind="stable").reset_index(drop=True), "inst": inst, "abas": abas,
            "cash_share": cash_share, "background_share": share, "identity": {"dD": dD, "inc": inc, "dep_out": dep_out_m, "card": card, "internal_in": internal_in, "internal_out": internal_out,
                                                   "incoming": incoming, "other_debits": other_debits,
                                                   "valid": valid, "months": months}}


def compute_variables(sim3, sim1, base, cfg) -> pd.DataFrame:
    s3 = cfg["step3"]
    n, M = len(base), cfg["step1"]["months"]
    floor_bal = cfg["step1"]["min_balance_for_pct"]
    tx, inst = sim3["tx"], sim3["inst"]
    D, A, av = sim1["deposit"], sim1["aum"], sim1["avail"]
    hist = base["history_months"].to_numpy()
    ext = tx[tx["category"].isin(EXTERNAL_OUT)]
    inc = tx[tx["category"] == "incoming"]

    def window_sum(df, lo, hi=0, mask=None):
        d = df if mask is None else df[mask]
        d = d[(d["day"] > lo) & (d["day"] <= hi)]
        return np.bincount(d["hh"], d["amount"], minlength=n)

    def balance(months):
        """Saldo promedio: depósitos + cash dentro de inversiones, en los meses de la ventana."""
        cols = [M - 1 + m for m in months]
        dep = D[:, cols].mean(axis=1)
        cash = sim3["cash_share"] * np.where(sim1["inv"], A[:, cols].mean(axis=1), 0.0)
        ok = av[:, cols].all(axis=1)
        return np.where(ok, dep + cash, np.nan)

    def pct(num, den):
        return np.where(den >= floor_bal, num / np.where(den > 0, den, 1), np.nan)

    out = pd.DataFrame({"household_id": base["household_id"].to_numpy()})
    b30, b60, b90 = balance([0]), balance([-1, 0]), balance([-2, -1, 0])
    s60 = window_sum(ext, -60)
    out["external_transfer_amount_60d"] = np.where(hist >= 2, s60.round(2), np.nan)
    out["external_transfer_pct_of_balance_60d"] = pct(s60, b60)
    out["external_transfer_pct_of_balance_30d"] = pct(window_sum(ext, -30), b30)

    # #8 destinos nuevos: primer envío dentro de la ventana, ninguno en los 12 meses previos,
    # y acumulado ≥ piso en la ventana.
    first = ext.groupby(["hh", "dest_id"])["day"].min()
    for W, lab in [(30, "30d"), (90, "90d")]:
        win = ext[(ext["day"] > -W)].groupby(["hh", "dest_id"])["amount"].sum()
        f = first.reindex(win.index)
        prior = ext[(ext["day"] > -W - s3["lookback_new_destination_days"]) & (ext["day"] <= -W)].groupby(
            ["hh", "dest_id"]).size().reindex(win.index, fill_value=0)
        new = (f > -W) & (prior == 0) & (win >= s3["new_destination_min_cumulative"])
        cnt = np.bincount(win.index.get_level_values(0)[new.to_numpy()], minlength=n)
        out[f"new_external_destinations_{lab}"] = pd.array(np.where(hist >= 13 + W // 30, cnt, pd.NA), dtype="Int16")

    comp_ids = set(inst.loc[inst["competitor_bank"], "inst_id"])
    comp_mask = ext["inst_id"].isin(comp_ids)
    s90c = window_sum(ext, -90, mask=comp_mask)
    out["transfer_to_competitor_bank_amount_90d"] = np.where(hist >= 3, s90c.round(2), np.nan)
    out["transfer_to_competitor_pct_90d"] = pct(s90c, b90)

    A1, A2, A3 = window_sum(ext, -30), window_sum(ext, -60, -30), window_sum(ext, -90, -60)
    any3 = (A1 + A2 + A3) > 0
    ok90 = any3 & (b90 >= floor_bal) & (hist >= 3)
    out["external_transfer_acceleration"] = np.where(ok90, ((A1 - A2) - (A2 - A3)) / np.where(ok90, b90, 1), np.nan)
    out["external_outflow_pct_30d"] = pct(A1, b90)

    # #23 solo wires / ACH (datos del Excel: "incoming and outgoing wires / ACH"); sin ACATS,
    # que sí cuenta en #7 por la definición base de transferencia externa.
    wire = ext[~ext["category"].isin(ACATS)]
    for W, lab in [(30, "30d"), (90, "90d")]:
        net = window_sum(inc, -W) - window_sum(wire, -W)
        out[f"net_external_flow_{lab}"] = np.where(hist >= W // 30, net.round(2), np.nan)
    out["net_external_flow_pct_90d"] = pct(window_sum(inc, -90) - window_sum(wire, -90), b90)

    # #24 concentración (HHI) por INSTITUCIÓN (no por ABA) en 90 días.
    e90 = ext[ext["day"] > -90]
    by_inst = e90.groupby(["hh", "inst_id"])["amount"].sum()
    tot = by_inst.groupby(level=0).transform("sum")
    hhi = ((by_inst / tot) ** 2).groupby(level=0).sum()
    conc = np.full(n, np.nan)
    conc[hhi.index.to_numpy()] = hhi.to_numpy()
    out["external_destination_concentration"] = np.where(hist >= 3, conc, np.nan)
    out["external_outflow_pct_90d"] = pct(A1 + A2 + A3, b90)

    # #25 último mes vs promedio mensual de los meses −7..−1, con piso PB en el denominador.
    base_m = window_sum(ext, -210, -30) / 6
    den = np.maximum(base_m, s3["outflow_baseline_floor_monthly"])
    out["outflow_vs_baseline_pct"] = np.where(hist >= 7, A1 / den - 1, np.nan)
    return out


def build_step3(base, truth, cfg, seeds, exit_ev, sim1, sim2):
    sim3 = simulate_transfers(base, truth, cfg, seeds, exit_ev, sim1, sim2)
    return compute_variables(sim3, sim1, base, cfg), sim3
