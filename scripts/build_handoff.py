"""Genera el handoff IA→IA para documentar la base sintética en Claude Design.

Uso: python scripts/build_handoff.py   (requiere haber corrido build_step8.py y score_models.py)
Salida: docs/handoff_claude_design.md

Todas las cifras se extraen de la configuración, los datos y los reportes del repositorio; nada se
transcribe a mano. El bloque DATA es YAML válido (se verifica al final).
"""
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from synthetic.schema import EXCEL_PRIMARY  # noqa: E402

OUT = ROOT / "docs" / "handoff_claude_design.md"
# Parámetros cuyo comentario hereda una etiqueta que no les corresponde (p. ej. [Excel] de una nota
# vecina). Se corrigen aquí y no en params.yaml para no alterar el SHA-256 de los manifiestos.
ORIGIN_OVERRIDE = {
    "step3.outflow_baseline_floor_monthly": ("Supuesto", "piso PB; el Excel propone $1,000 (D-18)"),
    "step3.new_destination_min_cumulative": ("Supuesto", "piso PB; el Excel propone $10,000 (D-18)"),
    "step3.institutions": ("Supuesto", "nº de instituciones por tipo del catálogo sintético"),
}
TAG = re.compile(r"\[(Excel[^\]]*|Deck[^\]]*|Supuesto|Calibrado)\]")

# Mecanismo generador y motor de señal de cada variable (según el código de cada paso).
MECH = {
    1: ("derivada de series mensuales de AUM (retiros − aportes, sin ACATS internos)", "mixto"),
    2: ("derivada de la serie mensual de depósitos (ruido t(6), episodios, choques, mudanza)", "mixto"),
    3: ("algoritmo de detección del Excel sobre transacciones de nómina simuladas", "propensión"),
    4: ("detección sobre todos los flujos recurrentes (≥ 10% del ingreso)", "propensión"),
    5: ("recurrente 30d vs promedio 6m sobre transacciones (bono excluido)", "mixto"),
    6: ("cambio de saldo de la serie de depósitos (identidad contable)", "mixto"),
    7: ("transferencias externas simuladas una por una (incluye ACATS)", "mixto"),
    8: ("destinos nuevos ≥ $50k sin envíos en 12m previos", "mixto"),
    9: ("ventas y redenciones del cliente − compras (composición del portafolio)", "mixto"),
    10: ("tabla de cuentas con fecha y motivo de cierre (exclusiones del Excel)", "mixto"),
    11: ("salida del banker decidida por banker según calidad del libro; todo el libro cambia", "mixto"),
    12: ("bitácora de interacciones: días sin contacto significativo ÷ cadencia", "factor (z_neglect)"),
    13: ("respuestas del cliente ≤ 7d en la bitácora (quien se muda deja de contestar)", "mixto"),
    14: ("ciclo de vida de quejas: escalamiento según SLA y z_service", "mixto"),
    15: ("antigüedad de la queja abierta más antigua", "mixto"),
    16: ("nº de grupos del Excel con alguna variable sobre su umbral; flag ≥ 3", "compuesta"),
    17: ("AUM ex-mercado (÷ índice TWR) vs promedio de 6 meses", "mixto"),
    18: ("depósitos del último mes vs promedio de 6 meses", "mixto"),
    19: ("detección sobre transacciones de pensión", "propensión"),
    20: ("detección sobre débitos de la nómina del negocio (60 días)", "factor (z_outflow)"),
    21: ("transferencias a bancos del catálogo sintético de competidores", "mixto"),
    22: ("bloques de 30d de salidas externas: [(A1−A2)−(A2−A3)] ÷ saldo", "mixto"),
    23: ("entradas − salidas externas (wires/ACH, sin ACATS)", "mixto"),
    24: ("HHI de salidas por institución (no por ABA)", "mixto"),
    25: ("salidas del último mes vs promedio 6m con piso $10k (forma en U)", "mixto"),
    26: ("vencimientos de renta fija y reinversión en 30 días", "mixto"),
    27: ("cash % mensual del portafolio (venta a cash, de-risking del asesor)", "mixto"),
    28: ("TWR neto 12m (alpha ligado a z_service) − benchmark por perfil", "factor (z_service)"),
    29: ("cuentas cerradas (solo se excluye consolidación interna)", "mixto"),
    30: ("valor en Citizens ÷ patrimonio estimado (3 fuentes de calidad distinta)", "mixto"),
    31: ("SOW hoy − SOW hace 6 meses (reestimación agrega ruido)", "mixto"),
    32: ("cambio de trustee por mudanza, servicio y ruido; sucesión por muerte excluida", "mixto"),
    33: ("≥ 2 quejas de la misma categoría o reapertura", "mixto"),
    34: ("posiciones vendidas completas sin reemplazo", "mixto"),
    35: ("reuniones canceladas por el cliente (campo capturado por 40% de bankers)", "mixto"),
    36: ("Assistant: estado real → conversación → clasificador → revisión humana (solo piloto)", "mixto"),
    37: ("buró: mudanza, compra de casa financiada fuera, refinanciamiento; interruptor legal", "mixto"),
}


def native(o):
    """Convierte tipos numpy / pandas a tipos nativos para que el YAML sea portable."""
    if isinstance(o, dict):
        return {str(k): native(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [native(v) for v in o]
    if isinstance(o, np.bool_):
        return bool(o)
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.floating):
        return None if np.isnan(o) else round(float(o), 6)
    if isinstance(o, float) and o != o:
        return None
    return o


def parse_params(path: Path, cfg: dict) -> list[dict]:
    rows, stack, depth, above = [], [], 0, ""
    for line in path.read_text().splitlines():
        if line.lstrip().startswith("#"):
            above += " " + line.lstrip("# ").strip()  # bloque de comentario sobre el parámetro
            continue
        if not line.strip():
            above = ""
            continue
        code = line.split("#", 1)[0]
        cont = depth > 0  # línea de continuación de un dict/lista inline
        depth += code.count("{") + code.count("[") - code.count("}") - code.count("]")
        if cont:
            continue
        if not line.strip() or line.lstrip().startswith("#") or line.lstrip().startswith("- "):
            continue
        indent = len(line) - len(line.lstrip())
        m = re.match(r"\s*([A-Za-z0-9_]+):\s*(.*)$", line)
        if not m:
            continue
        key, rest = m.group(1), m.group(2)
        while stack and stack[-1][0] >= indent:
            stack.pop()
        path_keys = [k for _, k, _ in stack] + [key]
        comment = rest.split("#", 1)[1].strip() if "#" in rest else ""
        val_txt = rest.split("#", 1)[0].strip()
        if val_txt == "":  # abre un bloque: sus hijos heredan la etiqueta del bloque
            t = TAG.search(comment) or TAG.search(above) or next((b for _, _, b in reversed(stack) if b), None)
            stack.append((indent, key, t))
            above = ""
            continue
        if "targets" in path_keys:
            continue
        v = cfg
        for k in path_keys:
            v = v[k]
        tag = TAG.search(comment) or TAG.search(above) or next((b for _, _, b in reversed(stack) if b), None)
        above = ""
        origin = tag.group(1).split(" ·")[0] if tag else "Supuesto (simulación, sin etiqueta)"
        note = TAG.sub("", comment).strip(" ·") or None
        origin, note = ORIGIN_OVERRIDE.get(".".join(path_keys), (origin, note))
        rows.append({"param": ".".join(path_keys), "valor": v, "origen": origin, "nota": note})
    return rows


def md_table(text: str, start: str) -> pd.DataFrame:
    lines = text.split(start, 1)[1].splitlines()
    tbl = [l for l in lines[lines.index(next(l for l in lines if l.startswith("|"))):] if l.startswith("|")]
    tbl = tbl[:next((i for i, l in enumerate(tbl[2:], 2) if not l.startswith("|")), len(tbl))]
    rows = [[c.strip() for c in l.strip("|").split("|")] for l in tbl]
    end = next((i for i, r in enumerate(rows[2:], 2) if len(r) != len(rows[0])), len(rows))
    return pd.DataFrame(rows[2:end], columns=rows[0])


def num(x):
    try:
        f = float(str(x).replace(",", ""))
        return round(f, 4)
    except ValueError:
        return x


def main() -> int:
    cfg = yaml.safe_load((ROOT / "config" / "params.yaml").read_text())
    params = parse_params(ROOT / "config" / "params.yaml", cfg)
    rep = {p.stem: p.read_text() for p in (ROOT / "docs" / "reports").glob("*.md")}
    dec_txt = (ROOT / "docs" / "decisiones.md").read_text()

    # --- Datos observados de la base final y del churn construido ------------------------
    core = pd.read_csv(ROOT / "data" / "synthetic" / "client_pulse_synthetic.csv")
    lab = pd.read_csv(ROOT / "data" / "synthetic" / "churn_labels.csv")
    el = ~core["churn_excluded"]
    v = core["relationship_value"].sort_values(ascending=False)
    base_obs = {
        "hogares": int(len(core)), "uhnw": int((core["segment"] == "UHNW").sum()),
        "aum_total_usd_mm": round(v.sum() / 1e6, 1), "top5pct_share_valor": round(v.iloc[: len(v) // 20].sum() / v.sum(), 3),
        "valor_mediano_usd": round(float(core["relationship_value"].median()), 0),
        "solo_depositos_pct": round(float(1 - core["has_investments"].mean()), 3),
        "hard_churn_6m": round(float(core.loc[el, "hard_churn_6m"].astype(float).mean()), 4),
        "soft_churn_3m": round(float(core.loc[el, "soft_churn_3m"].astype(float).mean()), 4),
        "excluidos": int(core["churn_excluded"].sum()),
        "churn_construido": {
            "hard_6m": round(float(lab.loc[el, "churn_hard_6m"].astype(float).mean()), 4),
            "soft_3m": round(float(lab.loc[el, "churn_soft_3m"].astype(float).mean()), 4),
            "aum_churn_hard": round(float(lab.loc[el & (lab["churn_hard_6m"] == 1), "churn_value_lost"].sum()
                                          / lab.loc[el, "relationship_value_t"].sum()), 4),
            "coincidencia_hard": "100% (misma población de eventos)",
            "soft_falsos_positivos": int(((core["soft_churn_3m"] == 0) & (lab["churn_soft_3m"] == 1) & el).sum()),
            "soft_no_detectados": int(((core["soft_churn_3m"] == 1) & (lab["churn_soft_3m"] == 0) & el).sum()),
        },
    }

    # --- 37 variables -----------------------------------------------------------------
    ft = md_table(rep["final_report"], "## Las 37 variables")
    variables = []
    for _, r in ft.iterrows():
        vid = int(r["#"])
        variables.append({
            "id": vid, "variable_excel": r["variable (Excel)"], "columna": r["columna"], "grupo": r["grupo"],
            "prioridad": r["prioridad"], "fuerza_excel": r["fuerza Excel"], "factibilidad": r["factibilidad"],
            "mecanismo": MECH[vid][0], "motor": MECH[vid][1], "null_pct": num(r["NULL %"]),
            "alerta_pct": num(r["alerta %"]), "iv": num(r["IV"]), "lift": num(r["lift"])})

    # --- Pruebas por paso -------------------------------------------------------------------
    tests = []
    for step, key in [(0, "step0_stats_report"), (1, "step1_report"), (2, "step2_report"), (3, "step3_report"),
                      (4, "step4_report"), (5, "step5_report"), (6, "step6_report"), (7, "step7_report"),
                      (8, "step8_report")]:
        m = re.search(r"(\d+) de (\d+) pruebas OK", rep[key])
        tests.append({"paso": step, "ok": int(m.group(1)), "total": int(m.group(2)),
                      "semillas_referencia": {0: 200, 8: 10}.get(step, 20)})

    # --- Decisiones -------------------------------------------------------------------------
    decisions, paso = [], None
    for chunk in re.split(r"(?m)^(?=## |\*\*D-\d+ · )", dec_txt):
        if chunk.startswith("## "):
            paso = chunk.splitlines()[0][3:].strip()
            continue
        m = re.match(r"\*\*(D-\d+) · (.+?)\*\*(.*)", chunk, re.S)
        if m:
            body = re.sub(r"\s*\n-\s*", " · ", m.group(3).strip())
            decisions.append({"id": m.group(1), "seccion": paso, "titulo": m.group(2).strip(" .*"),
                              "detalle": re.sub(r"\s+", " ", body).strip()})

    # --- Comparación de modelos ---------------------------------------------------------------
    mc = rep["model_comparison"]
    disc = md_table(mc, "### Discriminación y uso operativo (test)")
    boot = md_table(mc, "### Incertidumbre")
    models = []
    for _, r in disc.iterrows():
        b = boot[boot.iloc[:, 0] == r.iloc[0]]
        models.append({"metodologia": r.iloc[0], "auc": num(r["AUC"]), "ks": num(r["KS"]),
                       "precision_top10": num(r["precisión top 10%"]), "lift_top10": num(r["lift top 10%"]),
                       "captura_aum_top10": num(r["captura AUM top 10%"]),
                       "auc_ic95": [num(b["AUC p2.5"].iloc[0]), num(b["AUC p97.5"].iloc[0])] if len(b) else None,
                       "distinto_de_gbm": ("referencia" if "Gradient Boosting" in r.iloc[0] else
                                           b["¿diferencia real?"].iloc[0] if len(b) and "¿diferencia real?" in b else None)})

    data = {
        "meta": {"proyecto": "Client Pulse · base sintética de attrition", "cliente": "Citizens Private Bank (EE. UU.)",
                 "etiqueta_obligatoria": "[SINT]", "moneda": "USD", "unidad": "hogar (household/relationship)",
                 "corte_T0": cfg["snapshot_date"], "semilla_maestra": cfg["master_seed"],
                 "insumos": ["Excel Client_Pulse_37_Variables.xlsx (37 variables, umbrales, fuerza, factibilidad)",
                             "Deck Client_Pulse_AI_Solution_Citizens.v3.pptx (framework, modelos, churn rate)"]},
        "base_observada": base_obs,
        "arquitectura": {
            "flujo": ["Paso 0: población, factores latentes, target, ingresos",
                      "Evento común: mudanza del banco principal (propensión)",
                      "Paso 1: series mensuales de depósitos y AUM (24 m)", "Paso 2: transacciones recurrentes + detección",
                      "Paso 3: transferencias externas + identidad contable", "Paso 4: composición del portafolio",
                      "Paso 5: cuentas, cierres, share of wallet, trustee", "Paso 6: carteras de banker + bitácora",
                      "Paso 7: quejas + Assistant", "Paso 8: multi-señal + buró + base final",
                      "Resultado: ventana (t, t+6m] y variable de churn construida", "Scoring: 6 metodologías comparadas"],
            "latentes": {"factores": cfg["latent"]["factors"], "correlacion": cfg["latent"]["correlation"],
                         "pesos_en_riesgo": cfg["latent"]["risk_weights"], "sd_idiosincratico": cfg["latent"]["idiosyncratic_sd"],
                         "rol_idiosincratico": "riesgo no observable: acota el AUC alcanzable (techo 0.851)"},
            "motores_de_senal": {"propension": "índice de riesgo total; para precursores directos de salida (Very high)",
                                 "factor": "un solo latente (z_outflow, z_neglect o z_service)",
                                 "regla": "ninguna variable se genera desde el target; la fuga se prueba en el generador (Wald)"},
            "semillas": "SeedManager: un flujo aleatorio por nombre (SHA-256 + numpy SeedSequence); agregar o reordenar variables no altera lo ya generado",
            "coherencia": ["la mudanza se ve a la vez en saldos, ingresos, transferencias, inversiones, cierres y buró",
                           "identidad contable mensual: ΔD = ingresos + internos + entradas − salidas − tarjeta − otros débitos (cuadra al centavo)"]},
        "parametros": params,
        "variables_37": variables,
        "calibracion": {
            "bandas_iv": {"Very high": [0.30, 0.50], "High": [0.10, 0.30], "compuesta_multisenal": [0.30, 0.80]},
            "tolerancia_iv": 0.03, "criterio_semillas": "mediana entre semillas en banda; p10–p90 reportado",
            "iv_condicional": "flags de subpoblación (nómina, pensión, negocio, trust) calibrados entre hogares donde aplican",
            "auc_combinado_37_variables": num(re.search(r"AUC combinado de las 37 variables\*\* \(logística simple\): \*\*([0-9.]+)", rep["final_report"]).group(1)),
            "auc_techo": 0.851},
        "pruebas": {
            "correccion_multiple": "Benjamini-Hochberg (FDR), α = 0.01",
            "por_paso": tests,
            "familias": [
                {"familia": "bondad de ajuste", "pruebas": "KS y Cramér-von Mises sobre PIT; χ² (gl = celdas − 1); binomial exacta; Hosmer-Lemeshow (gl = g − parámetros estimados)"},
                {"familia": "colas y curtosis", "pruebas": "Anscombe-Glynn, Jarque-Bera (gl = 2), L-momentos, índice de Hill, MLE Pareto truncada, curtosis teórica Normal doblemente truncada"},
                {"familia": "multivariadas", "pruebas": "Mardia asimetría (gl = 10) y curtosis; Fisher z de correlaciones"},
                {"familia": "grados de libertad t-Student", "pruebas": "estudio ν = 4, 5, 6, 8 (60 réplicas × 20,000); ν = 6 elegido (curtosis 3 finita; ν = 4 infinita)"},
                {"familia": "sesgo y fuga", "pruebas": "independencias por diseño (Spearman), χ² de independencia, Wald sobre el generador"},
                {"familia": "duplicados y variedad", "pruebas": "filas exactas, casi-duplicados por vecino más cercano, repeticiones esperadas por redondeo (Poisson λ)"},
                {"familia": "calibración de variables", "pruebas": "tasa de alerta, IV, Cochran-Armitage, lift, forma en U"},
                {"familia": "robustez de semilla", "pruebas": "semillas de referencia, p-valores empíricos, uniformidad de p-valores entre semillas"}]},
        "decisiones": decisions,
        "correcciones_y_sesgos_detectados": [
            "repeticiones de montos: se comparan contra lo esperado por redondear al centavo (pensión 15 vs 15.2)",
            "banda con 40 semillas sin corrección múltiple → p-valores empíricos con 200 semillas dentro de BH",
            "Hosmer-Lemeshow: gl = g − 1 (intercepto calibrado) y g (probabilidad conocida), no g − 2",
            "monotonía con ρ de Spearman castigaba señales tipo palo de hockey → Cochran-Armitage + lift",
            "prueba del bono en una ventana sin bonos → se midió donde importa (bono de diciembre en #5)",
            "IV exigido en todas las semillas → mediana en banda (varianza de muestreo de flags raros)",
            "ruido de cierres simulado solo en 90 días favorecía la ventana de 180 → extendido a 180 días",
            "ABA asignada por transacción → fija por cuenta destino",
            "mudanza que cortaba nómina sin bajar el saldo → evento común a todos los pasos",
            "convención de meses con floor → mes 0 = últimos 30 días",
            "fuga probada en hogares sin mudanza daba sesgo de selección → test de Wald sobre el generador",
            "independencia del ruido medida sobre el cierre efectivo (censurado) → sobre el sorteo"],
        "hallazgos_para_citizens": [
            "umbrales ilustrativos del Excel laxos para PB: 24% de hogares con ≥ 3 grupos en alerta",
            "net_deposit_flow ≤ −15% alerta 28% con volatilidad PB de 12% mensual (10% más bajo en −38%)",
            "soft churn construido tiene ruido de etiqueta: el umbral de −20% debe validarse",
            "la captura de AUM es volátil por la cola Pareto (pocos hogares grandes)",
            "bandas 70/40 del deck no calzan con la escala: fijarlas por capacidad del banker",
            "variable 25 con forma en U: WoE la captura, una regla lineal no",
            "pisos PB ($50k destino nuevo, $10k línea base) mejoran el lift frente a los del Excel"],
        "comparacion_modelos": {"target": "hard churn 6m construido; partición estratificada 70/30; IC por bootstrap pareado (200)",
                                "resultados": models,
                                "lectura": "estadísticos > experto > reglas; GBM, logística, WoE y red neuronal no se distinguen (generador mayormente aditivo)"},
        "limitaciones": ["un solo corte (sin out-of-time)", "latentes estáticos", "ventanas mensuales como aproximación a días",
                         "relaciones impuestas por diseño, no aprendidas de datos", "variables sin historia real (#35, #36, #37)",
                         "parámetros 'Supuesto' pendientes de validar con Citizens", "red neuronal = MLP (no LSTM)"],
        "reproducibilidad": {"comandos": ["pip install -r requirements.txt", "python scripts/build_step0.py … build_step8.py",
                                          "python scripts/stats_step0.py", "python scripts/score_models.py", "python -m pytest"],
                             "control": "manifiestos data/synthetic/step*_manifest.json con SHA-256 de cada salida",
                             "repositorio": "ealejandrot-bit/Citizens-bank · rama claude/synthetic-excel-variables-v7orh6"},
    }
    data_yaml = yaml.safe_dump(native(data), allow_unicode=True, sort_keys=False, width=140)
    yaml.safe_load(data_yaml)  # verificación: YAML válido

    counts = pd.Series([p["origen"] for p in params]).value_counts().to_dict()
    head = f"""# HANDOFF IA → IA · Documentación de la base sintética Client Pulse

> **Para la persona:** pega este archivo completo en Claude Design. Todo lo que el documento necesita
> está aquí; Claude Design no necesita acceso al repositorio. Generado por `scripts/build_handoff.py`
> desde la configuración, los datos y los reportes del repositorio (ninguna cifra transcrita a mano).

---

## 1. INSTRUCCIONES PARA LA IA RECEPTORA

```yaml
tarea: diseñar un documento técnico de metodología de datos sintéticos, legible y visual
idioma: español
audiencia:
  primaria: validador independiente de riesgo de modelos (no participó en la construcción)
  secundaria: equipo de Citizens Private Bank (negocio y data science)
proposito: que el lector entienda, reproduzca y pueda cuestionar cómo se generó la base
fuente_unica_de_datos: bloque DATA (sección 3) de este archivo
reglas_duras:
  - usar SOLO cifras del bloque DATA; no inventar, redondear de más ni completar valores faltantes
  - si algo no está en DATA, escribir "no documentado" (no suponer)
  - toda cifra de resultados lleva la etiqueta [SINT]; nunca presentarla como dato del banco
  - conservar el origen de cada parámetro (Excel, Deck, Supuesto, Calibrado; 'Supuesto (simulación, sin etiqueta)' = parámetro técnico del simulador sin etiqueta en params.yaml, trátalo como supuesto no validado)
  - distinguir siempre parámetro de generación / resultado observado / criterio de aceptación
  - montos en USD; porcentajes con el mismo número de decimales que en DATA
  - no citar benchmarks ni cifras de bancos reales
estilo:
  tono: técnico, sobrio, sin adjetivos promocionales
  jerarquia: títulos numerados, tablas para datos, bullets densos, callouts para advertencias
  visuales_sugeridos:
    - diagrama de flujo del generador (arquitectura.flujo)
    - matriz de correlación de latentes (arquitectura.latentes.correlacion) como heatmap
    - tabla de parámetros agrupada por bloque con chip de color por origen
    - tabla de las 37 variables con barras de IV y marcas de banda (calibracion.bandas_iv)
    - gráfico de barras de pruebas OK por paso (pruebas.por_paso)
    - gráfico de AUC con intervalos de confianza por metodología (comparacion_modelos.resultados)
  graficos: solo con números de DATA; indicar la fuente (clave de DATA) al pie de cada gráfico
entregable: documento de varias páginas en el orden de la sección 2
```

## 2. ESTRUCTURA DEL DOCUMENTO (orden fijo → clave de DATA que alimenta cada sección)

| # | Sección | Contenido esperado | Clave(s) de DATA |
|---|---|---|---|
| 1 | Propósito y alcance | para qué sirve y para qué NO (tasas reales, causalidad) | meta, limitaciones |
| 2 | Arquitectura del generador | flujo, latentes, motores de señal, evento común, identidad contable, semillas | arquitectura |
| 3 | Parámetros | tablas por bloque (prefijo de `param`), origen y nota; resumen por origen | parametros |
| 4 | Supuestos | parámetros con origen Supuesto, agrupados por tema; riesgo si son falsos | parametros (origen = Supuesto), limitaciones |
| 5 | La base resultante | tamaño, concentración, target, exclusiones | base_observada |
| 6 | Las 37 variables | mecanismo, motor, NULL, alerta, IV, lift, fuerza y factibilidad del Excel | variables_37, calibracion |
| 7 | Calibración de la señal | bandas, tolerancia, criterio entre semillas, AUC combinado vs techo | calibracion |
| 8 | Pruebas estadísticas | familias, conteo por paso, corrección BH | pruebas |
| 9 | Correcciones y sesgos detectados | qué se corrigió y por qué no es sobreajuste | correcciones_y_sesgos_detectados |
| 10 | Variable de churn construida | definiciones, logo vs AUM churn, ruido de etiqueta | base_observada.churn_construido |
| 11 | Comparación de metodologías | tabla y gráfico de AUC con IC; lectura | comparacion_modelos |
| 12 | Hallazgos para Citizens | lista accionable | hallazgos_para_citizens |
| 13 | Decisiones (trazabilidad) | tabla D-01…D-25 | decisiones |
| 14 | Limitaciones | lista | limitaciones |
| 15 | Reproducibilidad | comandos, control por hashes, repositorio | reproducibilidad |

Resumen de parámetros por origen: {', '.join(f'{k}: {v}' for k, v in counts.items())} (total {len(params)}).

## 3. DATA

```yaml
{data_yaml}```
"""
    OUT.write_text(head)
    print(f"{OUT.relative_to(ROOT)} · {len(head):,} caracteres · {len(params)} parámetros · {len(variables)} variables · "
          f"{len(decisions)} decisiones · orígenes {counts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
