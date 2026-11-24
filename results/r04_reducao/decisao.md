# R4: Reduzir a dimensão ajuda?

O kbest escolhe as colunas usando o diagnóstico (f_classif), então fica fora da disputa: aparece na tabela, mas não pode vencer. A silhueta no espaço do PCA não é comparável com a do espaço original; o critério é o ARI.

Critério: **ari** (maior é melhor); empate se o IC 95% da diferença pareada (bootstrap, pacientes fora da reamostra) contém zero. Travas: Jaccard mínimo por grupo 0.75; atalho do colesterol até 2.0x a base; nenhum grupo com ≥ 90% numa categoria com < 20% da base.

| opção | ARI | ARI registr. | AUC escore | pureza | recall | espec. | silhueta | silh. nula | Jaccard por grupo | estab. sementes | lift ausente | Δ para a melhor [IC] | situação |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| sem_reducao | 0.498 | 0.516 | 0.914 | 0.853 | 0.878 | 0.822 | 0.165 | 0.082 | 0.98 0.98 | 1.000 | 1.44 | +0.001 [-0.021; +0.017] | VENCEDORA |
| pca_2 | 0.473 | 0.493 | 0.903 | 0.844 | 0.852 | 0.834 | 0.456 | 0.453 | 0.97 0.98 | 1.000 | 1.47 | +0.015 [-0.026; +0.059] | empatada com a melhor |
| pca_3 | 0.488 | 0.500 | 0.906 | 0.850 | 0.872 | 0.822 | 0.378 | 0.365 | 0.97 0.98 | 1.000 | 1.46 | +0.009 [-0.033; +0.052] | empatada com a melhor |
| pca_5 | 0.492 | 0.504 | 0.908 | 0.851 | 0.872 | 0.824 | 0.290 | 0.273 | 0.97 0.98 | 1.000 | 1.46 | +0.008 [-0.029; +0.058] | empatada com a melhor |
| pca_90pct | 0.501 | 0.516 | 0.913 | 0.854 | 0.880 | 0.822 | 0.181 | 0.166 | 0.98 0.98 | 1.000 | 1.45 | — | melhor média |
| kbest_4 | 0.407 | 0.438 | 0.884 | 0.819 | 0.839 | 0.795 | 0.543 | 0.284 | 1.00 1.00 | 1.000 | 1.30 | — | fora da disputa |
| kbest_8 | 0.476 | 0.508 | 0.905 | 0.845 | 0.868 | 0.817 | 0.319 | 0.166 | 0.97 0.97 | 0.999 | 1.38 | — | fora da disputa |

**Vencedora: sem_reducao** (gravada em vencedor.yaml).
