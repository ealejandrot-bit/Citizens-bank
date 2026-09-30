Dataset sintético, corte transversal: valida pipeline y metodología, no conclusiones sobre clientes reales.

# Paquete MRM · Client Pulse · Modelo 3 (NAM monótono)

## Limitaciones (SPEC §8)
L1 sin OOT ni cohortes (un snapshot); L2 señales pre-ingenierizadas sin timestamps; L3 compuestos sin regla documentada;
L4 dataset sintético; L5 UHNW pequeño (≈ 53 eventos B en test); L6 test ya mirado por M1 y M2 (tercera mirada).

## Decisión del gate (fase 10, única apertura del test)
| clave | valor |
|:--|:--|
| test abierto (UTC) | 2026-09-30 00:27 |
| gate | NAM vs A-lite · target A · test ∩ holdout A-lite |
| hogares | 1764 |
| eventos A | 106 |
| ΔPR-AUC | 0.04348 |
| ΔPR-AUC IC95 | [0.003077538820395653, 0.0895664044582207] |
| Δlift@5% | 0.5673 |
| Δlift@5% IC95 | [-0.6738441086342607, 1.6364566115702477] |
| criterios | {"ΔPR-AUC ≥ 0.03": true, "IC95 ΔPR-AUC inf > 0": true, "Δlift@5% ≥ 0.25": true, "IC95 Δlift@5% inf > 0": false, "violaciones de monotonía = 0": true} |
| UHNW (solo reportado) | {"eventos": 7, "ΔPR-AUC": -0.026724087932527868, "IC95": [-0.3134257947609951, 0.1726923867292358]} |
| decisión | NAM no reemplaza a A-lite: queda documentado como challenger |
| nota | NAM sin convergencia completa (8 de 10 miembros en epochs_max); decisión del usuario (c): ir al gate con el NAM actual |

## Todos los métodos en el mismo subconjunto (target A, test ∩ holdout A-lite)
| modelo | hogares | eventos | PR-AUC | lift@5% | AUC |
|:--|:--|:--|:--|:--|:--|
| M2 EBM (target B) | 1764 | 106 | 0.2091 | 5.295 | 0.716 |
| LightGBM | 1764 | 106 | 0.2083 | 4.728 | 0.7139 |
| EBM monótono (champion) | 1764 | 106 | 0.1991 | 5.295 | 0.7066 |
| XGBoost | 1764 | 106 | 0.1985 | 5.106 | 0.7151 |
| logística L2 | 1764 | 106 | 0.1975 | 5.106 | 0.717 |
| NAM monótono | 1764 | 106 | 0.1968 | 4.728 | 0.7131 |
| LightGBM monótono | 1764 | 106 | 0.1939 | 4.728 | 0.7045 |
| M1 scorecard (target B) | 1764 | 106 | 0.1906 | 4.728 | 0.7141 |
| A-lite (congelado, target A) | 1764 | 106 | 0.1534 | 4.16 | 0.6916 |

## Calibración (fase 11)
| modelo | elegido | ECE test sin calibrar (pp) | ECE test calibrado (pp) |
|:--|:--|:--|:--|
| EBM monótono (champion) | isotonic | 0.5629 | 1.184 |
| NAM monótono (challenger) | platt | 1.401 | 0.8103 |
| A-lite (congelado) | platt | 1.224 | 1.316 |

## Scorecard (fase 12)
| modelo | filas lookup compacto | % recortados | residual completeness: media |r| | corr(score exacto, lookup) |
|:--|:--|:--|:--|:--|
| EBM | 491 | 0 | 1.485 | 0.9993 |
| NAM | 445 | 0.01541 | 2.454 | 0.9974 |

## EWS (fase 13, alertas por mes = marcados ÷ 6)
| modelo | hogares marcados | alertas por mes (muestra) | churners capturados | captura % | churners por 100 alertas | captura RV de churners % |
|:--|:--|:--|:--|:--|:--|:--|
| EBM (champion) | 88 | 14.67 | 28 | 26.42 | 31.82 | 22.26 |
| NAM (challenger) | 88 | 14.67 | 25 | 23.58 | 28.41 | 21.58 |
| A-lite (congelado) | 88 | 14.67 | 22 | 20.75 | 25 | 18.42 |

- Umbral: no definido (ews.alerts_per_month en null): se entrega la curva completa en outputs/p13/ews_curve.csv.

## Preguntas centrales (SPEC §9)
1. **¿El NAM monótono supera al champion interpretable lo suficiente para justificar su complejidad?** No. En el gate pre-registrado (NAM vs A-lite, target A, 1,764 hogares, 106 eventos), el NAM mejora la PR-AUC en +0.043 (IC95 +0.003 a +0.090) y el lift@5% en +0.57 (IC95 -0.67 a +1.64); el segundo IC incluye 0 ⟹ NAM no reemplaza a A-lite: queda documentado como challenger. Frente al champion EBM el NAM empata (ver gate_bootstrap.csv) y su scorecard requiere binning (residual medio 2.5 puntos vs 1.5 del EBM).
2. **¿Cuántos churners (y cuánto RV) captura el EWS por cada 100 alertas?** Con el 5% de hogares marcados (subconjunto justo, EBM (champion): 31.8 churners por 100 alertas, captura 26.4% de los churners y 22.3% de su RV, NAM (challenger): 28.4 churners por 100 alertas, captura 23.6% de los churners y 21.6% de su RV, A-lite (congelado): 25.0 churners por 100 alertas, captura 20.8% de los churners y 18.4% de su RV). En todo el test, el EBM al 5% equivale a 162 alertas/mes en la cartera con 30.8 churners por 100 alertas.
3. **¿El modelo supera a la regla multi-señal reconstruida con los flags visibles?** Sí. La regla Σ flags visibles ≥ 2 marca 393 hogares del test con 97 churners (precisión 24.7%); al mismo volumen el EBM captura 104 (precisión 26.5%) y el NAM 101 (precisión 25.7%). Margen pequeño y sin IC: la regla simple de flags visibles captura casi lo mismo que el modelo a ese volumen.

_Todas las cifras provienen de outputs/p10–p13 (generado por src/p13_ews_mrm.py)._
