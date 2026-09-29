| modelo   | criterio                                                                                                 | umbral   | observado            | cumple   |
|:---------|:---------------------------------------------------------------------------------------------------------|:---------|:---------------------|:---------|
| A        | C1 · supera a multi_signal_count y multi_signal_flag en AUC y captura decil top (IC sin traslape) [GATE] | sí       | no                   | NO       |
| A        | C2 · AUC holdout: límite inferior IC95 > 0.65                                                            | > 0.65   | 0.696                | sí       |
| A        | C3 · KS ≥ 0.25                                                                                           | ≥ 0.25   | 0.329                | sí       |
| A        | C4 · captura de eventos en decil top ≥ 30% (3× azar)                                                     | ≥ 30%    | 37.7%                | sí       |
| A        | C5 · captura de valor (RV) en decil top ≥ 25%                                                            | ≥ 25%    | 35.8%                | sí       |
| A        | C6 · tasa por decil monótona (Spearman decil vs tasa ≤ −0.90)                                            | ≤ −0.90  | -0.915               | sí       |
| A        | C7 · UHNW: AUC ≥ 0.60 (informativo, 24 eventos)                                                          | ≥ 0.60   | 0.716 [0.626, 0.821] | sí       |
| A-lite   | C1 · supera a multi_signal_count y multi_signal_flag en AUC y captura decil top (IC sin traslape) [GATE] | sí       | no                   | NO       |
| A-lite   | C2 · AUC holdout: límite inferior IC95 > 0.65                                                            | > 0.65   | 0.680                | sí       |
| A-lite   | C3 · KS ≥ 0.25                                                                                           | ≥ 0.25   | 0.305                | sí       |
| A-lite   | C4 · captura de eventos en decil top ≥ 30% (3× azar)                                                     | ≥ 30%    | 37.3%                | sí       |
| A-lite   | C5 · captura de valor (RV) en decil top ≥ 25%                                                            | ≥ 25%    | 37.5%                | sí       |
| A-lite   | C6 · tasa por decil monótona (Spearman decil vs tasa ≤ −0.90)                                            | ≤ −0.90  | -0.952               | sí       |
| A-lite   | C7 · UHNW: AUC ≥ 0.60 (informativo, 24 eventos)                                                          | ≥ 0.60   | 0.711 [0.603, 0.818] | sí       |
