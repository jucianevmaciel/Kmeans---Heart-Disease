# R5: Os vencedores funcionam juntos?

"completa" é o vencedor acumulado de R1–R4, com o k da R3. Cada "sem_*" volta um vencedor ao valor da base. As retiradas vêm primeiro na ordem de desempate: se uma delas empatar com a completa, vence a versão com menos componentes. Retiradas que não mudam nada (o vencedor já era o valor da base) são ignoradas. O k é reajustado depois, na R5b, pela silhueta: aqui o critério é o ARI, que favorece k = 2, e reajustar o k por ele tornaria a escolha circular.

Critério: **ari** (maior é melhor); empate se o IC 95% da diferença pareada (bootstrap, pacientes fora da reamostra) contém zero. Travas: Jaccard mínimo por grupo 0.75; atalho do colesterol até 2.0x a base; nenhum grupo com ≥ 90% numa categoria com < 20% da base.

| opção | ARI | ARI registr. | AUC escore | pureza | recall | espec. | silhueta | silh. nula | Jaccard por grupo | estab. sementes | lift ausente | Δ para a melhor [IC] | situação |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| sem_escalonamento_vencedor | 0.318 | 0.344 | 0.858 | 0.782 | 0.774 | 0.793 | 0.176 | 0.102 | 0.97 0.97 | 1.000 | 1.43 | +0.178 [+0.119; +0.245] | — |
| completa k=2 | 0.498 | 0.516 | 0.914 | 0.853 | 0.878 | 0.822 | 0.165 | 0.082 | 0.98 0.98 | 1.000 | 1.44 | — | VENCEDORA |

**Vencedora: completa k=2** (gravada em vencedor.yaml).
