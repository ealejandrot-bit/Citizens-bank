"""Paso 2 · Recurring deposits & flows (variables 3, 4, 5, 6, 19, 20).

1) Simula cada crédito recurrente del hogar con su fecha (18 meses, calendario real de
   días hábiles de EE. UU. con feriados federales): nómina (con bono anual del mismo
   originador), pensión, dividendos, distribuciones del negocio, y los débitos de la
   nómina del negocio vinculado.
2) Aplica eventos:
   * SEÑAL: redirección del ingreso a otro banco (P depende de z_outflow) y traslado de
     la operación del negocio;
   * RUIDO / EXCLUSIONES (independientes del riesgo): cambio de empleo, retiro, licencia,
     muerte (hogares excluidos del target), venta del negocio, pagos atrasados u omitidos.
3) Corre el algoritmo de detección del Excel sobre esas transacciones.

Representación: cada flujo es una matriz (hogares × pagos) de días relativos a t
(0 = t, negativos = pasado; NaN = sin pago) y otra de montos en USD.
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from pandas.tseries.holiday import USFederalHolidayCalendar
from scipy import special

from .seeds import SeedManager

AVG_MONTH = 30.44


# ---------------------------------------------------------------------------
# Calendario
# ---------------------------------------------------------------------------
class Calendar:
    def __init__(self, t: pd.Timestamp, history_days: int):
        self.t = np.datetime64(t.date())
        start = t - pd.Timedelta(days=history_days + 40)
        self.holidays = USFederalHolidayCalendar().holidays(start, t + pd.Timedelta(days=40)).values.astype("datetime64[D]")
        self.months = pd.date_range(start.replace(day=1), t, freq="MS")
        self.start = -history_days

    def bday_back(self, dates: np.ndarray) -> np.ndarray:
        """Si cae en fin de semana o feriado, se paga el día hábil anterior."""
        return np.busday_offset(dates.astype("datetime64[D]"), 0, roll="backward", holidays=self.holidays)

    def offset(self, dates: np.ndarray) -> np.ndarray:
        return (dates.astype("datetime64[D]") - self.t).astype(float)

    def monthly(self, day: int, step: int = 1, phase: int = 0, last_day: bool = False) -> np.ndarray:
        out = []
        for m in self.months:
            if (m.month - 1 - phase) % step:
                continue
            d = m + pd.offsets.MonthEnd(0) if last_day else m.replace(day=min(day, m.days_in_month))
            out.append(np.datetime64(d.date()))
        off = self.offset(self.bday_back(np.array(out)))
        return off[(off > self.start) & (off <= 0)]


def _pad(rows: list[np.ndarray]) -> np.ndarray:
    k = max((len(r) for r in rows), default=1)
    out = np.full((len(rows), max(k, 1)), np.nan)
    for i, r in enumerate(rows):
        out[i, :len(r)] = r
    return out


def _by_param(params: np.ndarray, make) -> np.ndarray:
    """Construye la matriz de fechas calculando una sola vez cada parámetro distinto."""
    cache = {p: make(p) for p in np.unique(params)}
    return _pad([cache[p] for p in params])


# ---------------------------------------------------------------------------
# Detección (lógica del Excel)
# ---------------------------------------------------------------------------
def detect(dates, amounts, end, length, cv_max, min_occ, bonus_multiple=None):
    """¿Existe un patrón recurrente en (end − length, end]? Devuelve (existe, intervalo, monto_mediano).

    Si `bonus_multiple` está dado, los créditos > bonus_multiple × mediana se excluyen (bono)
    antes de medir la regularidad, para que el pago anual no rompa el patrón."""
    end = np.broadcast_to(np.asarray(end, dtype=float), (dates.shape[0],))[:, None]
    m = (dates > end - length) & (dates <= end)
    with np.errstate(all="ignore"), warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)  # filas sin pagos → NaN, es lo esperado
        if bonus_multiple is not None:
            med0 = np.nanmedian(np.where(m, amounts, np.nan), axis=1)
            m &= ~(amounts > bonus_multiple * med0[:, None])
        d = np.sort(np.where(m, dates, np.nan), axis=1)
        diffs = np.diff(d, axis=1)
        mean = np.nanmean(diffs, axis=1)
        cv = np.nanstd(diffs, axis=1) / mean
        exists = (m.sum(axis=1) >= min_occ) & (cv < cv_max)
        interval = np.nanmedian(diffs, axis=1)
        med_amt = np.nanmedian(np.where(m, amounts, np.nan), axis=1)
    return exists, interval, med_amt


def last_credit(dates, amounts=None, bonus_cap=None):
    d = dates if bonus_cap is None else np.where(amounts <= bonus_cap[:, None], dates, np.nan)
    with np.errstate(all="ignore"):
        return np.nanmax(np.where(np.isnan(d), -np.inf, d), axis=1)


# ---------------------------------------------------------------------------
# Simulación
# ---------------------------------------------------------------------------
def simulate_streams(base, truth, cfg, seeds: SeedManager) -> dict:
    s2 = cfg["step2"]
    n, H = len(base), s2["history_days"]
    cal = Calendar(pd.Timestamp(cfg["snapshot_date"]), H)
    z_out = truth["z_outflow"].to_numpy()
    open_day = -np.floor(base["history_months"].to_numpy() * AVG_MONTH)
    open_day = np.where(base["history_months"].to_numpy() >= cfg["population"]["history_months_cap"], -np.inf, open_day)

    def uni(name, lo, hi):
        return seeds.rng(name).uniform(lo, hi, n)

    def bern(name, p):
        return seeds.rng(name).random(n) < p

    streams = {}

    # --- Nómina (originador A) + bono anual del mismo originador ------------------
    has_pay = base["has_payroll_stream"].to_numpy()
    freq = base["pay_frequency"].fillna("none").to_numpy()
    phase = seeds.rng("s2.payroll_phase").integers(0, 14, n)
    biweekly = {p: np.arange(-H + p, 1, 14, dtype=float) for p in range(14)}
    semim = np.unique(np.concatenate([cal.monthly(15), cal.monthly(0, last_day=True)]))
    monthly_pay = cal.monthly(0, last_day=True)
    rows = []
    for i in range(n):
        if not has_pay[i]:
            rows.append(np.array([]))
        elif freq[i] == "biweekly":
            d = biweekly[phase[i]]
            d = cal.offset(cal.bday_back(cal.t + d.astype("timedelta64[D]")))
            rows.append(d[(d > -H) & (d <= 0)])
        elif freq[i] == "semimonthly":
            rows.append(semim)
        else:
            rows.append(monthly_pay)
    per_year = pd.Series(freq).map({"biweekly": 26, "semimonthly": 24, "monthly": 12}).fillna(12).to_numpy()
    paycheck = base["salary_base_annual"].fillna(0).to_numpy() * s2["net_pay_ratio_salary"] / per_year
    streams["payroll"] = {"dates": _pad(rows), "amount": paycheck, "kind": "payroll", "debit": False}

    bonus_month = seeds.rng("s2.bonus_month").choice(s2["bonus_months"], n)
    has_bonus = has_pay & (base["bonus_annual"].fillna(0).to_numpy() > 0)
    bdates = _by_param(bonus_month, lambda mth: cal.monthly(15, step=12, phase=mth - 1))
    bdates[~has_bonus] = np.nan
    streams["bonus"] = {"dates": bdates, "amount": base["bonus_annual"].fillna(0).to_numpy() * s2["net_pay_ratio_salary"],
                        "kind": "payroll", "debit": False}

    # --- Pensión (día del mes por hogar, p. ej. Social Security por cumpleaños) -----
    has_pen = base["has_pension_stream"].to_numpy()
    pen_day = seeds.rng("s2.pension_day").choice([1, 3, 10, 15, 20, 25, 28], n)
    pdates = _by_param(pen_day, lambda d: cal.monthly(d))
    pdates[~has_pen] = np.nan
    streams["pension"] = {"dates": pdates, "amount": base["pension_monthly"].fillna(0).to_numpy() * s2["net_pay_ratio_pension"],
                          "kind": "pension", "debit": False}

    # --- Dividendos y distribuciones del negocio (trimestrales) --------------------
    has_div = base["has_dividend_stream"].to_numpy()
    q_phase = seeds.rng("s2.dividend_phase").integers(0, 3, n)
    ddates = _by_param(q_phase, lambda ph: cal.monthly(15, step=3, phase=ph))
    ddates[~has_div] = np.nan
    streams["dividend"] = {"dates": ddates, "amount": base["dividend_annual"].fillna(0).to_numpy() / 4,
                           "kind": "dividend", "debit": False, "noise": s2["dividend_amount_noise_sd"]}
    has_bus = base["has_linked_business"].to_numpy()
    b_phase = seeds.rng("s2.business_dist_phase").integers(0, 3, n)
    bddates = _by_param(b_phase, lambda ph: cal.monthly(20, step=3, phase=ph))
    bddates[~has_bus] = np.nan
    streams["business_distribution"] = {"dates": bddates,
                                        "amount": base["business_distribution_annual"].fillna(0).to_numpy() / 4,
                                        "kind": "business_distribution", "debit": False,
                                        "noise": s2["business_distribution_amount_noise_sd"]}

    # --- Nómina del negocio (débitos ACH por lote) --------------------------------
    bp = s2["business_payroll_frequency"]
    bfreq = seeds.rng("s2.business_payroll_freq").choice(list(bp), n, p=np.array(list(bp.values())) / sum(bp.values()))
    bphase = seeds.rng("s2.business_payroll_phase").integers(0, 14, n)
    rows = []
    for i in range(n):
        if not has_bus[i]:
            rows.append(np.array([]))
        elif bfreq[i] == "biweekly":
            d = cal.offset(cal.bday_back(cal.t + biweekly[bphase[i]].astype("timedelta64[D]")))
            rows.append(d[(d > -H) & (d <= 0)])
        else:
            rows.append(semim)
    # Tamaño del lote proporcional a las distribuciones del negocio (≈ 1.5× por mes).
    batch = base["business_distribution_annual"].fillna(0).to_numpy() * 1.5 / 12 / pd.Series(bfreq).map(
        {"biweekly": 26 / 12, "semimonthly": 2}).to_numpy()
    streams["business_payroll"] = {"dates": _pad(rows), "amount": batch, "kind": "business_payroll", "debit": True}

    # --- Eventos -------------------------------------------------------------------
    ev = pd.DataFrame({"household_id": base["household_id"]})
    risk = truth["risk_index"].to_numpy()
    p_move = special.expit(s2["move_intercept"] + s2["move_slope"] * risk)
    move = bern("s2.move", p_move)
    r_day = np.floor(uni("s2.move_day", -s2["move_window_days"], 0))
    p_part = special.expit(s2["partial_intercept"] + s2["partial_slope"] * z_out)
    partial_ev = bern("s2.partial", p_part)
    part_day = np.floor(uni("s2.partial_day", -s2["move_window_days"], 0))
    ev["p_move"], ev["move"], ev["move_day"] = p_move, move, np.where(move, r_day, np.nan)
    ev["p_partial"], ev["partial"], ev["partial_day"] = p_part, partial_ev, np.where(partial_ev, part_day, np.nan)

    age = base["age_primary"].to_numpy()
    lo_r, hi_r = s2["retirement_age_range"]
    retire = has_pay & (age >= lo_r) & (age <= hi_r) & bern("s2.retirement", s2["retirement_p_12m"])
    ret_day = np.floor(uni("s2.retirement_day", -365, 0))
    ret_rep = retire & bern("s2.retirement_reported", s2["retirement_reported_p"])
    job = has_pay & ~retire & bern("s2.job_change", s2["job_change_p_12m"])
    job_day = np.floor(uni("s2.job_change_day", -365, 0))
    gap = np.floor(uni("s2.job_change_gap", *s2["job_change_gap_days"]))
    ratio = seeds.rng("s2.job_change_ratio").lognormal(0, s2["job_change_ratio_sigma"], n)
    leave = has_pay & ~retire & ~job & bern("s2.leave", s2["leave_p_12m"])
    leave_start = np.floor(uni("s2.leave_start", -200, -60))
    leave_len = np.floor(uni("s2.leave_len", 60, 120))
    leave_rep = leave & bern("s2.leave_reported", s2["leave_reported_p"])
    death = base["churn_excluded"].to_numpy()
    death_day = np.floor(uni("s2.death_day", -150, 0))
    death_rep = death & bern("s2.death_reported", s2["death_reported_p"])
    p_bm = special.expit(s2["business_move_intercept"] + s2["business_move_slope"] * z_out)
    bmove = has_bus & bern("s2.business_move", p_bm)
    bmove_day = np.floor(uni("s2.business_move_day", -180, 0))
    bsale = has_bus & ~bmove & bern("s2.business_sale", s2["business_sale_p_12m"])
    bsale_day = np.floor(uni("s2.business_sale_day", -365, 0))
    for c, v in dict(retire=retire, retire_day=np.where(retire, ret_day, np.nan), retire_reported=ret_rep,
                     job_change=job, job_change_day=np.where(job, job_day, np.nan),
                     job_change_ratio=np.where(job, ratio, np.nan), leave=leave, leave_reported=leave_rep,
                     death=death, death_day=np.where(death, death_day, np.nan), death_reported=death_rep,
                     p_business_move=p_bm, business_move=bmove, business_move_day=np.where(bmove, bmove_day, np.nan),
                     business_sale=bsale).items():
        ev[c] = v

    # Nuevos flujos creados por eventos: nómina del nuevo empleador y pensión al retirarse.
    new_pay = streams["payroll"]["dates"].copy()
    new_pay[~job] = np.nan
    new_pay[new_pay <= (job_day + gap)[:, None]] = np.nan
    streams["payroll_new"] = {"dates": new_pay, "amount": paycheck * ratio, "kind": "payroll", "debit": False}
    new_pen = _by_param(pen_day, lambda d: cal.monthly(d))
    new_pen[~(retire & ~has_pen)] = np.nan
    new_pen[new_pen <= (ret_day + 30)[:, None]] = np.nan
    pen_amt = seeds.rng("s2.new_pension_amount").lognormal(np.log(cfg["income"]["pension_monthly_median"]),
                                                          cfg["income"]["pension_sigma"], n)
    streams["pension_new"] = {"dates": new_pen, "amount": pen_amt * s2["net_pay_ratio_pension"], "kind": "pension",
                              "debit": False}

    # --- Montos con ruido, pagos atrasados / omitidos, apertura ----------------------
    for name, s in streams.items():
        d = s["dates"]
        amt = np.where(np.isnan(d), np.nan, s["amount"][:, None])
        amt = amt * (1 + s.get("noise", s2["amount_noise_sd"]) * seeds.rng(f"s2.{name}.amount_noise").standard_normal(d.shape))
        late = seeds.rng(f"s2.{name}.late").random(d.shape) < s2["late_payment_p"]
        shift = seeds.rng(f"s2.{name}.late_days").integers(1, 4, d.shape) * 1.4  # ≈ días hábiles → corridos
        d = np.where(late, np.floor(d + shift), d)
        miss = seeds.rng(f"s2.{name}.missed").random(n) < s2["missed_payment_p_per_year"] * H / 365
        col = seeds.rng(f"s2.{name}.missed_col").integers(0, d.shape[1], n)
        d[miss, col[miss]] = np.nan
        d[(d > 0) | (d < open_day[:, None])] = np.nan  # aún no llega / cuenta no abierta
        s["dates"], s["amount_m"] = d, np.where(np.isnan(d), np.nan, np.maximum(amt, 0.01))

    # --- Aplicación de eventos -------------------------------------------------------
    def stop(name, mask, day):
        d = streams[name]["dates"]
        d[mask[:, None] & (d > day[:, None])] = np.nan

    u = {k: seeds.rng(f"s2.move_{k}").random(n) for k in s2["p_stop_given_move"]}
    factor = uni("s2.partial_factor", *s2["partial_factor_range"])
    for kind, names in {"payroll": ["payroll", "bonus", "payroll_new"], "pension": ["pension", "pension_new"],
                        "dividend": ["dividend"], "business_distribution": ["business_distribution"]}.items():
        stopped = move & (u[kind] < s2["p_stop_given_move"][kind])
        ev[f"move_stop_{kind}"] = stopped
        for nm in names:
            stop(nm, stopped, r_day)
            a = streams[nm]["amount_m"]
            hit = partial_ev[:, None] & (streams[nm]["dates"] > part_day[:, None])
            streams[nm]["amount_m"] = np.where(hit, a * factor[:, None], a)
    stop("payroll", retire, ret_day)
    stop("bonus", retire, ret_day)
    stop("payroll", job, job_day)
    stop("bonus", job, job_day)
    d = streams["payroll"]["dates"]
    d[leave[:, None] & (d > leave_start[:, None]) & (d <= (leave_start + leave_len)[:, None])] = np.nan
    for nm in streams:
        stop(nm, death, death_day)
    stop("business_payroll", bmove, bmove_day)
    stop("business_payroll", bsale, bsale_day)
    stop("business_distribution", bsale, bsale_day)
    for s in streams.values():
        s["amount_m"] = np.where(np.isnan(s["dates"]), np.nan, s["amount_m"])
    return {"streams": streams, "events": ev}


# ---------------------------------------------------------------------------
# Variables
# ---------------------------------------------------------------------------
def compute_variables(sim2: dict, sim1: dict, base: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    s2, det = cfg["step2"], cfg["step2"]["detection"]
    st, ev = sim2["streams"], sim2["events"]
    n = len(base)
    cv, k, bm = det["cv_max"], det["min_occurrences"], det["bonus_multiple"]
    out = pd.DataFrame({"household_id": base["household_id"].to_numpy()})

    def cat(*names):
        return (np.concatenate([st[x]["dates"] for x in names], axis=1),
                np.concatenate([st[x]["amount_m"] for x in names], axis=1))

    def stop_threshold(interval):
        return np.maximum(det["stop_days_min"], det["stop_interval_multiple"] * np.nan_to_num(interval, nan=30.0))

    def evaluate(dates, amts, lookback, bonus=False):
        """Patrón a t − umbral y ausencia de créditos en (t − umbral, t]."""
        _, interval, _ = detect(dates, amts, -det["stop_days_min"], lookback, cv, k, bm if bonus else None)
        thr = stop_threshold(interval)
        exists, interval, med = detect(dates, amts, -thr, lookback, cv, k, bm if bonus else None)
        cap = bm * med if bonus else None
        last = last_credit(dates, amts, cap) if bonus else last_credit(dates)
        return exists, exists & (last <= -thr), interval, med, last

    excl_payroll = (ev["retire_reported"] | ev["leave_reported"] | ev["death_reported"]).to_numpy()
    excl_all = ev["death_reported"].to_numpy()

    # --- #3 salary_deposit_stopped_flag -------------------------------------------
    dA, aA = cat("payroll", "bonus")
    exA, stA, _, medA, lastA = evaluate(dA, aA, det["payroll_lookback_days"], bonus=True)
    dB, aB = st["payroll_new"]["dates"], st["payroll_new"]["amount_m"]
    exB, stB, _, medB, lastB = evaluate(dB, aB, det["payroll_lookback_days"])
    # Reemplazo (cambio de empleo): nueva nómina de otro originador ≥ 50% del monto anterior.
    with np.errstate(invalid="ignore"):
        replA = np.nanmax(np.where((dB > lastA[:, None]) & (aB >= det["replacement_min_ratio"] * medA[:, None]), 1, 0),
                          axis=1) > 0
    sal = (stA & ~replA) | stB
    out["salary_deposit_stopped_flag"] = pd.array(np.where(exA | exB, (sal & ~excl_payroll).astype(int), pd.NA), dtype="Int8")

    # --- #19 pension_deposit_stopped_flag --------------------------------------------
    exP, stP, *_ = evaluate(st["pension"]["dates"], st["pension"]["amount_m"], det["recurring_lookback_days"])
    exP2, stP2, *_ = evaluate(st["pension_new"]["dates"], st["pension_new"]["amount_m"], det["recurring_lookback_days"])
    out["pension_deposit_stopped_flag"] = pd.array(np.where(exP | exP2, ((stP | stP2) & ~excl_all).astype(int), pd.NA),
                                                   dtype="Int8")

    # --- #4 recurring_deposit_stopped_flag (+ tipo) ------------------------------------
    parts = {"payroll": (dA, aA, True, excl_payroll | replA), "payroll_new": (dB, aB, False, excl_payroll),
             "pension": (st["pension"]["dates"], st["pension"]["amount_m"], False, excl_all),
             "pension_new": (st["pension_new"]["dates"], st["pension_new"]["amount_m"], False, excl_all),
             "dividend": (st["dividend"]["dates"], st["dividend"]["amount_m"], False, excl_all),
             "business_distribution": (st["business_distribution"]["dates"], st["business_distribution"]["amount_m"],
                                       False, excl_all | ev["business_sale"].to_numpy())}
    res = {nm: evaluate(d, a, det["recurring_lookback_days"], bonus=b) + (x,) for nm, (d, a, b, x) in parts.items()}
    with np.errstate(divide="ignore", invalid="ignore"):
        monthly_eq = {nm: np.where(r[0], r[3] * AVG_MONTH / r[2], 0.0) for nm, r in res.items()}
    total = np.sum(list(monthly_eq.values()), axis=0)
    any_id = total > 0
    flag = np.zeros(n, bool)
    stype = np.full(n, None, dtype=object)
    for nm, r in res.items():
        weight = np.where(any_id, monthly_eq[nm] / np.where(any_id, total, 1), 0)
        hit = r[1] & (weight >= det["min_stream_weight"]) & ~r[5] & ~flag
        stype[hit] = nm.replace("_new", "")
        flag |= hit
    out["recurring_deposit_stopped_flag"] = pd.array(np.where(any_id, flag.astype(int), pd.NA), dtype="Int8")
    out["recurring_deposit_stopped_type"] = np.where(any_id & flag, stype, None)

    # --- #5 recurring_deposit_change_pct --------------------------------------------
    recent = np.zeros(n)
    baseline = np.zeros(n)
    ident = np.zeros(n, bool)
    for nm, (d, a, b, _) in parts.items():
        ex, interval, med = detect(d, a, -30, det["recurring_lookback_days"], cv, k, bm if b else None)
        aa = np.where(a <= bm * med[:, None], a, np.nan) if b else a  # bono fuera: no es recurrente
        quarterly = interval > 60
        win = np.where(quarterly, 90, 30)[:, None]
        rec = np.nansum(np.where((d > -win) & (d <= 0), aa, np.nan), axis=1) / np.where(quarterly, 3, 1)
        bas = np.nansum(np.where((d > -210) & (d <= -30), aa, np.nan), axis=1) / 6
        recent += np.where(ex, rec, 0)
        baseline += np.where(ex, bas, 0)
        ident |= ex
    ok = ident & (baseline > 0)
    out["recurring_deposit_change_pct"] = np.where(ok, recent / np.where(ok, baseline, 1) - 1, np.nan)

    # --- #6 net_deposit_flow (30d, 90d) desde la serie de depósitos del Paso 1 ----------
    D, av = sim1["deposit"], sim1["avail"]
    M = D.shape[1]
    floor = cfg["step1"]["min_balance_for_pct"]
    for kk, lab in [(1, "30d"), (3, "90d")]:
        okw = av[:, M - 1 - kk:].all(axis=1)
        net = D[:, -1] - D[:, -1 - kk]
        avg = D[:, M - kk:].mean(axis=1)
        out[f"net_deposit_flow_{lab}"] = np.where(okw, np.round(net, 2), np.nan)
        out[f"net_deposit_flow_pct_{lab}"] = np.where(okw & (avg >= floor), net / np.where(avg > 0, avg, 1), np.nan)

    # --- #20 business_payroll_stopped_flag -------------------------------------------
    bd, ba = st["business_payroll"]["dates"], st["business_payroll"]["amount_m"]
    stop_d = det["business_stop_days"]
    exBP, _, _ = detect(bd, ba, -stop_d, det["payroll_lookback_days"], cv, k)
    flagBP = exBP & (last_credit(bd) <= -stop_d) & ~ev["business_sale"].to_numpy() & ~excl_all
    out["business_payroll_stopped_flag"] = pd.array(np.where(exBP, flagBP.astype(int), pd.NA), dtype="Int8")
    return out


def transactions_long(sim2: dict, base: pd.DataFrame, t: str) -> pd.DataFrame:
    """Tabla larga de transacciones (para auditar la detección)."""
    frames = []
    t0 = np.datetime64(pd.Timestamp(t).date())
    for name, s in sim2["streams"].items():
        i, j = np.nonzero(~np.isnan(s["dates"]))
        frames.append(pd.DataFrame({
            "household_id": base["household_id"].to_numpy()[i],
            "date": t0 + s["dates"][i, j].astype(int).astype("timedelta64[D]"),
            "stream": name, "direction": "debit" if s["debit"] else "credit",
            "sec_code": "CCD" if s["debit"] else "PPD",
            "amount": np.round(s["amount_m"][i, j], 2)}))
    return pd.concat(frames, ignore_index=True).sort_values(["household_id", "date"], kind="stable")


def build_step2(base, truth, sim1, cfg, seeds):
    sim2 = simulate_streams(base, truth, cfg, seeds)
    feats = compute_variables(sim2, sim1, base, cfg)
    return feats, sim2
