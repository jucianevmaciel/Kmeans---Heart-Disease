# R1: O escalonamento importa?

standard_all padroniza também as colunas 0/1 (one-hot e FastingBS). No K-Means o peso de cada coluna na distância depende da escala dela: uma categoria com prevalência p fica com distância 1/sqrt(p(1-p)) entre "tem" e "não tem", então as raras ganham peso extra (ST_Slope = Down, p = 0,07: 3,9; uma comum: 2,0). A trava de categoria rara (decisao.trava_categoria) elimina opções em que um grupo é só uma categoria rara. A silhueta não é comparável entre escalonamentos (espaços diferentes), por isso o critério é o ARI.

Critério: **ari** (maior é melhor); empate se o IC 95% da diferença pareada (bootstrap, pacientes fora da reamostra) contém zero. Travas: Jaccard mínimo por grupo 0.75; atalho do colesterol até 2.0x a base; nenhum grupo com ≥ 90% numa categoria com < 20% da base.

| opção | ARI | ARI registr. | AUC escore | pureza | recall | espec. | silhueta | silh. nula | Jaccard por grupo | estab. sementes | lift ausente | Δ para a melhor [IC] | situação |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| nenhum | -0.001 | 0.011 | — | 0.553 | 1.000 | 0.000 | 0.395 | 0.391 | 0.98 0.94 | 1.000 | 1.35 | +0.493 [+0.417; +0.570] | — |
| standard | 0.318 | 0.344 | 0.858 | 0.782 | 0.774 | 0.793 | 0.176 | 0.102 | 0.97 0.97 | 1.000 | 1.43 | +0.178 [+0.119; +0.245] | — |
| standard_all | 0.498 | 0.516 | 0.914 | 0.853 | 0.878 | 0.822 | 0.165 | 0.082 | 0.98 0.98 | 1.000 | 1.44 | — | VENCEDORA |
| minmax | 0.410 | 0.438 | 0.902 | 0.820 | 0.843 | 0.793 | 0.234 | 0.105 | 1.00 1.00 | 1.000 | 1.30 | +0.088 [+0.023; +0.144] | — |
| robust | 0.348 | 0.410 | 0.882 | 0.795 | 0.772 | 0.824 | 0.158 | 0.110 | 0.96 0.96 | 1.000 | 1.36 | +0.134 [+0.056; +0.221] | — |

**Vencedora: standard_all** (gravada em vencedor.yaml).
