# R0: Quais são as referências?

As referências supervisionadas usam o diagnóstico no treino (validação cruzada 5 dobras, previsões fora da dobra). Servem de teto para o K-Means, que não vê o rótulo. Todas são comparadas pelas mesmas métricas: ARI, pureza e AUC do escore.

Rodada sem escolha (referências).

| opção | ARI | ARI registr. | AUC escore | pureza | recall | espec. | silhueta | silh. nula | Jaccard por grupo | estab. sementes | lift ausente | Δ para a melhor [IC] | situação |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| dummy | 0.000 | 0.000 | 0.499 | 0.553 | 1.000 | 0.000 | — | — | — | 1.000 | — | — | referência supervisionada |
| regressao_logistica | 0.518 | 0.519 | 0.922 | 0.860 | 0.887 | 0.826 | — | — | — | 0.930 | 1.49 | — | referência supervisionada |
| gradient_boosting | 0.531 | 0.520 | 0.922 | 0.865 | 0.891 | 0.832 | — | — | — | 0.818 | 1.56 | — | referência supervisionada |
| kmeans_k2 | 0.318 | 0.344 | 0.858 | 0.782 | 0.774 | 0.793 | 0.176 | 0.102 | 0.97 0.97 | 1.000 | 1.43 | — | — |
| gmm_k2 | 0.340 | 0.386 | 0.849 | 0.792 | 0.713 | 0.890 | 0.112 | 0.102 | 0.59 0.63 | 1.000 | 1.52 | — | instável (Jaccard < 0.75) |
| ward_k2 | 0.345 | 0.338 | 0.870 | 0.794 | 0.829 | 0.751 | 0.152 | 0.102 | 0.81 0.77 | 1.000 | 1.48 | — | — |

