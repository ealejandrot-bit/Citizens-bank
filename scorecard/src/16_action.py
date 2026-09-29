"""Paso 16 · Acción: arquetipos de churners, playbook y especificación de EWS.

El score predice; no decide la acción. La acción depende del porqué (arquetipo).
- Arquetipos: K-means sobre el riesgo por señal (−WoE; > 0 = más riesgo que la media) de los churners hard de
  desarrollo (840). Señales: las 10 de A + 4 representantes de dimensiones que A no cubre directamente
  (depósitos vs 6m, AUM vs baseline, transferencias a competidores, queja escalada). K ∈ {3, 4}: tamaño mínimo 10%,
  estabilidad bootstrap (ARI ≥ 0.70), mayor silhouette. Nombres fijados después de ver los centroides (D16.1).
- Los churners de holdout y los hogares alertados (Crítico / Alto) se asignan al centroide más cercano.
- Playbook tramo × arquetipo y EWS como especificación.
"""
from __future__ import annotations

import json
import pickle

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, silhouette_score

from common import FIGURES, MODELS, OUT, PARAMS, QC, SCORED, SEED, TABLES, save_table, set_seed
from woe import load_sample, woe_frame

set_seed()
T = PARAMS["target_primary"]
ALL = load_sample(OUT, TABLES, sample=None)
sc = pd.read_csv(SCORED / "scored_households.csv")[["household_id", "tramo", "tramo_lite", "probabilidad", "p_x_valor"]]
ALL = ALL.merge(sc, on="household_id")
with open(MODELS / "09_binning.pkl", "rb") as fh:
    B = pickle.load(fh)
cfg = json.loads((MODELS / "11_final_vars.json").read_text())
iv = pd.read_csv(TABLES / "09_iv_summary.csv").set_index("variable")
SIG = [v for v in cfg["models"]["A"] if v != "segment"] + ["deposit_balance_vs_6m_avg_pct", "aum_vs_baseline_pct",
                                                           "transfer_to_competitor_pct_90d", "complaint_escalated_flag"]
DIM = {v: iv.loc[v, "dimensión"] for v in SIG}
LABEL = {"banker_change_6m_flag": "cambio de banquero", "external_transfer_pct_of_balance_60d": "transferencias externas",
         "products_closed_180d": "productos cerrados", "share_of_wallet": "share of wallet bajo", "recurring_deposit_change_pct": "caída de ingresos recurrentes",
         "investment_redemption_pct": "redenciones", "repeat_complaint_flag": "queja repetida", "return_vs_benchmark": "bajo rendimiento vs benchmark",
         "client_reply_rate": "< 3 contactos del banquero en 90d", "contact_gap_ratio": "brecha de contacto", "deposit_balance_vs_6m_avg_pct": "caída de depósitos",
         "aum_vs_baseline_pct": "caída de AUM", "transfer_to_competitor_pct_90d": "envíos a competidores", "complaint_escalated_flag": "queja escalada"}
R = -woe_frame(ALL, B, SIG)            # riesgo por señal: > 0 = peor que la media
elig = ~ALL.churn_excluded.astype(bool)
ch_dev = (ALL.muestra == "desarrollo") & elig & (ALL[T] == 1)
ch_hold = (ALL.muestra == "holdout") & elig & (ALL[T] == 1)
Xd = R[ch_dev].to_numpy()
qc = QC("16")
qc.check("Churners de desarrollo", ch_dev.sum() == 840, 840, int(ch_dev.sum()))

rng = np.random.default_rng(SEED)
sel, fits = [], {}
for k in (3, 4):
    km = KMeans(k, n_init=50, random_state=SEED).fit(Xd)
    aris = []
    for b in range(30):
        bi = rng.choice(len(Xd), len(Xd), replace=True)
        aris.append(adjusted_rand_score(km.labels_, KMeans(k, n_init=10, random_state=SEED + b).fit(Xd[bi]).predict(Xd)))
    sel.append({"K": k, "silhouette": silhouette_score(Xd, km.labels_), "ARI bootstrap": np.mean(aris),
                "cluster mín %": 100 * np.bincount(km.labels_).min() / len(Xd)})
    fits[k] = km
sel = pd.DataFrame(sel)
ok = sel[(sel["cluster mín %"] >= 10) & (sel["ARI bootstrap"] >= 0.70)]
K = int(ok.loc[ok.silhouette.idxmax(), "K"]) if len(ok) else int(sel.loc[sel["ARI bootstrap"].idxmax(), "K"])
km = fits[K]
save_table(sel.round(4), "16_archetype_k")

# ── Perfil de centroides y nombre ───────────────────────────────────────────────────────
lab_dev = km.labels_
prof = pd.DataFrame(km.cluster_centers_, columns=SIG)
overall = Xd.mean(axis=0)
lift = prof - overall                 # riesgo del cluster vs churner promedio
dim_lift = lift.T.groupby(pd.Series(DIM)).mean().T
NAMES = {"relación con banquero": "Desconexión del banquero", "externalización/competencia": "Externalización activa",
         "pérdida de productos": "Desinversión de la relación", "nivel patrimonial": "Erosión silenciosa de wallet",
         "fricción de servicio": "Fricción de servicio", "ingresos recurrentes": "Redirección de ingresos",
         "salida de activos": "Salida de inversiones", "deterioro de saldos": "Drenaje de depósitos", "rendimiento": "Insatisfacción con el rendimiento"}
# Nombres fijados después de ver los centroides (D16.1), con reglas reproducibles:
#   mayor riesgo en envíos a competidores → "Externalización activa";
#   mayor riesgo en cambio de banquero (si es otro cluster) → "Salida con el banquero";
#   el resto (sin movimiento de dinero ni cambio de banquero; señal dominante: deja de responder) → "Desenganche silencioso".
C = pd.DataFrame(km.cluster_centers_, columns=SIG)
names = {}
c_ext = int(C["transfer_to_competitor_pct_90d"].idxmax())
names[c_ext] = "Externalización activa"
c_bk = int(C.drop(index=c_ext)["banker_change_6m_flag"].idxmax())
names[c_bk] = "Salida con el banquero"
for c in range(K):
    names.setdefault(c, "Desenganche silencioso" if len(names) == 2 else f"Arquetipo {c + 1}")
# % de churners del cluster en el bin de mayor riesgo de cada señal (legible)
worst = {}
for v in SIG:
    labs = B[v].bin_labels(ALL[v], ALL[f"{v}__miss"] if f"{v}__miss" in ALL else None)
    wb = min(B[v].woe, key=B[v].woe.get)
    worst[v] = labs == wb
W = pd.DataFrame(worst)
dev_ch = ALL[ch_dev].reset_index(drop=True)
Wd = W[ch_dev].reset_index(drop=True)
rows = []
for c in range(K):
    m = lab_dev == c
    pw = Wd.loc[m].mean().sort_values(ascending=False)
    rows.append({"arquetipo": names[c], "churners dev": int(m.sum()), "% churners": 100 * m.mean(),
                 "RV mediano $M": dev_ch.relationship_value[m].median() / 1e6, "% RV de churners": 100 * dev_ch.relationship_value[m].sum() / dev_ch.relationship_value.sum(),
                 "% UHNW": 100 * dev_ch.segment[m].mean(),
                 "señales dominantes (% del arquetipo en el peor bin)": "; ".join(f"{LABEL[v]} {100 * pw[v]:.0f}%" for v in pw.index[:4]),
                 **{f"% en peor bin: {LABEL[v]}": 100 * Wd.loc[m, v].mean() for v in SIG}})
arch = pd.DataFrame(rows)
save_table(arch.round(2), "16_archetypes")
save_table(lift.rename(index=names).round(3).reset_index().rename(columns={"index": "arquetipo"}), "16_archetype_centroids_lift")

# Asignación: churners de holdout y hogares alertados
ALL["arquetipo"] = [names[c] for c in km.predict(R.to_numpy())]
hold_mix = ALL[ch_hold].arquetipo.value_counts(normalize=True).mul(100).rename("% churners holdout")
dev_mix = pd.Series([names[c] for c in lab_dev]).value_counts(normalize=True).mul(100).rename("% churners dev")
mix = pd.concat([dev_mix, hold_mix], axis=1).round(2).reset_index().rename(columns={"index": "arquetipo"})
det = []
for a in [names[c] for c in range(K)]:
    for smp, msk in (("desarrollo", ch_dev), ("holdout", ch_hold)):
        g = ALL[msk & (ALL.arquetipo == a)]
        det.append({"arquetipo": a, "muestra": smp, "churners": len(g), "% en Crítico": 100 * (g.tramo == "Crítico").mean(),
                    "% en Alto": 100 * (g.tramo == "Alto").mean(), "% detectado (Crítico + Alto)": 100 * g.tramo.isin(["Crítico", "Alto"]).mean(),
                    "% en Vigilancia": 100 * (g.tramo == "Vigilancia").mean(), "% en Estable": 100 * (g.tramo == "Estable").mean()})
det = pd.DataFrame(det)
save_table(det.round(2), "16_archetype_detection")
save_table(mix, "16_archetype_mix")
alert = ALL[elig & ALL.tramo.isin(["Crítico", "Alto"])]
tx = pd.crosstab(alert.tramo, alert.arquetipo, margins=True).reset_index()
save_table(tx, "16_tramo_x_archetype")
with open(MODELS / "16_archetypes.pkl", "wb") as fh:
    pickle.dump({"kmeans": km, "signals": SIG, "names": names}, fh)
ALL[["household_id", "arquetipo"]].to_csv(OUT / "data" / "16_archetype_assignment.csv", index=False)

# ── Playbook ────────────────────────────────────────────────────────────────────────────
ACTION = {
    "Desconexión del banquero": ("Reasignar / presentar banquero senior; reunión presencial de relación; revisar cadencia pactada",
                                 "Head of PB asigna; banquero ejecuta"),
    "Externalización activa": ("Conversación de consolidación: entender a dónde va el dinero, oferta competitiva (tasa, pricing, crédito), plan de wealth",
                               "banquero + especialista de producto"),
    "Desinversión de la relación": ("Revisión de productos cerrados y necesidades no cubiertas; retención de productos ancla (trust, crédito, advisory)",
                                    "banquero + especialista"),
    "Erosión silenciosa de wallet": ("Wealth planning para recuperar share of wallet; mapeo de patrimonio externo; propuesta de consolidación",
                                     "banquero + wealth planner"),
    "Fricción de servicio": ("Service recovery: cerrar la queja, disculpa del responsable, seguimiento a 30 días; revisar SLA de quejas",
                             "banquero + service manager"),
    "Redirección de ingresos": ("Entender el cambio (empleo, pensión, negocio); ofrecer soluciones de flujo (cash management, nómina del negocio)",
                                "banquero"),
    "Salida con el banquero": ("Transición de relación: llamada del Head of PB, presentación de banquero senior, plan de 90 días; si el banquero anterior se fue a un competidor, contacto antes de que el cliente lo siga",
                               "Head of PB + nuevo banquero"),
    "Desenganche silencioso": ("Restablecer cobertura: el banquero tuvo < 3 contactos en 90 días con la mayoría de estos hogares; contacto proactivo, "
                               "revisión de objetivos y familia (next gen), invitación a evento; escalar si no hay respuesta",
                               "banquero (Head of PB revisa cobertura del book)"),
    "Salida de inversiones": ("Revisión de portafolio vs objetivos; conversación de rendimiento y fees", "banquero + asesor de inversión"),
    "Drenaje de depósitos": ("Revisión de liquidez y tasas de depósito; contraoferta de pricing", "banquero"),
    "Insatisfacción con el rendimiento": ("Revisión de desempeño vs benchmark, rebalanceo y explicación de fees", "banquero + asesor de inversión"),
}
SLA = {"Crítico": ("≤ 5 días hábiles", "semanal hasta cerrar el caso; comité mensual revisa el 100%"),
       "Alto": ("≤ 15 días hábiles", "quincenal; comité revisa muestra y overrides")}
pb = []
for t in ("Crítico", "Alto"):
    for a in [names[c] for c in range(K)]:
        act, who = ACTION[a]
        n_all = int(((alert.tramo == t) & (alert.arquetipo == a)).sum())
        pb.append({"tramo": t, "arquetipo": a, "hogares en cartera": n_all, "acción": act, "responsable": who,
                   "SLA primer contacto": SLA[t][0], "cadencia": SLA[t][1]})
# Vigilancia: el desenganche silencioso vive ahí (D16.2) → campaña de bajo costo, no caso individual
n_v = int(((ALL.tramo == "Vigilancia") & (ALL.arquetipo == "Desenganche silencioso") & elig).sum())
pb.append({"tramo": "Vigilancia", "arquetipo": "Desenganche silencioso", "hogares en cartera": n_v,
           "acción": "Campaña de cobertura de bajo costo (contacto proactivo, revisión anual de objetivos, invitación a evento); "
                     "prioriza hogares con < 3 contactos del banquero en 90 días y mayor p × valor", "responsable": "banquero (con apoyo de marketing / Copilot)",
           "SLA primer contacto": "≤ 30 días (campaña mensual)", "cadencia": "mensual; pasa a caso individual si sube a Alto"})
pb = pd.DataFrame(pb)
save_table(pb, "16_playbook")

ews = pd.DataFrame([
    {"disparador": "Entrada a Crítico", "condición": "tramo pasa a Crítico en el refresco", "acción": "alerta inmediata al banquero y Head of PB; SLA 5 días", "prioridad": "1"},
    {"disparador": "Override activo", "condición": "se activa una regla de override (pensión detenida → Crítico; transferencias a competidores ≥ 10%, ≥ 2 destinos nuevos, queja repetida, cambio de trustee, insatisfacción → Alto)",
     "acción": "alerta con la regla como razón principal", "prioridad": "1–2"},
    {"disparador": "Subida de dos tramos", "condición": "Estable → Alto, Vigilancia → Crítico entre dos refrescos", "acción": "alerta aunque no llegue a Crítico: aceleración del riesgo", "prioridad": "2"},
    {"disparador": "Entrada a Alto", "condición": "tramo pasa a Alto (dentro de la capacidad del 10%)", "acción": "tarea al banquero; SLA 15 días", "prioridad": "2"},
    {"disparador": "Cambio de arquetipo en alertado", "condición": "hogar en Crítico/Alto cambia de arquetipo", "acción": "actualizar la acción del playbook", "prioridad": "3"},
])
save_table(ews, "16_ews_spec")
mig = pd.DataFrame(np.full((4, 4), "t+1 (por calcular)"), index=["Crítico", "Alto", "Vigilancia", "Estable"], columns=["→ Crítico", "→ Alto", "→ Vigilancia", "→ Estable"]).reset_index().rename(columns={"index": "tramo en t"})
save_table(mig, "16_migration_matrix_design")

qc.check("Arquetipos: tamaño mínimo ≥ 10%", float(sel.loc[sel.K == K, "cluster mín %"].iloc[0]) >= 10, "≥ 10%", f"{float(sel.loc[sel.K == K, 'cluster mín %'].iloc[0]):.1f}%", severity="warn")
qc.check("Arquetipos: estabilidad bootstrap ARI ≥ 0.70", float(sel.loc[sel.K == K, "ARI bootstrap"].iloc[0]) >= 0.70, "≥ 0.70", f"{float(sel.loc[sel.K == K, 'ARI bootstrap'].iloc[0]):.3f}", severity="warn")
qc.check("Nombres únicos por arquetipo", len(set(names.values())) == K, K, len(set(names.values())))
diffmix = (mix["% churners dev"] - mix["% churners holdout"]).abs().max()
qc.check("Mezcla de arquetipos dev vs holdout (≤ 10 pp)", diffmix <= 10, "≤ 10 pp", f"{diffmix:.1f} pp", severity="warn")
qc.check("Todo alertado tiene arquetipo y acción", alert.arquetipo.notna().all() and set(alert.arquetipo) <= set(ACTION), "100%", "ok")

# Figura: centroides (lift de riesgo por señal)
INK, MUTED = "#0b0b0b", "#52514e"
import matplotlib.colors as mcolors
div = mcolors.LinearSegmentedColormap.from_list("div", ["#2a78d6", "#f2f1ed", "#e34948"])
L = pd.DataFrame({names[c]: Wd.loc[lab_dev == c].mean() * 100 for c in range(K)}).T[SIG]
seq = mcolors.LinearSegmentedColormap.from_list("seq", ["#f2f1ed", "#2a78d6"])
fig, ax = plt.subplots(figsize=(12, 1.2 + 0.7 * K))
im = ax.imshow(L.to_numpy(), cmap=seq, vmin=0, vmax=100, aspect="auto")
ax.set_xticks(range(len(SIG)), [LABEL[s_] for s_ in SIG], rotation=40, ha="right", fontsize=8, color=INK)
ax.set_yticks(range(K), [f"{n} ({arch.set_index('arquetipo').loc[n, '% churners']:.0f}% de churners)" for n in L.index], fontsize=9, color=INK)
for i in range(K):
    for j in range(len(SIG)):
        val = L.iat[i, j]
        ax.text(j, i, f"{val:.0f}", ha="center", va="center", fontsize=7.5, color="white" if val > 60 else INK)
ax.tick_params(length=0)
for sp in ax.spines.values():
    sp.set_visible(False)
fig.colorbar(im, ax=ax, shrink=0.8).set_label("% en el peor bin", color=MUTED)
ax.set_title("Arquetipos de churners · desarrollo [DATA-SINT]", loc="left", color=INK, fontsize=10)
fig.tight_layout()
fig.savefig(FIGURES / "16_archetypes.png", dpi=140)

print(sel.round(3).to_string(index=False))
print(dim_lift.round(3).to_string())
print(names)
print(arch.iloc[:, :7].round(2).to_string(index=False))
print(mix.to_string(index=False))
print(tx.to_string(index=False))
print(det.round(1).to_string(index=False))
qc.gate()
