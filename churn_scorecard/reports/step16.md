# Paso 16 · Acción, arquetipos, EWS

## Objetivo
- Describir los tipos de churner (arquetipos) para diseñar acciones distintas por tramo y tipo, y definir las alertas.

## Método
- Eventos B de dev (1,871) [DATA] descritos por 18 señales pre-T0 en WoE (missing como categoría, sin imputar).
- K-means K = 2..6 (K = 2 como referencia); elección dentro de K ∈ (3, 4) (SPEC); regla previa: tamaño ≥ 10%, ARI bootstrap ≥ 0.80, mayor silhouette (D16.1). GMM como comparación.
  Eventos de val asignados sin reajuste. Perfiles descriptivos, nunca causales.
- Playbook con SLA del SPEC (Crítico ≤ 5, Alto ≤ 15 días hábiles) y control 12.5% en Alto [DEF G3-4].

## Código
- `src/step16_archetypes.py` · `tests/test_step16.py` · `step16_*.csv`, `outputs/model/step16_archetypes.pkl`.

## Resultados

### Selección de K [DATA]
|   K |   silhouette |   ARI bootstrap |   arquetipo mín % |    BIC GMM |   ARI K-means vs GMM | elegido   |
|----:|-------------:|----------------:|------------------:|-----------:|---------------------:|:----------|
|   2 |        0.331 |           0.988 |            20.257 | 56,924.658 |                0.728 |           |
|   3 |        0.134 |           0.968 |            19.401 | 23,389.430 |                0.292 | ◀         |
|   4 |        0.146 |           0.889 |             3.474 | 20,111.845 |                0.289 |           |
|   5 |        0.148 |           0.792 |             3.474 | 16,303.313 |                0.314 |           |
|   6 |        0.151 |           0.738 |             3.474 | 21,944.183 |                0.575 |           |

### Perfil de arquetipos [DATA]
|   arquetipo |   eventos dev |   % eventos dev |   eventos val |   % eventos val |   RV mediano $M |   % RV de eventos dev |   % UHNW |   % Crítico |   % Alto |   % Vigilancia |   % Estable | señales dominantes (z centroide)                                                                                                         | nombre                     |
|------------:|--------------:|----------------:|--------------:|----------------:|----------------:|----------------------:|---------:|------------:|---------:|---------------:|------------:|:-----------------------------------------------------------------------------------------------------------------------------------------|:---------------------------|
|           0 |           682 |            36.5 |           266 |            33.1 |             4.9 |                  35.1 |      5.9 |         6.2 |     49.6 |           43.7 |         0.6 | contact_gap_ratio_peer +0.81, contact_gap_ratio +0.80, client_reply_rate +0.46, return_vs_benchmark -0.01                                | relación desatendida       |
|           1 |           363 |            19.4 |           155 |            19.3 |             5.1 |                  22.0 |      7.7 |        69.1 |     30.6 |            0.3 |         0.0 | net_external_flow_pct_90d +1.73, transfer_to_competitor_bank_amount_90d +1.72, share_of_wallet_change +1.39, outflow_x_contact_gap +1.30 | salida activa a competidor |
|           2 |           826 |            44.1 |           382 |            47.6 |             4.7 |                  42.9 |      6.5 |         1.8 |     33.8 |           43.2 |        21.2 | business_payroll_stopped_flag -0.05, return_vs_benchmark -0.08, meetings_cancelled_by_client -0.12, repeat_complaint_flag -0.12          | desgaste silencioso        |

- Verificación: % eventos dev suma 100.0%; % eventos val suma 100.0% [DATA].

### Señales por arquetipo (medianas; flags en % con 1) [DATA]
| señal                                            |          0 |             1 |          2 |   todos los eventos |   no eventos (dev) |
|:-------------------------------------------------|-----------:|--------------:|-----------:|--------------------:|-------------------:|
| banker_change_6m_flag (% con 1)                  |     24.633 |        66.116 |     26.150 |              33.351 |             11.653 |
| client_reply_rate (mediana)                      |      0.333 |         0.333 |      0.667 |               0.571 |              0.667 |
| share_of_wallet (mediana)                        |      0.437 |         0.143 |      0.430 |               0.369 |              0.472 |
| contact_gap_ratio (mediana)                      |      0.844 |         0.733 |      0.156 |               0.422 |              0.256 |
| cash_pct_of_portfolio_chg (mediana)              |      0.005 |         0.023 |      0.005 |               0.007 |              0.004 |
| streams_stopped_count (mediana)                  |      0.000 |         1.000 |      0.000 |               0.000 |              0.000 |
| complaint_escalated_flag (% con 1)               |      9.677 |        26.446 |      7.990 |              12.186 |              4.186 |
| repeat_complaint_flag (% con 1)                  |      7.625 |        22.314 |      6.295 |               9.888 |              2.756 |
| transfer_to_competitor_bank_amount_90d (mediana) | 13,175.610 | 2,137,879.820 | 10,547.185 |          18,486.670 |         12,388.100 |
| net_external_flow_pct_90d (mediana)              |      0.085 |        -0.417 |      0.084 |               0.056 |              0.085 |
| return_vs_benchmark (mediana)                    |     -0.022 |        -0.030 |     -0.016 |              -0.022 |             -0.008 |
| fixed_income_maturity_not_reinvested (mediana)   |      0.431 |         1.000 |      0.187 |               0.515 |              0.000 |
| meetings_cancelled_by_client (mediana)           |      0.000 |         1.000 |      0.000 |               0.000 |              0.000 |

### Playbook tramo × arquetipo
| tramo      | arquetipo                  | responsable                    | SLA               | acción                                                                                                                                                      | cadencia               | control aleatorio                       |   eventos val en la celda |
|:-----------|:---------------------------|:-------------------------------|:------------------|:------------------------------------------------------------------------------------------------------------------------------------------------------------|:-----------------------|:----------------------------------------|--------------------------:|
| Crítico    | relación desatendida       | banquero + líder de equipo     | ≤ 5 días hábiles  | reactivar la relación: reunión del banquero, revisión de necesidades y plan de contacto (brecha de contacto 0.84 vs 0.26 de no eventos; respuesta 0.33)     | semanal hasta resolver | —                                       |                        17 |
| Crítico    | salida activa a competidor | banquero + líder de equipo     | ≤ 5 días hábiles  | retención inmediata: líder + banquero, entender el destino de las transferencias, atender la queja y el cambio de banquero, propuesta de reinversión        | semanal hasta resolver | —                                       |                       112 |
| Crítico    | desgaste silencioso        | banquero + líder de equipo     | ≤ 5 días hábiles  | revisión proactiva ligera: revisión de portafolio y rendimiento vs referencia, contacto dentro del ciclo; las señales se parecen a las de quienes se quedan | semanal hasta resolver | —                                       |                        10 |
| Alto       | relación desatendida       | banquero                       | ≤ 15 días hábiles | reactivar la relación: reunión del banquero, revisión de necesidades y plan de contacto (brecha de contacto 0.84 vs 0.26 de no eventos; respuesta 0.33)     | quincenal              | 12.5% sin contacto adicional [DEF G3-4] |                       129 |
| Alto       | salida activa a competidor | banquero                       | ≤ 15 días hábiles | retención inmediata: líder + banquero, entender el destino de las transferencias, atender la queja y el cambio de banquero, propuesta de reinversión        | quincenal              | 12.5% sin contacto adicional [DEF G3-4] |                        42 |
| Alto       | desgaste silencioso        | banquero                       | ≤ 15 días hábiles | revisión proactiva ligera: revisión de portafolio y rendimiento vs referencia, contacto dentro del ciclo; las señales se parecen a las de quienes se quedan | quincenal              | 12.5% sin contacto adicional [DEF G3-4] |                       117 |
| Vigilancia | relación desatendida       | banquero (revisión de cartera) | revisión mensual  | reactivar la relación: reunión del banquero, revisión de necesidades y plan de contacto (brecha de contacto 0.84 vs 0.26 de no eventos; respuesta 0.33)     | mensual                | —                                       |                       120 |
| Vigilancia | salida activa a competidor | banquero (revisión de cartera) | revisión mensual  | retención inmediata: líder + banquero, entender el destino de las transferencias, atender la queja y el cambio de banquero, propuesta de reinversión        | mensual                | —                                       |                         1 |
| Vigilancia | desgaste silencioso        | banquero (revisión de cartera) | revisión mensual  | revisión proactiva ligera: revisión de portafolio y rendimiento vs referencia, contacto dentro del ciclo; las señales se parecen a las de quienes se quedan | mensual                | —                                       |                       160 |

### EWS
| disparador             | regla                                                                             | acción                                                   | evaluable hoy                 |
|:-----------------------|:----------------------------------------------------------------------------------|:---------------------------------------------------------|:------------------------------|
| Entrada a Crítico      | score ≤ 445 en el refresco                                                        | alerta al banquero y líder; SLA 5 días hábiles           | sí (con el snapshot)          |
| Entrada a Alto         | 445 < score ≤ 517, o override activo                                              | alerta al banquero; SLA 15 días hábiles; 12.5% a control | sí (con el snapshot)          |
| Override               | cambio de banquero, queja escalada o transferencia a competidor ≥ 10%             | sube a Alto aunque el score no lo indique                | sí (con el snapshot)          |
| Migración              | caída ≥ 40 puntos (1 PDO = odds ×2) entre refrescos mensuales, o baja de 2 tramos | alerta de deterioro aunque no llegue a Alto              | no: requiere 2 snapshots (L1) |
| Salida de Crítico/Alto | 2 refrescos seguidos en tramo inferior                                            | cierre del caso                                          | no: requiere 2 snapshots (L1) |

## Tests
- `tests/test_step16.py` (ver pytest).

## Decisiones y preguntas abiertas
- D16.1–D16.2 en `reports/decision_log.md`.
