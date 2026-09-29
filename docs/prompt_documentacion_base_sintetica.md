# Prompt · Documentación técnica de la base sintética Client Pulse

Copia todo lo que está debajo de la línea y úsalo en una sesión con acceso al repositorio
`ealejandrot-bit/Citizens-bank`, rama `claude/synthetic-excel-variables-v7orh6`.

---

## ROL

Eres un **especialista en documentación de modelos y datos sintéticos** para banca privada, con
experiencia en Model Risk Management (SR 11-7 o equivalente), estadística aplicada y generación de
datos sintéticos. Tu tarea es producir la **documentación técnica completa y auditable** de cómo se
generó la base sintética Client Pulse: supuestos, distribuciones, parámetros, calibración, pruebas
estadísticas, decisiones y limitaciones. El lector es un **validador independiente** que no participó
en la construcción y que debe poder reproducir y cuestionar cada elección.

## FUENTES DE VERDAD (en este orden de prioridad)

1. **Código:** `synthetic/*.py` (generador, validaciones, pruebas) y `scripts/*.py` (construcción y reportes).
2. **Parámetros:** `config/params.yaml` (cada parámetro tiene un comentario con su origen:
   `[Excel]`, `[Deck]`, `[Supuesto]` o `[Calibrado]`) y `config/validation.yaml` (criterios de pruebas).
3. **Decisiones:** `docs/decisiones.md` (D-01 a D-25).
4. **Resultados:** `docs/reports/step0_report.md`, `step0_stats_report.md`, `step1_report.md` …
   `step8_report.md`, `final_report.md` y `model_comparison.md`.
5. **Insumos del cliente:** `docs/Client_Pulse_37_Variables.xlsx` (37 variables, umbrales, fuerza
   predictiva, factibilidad) y `data/catalog/variables_catalog.csv`.
6. **Diccionario y mapa:** `synthetic/schema.py` (unidades de cada columna y `EXCEL_PRIMARY`, que
   mapea las 37 variables del Excel a su columna principal).
7. **Reproducibilidad:** `data/synthetic/step*_manifest.json` (semilla, flujos de semilla, SHA-256).

Si una cifra de un reporte contradice el código o los parámetros, **manda el código**. Si puedes
ejecutar, regenera con `python scripts/build_step0.py … build_step8.py`, `python scripts/stats_step0.py`
y `python scripts/score_models.py`, y usa las cifras regeneradas.

## REGLAS (no negociables)

1. **Nada inventado.** Cada parámetro, distribución, cifra y resultado debe citar su fuente
   (archivo y, si aplica, clave o sección). Si algo no está en las fuentes, escribe
   "no documentado en el repositorio" y agrégalo a la lista de preguntas abiertas.
2. **Todo resultado es sintético:** etiqueta cada cifra con **[SINT]**. Nunca la presentes como dato del banco.
3. **Origen de cada parámetro:** clasifícalo siempre como `Excel`, `Deck`, `Supuesto` (pendiente de
   validar con Citizens) o `Calibrado` (ajustado para lograr una banda de IV o una tasa de alerta).
   Para los calibrados, indica el objetivo de calibración y el valor inicial si consta en `decisiones.md`.
4. **Distingue tres cosas:** parámetro de generación (lo que se fijó), resultado observado en la
   base (lo que salió) y criterio de aceptación (contra qué se probó).
5. **Consistencia aritmética:** los porcentajes de categorías suman 100%; las tasas de alerta, IV y
   eventos cuadran con los reportes. Si no cuadran, repórtalo, no lo corrijas en silencio.
6. **Transparencia sobre correcciones:** documenta explícitamente las pruebas que estaban mal
   planteadas y se corrigieron, los sesgos que se detectaron en el propio código y los criterios que se
   relajaron (por ejemplo, tolerancia ±0.03 a las bandas de IV), con la justificación que consta en
   `decisiones.md`. Un validador debe poder ver qué se ajustó para que las pruebas pasaran y por qué no
   es sobreajuste.
7. **Español, montos en USD**, tablas markdown, fórmulas en notación matemática, sin relleno.

## ESTRUCTURA DEL DOCUMENTO (orden fijo)

### 1. Propósito, alcance y uso previsto
- Para qué sirve la base (prototipar el score de attrition de Citizens Private Bank: scorecard, ML, red neuronal) y para qué **no** sirve (estimar tasas reales del banco, inferir causalidad).
- Unidad (hogar), tamaño (20,000), corte (T0 = 2025-12-31), moneda (USD), ventanas.

### 2. Arquitectura del generador
- Diagrama en texto del flujo: Paso 0 (población, factores latentes, target, ingresos) → evento común de mudanza del banco principal → Pasos 1–8 → base final → ventana de resultado y churn construido.
- **Factores latentes:** `z_outflow`, `z_neglect`, `z_service` (normal multivariada con su matriz de correlación), índice de riesgo, componente idiosincrático ε y su rol (acotar el AUC alcanzable).
- **Dos motores de señal** (D-14): "propensión" (índice de riesgo total, para precursores directos "Very high") y "factor" (un latente). Qué variables usan cada uno.
- **Evento común** (D-17): cómo la mudanza se ve de forma coherente en saldos, ingresos, transferencias, inversiones, cierres, buró.
- **Coherencia contable** (D-18): la identidad mensual del saldo que cuadra transferencias, ingresos y gasto.
- **Semillas** (D-01): `SeedManager`, un flujo por nombre (SHA-256 + `SeedSequence`), por qué agregar variables no altera lo ya generado, y la prueba que lo verifica.

### 3. Parámetros
- Una tabla por bloque de `config/params.yaml` (población, ingresos, latentes, target, distribuciones, exit_move, step1 … step8, outcome): **parámetro · valor · unidad · origen (Excel/Deck/Supuesto/Calibrado) · qué controla · efecto esperado si se mueve**.
- Resumen: cuántos parámetros hay por origen, y lista de los **Supuestos** que Citizens debe validar primero, ordenados por impacto en el target o en el IV.

### 4. Supuestos
- Supuestos de negocio (PB en EE. UU.: ingresos altos, pisos PB de $10k y $50k, volatilidad del saldo 12% mensual, volumen de quejas, etc.).
- Supuestos estadísticos (independencia condicional dado los latentes, forma de las colas, t(6), Pareto α = 1.5 con tope $1B, etc.).
- Supuestos de construcción (ventanas en meses como aproximación a días del Excel, convención de meses, un solo corte).
- Para cada uno: descripción, fuente, estado (validado / pendiente), riesgo si es falso.

### 5. Distribuciones
- **Atributos del Paso 0:** familia, parámetros, truncamientos, forma de los pisos (remuestreo, no recorte), dependencia con el patrimonio.
- **Las 37 variables:** una fila por variable con: # Excel · columna principal · familia generadora o mecanismo (hurdle, log-ratio t(6), Bernoulli-logit, conteo, derivada de series, detección sobre transacciones) · motor (propensión/factor/mixto) · regla de NULL · umbral de alerta del Excel · tasa de alerta observada · IV observado (semilla y mediana entre semillas) · lift.
- **Mecanismos de ruido** que imitan señal (choques de liquidez, cambios de empleo, de-risking del asesor, rebalanceos, conversiones, etc.) y por qué existen (IV realista, falsos positivos).
- **Series y transacciones:** qué se simula a nivel mensual (Paso 1) y a nivel transacción (Pasos 2, 3, 6, 7), volúmenes y calendario (días hábiles, feriados federales).

### 6. Target y variable de churn construida
- Target del Paso 0 (hard 6m 6%, soft 3m 9%, exclusiones) y cómo se calibra el intercepto.
- Ventana de resultado (t, t+6m] (`synthetic/outcome.py`): definiciones de hard y soft churn construidos, logo churn vs AUM churn, y la matriz de coincidencia etiqueta construida vs evento real (ruido de etiqueta en soft churn).

### 7. Pruebas estadísticas
- **Catálogo completo** por paso, en una tabla: prueba · hipótesis nula · estadístico · grados de libertad · criterio de aceptación · resultado [SINT]. Incluye como mínimo:
  - Bondad de ajuste: KS y Cramér-von Mises sobre la PIT, χ² (gl = celdas − 1), binomial exacta, Hosmer-Lemeshow (gl = g − parámetros estimados en la muestra; explica por qué g − 1 y g).
  - Colas y curtosis: Anscombe-Glynn, Jarque-Bera (gl = 2), L-momentos, índice de Hill, MLE de Pareto truncada, curtosis teórica de la Normal doblemente truncada.
  - Multivariadas: Mardia asimetría (gl = p(p+1)(p+2)/6) y curtosis; Fisher z para correlaciones.
  - Grados de libertad de la t-Student: el estudio de ν = 4, 5, 6, 8 y por qué se eligió ν = 6.
  - Sesgo y fuga: independencias por diseño (Spearman), χ² de independencia, tests de Wald sobre el generador (por qué se prueba el generador y no la variable filtrada: sesgo de selección).
  - Duplicados y variedad: filas exactas, casi-duplicados por vecino más cercano, repeticiones esperadas por redondeo (λ de la paradoja del cumpleaños).
  - Calibración de variables: tasa de alerta, IV, Cochran-Armitage, lift, forma en U de #25.
  - Robustez de la semilla: semillas de referencia (200 en el Paso 0; 20 en los Pasos 1–7; 10 en el 8), p-valores empíricos, uniformidad de p-valores entre semillas.
- **Corrección por pruebas múltiples:** Benjamini-Hochberg con α = 0.01; por qué no Bonferroni.
- **Conteo total** de pruebas por paso y su resultado.

### 8. Calibración de la señal
- Bandas de IV por fuerza del Excel ("Very high" 0.30–0.50, "High" 0.10–0.30), IV condicional para variables de subpoblación, tolerancia ±0.03 (desde el Paso 3) y su justificación.
- Criterio entre semillas: mediana en banda y p10–p90 reportado (D-16) en vez de "todas las semillas".
- AUC combinado por paso vs el techo (0.851) como control de que la base es predictiva sin ser irreal.

### 9. Correcciones, sesgos detectados y hallazgos
- Pruebas mal planteadas que se corrigieron (repeticiones por redondeo, banda con 40 semillas, monotonía con ρ, ventana del bono, flujo neto < −100%, bienvenida del banker, censura en conversiones, etc.).
- Sesgos detectados en el propio código (ruido de cierres solo en 90 días, ABA por transacción, convención de meses, mudanza sin reflejo en el saldo) y su corrección.
- Hallazgos útiles para Citizens (umbrales del Excel laxos para PB, ruido de etiqueta del soft churn, volatilidad de la captura de AUM, bandas 70/40 del deck).

### 10. Trazabilidad de decisiones
- Tabla D-01 … D-25: decisión · paso · motivo · alternativas descartadas · impacto en otros pasos.

### 11. Resultados de uso (resumen)
- Resumen de `docs/reports/model_comparison.md`: metodologías, AUC con IC por bootstrap pareado, calibración, y qué significa que no se distingan entre sí en esta base (generador mayormente aditivo).

### 12. Limitaciones
- Un solo corte (sin out-of-time), latentes estáticos, ventanas mensuales como aproximación, relaciones causales impuestas por el diseño (no aprendidas de datos), variables sin historia real (#35, #36, #37), dependencia de supuestos no validados.

### 13. Reproducibilidad
- Versiones de Python y librerías (`requirements.txt`), comandos exactos en orden, semilla maestra, tiempos aproximados, cómo verificar con los SHA-256 de los manifiestos y con `python -m pytest`.

### Anexos
- A. Diccionario de la base final (columna · unidad · descripción) desde `synthetic/schema.py`.
- B. Mapa Excel → columna principal (`EXCEL_PRIMARY`).
- C. Preguntas abiertas para Citizens (parámetros `Supuesto` de mayor impacto, datos que reemplazarían supuestos).

## ENTREGABLE

- Un solo documento markdown: `docs/documentacion_base_sintetica.md`, en el orden 1–13 + anexos.
- Antes de escribir: lista en 5 líneas cómo entendiste la tarea y cualquier contradicción que encuentres
  entre fuentes; luego escribe el documento completo sin esperar confirmación, salvo que falte una
  fuente clave.
- Al final del documento: sección "Verificación" con las cifras que regeneraste y las que tomaste de
  reportes sin regenerar, y cualquier inconsistencia encontrada.
