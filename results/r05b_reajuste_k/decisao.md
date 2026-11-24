# R5b: Com a combinação final, o melhor k continua o mesmo?

Mesmo critério da R3 (só k com todos os grupos estáveis; silhueta com empate pelo bootstrap pareado; entre os empatados, o menor k; ARI só relatado), agora sobre a combinação vencedora da R5. O vencedor desta rodada é a configuração final, usada em R6, R7 e R8.

Critério: **silhueta** (maior é melhor); empate se o IC 95% da diferença pareada (bootstrap, pacientes fora da reamostra) contém zero. Travas: Jaccard mínimo por grupo 0.75; atalho do colesterol até 2.0x a base; nenhum grupo com ≥ 90% numa categoria com < 20% da base.

| opção | ARI | ARI registr. | AUC escore | pureza | recall | espec. | silhueta | silh. nula | Jaccard por grupo | estab. sementes | lift ausente | Δ para a melhor [IC] | situação |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| k=2 | 0.498 | 0.516 | 0.914 | 0.853 | 0.878 | 0.822 | 0.165 | 0.082 | 0.98 0.98 | 1.000 | 1.44 | — | VENCEDORA |
| k=3 | 0.428 | 0.474 | 0.909 | 0.848 | 0.876 | 0.813 | 0.181 | 0.082 | 0.92 0.96 0.85 | 0.996 | 1.69 | — | grupo de uma categoria rara |
| k=4 | 0.264 | 0.288 | 0.889 | 0.815 | 0.937 | 0.663 | 0.162 | 0.073 | 0.76 0.88 0.89 0.78 | 0.994 | 1.86 | — | grupo de uma categoria rara |
| k=5 | 0.232 | 0.264 | 0.892 | 0.807 | 0.933 | 0.651 | 0.172 | 0.075 | 0.87 0.78 0.80 0.77 0.86 | 0.978 | 1.80 | — | grupo de uma categoria rara |
| k=6 | 0.220 | 0.245 | 0.883 | 0.813 | 0.896 | 0.709 | 0.184 | 0.080 | 0.64 0.83 0.65 0.92 0.83 0.80 | 0.888 | 1.82 | — | instável (Jaccard < 0.75) |

- k=3: grupo 2: 100% ST_Slope=Down (base 7%)
- k=4: grupo 0: 100% RestingECG=ST (base 19%)
- k=5: grupo 2: 100% RestingECG=ST (base 19%)

**Vencedora: k=2** (gravada em vencedor.yaml).
