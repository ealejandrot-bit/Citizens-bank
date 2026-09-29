| modelo   | regla                                 | tramo     |   precisión dev % |   precisión holdout % |   tasa oficial del tramo % |   precisión ≥ tasa oficial del tramo (holdout) |
|:---------|:--------------------------------------|:----------|------------------:|----------------------:|---------------------------:|-----------------------------------------------:|
| A        | banker_change_6m_flag                 | eliminado |            17.442 |                15.642 |                   nan      |                                                |
| A        | complaint_escalated_flag              | eliminado |            17.274 |                15.888 |                   nan      |                                                |
| A        | repeat_complaint_flag                 | Alto      |            20.629 |                24.658 |                    14.2357 |                                              1 |
| A        | relationship_dissatisfaction_flag     | Alto      |            15.854 |                19.231 |                    14.2357 |                                              1 |
| A        | trustee_change_flag                   | Alto      |            19.487 |                24.468 |                    14.2357 |                                              1 |
| A        | transfer_to_competitor_pct_90d ≥ 0.10 | Alto      |            30.263 |                27.673 |                    14.2357 |                                              1 |
| A        | new_external_destinations_90d ≥ 2     | Alto      |            21.818 |                33.028 |                    14.2357 |                                              1 |
| A        | pension_deposit_stopped_flag (D9.1)   | Crítico   |            29.032 |                37.5   |                    38.4557 |                                              0 |
| A-lite   | banker_change_6m_flag                 | eliminado |            17.442 |                15.642 |                   nan      |                                                |
| A-lite   | complaint_escalated_flag              | eliminado |            17.274 |                15.888 |                   nan      |                                                |
| A-lite   | repeat_complaint_flag                 | Alto      |            20.629 |                24.658 |                    14.0189 |                                              1 |
| A-lite   | relationship_dissatisfaction_flag     | Alto      |            15.854 |                19.231 |                    14.0189 |                                              1 |
| A-lite   | trustee_change_flag                   | Alto      |            19.487 |                24.468 |                    14.0189 |                                              1 |
| A-lite   | transfer_to_competitor_pct_90d ≥ 0.10 | Alto      |            30.263 |                27.673 |                    14.0189 |                                              1 |
| A-lite   | new_external_destinations_90d ≥ 2     | Alto      |            21.818 |                33.028 |                    14.0189 |                                              1 |
| A-lite   | pension_deposit_stopped_flag (D9.1)   | Crítico   |            29.032 |                37.5   |                    35.8445 |                                              1 |
