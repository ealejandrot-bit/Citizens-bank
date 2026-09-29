"""Paso 16 · Arquetipos de churners, playbook tramo × arquetipo y EWS.

- Solo eventos B de dev, descritos por sus señales pre-T0 en WoE (bins del paso 9: el missing queda como categoría, sin
  imputar): unión de variables del campeón y del challenger sin compuestos ni cluster.
- K-means K ∈ 2..6 (n_init 20) y GMM diagonal como comparación; se elige dentro de K ∈ {3, 4} (SPEC). Regla: tamaño mínimo
  ≥ 10% de los eventos, ARI bootstrap ≥ 0.80, mayor silhouette; si ninguno cumple ARI, el de mayor ARI (D16.1).
- Eventos de val asignados sin reajuste. Perfil por arquetipo: señales con mayor diferencia estandarizada vs el total de
  eventos; nombres asignados después de revisar el perfil (ARCH_NAMES). Descriptivo, nunca causal.
- Playbook: SLA Crítico ≤ 5 días hábiles, Alto ≤ 15 [DEF SPEC]; control aleatorio 12.5% en Alto [DEF G3-4].
- EWS: entrada a Crítico / Alto, overrides, regla de migración para el refresco mensual (no evaluable con un snapshot).
"""
from __future__ import annotations

import pickle

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler

from common import COMPOSITES, MODEL, PROC, REPORTS, SEED, load_split, md_table, save_table, set_seed
from woe import woe_frame

set_seed()
SC = pd.read_parquet(PROC / "step12_scores.parquet")
B9 = pickle.load(open(MODEL / "step09_binning.pkl", "rb"))
SEL = pickle.load(open(MODEL / "step10_selection.pkl", "rb"))
SIG = [c for c in dict.fromkeys(SEL["champion"] + SEL["challenger"]) if c not in COMPOSITES and c != "cluster" and c in B9]
TR = ["Crítico", "Alto", "Vigilancia", "Estable"]


def events(p):
    d = load_split(p).merge(SC, on="household_id")
    return d[d.in_pop_B & (d.y_B == 1)].reset_index(drop=True)


ed, ev = events("dev"), events("val")
Wd, Wv = woe_frame(ed, B9, SIG), woe_frame(ev, B9, SIG)
sc = StandardScaler().fit(-Wd)                                  # −WoE: alto = señal de riesgo
Zd, Zv = sc.transform(-Wd), sc.transform(-Wv)
rng = np.random.default_rng(SEED)
rows, fits = [], {}
for k in range(2, 7):
    km = KMeans(k, n_init=20, random_state=SEED).fit(Zd)
    aris = [adjusted_rand_score(km.labels_, KMeans(k, n_init=5, random_state=SEED + b).fit(Zd[rng.choice(len(Zd), len(Zd))]).predict(Zd)) for b in range(20)]
    gm = GaussianMixture(k, covariance_type="diag", random_state=SEED, n_init=3).fit(Zd)
    rows.append({"K": k, "silhouette": silhouette_score(Zd, km.labels_), "ARI bootstrap": np.mean(aris), "arquetipo mín %": 100 * np.bincount(km.labels_).min() / len(Zd),
                 "BIC GMM": gm.bic(Zd), "ARI K-means vs GMM": adjusted_rand_score(km.labels_, gm.predict(Zd))})
    fits[k] = km
KS = pd.DataFrame(rows)
ok = KS[KS.K.isin([3, 4]) & (KS["arquetipo mín %"] >= 10) & (KS["ARI bootstrap"] >= 0.80)]   # SPEC: 3–4 arquetipos
K = int(ok.loc[ok.silhouette.idxmax(), "K"]) if len(ok) else int(KS.loc[KS["ARI bootstrap"].idxmax(), "K"])
KS["elegido"] = np.where(KS.K == K, "◀", "")
save_table(KS, "step16_k_selection")
km = fits[K]
ed["arq"], ev["arq"] = km.labels_, km.predict(Zv)
with open(MODEL / "step16_archetypes.pkl", "wb") as fh:
    pickle.dump({"signals": SIG, "scaler": sc, "kmeans": km, "K": K}, fh)

# Perfil: diferencia estandarizada del centroide (z medio) y valores crudos
cent = pd.DataFrame(km.cluster_centers_, columns=SIG)
prof = []
for a in range(K):
    g = ed[ed.arq == a]
    top = cent.loc[a].sort_values(ascending=False)
    prof.append({"arquetipo": a, "eventos dev": len(g), "% eventos dev": 100 * len(g) / len(ed), "eventos val": int((ev.arq == a).sum()),
                 "% eventos val": 100 * (ev.arq == a).mean(), "RV mediano $M": g.relationship_value.median() / 1e6,
                 "% RV de eventos dev": 100 * g.relationship_value.sum() / ed.relationship_value.sum(), "% UHNW": 100 * g.segment_uhnw.mean(),
                 **{f"% {t}": 100 * (g.tramo == t).mean() for t in TR},
                 "señales dominantes (z centroide)": ", ".join(f"{c} {top[c]:+.2f}" for c in top.index[:4])})
PR = pd.DataFrame(prof)
RAW = ["banker_change_6m_flag", "client_reply_rate", "share_of_wallet", "contact_gap_ratio", "cash_pct_of_portfolio_chg", "streams_stopped_count",
       "complaint_escalated_flag", "repeat_complaint_flag", "transfer_to_competitor_bank_amount_90d", "net_external_flow_pct_90d", "return_vs_benchmark",
       "fixed_income_maturity_not_reinvested", "meetings_cancelled_by_client"]
RAW = [c for c in RAW if c in ed]
RW = ed.groupby("arq")[RAW].median().T
RW["todos los eventos"] = ed[RAW].median()
RW["no eventos (dev)"] = load_split("dev").query("in_pop_B and y_B == 0")[RAW].median()
FLAGS = [c for c in RAW if c.endswith("_flag")]
for c in FLAGS:                                                  # flags: % con 1 en vez de mediana
    RW.loc[c, list(range(K))] = [100 * ed.loc[ed.arq == a, c].mean() for a in range(K)]
    RW.loc[c, "todos los eventos"] = 100 * ed[c].mean()
    RW.loc[c, "no eventos (dev)"] = 100 * load_split("dev").query("in_pop_B and y_B == 0")[c].mean()
RW.index = [f"{c} (% con 1)" if c in FLAGS else f"{c} (mediana)" for c in RW.index]
RW = RW.reset_index().rename(columns={"index": "señal"})

# Nombres asignados tras revisar perfiles (se rellenan después de la primera corrida; D16.2)
ARCH_NAMES = {0: "relación desatendida", 1: "salida activa a competidor", 2: "desgaste silencioso"}
ARCH_ACTION = {
    0: "reactivar la relación: reunión del banquero, revisión de necesidades y plan de contacto (brecha de contacto 0.84 vs 0.26 de no eventos; respuesta 0.33)",
    1: "retención inmediata: líder + banquero, entender el destino de las transferencias, atender la queja y el cambio de banquero, propuesta de reinversión",
    2: "revisión proactiva ligera: revisión de portafolio y rendimiento vs referencia, contacto dentro del ciclo; las señales se parecen a las de quienes se quedan",
}
PR["nombre"] = PR.arquetipo.map(ARCH_NAMES).fillna(PR.arquetipo.map(lambda a: f"arquetipo {a}"))
save_table(PR, "step16_archetype_profile")
save_table(RW, "step16_archetype_signals")

# Playbook tramo × arquetipo
RESP = {"Crítico": "banquero + líder de equipo", "Alto": "banquero", "Vigilancia": "banquero (revisión de cartera)", "Estable": "—"}
SLA = {"Crítico": "≤ 5 días hábiles", "Alto": "≤ 15 días hábiles", "Vigilancia": "revisión mensual", "Estable": "gestión normal"}
CAD = {"Crítico": "semanal hasta resolver", "Alto": "quincenal", "Vigilancia": "mensual", "Estable": "ciclo normal"}
pb = []
for t in TR[:3]:
    for a in range(K):
        pb.append({"tramo": t, "arquetipo": PR.loc[a, "nombre"], "responsable": RESP[t], "SLA": SLA[t], "acción": ARCH_ACTION.get(a, "(tras revisión de perfil)"),
                   "cadencia": CAD[t], "control aleatorio": "12.5% sin contacto adicional [DEF G3-4]" if t == "Alto" else "—",
                   "eventos val en la celda": int(((ev.tramo == t) & (ev.arq == a)).sum())})
PB = pd.DataFrame(pb)
save_table(PB, "step16_playbook")

EWS = pd.DataFrame([
    ("Entrada a Crítico", "score ≤ 445 en el refresco", "alerta al banquero y líder; SLA 5 días hábiles", "sí (con el snapshot)"),
    ("Entrada a Alto", "445 < score ≤ 517, o override activo", "alerta al banquero; SLA 15 días hábiles; 12.5% a control", "sí (con el snapshot)"),
    ("Override", "cambio de banquero, queja escalada o transferencia a competidor ≥ 10%", "sube a Alto aunque el score no lo indique", "sí (con el snapshot)"),
    ("Migración", "caída ≥ 40 puntos (1 PDO = odds ×2) entre refrescos mensuales, o baja de 2 tramos", "alerta de deterioro aunque no llegue a Alto",
     "no: requiere 2 snapshots (L1)"),
    ("Salida de Crítico/Alto", "2 refrescos seguidos en tramo inferior", "cierre del caso", "no: requiere 2 snapshots (L1)"),
], columns=["disparador", "regla", "acción", "evaluable hoy"])
save_table(EWS, "step16_ews")

rep = f"""# Paso 16 · Acción, arquetipos, EWS

## Objetivo
- Describir los tipos de churner (arquetipos) para diseñar acciones distintas por tramo y tipo, y definir las alertas.

## Método
- Eventos B de dev ({len(ed):,}) [DATA] descritos por {len(SIG)} señales pre-T0 en WoE (missing como categoría, sin imputar).
- K-means K = 2..6 (K = 2 como referencia); elección dentro de K ∈ {3, 4} (SPEC); regla previa: tamaño ≥ 10%, ARI bootstrap ≥ 0.80, mayor silhouette (D16.1). GMM como comparación.
  Eventos de val asignados sin reajuste. Perfiles descriptivos, nunca causales.
- Playbook con SLA del SPEC (Crítico ≤ 5, Alto ≤ 15 días hábiles) y control 12.5% en Alto [DEF G3-4].

## Código
- `src/step16_archetypes.py` · `tests/test_step16.py` · `step16_*.csv`, `outputs/model/step16_archetypes.pkl`.

## Resultados

### Selección de K [DATA]
{md_table(KS, floatfmt=",.3f")}

### Perfil de arquetipos [DATA]
{md_table(PR, floatfmt=",.1f")}

- Verificación: % eventos dev suma {PR['% eventos dev'].sum():.1f}%; % eventos val suma {PR['% eventos val'].sum():.1f}% [DATA].

### Señales por arquetipo (medianas; flags en % con 1) [DATA]
{md_table(RW, floatfmt=",.3f")}

### Playbook tramo × arquetipo
{md_table(PB)}

### EWS
{md_table(EWS)}

## Tests
- `tests/test_step16.py` (ver pytest).

## Decisiones y preguntas abiertas
- D16.1–D16.2 en `reports/decision_log.md`.
"""
(REPORTS / "step16.md").write_text(rep, encoding="utf-8")
print(KS.round(3).to_string(index=False)); print(PR.round(1).to_string(index=False)); print(RW.round(3).to_string(index=False))
