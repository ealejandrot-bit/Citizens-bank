# Paso 6 · Escalamiento, tramos, salida

## Objetivo
- Pasar el EBM a puntos PDO con tabla exacta por bin, definir tramos con las reglas del M1 y entregar el score por hogar
  con el M1 y el XGBoost al lado.

## Método
- Score = base + Σ puntos; puntos_j = round(−Factor·b·f_j) con b de Platt = 1.030; base = 545 [DATA]. Probabilidad
  publicada = la del score. Tramos H-3 en dev (mayor IV entre 4,047 configuraciones factibles para EBM y 5,043 para
  XGBoost) [DATA]; vista a igual % de hogares que M1 (I-6). Overrides re-evaluados.

## Código
- `src/step06_scaling.py` · `tests/test_step06.py` · `step06_*.csv`, `outputs/scores/household_scores_ml.csv`.

## Resultados

### Cortes [DATA]
| modelo               | corte              |   percentil dev |   score ≤ |
|:---------------------|:-------------------|----------------:|----------:|
| EBM                  | Crítico/Alto       |             4.0 |     444.0 |
| EBM                  | Alto/Vigilancia    |            20.0 |     519.0 |
| EBM                  | Vigilancia/Estable |            76.0 |     578.0 |
| XGBoost              | Crítico/Alto       |             5.0 |     462.0 |
| XGBoost              | Alto/Vigilancia    |            23.0 |     522.0 |
| XGBoost              | Vigilancia/Estable |            78.0 |     584.0 |
| EBM a igual % que M1 | Crítico/Alto       |             4.0 |     444.0 |
| EBM a igual % que M1 | Alto/Vigilancia    |            21.4 |     521.0 |
| EBM a igual % que M1 | Vigilancia/Estable |            71.3 |     573.0 |

### Escala maestra EBM (dev, con overrides) [DATA]
| tramo      |   score mín |   score máx |   hogares |   % hogares |   % RV |   p media % |   eventos |   tasa % |   captura eventos % |   captura RV eventos % |   lift |
|:-----------|------------:|------------:|----------:|------------:|-------:|------------:|----------:|---------:|--------------------:|-----------------------:|-------:|
| Crítico    |         265 |         444 |       547 |        4.06 |   4.22 |       59.77 |       328 |    59.96 |               17.53 |                  16.17 |   4.32 |
| Alto       |         445 |         609 |      2939 |       21.80 |  21.42 |       21.41 |       661 |    22.49 |               35.33 |                  37.16 |   1.62 |
| Vigilancia |         520 |         578 |      6870 |       50.96 |  50.00 |       10.68 |       739 |    10.76 |               39.50 |                  40.25 |   0.78 |
| Estable    |         579 |         638 |      3126 |       23.19 |  24.36 |        5.28 |       143 |     4.57 |                7.64 |                   6.42 |   0.33 |

- Verificación: % hogares suma 100.0%; captura suma 100.0%; Σ share × tasa =
  13.88% = tasa dev 13.88% [DATA].

### Comparación de tramos en dev: EBM vs XGBoost vs M1 [DATA]
| modelo                     | tramo      |   % hogares |   eventos |   tasa % |   captura eventos % |   captura RV eventos % |   lift |
|:---------------------------|:-----------|------------:|----------:|---------:|--------------------:|-----------------------:|-------:|
| EBM (final, con overrides) | Crítico    |        4.06 |       328 |    59.96 |               17.53 |                  16.17 |   4.32 |
| EBM (final, con overrides) | Alto       |       21.80 |       661 |    22.49 |               35.33 |                  37.16 |   1.62 |
| EBM (final, con overrides) | Vigilancia |       50.96 |       739 |    10.76 |               39.50 |                  40.25 |   0.78 |
| EBM (final, con overrides) | Estable    |       23.19 |       143 |     4.57 |                7.64 |                   6.42 |   0.33 |
| EBM (modelo)               | Crítico    |        4.06 |       328 |    59.96 |               17.53 |                  16.17 |   4.32 |
| EBM (modelo)               | Alto       |       16.34 |       559 |    25.37 |               29.88 |                  30.96 |   1.83 |
| EBM (modelo)               | Vigilancia |       56.07 |       836 |    11.06 |               44.68 |                  46.33 |   0.80 |
| EBM (modelo)               | Estable    |       23.53 |       148 |     4.67 |                7.91 |                   6.54 |   0.34 |
| EBM a igual % que M1       | Crítico    |        4.06 |       328 |    59.96 |               17.53 |                  16.17 |   4.32 |
| EBM a igual % que M1       | Alto       |       17.42 |       584 |    24.87 |               31.21 |                  31.90 |   1.79 |
| EBM a igual % que M1       | Vigilancia |       50.33 |       756 |    11.14 |               40.41 |                  41.87 |   0.80 |
| EBM a igual % que M1       | Estable    |       28.20 |       203 |     5.34 |               10.85 |                  10.07 |   0.38 |
| XGBoost (modelo)           | Crítico    |        5.07 |       397 |    58.04 |               21.22 |                  20.10 |   4.18 |
| XGBoost (modelo)           | Alto       |       18.40 |       579 |    23.34 |               30.95 |                  30.19 |   1.68 |
| XGBoost (modelo)           | Vigilancia |       55.13 |       779 |    10.48 |               41.64 |                  45.09 |   0.76 |
| XGBoost (modelo)           | Estable    |       21.40 |       116 |     4.02 |                6.20 |                   4.61 |   0.29 |
| M1 (final)                 | Crítico    |        4.04 |       308 |    56.62 |               16.46 |                  17.99 |   4.08 |
| M1 (final)                 | Alto       |       23.62 |       728 |    22.86 |               38.91 |                  40.55 |   1.65 |
| M1 (final)                 | Vigilancia |       44.33 |       656 |    10.98 |               35.06 |                  30.94 |   0.79 |
| M1 (final)                 | Estable    |       28.02 |       179 |     4.74 |                9.57 |                  10.52 |   0.34 |

### Overrides (dev) [DATA]
| regla                                | destino   |   movidos dev |   precisión % |   movidos / tramo % | cumple   | decisión   |
|:-------------------------------------|:----------|--------------:|--------------:|--------------------:|:---------|:-----------|
| banker_change_6m_flag = 1            | Crítico   |          1538 |          23.1 |               281.2 | False    | Alto       |
| banker_change_6m_flag = 1            | Alto      |           461 |          13.9 |                20.9 | True     | Alto       |
| complaint_escalated_flag = 1         | Crítico   |           543 |          21.9 |                99.3 | False    | Alto       |
| complaint_escalated_flag = 1         | Alto      |           290 |          14.1 |                13.2 | True     | Alto       |
| transfer_to_competitor_pct_90d ≥ 10% | Crítico   |           230 |          31.3 |                42.0 | False    | eliminada  |
| transfer_to_competitor_pct_90d ≥ 10% | Alto      |            36 |           2.8 |                 1.6 | False    | eliminada  |

### Ejemplo: base + Σ puntos = score (hogar HH000001) [DATA]
| componente                     |   puntos |
|:-------------------------------|---------:|
| base                           |      545 |
| banker_change_6m_flag          |        7 |
| client_reply_rate              |       20 |
| share_of_wallet                |        7 |
| transfer_to_competitor_pct_90d |       -7 |
| repeat_complaint_flag          |        2 |
| contact_gap_ratio              |        7 |
| recurring_deposit_change_pct   |        2 |
| return_vs_benchmark            |       -3 |
| cash_pct_of_portfolio_chg      |        3 |
| complaint_age_days             |        1 |
| meetings_cancelled_by_client   |        0 |
| positions_liquidated_pct       |        2 |

- Verificación: 545 + 41 = 586 = score 586; el test lo verifica en los 20,000 hogares [DATA].
- Redondeo: |   error máx. |p del score − p exacta| |   error máx. score (puntos) |
|--------------------------------------:|----------------------------:|
|                                0.0143 |                      3.6421 |

### Lookup EBM compacto (puntos por tramo de valor) [DATA]
| variable                       | desde       |      hasta |   puntos |   bins EBM unidos |
|:-------------------------------|:------------|-----------:|---------:|------------------:|
| banker_change_6m_flag          | -inf        |   0.5      |        7 |                 1 |
| banker_change_6m_flag          | 0.5         | inf        |      -43 |                 1 |
| banker_change_6m_flag          | missing     |            |        0 |                 1 |
| client_reply_rate              | -inf        |   0.1181   |       -9 |                 2 |
| client_reply_rate              | 0.118056    |   0.1833   |       -8 |                 3 |
| client_reply_rate              | 0.183333    |   0.2614   |       -7 |                 3 |
| client_reply_rate              | 0.261364    |   0.2929   |       -6 |                 2 |
| client_reply_rate              | 0.292857    |   0.3693   |       -5 |                 5 |
| client_reply_rate              | 0.369318    |   0.4059   |       -4 |                 3 |
| client_reply_rate              | 0.405882    |   0.4226   |        2 |                 2 |
| client_reply_rate              | 0.422619    |   0.458    |        5 |                 5 |
| client_reply_rate              | 0.458042    |   0.4686   |        6 |                 3 |
| client_reply_rate              | 0.468627    |   0.5401   |        7 |                 5 |
| client_reply_rate              | 0.540064    |   0.5639   |        8 |                 6 |
| client_reply_rate              | 0.563859    |   0.5811   |        9 |                 4 |
| client_reply_rate              | 0.58114     |   0.5976   |       10 |                 4 |
| client_reply_rate              | 0.597619    |   0.6141   |       11 |                 4 |
| client_reply_rate              | 0.614144    |   0.6306   |       12 |                 5 |
| client_reply_rate              | 0.630604    |   0.6396   |       13 |                 3 |
| client_reply_rate              | 0.63961     |   0.6515   |       14 |                 5 |
| client_reply_rate              | 0.651484    |   0.6757   |       15 |                 6 |
| client_reply_rate              | 0.675666    |   0.6836   |       16 |                 5 |
| client_reply_rate              | 0.683569    |   0.694    |       17 |                 5 |
| client_reply_rate              | 0.69398     |   0.7032   |       18 |                 4 |
| client_reply_rate              | 0.703203    |   0.712    |       19 |                 5 |
| client_reply_rate              | 0.711982    |   0.7246   |       20 |                 6 |
| client_reply_rate              | 0.724569    |   0.738    |       21 |                 5 |
| client_reply_rate              | 0.737986    |   0.7464   |       22 |                 4 |
| client_reply_rate              | 0.746429    |   0.7625   |       23 |                 3 |
| client_reply_rate              | 0.762531    |   0.7703   |       24 |                 5 |
| client_reply_rate              | 0.77033     |   0.7847   |       25 |                 7 |
| client_reply_rate              | 0.784749    |   0.7906   |       26 |                 4 |
| client_reply_rate              | 0.79057     |   0.811    |       27 |                 6 |
| client_reply_rate              | 0.811012    |   0.8441   |       28 |                 7 |
| client_reply_rate              | 0.84413     |   0.8856   |       29 |                12 |
| client_reply_rate              | 0.885621    | inf        |       30 |                11 |
| client_reply_rate              | missing     |            |      -14 |                 1 |
| share_of_wallet                | -inf        |   0.07571  |      -21 |                20 |
| share_of_wallet                | 0.0757134   |   0.1017   |      -20 |                17 |
| share_of_wallet                | 0.10166     |   0.1195   |      -19 |                15 |
| share_of_wallet                | 0.119499    |   0.1417   |      -18 |                21 |
| share_of_wallet                | 0.14175     |   0.1581   |      -17 |                18 |
| share_of_wallet                | 0.158058    |   0.1698   |      -16 |                14 |
| share_of_wallet                | 0.169807    |   0.1899   |      -15 |                24 |
| share_of_wallet                | 0.18987     |   0.1969   |      -14 |                 9 |
| share_of_wallet                | 0.196938    |   0.1975   |      -13 |                 1 |
| share_of_wallet                | 0.197501    |   0.2102   |      -12 |                18 |
| share_of_wallet                | 0.21017     |   0.2197   |      -10 |                13 |
| share_of_wallet                | 0.219674    |   0.2273   |       -9 |                11 |
| share_of_wallet                | 0.227289    |   0.2472   |       -8 |                27 |
| share_of_wallet                | 0.247166    |   0.2707   |       -7 |                33 |
| share_of_wallet                | 0.270665    |   0.2933   |       -6 |                36 |
| share_of_wallet                | 0.29333     |   0.3145   |       -5 |                34 |
| share_of_wallet                | 0.314496    |   0.3386   |       -4 |                37 |
| share_of_wallet                | 0.338599    |   0.3682   |       -3 |                46 |
| share_of_wallet                | 0.3682      |   0.3952   |       -2 |                42 |
| share_of_wallet                | 0.395203    |   0.4163   |       -1 |                36 |
| share_of_wallet                | 0.416288    |   0.4574   |        0 |                67 |
| share_of_wallet                | 0.457441    |   0.4877   |        1 |                48 |
| share_of_wallet                | 0.48771     |   0.5189   |        2 |                48 |
| share_of_wallet                | 0.518914    |   0.5419   |        3 |                32 |
| share_of_wallet                | 0.541864    |   0.5676   |        4 |                33 |
| share_of_wallet                | 0.567595    |   0.6143   |        5 |                58 |
| share_of_wallet                | 0.614302    |   0.6611   |        6 |                56 |
| share_of_wallet                | 0.661107    |   0.7086   |        7 |                49 |
| share_of_wallet                | 0.708646    |   0.7816   |        8 |                59 |
| share_of_wallet                | 0.7816      |   0.8552   |        9 |                47 |
| share_of_wallet                | 0.855216    |   0.9557   |       10 |                41 |
| share_of_wallet                | 0.955739    |   0.9838   |       11 |                 7 |
| share_of_wallet                | 0.983761    |   0.9885   |       13 |                 1 |
| share_of_wallet                | 0.988486    | inf        |       21 |                 4 |
| share_of_wallet                | missing     |            |        0 |                 1 |
| transfer_to_competitor_pct_90d | -inf        |   0.00412  |        5 |               210 |
| transfer_to_competitor_pct_90d | 0.00412039  |   0.006474 |        4 |               163 |
| transfer_to_competitor_pct_90d | 0.00647419  |   0.008929 |        3 |               148 |
| transfer_to_competitor_pct_90d | 0.00892897  |   0.01104  |        2 |                99 |
| transfer_to_competitor_pct_90d | 0.0110416   |   0.01305  |        1 |                73 |
| transfer_to_competitor_pct_90d | 0.0130534   |   0.01442  |        0 |                43 |
| transfer_to_competitor_pct_90d | 0.0144206   |   0.01649  |       -1 |                52 |
| transfer_to_competitor_pct_90d | 0.0164935   |   0.01808  |       -2 |                29 |
| transfer_to_competitor_pct_90d | 0.0180793   |   0.02068  |       -3 |                36 |
| transfer_to_competitor_pct_90d | 0.0206782   |   0.02267  |       -4 |                22 |
| transfer_to_competitor_pct_90d | 0.0226653   |   0.02452  |       -5 |                16 |
| transfer_to_competitor_pct_90d | 0.0245218   |   0.02776  |       -6 |                21 |
| transfer_to_competitor_pct_90d | 0.0277554   |   0.03152  |       -7 |                16 |
| transfer_to_competitor_pct_90d | 0.031522    |   0.03646  |       -8 |                13 |
| transfer_to_competitor_pct_90d | 0.0364595   |   0.04007  |       -9 |                 6 |
| transfer_to_competitor_pct_90d | 0.0400688   |   0.05144  |      -10 |                10 |
| transfer_to_competitor_pct_90d | 0.0514402   |   0.1028   |      -11 |                 7 |
| transfer_to_competitor_pct_90d | 0.10282     |   0.118    |      -12 |                 1 |
| transfer_to_competitor_pct_90d | 0.118047    |   0.1471   |      -36 |                 1 |
| transfer_to_competitor_pct_90d | 0.147082    |   0.2705   |      -39 |                 5 |
| transfer_to_competitor_pct_90d | 0.270505    |   0.3112   |      -40 |                 2 |
| transfer_to_competitor_pct_90d | 0.311229    |   0.4309   |      -41 |                 7 |
| transfer_to_competitor_pct_90d | 0.430889    |   0.7576   |      -42 |                14 |
| transfer_to_competitor_pct_90d | 0.75759     |   1.14     |      -43 |                10 |
| transfer_to_competitor_pct_90d | 1.13998     |   2.979    |      -44 |                15 |
| transfer_to_competitor_pct_90d | 2.97925     |   4.867    |      -45 |                 2 |
| transfer_to_competitor_pct_90d | 4.8671      | inf        |      -48 |                 1 |
| transfer_to_competitor_pct_90d | missing     |            |        0 |                 1 |
| repeat_complaint_flag          | -inf        |   0.5      |        2 |                 1 |
| repeat_complaint_flag          | 0.5         | inf        |      -40 |                 1 |
| repeat_complaint_flag          | missing     |            |        0 |                 1 |
| contact_gap_ratio              | -inf        |   0.005556 |       12 |                 1 |
| contact_gap_ratio              | 0.00555556  |   0.03889  |        9 |                 3 |
| contact_gap_ratio              | 0.0388889   |   0.08333  |        7 |                 4 |
| contact_gap_ratio              | 0.0833333   |   0.09444  |        6 |                 1 |
| contact_gap_ratio              | 0.0944444   |   0.1167   |        5 |                 2 |
| contact_gap_ratio              | 0.116667    |   0.2722   |        4 |                14 |
| contact_gap_ratio              | 0.272222    |   0.3389   |        3 |                 6 |
| contact_gap_ratio              | 0.338889    |   0.35     |       -1 |                 1 |
| contact_gap_ratio              | 0.35        |   0.4389   |       -2 |                 8 |
| contact_gap_ratio              | 0.438889    |   0.55     |       -3 |                10 |
| contact_gap_ratio              | 0.55        |   0.6722   |       -4 |                11 |
| contact_gap_ratio              | 0.672222    |   0.7833   |       -5 |                10 |
| contact_gap_ratio              | 0.783333    |   0.8833   |       -6 |                 9 |
| contact_gap_ratio              | 0.883333    |   0.9833   |       -7 |                 9 |
| contact_gap_ratio              | 0.983333    |   1.094    |       -8 |                10 |
| contact_gap_ratio              | 1.09444     |   1.217    |       -9 |                11 |
| contact_gap_ratio              | 1.21667     |   1.306    |      -10 |                 8 |
| contact_gap_ratio              | 1.30556     |   1.428    |      -11 |                11 |
| contact_gap_ratio              | 1.42778     |   1.494    |      -12 |                 6 |
| contact_gap_ratio              | 1.49444     |   1.561    |      -13 |                 6 |
| contact_gap_ratio              | 1.56111     |   1.628    |      -14 |                 6 |
| contact_gap_ratio              | 1.62778     |   1.739    |      -15 |                 9 |
| contact_gap_ratio              | 1.73889     |   1.839    |      -16 |                 8 |
| contact_gap_ratio              | 1.83889     |   1.983    |      -17 |                13 |
| contact_gap_ratio              | 1.98333     |   2.083    |      -18 |                 8 |
| contact_gap_ratio              | 2.08333     |   2.183    |      -19 |                 8 |
| contact_gap_ratio              | 2.18333     |   2.283    |      -20 |                 9 |
| contact_gap_ratio              | 2.28333     |   2.417    |      -21 |                11 |
| contact_gap_ratio              | 2.41667     |   2.517    |      -22 |                 9 |
| contact_gap_ratio              | 2.51667     |   2.65     |      -23 |                 9 |
| contact_gap_ratio              | 2.65        |   2.717    |      -24 |                 6 |
| contact_gap_ratio              | 2.71667     |   2.828    |      -25 |                 7 |
| contact_gap_ratio              | 2.82778     |   2.956    |      -26 |                 8 |
| contact_gap_ratio              | 2.95556     |   3.094    |      -27 |                 6 |
| contact_gap_ratio              | 3.09444     |   3.239    |      -28 |                 5 |
| contact_gap_ratio              | 3.23889     |   3.383    |      -29 |                 6 |
| contact_gap_ratio              | 3.38333     |   3.478    |      -30 |                 3 |
| contact_gap_ratio              | 3.47778     |   3.528    |      -32 |                 2 |
| contact_gap_ratio              | 3.52778     |   3.672    |      -33 |                 5 |
| contact_gap_ratio              | 3.67222     |   3.883    |      -34 |                 5 |
| contact_gap_ratio              | 3.88333     |   4.078    |      -35 |                 4 |
| contact_gap_ratio              | 4.07778     | inf        |      -42 |                 5 |
| contact_gap_ratio              | missing     |            |        0 |                 1 |
| recurring_deposit_change_pct   | -inf        |  -0.5173   |      -13 |                49 |
| recurring_deposit_change_pct   | -0.517298   |  -0.328    |      -12 |                47 |
| recurring_deposit_change_pct   | -0.328017   |  -0.2796   |      -11 |                16 |
| recurring_deposit_change_pct   | -0.279585   |  -0.2759   |       -8 |                 1 |
| recurring_deposit_change_pct   | -0.275902   |  -0.2744   |       -7 |                 1 |
| recurring_deposit_change_pct   | -0.274439   |  -0.266    |       -6 |                 2 |
| recurring_deposit_change_pct   | -0.266045   |  -0.1841   |       -5 |                33 |
| recurring_deposit_change_pct   | -0.184087   |  -0.1327   |       -4 |                25 |
| recurring_deposit_change_pct   | -0.132671   |  -0.1      |       -3 |                22 |
| recurring_deposit_change_pct   | -0.100021   |  -0.07835  |       -2 |                51 |
| recurring_deposit_change_pct   | -0.0783477  |  -0.06526  |       -1 |                63 |
| recurring_deposit_change_pct   | -0.0652565  |  -0.04035  |        0 |                61 |
| recurring_deposit_change_pct   | -0.0403512  |  -0.01395  |        1 |                77 |
| recurring_deposit_change_pct   | -0.0139458  |  -0.003371 |        2 |                98 |
| recurring_deposit_change_pct   | -0.00337144 |   0.0101   |        3 |               163 |
| recurring_deposit_change_pct   | 0.0101002   |   0.28     |        4 |               258 |
| recurring_deposit_change_pct   | 0.280049    |   0.4994   |        5 |                36 |
| recurring_deposit_change_pct   | 0.499416    |   0.6413   |        6 |                10 |
| recurring_deposit_change_pct   | 0.641306    |   0.6821   |        7 |                 1 |
| recurring_deposit_change_pct   | 0.682147    |   1.418    |        8 |                 7 |
| recurring_deposit_change_pct   | 1.41828     | inf        |       11 |                 1 |
| recurring_deposit_change_pct   | missing     |            |        4 |                 1 |
| return_vs_benchmark            | -inf        |  -0.0486   |       -9 |               176 |
| return_vs_benchmark            | -0.0486026  |  -0.04229  |       -8 |                42 |
| return_vs_benchmark            | -0.0422939  |  -0.04171  |       -6 |                 5 |
| return_vs_benchmark            | -0.0417069  |  -0.03988  |       -5 |                15 |
| return_vs_benchmark            | -0.0398836  |  -0.03399  |       -4 |                47 |
| return_vs_benchmark            | -0.0339909  |  -0.02446  |       -3 |                89 |
| return_vs_benchmark            | -0.0244625  |  -0.01785  |       -2 |                69 |
| return_vs_benchmark            | -0.017854   |  -0.01331  |       -1 |                44 |
| return_vs_benchmark            | -0.013314   |  -0.01206  |        0 |                11 |
| return_vs_benchmark            | -0.0120619  |  -0.00513  |        1 |                65 |
| return_vs_benchmark            | -0.00513032 |   0.002909 |        2 |                73 |
| return_vs_benchmark            | 0.00290884  |   0.007159 |        3 |                38 |
| return_vs_benchmark            | 0.00715939  |   0.007705 |        4 |                 6 |
| return_vs_benchmark            | 0.00770525  |   0.008277 |        5 |                 4 |
| return_vs_benchmark            | 0.00827681  |   0.009049 |        8 |                 9 |
| return_vs_benchmark            | 0.00904898  |   0.009443 |        9 |                 3 |
| return_vs_benchmark            | 0.00944306  |   0.01708  |       10 |                67 |
| return_vs_benchmark            | 0.0170788   |   0.02349  |       11 |                48 |
| return_vs_benchmark            | 0.0234902   |   0.02632  |       13 |                19 |
| return_vs_benchmark            | 0.0263169   |   0.03451  |       14 |                48 |
| return_vs_benchmark            | 0.0345056   |   0.04394  |       15 |                45 |
| return_vs_benchmark            | 0.0439402   |   0.06722  |       16 |                61 |
| return_vs_benchmark            | 0.0672196   | inf        |       17 |                38 |
| return_vs_benchmark            | missing     |            |       -3 |                 1 |
| cash_pct_of_portfolio_chg      | -inf        |  -0.008357 |        3 |               167 |
| cash_pct_of_portfolio_chg      | -0.00835666 |   0.002597 |        2 |               294 |
| cash_pct_of_portfolio_chg      | 0.00259711  |   0.008259 |        1 |               151 |
| cash_pct_of_portfolio_chg      | 0.00825895  |   0.01329  |        0 |                95 |
| cash_pct_of_portfolio_chg      | 0.0132913   |   0.01814  |       -1 |                61 |
| cash_pct_of_portfolio_chg      | 0.018141    |   0.02374  |       -2 |                46 |
| cash_pct_of_portfolio_chg      | 0.0237378   |   0.03479  |       -3 |                43 |
| cash_pct_of_portfolio_chg      | 0.0347855   |   0.0414   |       -4 |                19 |
| cash_pct_of_portfolio_chg      | 0.0413973   |   0.04784  |       -6 |                15 |
| cash_pct_of_portfolio_chg      | 0.0478364   |   0.06701  |       -7 |                30 |
| cash_pct_of_portfolio_chg      | 0.0670124   |   0.1102   |       -9 |                27 |
| cash_pct_of_portfolio_chg      | 0.110197    |   0.1647   |      -10 |                18 |
| cash_pct_of_portfolio_chg      | 0.164747    |   0.2505   |      -11 |                17 |
| cash_pct_of_portfolio_chg      | 0.250487    |   0.3525   |      -12 |                18 |
| cash_pct_of_portfolio_chg      | 0.352475    |   0.4548   |      -13 |                10 |
| cash_pct_of_portfolio_chg      | 0.454794    |   0.5662   |      -14 |                 7 |
| cash_pct_of_portfolio_chg      | 0.566198    | inf        |      -15 |                 4 |
| cash_pct_of_portfolio_chg      | missing     |            |        3 |                 1 |
| complaint_age_days             | -inf        |   0.5      |        1 |                 1 |
| complaint_age_days             | 0.5         |   1.5      |        0 |                 1 |
| complaint_age_days             | 1.5         |   2.5      |       -1 |                 1 |
| complaint_age_days             | 2.5         |   3.5      |       -2 |                 1 |
| complaint_age_days             | 3.5         |   6.5      |       -3 |                 3 |
| complaint_age_days             | 6.5         |   8.5      |       -4 |                 2 |
| complaint_age_days             | 8.5         |  11.5      |       -5 |                 3 |
| complaint_age_days             | 11.5        |  15.5      |       -6 |                 4 |
| complaint_age_days             | 15.5        |  17.5      |       -7 |                 2 |
| complaint_age_days             | 17.5        |  19.5      |       -8 |                 2 |
| complaint_age_days             | 19.5        |  22.5      |       -9 |                 3 |
| complaint_age_days             | 22.5        |  25.5      |      -10 |                 3 |
| complaint_age_days             | 25.5        |  27.5      |      -11 |                 2 |
| complaint_age_days             | 27.5        |  30.5      |      -12 |                 3 |
| complaint_age_days             | 30.5        |  33.5      |      -13 |                 3 |
| complaint_age_days             | 33.5        |  35.5      |      -14 |                 2 |
| complaint_age_days             | 35.5        |  37.5      |      -15 |                 2 |
| complaint_age_days             | 37.5        |  40.5      |      -16 |                 2 |
| complaint_age_days             | 40.5        |  42.5      |      -17 |                 2 |
| complaint_age_days             | 42.5        |  45.5      |      -18 |                 3 |
| complaint_age_days             | 45.5        |  51.5      |      -19 |                 4 |
| complaint_age_days             | 51.5        |  53.5      |      -20 |                 2 |
| complaint_age_days             | 53.5        |  56.5      |      -21 |                 2 |
| complaint_age_days             | 56.5        |  60.5      |      -22 |                 3 |
| complaint_age_days             | 60.5        |  63.5      |      -23 |                 2 |
| complaint_age_days             | 63.5        |  67.5      |      -24 |                 3 |
| complaint_age_days             | 67.5        |  71.5      |      -25 |                 2 |
| complaint_age_days             | 71.5        |  78.5      |      -26 |                 4 |
| complaint_age_days             | 78.5        |  85.5      |      -27 |                 3 |
| complaint_age_days             | 85.5        |  89.5      |      -28 |                 2 |
| complaint_age_days             | 89.5        |  95.5      |      -29 |                 3 |
| complaint_age_days             | 95.5        | 100        |      -30 |                 2 |
| complaint_age_days             | 100         | 102.5      |      -31 |                 2 |
| complaint_age_days             | 102.5       | 109.5      |      -32 |                 3 |
| complaint_age_days             | 109.5       | 111.5      |      -33 |                 1 |
| complaint_age_days             | 111.5       | 115        |      -34 |                 2 |
| complaint_age_days             | 115         | 125.5      |      -35 |                 2 |
| complaint_age_days             | 125.5       | 129.5      |      -36 |                 2 |
| complaint_age_days             | 129.5       | 140        |      -37 |                 2 |
| complaint_age_days             | 140         | 142        |      -38 |                 1 |
| complaint_age_days             | 142         | 151.5      |      -39 |                 2 |
| complaint_age_days             | 151.5       | 161        |      -40 |                 2 |
| complaint_age_days             | 161         | 183.5      |      -41 |                 4 |
| complaint_age_days             | 183.5       | 186.5      |      -42 |                 1 |
| complaint_age_days             | 186.5       | 196        |      -43 |                 3 |
| complaint_age_days             | 196         | 198        |      -44 |                 1 |
| complaint_age_days             | 198         | 205.5      |      -46 |                 2 |
| complaint_age_days             | 205.5       | 212        |      -47 |                 1 |
| complaint_age_days             | 212         | 229        |      -48 |                 3 |
| complaint_age_days             | 229         | 234        |      -49 |                 1 |
| complaint_age_days             | 234         | 241.5      |      -50 |                 1 |
| complaint_age_days             | 241.5       | 261.5      |      -51 |                 2 |
| complaint_age_days             | 261.5       | 287        |      -52 |                 1 |
| complaint_age_days             | 287         | 306        |      -53 |                 2 |
| complaint_age_days             | 306         | inf        |      -54 |                 3 |
| complaint_age_days             | missing     |            |        0 |                 1 |
| meetings_cancelled_by_client   | -inf        |   0.5      |        0 |                 1 |
| meetings_cancelled_by_client   | 0.5         |   1.5      |      -12 |                 1 |
| meetings_cancelled_by_client   | 1.5         |   2.5      |      -17 |                 1 |
| meetings_cancelled_by_client   | 2.5         |   3.5      |      -29 |                 1 |
| meetings_cancelled_by_client   | 3.5         |   4.5      |      -31 |                 1 |
| meetings_cancelled_by_client   | 4.5         |   5.5      |      -35 |                 1 |
| meetings_cancelled_by_client   | 5.5         |   6.5      |      -37 |                 1 |
| meetings_cancelled_by_client   | 6.5         |   7.5      |      -38 |                 1 |
| meetings_cancelled_by_client   | 7.5         | inf        |      -60 |                 1 |
| meetings_cancelled_by_client   | missing     |            |        2 |                 1 |
| positions_liquidated_pct       | -inf        |   0.009777 |        2 |                13 |
| positions_liquidated_pct       | 0.00977684  |   0.01348  |        1 |                42 |
| positions_liquidated_pct       | 0.0134795   |   0.01574  |        0 |                40 |
| positions_liquidated_pct       | 0.0157426   |   0.01773  |       -1 |                36 |
| positions_liquidated_pct       | 0.0177309   |   0.02038  |       -2 |                35 |
| positions_liquidated_pct       | 0.0203794   |   0.02345  |       -3 |                43 |
| positions_liquidated_pct       | 0.0234501   |   0.02671  |       -4 |                43 |
| positions_liquidated_pct       | 0.0267092   |   0.02941  |       -5 |                42 |
| positions_liquidated_pct       | 0.0294052   |   0.03206  |       -6 |                37 |
| positions_liquidated_pct       | 0.0320572   |   0.03442  |       -7 |                33 |
| positions_liquidated_pct       | 0.0344172   |   0.03625  |       -8 |                35 |
| positions_liquidated_pct       | 0.0362478   |   0.03857  |       -9 |                32 |
| positions_liquidated_pct       | 0.0385686   |   0.0406   |      -10 |                16 |
| positions_liquidated_pct       | 0.0405965   |   0.04278  |      -11 |                33 |
| positions_liquidated_pct       | 0.0427812   |   0.04442  |      -12 |                21 |
| positions_liquidated_pct       | 0.0444176   |   0.04572  |      -13 |                24 |
| positions_liquidated_pct       | 0.0457188   |   0.04739  |      -14 |                24 |
| positions_liquidated_pct       | 0.0473915   |   0.04869  |      -15 |                25 |
| positions_liquidated_pct       | 0.0486871   |   0.04982  |      -16 |                17 |
| positions_liquidated_pct       | 0.0498185   |   0.05159  |      -17 |                26 |
| positions_liquidated_pct       | 0.0515937   |   0.05276  |      -18 |                21 |
| positions_liquidated_pct       | 0.052759    |   0.05407  |      -19 |                23 |
| positions_liquidated_pct       | 0.0540687   |   0.05471  |      -20 |                17 |
| positions_liquidated_pct       | 0.0547071   |   0.05597  |      -21 |                18 |
| positions_liquidated_pct       | 0.0559713   |   0.05747  |      -22 |                18 |
| positions_liquidated_pct       | 0.0574674   |   0.05892  |      -23 |                13 |
| positions_liquidated_pct       | 0.0589178   |   0.06007  |      -24 |                 9 |
| positions_liquidated_pct       | 0.0600727   |   0.0619   |      -25 |                13 |
| positions_liquidated_pct       | 0.0618951   |   0.07111  |      -26 |                21 |
| positions_liquidated_pct       | 0.0711139   |   0.07725  |      -27 |                13 |
| positions_liquidated_pct       | 0.0772543   |   0.08588  |      -28 |                19 |
| positions_liquidated_pct       | 0.0858846   |   0.09502  |      -29 |                19 |
| positions_liquidated_pct       | 0.0950245   |   0.1062   |      -30 |                19 |
| positions_liquidated_pct       | 0.106198    |   0.1152   |      -31 |                11 |
| positions_liquidated_pct       | 0.115247    |   0.1218   |      -32 |                13 |
| positions_liquidated_pct       | 0.12182     |   0.13     |      -33 |                 9 |
| positions_liquidated_pct       | 0.129966    |   0.1401   |      -34 |                18 |
| positions_liquidated_pct       | 0.140108    |   0.1506   |      -35 |                13 |
| positions_liquidated_pct       | 0.150647    |   0.1623   |      -36 |                19 |
| positions_liquidated_pct       | 0.162308    |   0.1886   |      -37 |                27 |
| positions_liquidated_pct       | 0.188639    |   0.2017   |      -38 |                18 |
| positions_liquidated_pct       | 0.201658    |   0.218    |      -39 |                16 |
| positions_liquidated_pct       | 0.217984    |   0.2344   |      -40 |                12 |
| positions_liquidated_pct       | 0.234382    |   0.3372   |      -41 |                22 |
| positions_liquidated_pct       | 0.337163    |   0.3416   |      -43 |                 1 |
| positions_liquidated_pct       | 0.341622    | inf        |      -57 |                 3 |
| positions_liquidated_pct       | missing     |            |        2 |                 1 |

- 6,730 bins del EBM se reducen a 323 filas uniendo bins consecutivos con los mismos puntos; el score no cambia
  (lookup completo en `step06_lookup.csv`) [DATA].

## Tests
- `tests/test_step06.py` (ver pytest).

## Decisiones y preguntas abiertas
- D6.1–D6.2 en `reports/decision_log.md`; preguntas G2 en `reports/gate_2.md`.
