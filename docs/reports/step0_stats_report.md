# Paso 0 · Pruebas estadísticas

**200 de 200 pruebas OK.** α = 0.01 con corrección Benjamini-Hochberg sobre todas las pruebas con p-valor. Montos en USD.

## Resumen por sección

| Sección | Pruebas | OK |
|---|---|---|
| A · Bondad de ajuste | 31 | 31 |
| B · Latentes | 12 | 12 |
| C · Target | 3 | 3 |
| D · Colas y curtosis | 71 | 71 |
| F · Dinero y medias | 26 | 26 |
| G · Sesgo | 38 | 38 |
| H · Variedad y duplicados | 7 | 7 |
| I · Semilla | 12 | 12 |

## A · Bondad de ajuste

| Prueba | Estadístico | gl | p | p BH | Criterio | Detalle | OK |
|---|---|---|---|---|---|---|---|
| KS sobre PIT: relationship_value · LogNormal truncada | 0.0057 |  | 0.5410 | 0.8271 | PIT ~ U(0,1) | n = 20,000 | OK |
| Cramér-von Mises (colas): relationship_value · LogNormal truncada | 0.1395 |  | 0.4233 | 0.8050 | Φ⁻¹(PIT) ~ N(0,1) |  | OK |
| KS sobre PIT: proporción depósitos · Beta(2,5) | 0.0079 |  | 0.2377 | 0.7676 | PIT ~ U(0,1) | n = 16,991 | OK |
| Cramér-von Mises (colas): proporción depósitos · Beta(2,5) | 0.2437 |  | 0.1967 | 0.7676 | Φ⁻¹(PIT) ~ N(0,1) |  | OK |
| KS sobre PIT: tenure_years (edad ≥ 68) · Gamma(2, 4.5) | 0.0194 |  | 0.0308 | 0.5899 | PIT ~ U(0,1) | n = 5,523 | OK |
| Cramér-von Mises (colas): tenure_years (edad ≥ 68) · Gamma(2, 4.5) | 0.5688 |  | 0.0267 | 0.5899 | Φ⁻¹(PIT) ~ N(0,1) |  | OK |
| KS sobre PIT: salary_base_annual · LogNormal ligada, piso $150k | 0.0056 |  | 0.8923 | 0.9693 | PIT ~ U(0,1) | n = 10,772 | OK |
| Cramér-von Mises (colas): salary_base_annual · LogNormal ligada, piso $150k | 0.0296 |  | 0.9775 | 0.9801 | Φ⁻¹(PIT) ~ N(0,1) |  | OK |
| KS sobre PIT: pension_monthly · LogNormal ligada, piso $2.5k | 0.0068 |  | 0.9054 | 0.9693 | PIT ~ U(0,1) | n = 6,801 | OK |
| Cramér-von Mises (colas): pension_monthly · LogNormal ligada, piso $2.5k | 0.0602 |  | 0.8126 | 0.9363 | Φ⁻¹(PIT) ~ N(0,1) |  | OK |
| KS sobre PIT: business_distribution_annual · LogNormal ligada | 0.0152 |  | 0.1693 | 0.7676 | PIT ~ U(0,1) | n = 5,287 | OK |
| Cramér-von Mises (colas): business_distribution_annual · LogNormal ligada | 0.2953 |  | 0.1394 | 0.7676 | Φ⁻¹(PIT) ~ N(0,1) |  | OK |
| KS sobre PIT: bono / sueldo · 1.5·Beta(1.5,3) | 0.0103 |  | 0.2016 | 0.7676 | PIT ~ U(0,1) | n = 10,772 | OK |
| Cramér-von Mises (colas): bono / sueldo · 1.5·Beta(1.5,3) | 0.3266 |  | 0.1139 | 0.7676 | Φ⁻¹(PIT) ~ N(0,1) |  | OK |
| KS sobre PIT: rendimiento dividendos · Beta(4,196) | 0.0081 |  | 0.5791 | 0.8491 | PIT ~ U(0,1) | n = 9,284 | OK |
| Cramér-von Mises (colas): rendimiento dividendos · Beta(4,196) | 0.1195 |  | 0.4974 | 0.8153 | Φ⁻¹(PIT) ~ N(0,1) |  | OK |
| χ² edad entera · Normal truncada discretizada | 61.2700 | 66 | 0.6419 | 0.8953 | gl = celdas − 1 | 67 celdas tras unir esperadas < 5 | OK |
| χ² frecuencia de pago | 1.7650 | 2 | 0.4137 | 0.8050 | gl = categorías − 1 |  | OK |
| Binomial exacta: has_investments | 0.8496 |  | 0.8585 | 0.9570 | p = 0.85 | n = 20,000 | OK |
| Binomial exacta: has_linked_business · HNW | 0.2494 |  | 0.8402 | 0.9559 | p = 0.25 | n = 18,897 | OK |
| Binomial exacta: has_linked_business · UHNW | 0.5213 |  | 0.0566 | 0.5899 | p = 0.55 | n = 1,103 | OK |
| Binomial exacta: has_trust · HNW | 0.2961 |  | 0.2433 | 0.7676 | p = 0.3 | n = 18,897 | OK |
| Binomial exacta: has_trust · UHNW | 0.7063 |  | 0.6694 | 0.9127 | p = 0.7 | n = 1,103 | OK |
| Binomial exacta: has_advisory | inversiones | 0.7037 |  | 0.2916 | 0.7858 | p = 0.7 | n = 16,991 | OK |
| Binomial exacta: has_credit_anchor | 0.3424 |  | 0.0242 | 0.5899 | p = 0.35 | n = 20,000 | OK |
| Binomial exacta: has_payroll_stream · activos | 0.7951 |  | 0.1657 | 0.7676 | p = 0.8 | n = 12,706 | OK |
| Binomial exacta: has_payroll_stream · retirados | 0.0919 |  | 0.0202 | 0.5899 | p = 0.1 | n = 7,294 | OK |
| Binomial exacta: has_pension_stream · activos | 0.0505 |  | 0.7757 | 0.9174 | p = 0.05 | n = 12,706 | OK |
| Binomial exacta: has_pension_stream · retirados | 0.8444 |  | 0.1788 | 0.7676 | p = 0.85 | n = 7,294 | OK |
| Binomial exacta: has_dividend_stream | inversiones | 0.5464 |  | 0.3469 | 0.7943 | p = 0.55 | n = 16,991 | OK |
| Binomial exacta: churn_excluded | 0.0062 |  | 0.7834 | 0.9174 | p = 0.006 | n = 20,000 | OK |

## B · Latentes

| Prueba | Estadístico | gl | p | p BH | Criterio | Detalle | OK |
|---|---|---|---|---|---|---|---|
| KS z_outflow ~ N(0,1) | 0.0051 |  | 0.6847 | 0.9174 | N(0,1) |  | OK |
| Curtosis (Anscombe-Glynn) z_outflow | 0.7105 |  | 0.4774 | 0.8153 | exceso = 0 | exceso = +0.0240 | OK |
| KS z_neglect ~ N(0,1) | 0.0061 |  | 0.4508 | 0.8084 | N(0,1) |  | OK |
| Curtosis (Anscombe-Glynn) z_neglect | 0.9086 |  | 0.3635 | 0.7943 | exceso = 0 | exceso = +0.0310 | OK |
| KS z_service ~ N(0,1) | 0.0059 |  | 0.4875 | 0.8153 | N(0,1) |  | OK |
| Curtosis (Anscombe-Glynn) z_service | 1.8087 |  | 0.0705 | 0.5899 | exceso = 0 | exceso = +0.0637 | OK |
| Fisher z: ρ(outflow, neglect) | -1.5214 |  | 0.1282 | 0.7676 | ρ = 0.35 | r = 0.3405 | OK |
| Fisher z: ρ(outflow, service) | -1.9947 |  | 0.0461 | 0.5899 | ρ = 0.25 | r = 0.2367 | OK |
| Fisher z: ρ(neglect, service) | -0.0614 |  | 0.9510 | 0.9693 | ρ = 0.3 | r = 0.2996 | OK |
| Mardia asimetría multivariada | 12.9553 | 10 | 0.2262 | 0.7676 | gl = p(p+1)(p+2)/6 |  | OK |
| Mardia curtosis multivariada | 2.3863 |  | 0.0170 | 0.5899 | b2 = p(p+2) = 15 |  | OK |
| KS riesgo idiosincrático ~ N(0, 0.6) | 0.0061 |  | 0.4349 | 0.8050 | N(0,σ) |  | OK |

## C · Target

| Prueba | Estadístico | gl | p | p BH | Criterio | Detalle | OK |
|---|---|---|---|---|---|---|---|
| Hosmer-Lemeshow hard churn 6m | 5.1022 | 8 | 0.7466 | 0.9174 | gl = grupos − 2 |  | OK |
| Hosmer-Lemeshow soft churn 3m | 6.1398 | 8 | 0.6316 | 0.8953 | gl = grupos − 2 |  | OK |
| Eventos hard observados vs Σ p_i | 0.2418 |  | 0.8090 | 0.9363 | E[eventos] = Σp | 1200 vs 1192.6 | OK |

## D · Colas y curtosis

| Prueba | Estadístico | gl | p | p BH | Criterio | Detalle | OK |
|---|---|---|---|---|---|---|---|
| Cola pesada en escala USD: relationship_value | 98.0695 |  |  |  | exceso > 0 (p < α) | exceso = 375.7; p = 0.0e+00 | OK |
| Cola pesada en escala USD: deposit_balance | 105.6908 |  |  |  | exceso > 0 (p < α) | exceso = 2,058.8; p = 0.0e+00 | OK |
| Cola pesada en escala USD: aum | 85.7704 |  |  |  | exceso > 0 (p < α) | exceso = 175.9; p = 0.0e+00 | OK |
| Cola pesada en escala USD: salary_base_annual | 37.5034 |  |  |  | exceso > 0 (p < α) | exceso = 6.3; p = 4.1e-308 | OK |
| Cola pesada en escala USD: bonus_annual | 42.8220 |  |  |  | exceso > 0 (p < α) | exceso = 9.6; p = 0.0e+00 | OK |
| Cola pesada en escala USD: pension_monthly | 26.8469 |  |  |  | exceso > 0 (p < α) | exceso = 4.7; p = 4.6e-159 | OK |
| Cola pesada en escala USD: dividend_annual | 69.6317 |  |  |  | exceso > 0 (p < α) | exceso = 796.8; p = 0.0e+00 | OK |
| Cola pesada en escala USD: business_distribution_annual | 43.3526 |  |  |  | exceso > 0 (p < α) | exceso = 62.7; p = 0.0e+00 | OK |
| Cola pesada en escala USD: recurring_income_monthly | 85.9586 |  |  |  | exceso > 0 (p < α) | exceso = 107.2; p = 0.0e+00 | OK |
| Curtosis de Φ⁻¹(PIT): relationship_value · LogNormal truncada | 1.1765 |  | 0.2394 | 0.7676 | exceso = 0 | exceso = +0.0406 | OK |
| Jarque-Bera de Φ⁻¹(PIT): relationship_value · LogNormal truncada | 1.4510 | 2 | 0.4841 | 0.8153 | gl = 2 |  | OK |
| Curtosis de Φ⁻¹(PIT): proporción depósitos · Beta(2,5) | 0.3718 |  | 0.7100 | 0.9174 | exceso = 0 | exceso = +0.0130 | OK |
| Jarque-Bera de Φ⁻¹(PIT): proporción depósitos · Beta(2,5) | 0.3134 | 2 | 0.8549 | 0.9570 | gl = 2 |  | OK |
| Curtosis de Φ⁻¹(PIT): tenure_years (edad ≥ 68) · Gamma(2, 4.5) | -1.0989 |  | 0.2718 | 0.7718 | exceso = 0 | exceso = -0.0728 | OK |
| Jarque-Bera de Φ⁻¹(PIT): tenure_years (edad ≥ 68) · Gamma(2, 4.5) | 1.6500 | 2 | 0.4382 | 0.8050 | gl = 2 |  | OK |
| Curtosis de Φ⁻¹(PIT): salary_base_annual · LogNormal ligada, piso $150k | -1.2452 |  | 0.2131 | 0.7676 | exceso = 0 | exceso = -0.0586 | OK |
| Jarque-Bera de Φ⁻¹(PIT): salary_base_annual · LogNormal ligada, piso $150k | 1.8430 | 2 | 0.3979 | 0.8050 | gl = 2 |  | OK |
| Curtosis de Φ⁻¹(PIT): pension_monthly · LogNormal ligada, piso $2.5k | -1.0794 |  | 0.2804 | 0.7774 | exceso = 0 | exceso = -0.0645 | OK |
| Jarque-Bera de Φ⁻¹(PIT): pension_monthly · LogNormal ligada, piso $2.5k | 1.2321 | 2 | 0.5401 | 0.8271 | gl = 2 |  | OK |
| Curtosis de Φ⁻¹(PIT): business_distribution_annual · LogNormal ligada | 0.4320 |  | 0.6657 | 0.9127 | exceso = 0 | exceso = +0.0260 | OK |
| Jarque-Bera de Φ⁻¹(PIT): business_distribution_annual · LogNormal ligada | 0.5022 | 2 | 0.7779 | 0.9174 | gl = 2 |  | OK |
| Curtosis de Φ⁻¹(PIT): bono / sueldo · 1.5·Beta(1.5,3) | 0.3507 |  | 0.7258 | 0.9174 | exceso = 0 | exceso = +0.0150 | OK |
| Jarque-Bera de Φ⁻¹(PIT): bono / sueldo · 1.5·Beta(1.5,3) | 0.1284 | 2 | 0.9378 | 0.9693 | gl = 2 |  | OK |
| Curtosis de Φ⁻¹(PIT): rendimiento dividendos · Beta(4,196) | 0.6239 |  | 0.5327 | 0.8271 | exceso = 0 | exceso = +0.0302 | OK |
| Jarque-Bera de Φ⁻¹(PIT): rendimiento dividendos · Beta(4,196) | 1.9108 | 2 | 0.3847 | 0.7943 | gl = 2 |  | OK |
| Curtosis log(relationship_value) vs teórica | 0.7765 |  | 0.4375 | 0.8050 | igual a la teórica | obs -0.0539 vs teo -0.0808 | OK |
| media típico vs semillas: relationship_value | 9.44e+06 |  | 0.2438 | 0.7676 | p empírico vs 200 semillas | percentil 87.8 | OK |
| media típico vs semillas: deposit_balance | 3.79e+06 |  | 0.0050 | 0.5899 | p empírico vs 200 semillas | percentil 99.8 | OK |
| media típico vs semillas: aum | 6.64e+06 |  | 0.9403 | 0.9693 | p empírico vs 200 semillas | percentil 53.0 | OK |
| media típico vs semillas: salary_base_annual | 440,425.3937 |  | 0.5323 | 0.8271 | p empírico vs 200 semillas | percentil 73.4 | OK |
| media típico vs semillas: bonus_annual | 218,427.5747 |  | 0.5522 | 0.8284 | p empírico vs 200 semillas | percentil 27.6 | OK |
| media típico vs semillas: pension_monthly | 10,512.0412 |  | 0.5323 | 0.8271 | p empírico vs 200 semillas | percentil 26.6 | OK |
| media típico vs semillas: dividend_annual | 135,942.6418 |  | 0.2338 | 0.7676 | p empírico vs 200 semillas | percentil 88.3 | OK |
| media típico vs semillas: business_distribution_annual | 852,224.2910 |  | 0.3234 | 0.7943 | p empírico vs 200 semillas | percentil 16.2 | OK |
| media típico vs semillas: recurring_income_monthly | 50,798.7184 |  | 0.4527 | 0.8084 | p empírico vs 200 semillas | percentil 22.6 | OK |
| curtosis_exceso típico vs semillas: relationship_value | 375.6680 |  | 0.2139 | 0.7676 | p empírico vs 200 semillas | percentil 89.3 | OK |
| curtosis_exceso típico vs semillas: deposit_balance | 2,058.8015 |  | 0.0448 | 0.5899 | p empírico vs 200 semillas | percentil 97.8 | OK |
| curtosis_exceso típico vs semillas: aum | 175.8524 |  | 0.7214 | 0.9174 | p empírico vs 200 semillas | percentil 63.9 | OK |
| curtosis_exceso típico vs semillas: salary_base_annual | 6.3017 |  | 0.3433 | 0.7943 | p empírico vs 200 semillas | percentil 17.2 | OK |
| curtosis_exceso típico vs semillas: bonus_annual | 9.5658 |  | 0.8607 | 0.9570 | p empírico vs 200 semillas | percentil 43.0 | OK |
| curtosis_exceso típico vs semillas: pension_monthly | 4.7345 |  | 0.6418 | 0.8953 | p empírico vs 200 semillas | percentil 32.1 | OK |
| curtosis_exceso típico vs semillas: dividend_annual | 796.8048 |  | 0.1144 | 0.7676 | p empírico vs 200 semillas | percentil 94.3 | OK |
| curtosis_exceso típico vs semillas: business_distribution_annual | 62.7433 |  | 0.2438 | 0.7676 | p empírico vs 200 semillas | percentil 87.8 | OK |
| curtosis_exceso típico vs semillas: recurring_income_monthly | 107.1908 |  | 0.1542 | 0.7676 | p empírico vs 200 semillas | percentil 92.3 | OK |
| curtosis_exceso_log típico vs semillas: relationship_value | -0.0539 |  | 0.4129 | 0.8050 | p empírico vs 200 semillas | percentil 79.4 | OK |
| curtosis_exceso_log típico vs semillas: deposit_balance | 0.1852 |  | 0.0547 | 0.5899 | p empírico vs 200 semillas | percentil 97.3 | OK |
| curtosis_exceso_log típico vs semillas: aum | -0.0463 |  | 0.7612 | 0.9174 | p empírico vs 200 semillas | percentil 61.9 | OK |
| curtosis_exceso_log típico vs semillas: salary_base_annual | -0.2513 |  | 0.3831 | 0.7943 | p empírico vs 200 semillas | percentil 19.2 | OK |
| curtosis_exceso_log típico vs semillas: bonus_annual | 1.8626 |  | 0.2537 | 0.7676 | p empírico vs 200 semillas | percentil 87.3 | OK |
| curtosis_exceso_log típico vs semillas: pension_monthly | -0.1936 |  | 0.3731 | 0.7943 | p empírico vs 200 semillas | percentil 18.7 | OK |
| curtosis_exceso_log típico vs semillas: dividend_annual | 0.1014 |  | 0.0647 | 0.5899 | p empírico vs 200 semillas | percentil 96.8 | OK |
| curtosis_exceso_log típico vs semillas: business_distribution_annual | 0.0657 |  | 0.1940 | 0.7676 | p empírico vs 200 semillas | percentil 90.3 | OK |
| curtosis_exceso_log típico vs semillas: recurring_income_monthly | 0.7310 |  | 0.9801 | 0.9801 | p empírico vs 200 semillas | percentil 49.0 | OK |
| L_curtosis típico vs semillas: relationship_value | 0.3596 |  | 0.3731 | 0.7943 | p empírico vs 200 semillas | percentil 81.3 | OK |
| L_curtosis típico vs semillas: deposit_balance | 0.4284 |  | 0.0348 | 0.5899 | p empírico vs 200 semillas | percentil 98.3 | OK |
| L_curtosis típico vs semillas: aum | 0.3614 |  | 0.9403 | 0.9693 | p empírico vs 200 semillas | percentil 53.0 | OK |
| L_curtosis típico vs semillas: salary_base_annual | 0.1711 |  | 0.6716 | 0.9127 | p empírico vs 200 semillas | percentil 33.6 | OK |
| L_curtosis típico vs semillas: bonus_annual | 0.1838 |  | 0.4328 | 0.8050 | p empírico vs 200 semillas | percentil 21.6 | OK |
| L_curtosis típico vs semillas: pension_monthly | 0.1602 |  | 0.2836 | 0.7774 | p empírico vs 200 semillas | percentil 14.2 | OK |
| L_curtosis típico vs semillas: dividend_annual | 0.4108 |  | 0.0846 | 0.6724 | p empírico vs 200 semillas | percentil 95.8 | OK |
| L_curtosis típico vs semillas: business_distribution_annual | 0.2777 |  | 0.2537 | 0.7676 | p empírico vs 200 semillas | percentil 87.3 | OK |
| L_curtosis típico vs semillas: recurring_income_monthly | 0.2875 |  | 0.9303 | 0.9693 | p empírico vs 200 semillas | percentil 53.5 | OK |
| hill_alpha_top1% típico vs semillas: relationship_value | 2.3856 |  | 0.4627 | 0.8084 | p empírico vs 200 semillas | percentil 23.1 | OK |
| hill_alpha_top1% típico vs semillas: deposit_balance | 2.1560 |  | 0.5821 | 0.8491 | p empírico vs 200 semillas | percentil 29.1 | OK |
| hill_alpha_top1% típico vs semillas: aum | 2.4760 |  | 0.9502 | 0.9693 | p empírico vs 200 semillas | percentil 52.5 | OK |
| hill_alpha_top1% típico vs semillas: salary_base_annual | 5.4016 |  | 0.8806 | 0.9656 | p empírico vs 200 semillas | percentil 44.0 | OK |
| hill_alpha_top1% típico vs semillas: bonus_annual | 4.6562 |  | 0.7711 | 0.9174 | p empírico vs 200 semillas | percentil 61.4 | OK |
| hill_alpha_top1% típico vs semillas: pension_monthly | 5.7352 |  | 0.7015 | 0.9174 | p empírico vs 200 semillas | percentil 35.1 | OK |
| hill_alpha_top1% típico vs semillas: dividend_annual | 2.1097 |  | 0.3831 | 0.7943 | p empírico vs 200 semillas | percentil 19.2 | OK |
| hill_alpha_top1% típico vs semillas: business_distribution_annual | 2.8513 |  | 0.2537 | 0.7676 | p empírico vs 200 semillas | percentil 12.7 | OK |
| hill_alpha_top1% típico vs semillas: recurring_income_monthly | 2.6723 |  | 0.0348 | 0.5899 | p empírico vs 200 semillas | percentil 1.7 | OK |

## F · Dinero y medias

| Prueba | Estadístico | gl | p | p BH | Criterio | Detalle | OK |
|---|---|---|---|---|---|---|---|
| USD válido: relationship_value | 7.82e+08 |  |  |  | ≥ 0, finito, centavos, ≤ máx plausible | negativos 0, no finitos 0, máx $782,205,500 | OK |
| USD válido: deposit_balance | 7.82e+08 |  |  |  | ≥ 0, finito, centavos, ≤ máx plausible | negativos 0, no finitos 0, máx $782,205,500 | OK |
| USD válido: aum | 4.19e+08 |  |  |  | ≥ 0, finito, centavos, ≤ máx plausible | negativos 0, no finitos 0, máx $418,825,870 | OK |
| USD válido: salary_base_annual | 2.65e+06 |  |  |  | ≥ 0, finito, centavos, ≤ máx plausible | negativos 0, no finitos 0, máx $2,645,329 | OK |
| USD válido: bonus_annual | 2.33e+06 |  |  |  | ≥ 0, finito, centavos, ≤ máx plausible | negativos 0, no finitos 0, máx $2,334,627 | OK |
| USD válido: pension_monthly | 53,462.4600 |  |  |  | ≥ 0, finito, centavos, ≤ máx plausible | negativos 0, no finitos 0, máx $53,462 | OK |
| USD válido: dividend_annual | 1.58e+07 |  |  |  | ≥ 0, finito, centavos, ≤ máx plausible | negativos 0, no finitos 0, máx $15,839,451 | OK |
| USD válido: business_distribution_annual | 2.18e+07 |  |  |  | ≥ 0, finito, centavos, ≤ máx plausible | negativos 0, no finitos 0, máx $21,847,768 | OK |
| USD válido: recurring_income_monthly | 2.19e+06 |  |  |  | ≥ 0, finito, centavos, ≤ máx plausible | negativos 0, no finitos 0, máx $2,194,450 | OK |
| USD válido: value_lost_6m | 3.27e+08 |  |  |  | ≥ 0, finito, centavos, ≤ máx plausible | negativos 0, no finitos 0, máx $327,316,665 | OK |
| Media = teórica: relationship_value | 1.2185 |  | 0.2230 | 0.7676 | t de una muestra | obs 9,436,103.6020 vs teo 9,294,097.2849 | OK |
| Media = teórica: proporción depósitos (inversión) | 1.4947 |  | 0.1350 | 0.7676 | t de una muestra | obs 0.2876 vs teo 0.2857 | OK |
| Media = teórica: tenure_years (edad ≥ 68) | 1.6343 |  | 0.1022 | 0.7676 | t de una muestra | obs 9.1385 vs teo 9.0000 | OK |
| Media = teórica: age_primary | -0.4752 |  | 0.6346 | 0.8953 | t de una muestra | obs 60.4834 vs teo 60.5228 | OK |
| Banda de negocio: relationship_value_mean | 9.44e+06 |  |  |  | [5,000,000, 15,000,000] |  | OK |
| Banda de negocio: relationship_value_median | 4.84e+06 |  |  |  | [3,000,000, 8,000,000] |  | OK |
| Banda de negocio: deposit_share_mean | 0.2876 |  |  |  | [0.2, 0.45] |  | OK |
| Banda de negocio: salary_base_annual_median | 379,203.0200 |  |  |  | [250,000, 600,000] |  | OK |
| Banda de negocio: bonus_to_salary_mean | 0.4950 |  |  |  | [0.3, 0.8] |  | OK |
| Banda de negocio: pension_monthly_median | 9,275.7800 |  |  |  | [5,000, 15,000] |  | OK |
| Banda de negocio: dividend_yield_mean | 0.0200 |  |  |  | [0.015, 0.025] |  | OK |
| Banda de negocio: recurring_income_monthly_median | 33,323.8900 |  |  |  | [15,000, 60,000] |  | OK |
| Banda de negocio: age_primary_mean | 60.4834 |  |  |  | [55, 65] |  | OK |
| Banda de negocio: tenure_years_mean | 8.9860 |  |  |  | [6, 12] |  | OK |
| Banda de negocio: hard_churn_6m_rate | 0.0604 |  |  |  | [0.03, 0.1] |  | OK |
| Banda de negocio: soft_churn_3m_rate | 0.0883 |  |  |  | [0.05, 0.15] |  | OK |

## G · Sesgo

| Prueba | Estadístico | gl | p | p BH | Criterio | Detalle | OK |
|---|---|---|---|---|---|---|---|
| Independencia Spearman: relationship_value ⟂ age_primary | -0.0034 |  | 0.6346 | 0.8953 | ρ = 0 | n = 20,000 | OK |
| Independencia Spearman: relationship_value ⟂ tenure_years | 0.0055 |  | 0.4404 | 0.8050 | ρ = 0 | n = 20,000 | OK |
| Independencia Spearman: bonus_share ⟂ salary_base_annual | 0.0096 |  | 0.3204 | 0.7943 | ρ = 0 | n = 10,772 | OK |
| Independencia Spearman: div_yield ⟂ aum | 0.0098 |  | 0.3465 | 0.7943 | ρ = 0 | n = 9,284 | OK |
| Independencia Spearman: has_credit_anchor ⟂ relationship_value | 0.0065 |  | 0.3563 | 0.7943 | ρ = 0 | n = 20,000 | OK |
| Independencia Spearman: age_primary ⟂ has_credit_anchor | -0.0128 |  | 0.0693 | 0.5899 | ρ = 0 | n = 20,000 | OK |
| Independencia Spearman: z_outflow ⟂ relationship_value | -3.09e-04 |  | 0.9651 | 0.9774 | ρ = 0 | n = 20,000 | OK |
| Independencia Spearman: z_outflow ⟂ age_primary | 0.0091 |  | 0.1983 | 0.7676 | ρ = 0 | n = 20,000 | OK |
| Independencia Spearman: z_outflow ⟂ tenure_years | 0.0022 |  | 0.7596 | 0.9174 | ρ = 0 | n = 20,000 | OK |
| Independencia Spearman: z_outflow ⟂ salary_base_annual | 0.0036 |  | 0.7081 | 0.9174 | ρ = 0 | n = 10,772 | OK |
| Independencia Spearman: z_outflow ⟂ has_investments | -0.0027 |  | 0.7046 | 0.9174 | ρ = 0 | n = 20,000 | OK |
| Independencia Spearman: z_outflow ⟂ has_trust | -0.0072 |  | 0.3092 | 0.7943 | ρ = 0 | n = 20,000 | OK |
| Independencia Spearman: z_neglect ⟂ relationship_value | 5.08e-04 |  | 0.9427 | 0.9693 | ρ = 0 | n = 20,000 | OK |
| Independencia Spearman: z_neglect ⟂ age_primary | 0.0079 |  | 0.2641 | 0.7676 | ρ = 0 | n = 20,000 | OK |
| Independencia Spearman: z_neglect ⟂ tenure_years | -0.0049 |  | 0.4923 | 0.8153 | ρ = 0 | n = 20,000 | OK |
| Independencia Spearman: z_neglect ⟂ salary_base_annual | 0.0124 |  | 0.1966 | 0.7676 | ρ = 0 | n = 10,772 | OK |
| Independencia Spearman: z_neglect ⟂ has_investments | 0.0045 |  | 0.5244 | 0.8271 | ρ = 0 | n = 20,000 | OK |
| Independencia Spearman: z_neglect ⟂ has_trust | -5.49e-04 |  | 0.9381 | 0.9693 | ρ = 0 | n = 20,000 | OK |
| Independencia Spearman: z_service ⟂ relationship_value | -0.0042 |  | 0.5497 | 0.8284 | ρ = 0 | n = 20,000 | OK |
| Independencia Spearman: z_service ⟂ age_primary | 0.0157 |  | 0.0267 | 0.5899 | ρ = 0 | n = 20,000 | OK |
| Independencia Spearman: z_service ⟂ tenure_years | 0.0021 |  | 0.7642 | 0.9174 | ρ = 0 | n = 20,000 | OK |
| Independencia Spearman: z_service ⟂ salary_base_annual | 0.0175 |  | 0.0690 | 0.5899 | ρ = 0 | n = 10,772 | OK |
| Independencia Spearman: z_service ⟂ has_investments | -0.0050 |  | 0.4783 | 0.8153 | ρ = 0 | n = 20,000 | OK |
| Independencia Spearman: z_service ⟂ has_trust | 0.0137 |  | 0.0519 | 0.5899 | ρ = 0 | n = 20,000 | OK |
| Independencia Spearman: eps_idiosyncratic ⟂ relationship_value | 0.0043 |  | 0.5385 | 0.8271 | ρ = 0 | n = 20,000 | OK |
| Independencia Spearman: eps_idiosyncratic ⟂ age_primary | 0.0095 |  | 0.1777 | 0.7676 | ρ = 0 | n = 20,000 | OK |
| Independencia Spearman: eps_idiosyncratic ⟂ tenure_years | 0.0138 |  | 0.0505 | 0.5899 | ρ = 0 | n = 20,000 | OK |
| Independencia Spearman: eps_idiosyncratic ⟂ salary_base_annual | -0.0032 |  | 0.7406 | 0.9174 | ρ = 0 | n = 10,772 | OK |
| Independencia Spearman: eps_idiosyncratic ⟂ has_investments | -0.0066 |  | 0.3492 | 0.7943 | ρ = 0 | n = 20,000 | OK |
| Independencia Spearman: eps_idiosyncratic ⟂ has_trust | -0.0079 |  | 0.2648 | 0.7676 | ρ = 0 | n = 20,000 | OK |
| Target ⟂ frecuencia de pago (con nómina) | 2.0072 | 2 | 0.3666 | 0.7943 | gl = (r−1)(c−1) |  | OK |
| Target ⟂ advisory (con inversiones) | 1.2397 | 1 | 0.2655 | 0.7676 | gl = (r−1)(c−1) |  | OK |
| Target ⟂ dividendos (con inversiones) | 0.8237 | 1 | 0.3641 | 0.7943 | gl = (r−1)(c−1) |  | OK |
| Target ⟂ trust (HNW) | 0.0134 | 1 | 0.9077 | 0.9693 | gl = (r−1)(c−1) |  | OK |
| Target ⟂ negocio vinculado (HNW) | 0.0399 | 1 | 0.8416 | 0.9559 | gl = (r−1)(c−1) |  | OK |
| Efecto diseñado: crédito ancla reduce riesgo | -0.1505 |  |  |  | signo correcto y p < α | Δ índice = -0.151; p = 8.1e-24 | OK |
| Efecto diseñado: UHNW aumenta riesgo | 0.1278 |  |  |  | signo correcto y p < α | Δ índice = +0.128; p = 7.5e-05 | OK |
| Efecto diseñado: antigüedad reduce riesgo | -0.0731 |  |  |  | ρ < 0 y p < α | p = 5.5e-25 | OK |

## H · Variedad y duplicados

| Prueba | Estadístico | gl | p | p BH | Criterio | Detalle | OK |
|---|---|---|---|---|---|---|---|
| Filas duplicadas exactas (sin id) | 0.0000 |  |  |  | = 0 |  | OK |
| Vectores latentes duplicados | 0.0000 |  |  |  | = 0 |  | OK |
| Repeticiones de monto por redondeo: relationship_value | 1.0000 |  |  |  | ≤ Poisson(λ) p99.9 | obs 1 vs esperadas λ = 0.2 (máx 2) | OK |
| Repeticiones de monto por redondeo: salary_base_annual | 1.0000 |  |  |  | ≤ Poisson(λ) p99.9 | obs 1 vs esperadas λ = 1.0 (máx 5) | OK |
| Repeticiones de monto por redondeo: pension_monthly | 15.0000 |  |  |  | ≤ Poisson(λ) p99.9 | obs 15 vs esperadas λ = 15.2 (máx 29) | OK |
| Repeticiones de monto por redondeo: business_distribution_annual | 0.0000 |  |  |  | ≤ Poisson(λ) p99.9 | obs 0 vs esperadas λ = 0.1 (máx 2) | OK |
| Pares casi idénticos (dist < 0.01 d.e., mismas banderas) | 0.0000 |  |  |  | = 0 | distancia mínima al vecino = 0.0351 | OK |

## I · Semilla

| Prueba | Estadístico | gl | p | p BH | Criterio | Detalle | OK |
|---|---|---|---|---|---|---|---|
| Semilla no atípica: tasa hard 6m | 0.0604 |  | 0.8706 | 0.9613 | percentil en rango | percentil 56 | OK |
| Semilla no atípica: tasa soft 3m | 0.0883 |  | 0.3085 | 0.7943 | percentil en rango | percentil 15 | OK |
| Semilla no atípica: AUC techo | 0.8508 |  | 0.7612 | 0.9174 | percentil en rango | percentil 62 | OK |
| Semilla no atípica: media relationship_value | 9.44e+06 |  | 0.2438 | 0.7676 | percentil en rango | percentil 88 | OK |
| Semilla no atípica: mediana relationship_value | 4.84e+06 |  | 0.5821 | 0.8491 | percentil en rango | percentil 71 | OK |
| Semilla no atípica: share UHNW | 0.0551 |  | 0.2040 | 0.7676 | percentil en rango | percentil 90 | OK |
| Semilla no atípica: mediana sueldo | 379,203.0200 |  | 0.7413 | 0.9174 | percentil en rango | percentil 63 | OK |
| Semilla no atípica: curtosis log valor | -0.0539 |  | 0.4129 | 0.8050 | percentil en rango | percentil 79 | OK |
| Semilla no atípica: L-curtosis valor | 0.3596 |  | 0.3731 | 0.7943 | percentil en rango | percentil 81 | OK |
| Semilla no atípica: Hill α valor | 2.3856 |  | 0.4627 | 0.8084 | percentil en rango | percentil 23 | OK |
| p-valores entre semillas ~ U(0,1): KS p relationship_value | 0.0742 |  | 0.2106 | 0.7676 | generador sin sesgo sistemático |  | OK |
| p-valores entre semillas ~ U(0,1): KS p sueldo | 0.0455 |  | 0.7847 | 0.9174 | generador sin sesgo sistemático |  | OK |

## Perfil de colas por columna (USD, valores > 0)

|                              |          n |         media |       mediana |             sd |   asimetría |   curtosis_exceso |   curtosis_exceso_log |   L_asimetría |   L_curtosis |   p99/p50 |   hill_alpha_top1% |
|:-----------------------------|-----------:|--------------:|--------------:|---------------:|------------:|------------------:|----------------------:|--------------:|-------------:|----------:|-------------------:|
| relationship_value           | 20,000.000 | 9,436,103.602 | 4,841,540.750 | 16,481,070.563 |      12.622 |           375.668 |                -0.054 |         0.547 |        0.360 |    14.414 |              2.386 |
| deposit_balance              | 20,000.000 | 3,793,483.859 | 1,513,240.065 |  9,955,701.939 |      31.301 |         2,058.802 |                 0.185 |         0.611 |        0.428 |    23.610 |              2.156 |
| aum                          | 16,991.000 | 6,641,892.465 | 3,394,349.530 | 11,170,310.824 |       8.836 |           175.852 |                -0.046 |         0.547 |        0.361 |    14.901 |              2.476 |
| salary_base_annual           | 10,772.000 |   440,425.394 |   379,203.020 |    242,565.242 |       1.941 |             6.302 |                -0.251 |         0.284 |        0.171 |     3.386 |              5.402 |
| bonus_annual                 | 10,772.000 |   218,427.575 |   166,704.735 |    192,529.802 |       2.291 |             9.566 |                 1.863 |         0.311 |        0.184 |     5.498 |              4.656 |
| pension_monthly              |  6,801.000 |    10,512.041 |     9,275.780 |      5,440.862 |       1.642 |             4.735 |                -0.194 |         0.242 |        0.160 |     3.068 |              5.735 |
| dividend_annual              |  9,284.000 |   135,942.642 |    60,951.705 |    306,319.422 |      19.387 |           796.805 |                 0.101 |         0.589 |        0.411 |    19.436 |              2.110 |
| business_distribution_annual |  5,287.000 |   852,224.291 |   567,076.240 |    984,022.956 |       5.415 |            62.743 |                 0.066 |         0.433 |        0.278 |     8.123 |              2.851 |
| recurring_income_monthly     | 18,652.000 |    50,798.718 |    33,323.890 |     64,322.764 |       6.527 |           107.191 |                 0.731 |         0.432 |        0.287 |     8.801 |              2.672 |

## Grados de libertad de la t-Student (estudio para los Pasos 1+)

Réplicas de n = 20,000. La curtosis de exceso teórica de t(ν) es 6/(ν−4): infinita para ν ≤ 4.

|   ν |   curtosis_exceso_teórica |   curtosis_muestral_mediana |   curtosis_muestral_p5 |   curtosis_muestral_p95 |   CV_curtosis |   ν_MLE_media |   ν_MLE_sesgo_% |   ν_MLE_p5 |   ν_MLE_p95 |
|----:|--------------------------:|----------------------------:|-----------------------:|------------------------:|--------------:|--------------:|----------------:|-----------:|------------:|
|   4 |                   inf     |                      10.513 |                  6.027 |                  43.298 |         1.983 |         4.000 |          -0.004 |      3.821 |       4.160 |
|   5 |                     6.000 |                       4.285 |                  2.869 |                   9.714 |         0.451 |         4.991 |          -0.179 |      4.731 |       5.309 |
|   6 |                     3.000 |                       2.536 |                  2.015 |                   3.817 |         0.199 |         5.956 |          -0.727 |      5.590 |       6.276 |
|   8 |                     1.500 |                       1.402 |                  1.160 |                   1.842 |         0.247 |         7.996 |          -0.055 |      7.335 |       8.908 |

## Semilla de producción vs 200 semillas de referencia

| métrica                    |   semilla producción |         ref p5 |    ref mediana |        ref p95 |   percentil |
|:---------------------------|---------------------:|---------------:|---------------:|---------------:|------------:|
| tasa hard 6m               |               0.0604 |         0.0579 |         0.0601 |         0.0626 |     56.4677 |
| tasa soft 3m               |               0.0883 |         0.0870 |         0.0901 |         0.0931 |     15.4229 |
| AUC techo                  |               0.8508 |         0.8398 |         0.8494 |         0.8574 |     61.9403 |
| media relationship_value   |       9,436,103.6020 | 9,121,683.7089 | 9,301,819.9464 | 9,489,515.3273 |     87.8109 |
| mediana relationship_value |       4,841,540.7500 | 4,740,295.3707 | 4,821,827.8150 | 4,895,271.0785 |     70.8955 |
| share UHNW                 |               0.0551 |         0.0505 |         0.0534 |         0.0557 |     89.8010 |
| mediana sueldo             |         379,203.0200 |   374,503.7833 |   378,434.4150 |   382,634.0355 |     62.9353 |
| curtosis log valor         |              -0.0539 |        -0.1544 |        -0.0902 |         0.0023 |     79.3532 |
| L-curtosis valor           |               0.3596 |         0.3420 |         0.3537 |         0.3691 |     81.3433 |
| Hill α valor               |               2.3856 |         2.2443 |         2.5184 |         2.8029 |     23.1343 |
| KS p relationship_value    |               0.5410 |         0.0404 |         0.5224 |         0.9494 |     50.4975 |
| KS p sueldo                |               0.8923 |         0.0631 |         0.5188 |         0.9478 |     91.2935 |

## Variedad

- combinaciones de banderas: 303
- la más común (%): 5.1050
- distancia al vecino p1: 0.1688
- distancia al vecino mediana: 0.5071
