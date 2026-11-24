# R2: Como tratar os zeros, o atalho do colesterol e o Oldpeak negativo?

O colesterol registrado como 0 está ligado ao diagnóstico (88% dos zerados são doentes), provavelmente pelo hospital de origem. Esse atalho pode aumentar o ARI sem nenhum motivo clínico. Por isso a rodada decide pelo ARI só nos pacientes com colesterol registrado, em quem o atalho não tem como ajudar; o ARI total é relatado. A trava relativa (decisao.trava_atalho_lift) e a de categoria rara impedem um grupo formado pelos ausentes.

Critério: **ari_registrado** (maior é melhor); empate se o IC 95% da diferença pareada (bootstrap, pacientes fora da reamostra) contém zero. Travas: Jaccard mínimo por grupo 0.75; atalho do colesterol até 2.0x a base; nenhum grupo com ≥ 90% numa categoria com < 20% da base.

| opção | ARI | ARI registr. | AUC escore | pureza | recall | espec. | silhueta | silh. nula | Jaccard por grupo | estab. sementes | lift ausente | Δ para a melhor [IC] | situação |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| mediana | 0.498 | 0.516 | 0.914 | 0.853 | 0.878 | 0.822 | 0.165 | 0.082 | 0.98 0.98 | 1.000 | 1.44 | -0.000 [-0.024; +0.021] | VENCEDORA |
| sem_colesterol | 0.504 | 0.523 | 0.914 | 0.855 | 0.880 | 0.824 | 0.175 | 0.075 | 0.98 0.98 | 1.000 | 1.44 | +0.001 [-0.021; +0.021] | empatada com a melhor |
| sem_colesterol_fastingbs | 0.486 | 0.523 | 0.911 | 0.849 | 0.863 | 0.832 | 0.185 | 0.093 | 0.98 0.98 | 0.998 | 1.41 | -0.001 [-0.041; +0.031] | empatada com a melhor |
| mediana_flag | 0.529 | 0.527 | 0.918 | 0.864 | 0.894 | 0.827 | 0.160 | 0.075 | 0.99 0.98 | 1.000 | 1.51 | — | melhor média |
| oldpeak_zero | 0.495 | 0.516 | 0.914 | 0.852 | 0.876 | 0.822 | 0.166 | 0.082 | 0.98 0.98 | 1.000 | 1.43 | +0.001 [-0.021; +0.021] | empatada com a melhor |
| oldpeak_abs | 0.495 | 0.516 | 0.914 | 0.852 | 0.876 | 0.822 | 0.166 | 0.087 | 0.98 0.98 | 1.000 | 1.43 | +0.001 [-0.021; +0.021] | empatada com a melhor |

**Vencedora: mediana** (gravada em vencedor.yaml).
