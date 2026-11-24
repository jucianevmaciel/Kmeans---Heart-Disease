# R3: Qual o número de grupos e qual inicialização?

O k NÃO é escolhido pelo ARI: o diagnóstico tem 2 classes e o ARI favorece k = 2, o que tornaria a escolha circular. Só concorrem os k com todos os grupos estáveis (Jaccard por bootstrap >= decisao.jaccard_min). Entre eles, decide a silhueta, com empate pelo bootstrap pareado; entre os empatados vence o menor k (parcimônia) e depois k-means++ (ordem da grade). A silhueta de referência (colunas embaralhadas) é relatada: o que indica estrutura é o excesso sobre ela. Davies-Bouldin, Calinski-Harabasz, inércia e ARI são relatados (python -m src.cotovelo).

Critério: **silhueta** (maior é melhor); empate se o IC 95% da diferença pareada (bootstrap, pacientes fora da reamostra) contém zero. Travas: Jaccard mínimo por grupo 0.75; atalho do colesterol até 2.0x a base; nenhum grupo com ≥ 90% numa categoria com < 20% da base.

| opção | ARI | ARI registr. | AUC escore | pureza | recall | espec. | silhueta | silh. nula | Jaccard por grupo | estab. sementes | lift ausente | Δ para a melhor [IC] | situação |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| k=2 init=k-means++ | 0.498 | 0.516 | 0.914 | 0.853 | 0.878 | 0.822 | 0.165 | 0.082 | 0.98 0.98 | 1.000 | 1.44 | — | VENCEDORA |
| k=2 init=random | 0.497 | 0.516 | 0.914 | 0.853 | 0.878 | 0.822 | 0.165 | 0.082 | 0.98 0.98 | 1.000 | 1.44 | +0.000 [+0.000; +0.000] | empatada com a melhor |
| k=3 init=k-means++ | 0.428 | 0.474 | 0.909 | 0.848 | 0.876 | 0.813 | 0.181 | 0.082 | 0.92 0.96 0.85 | 0.996 | 1.69 | — | grupo de uma categoria rara |
| k=3 init=random | 0.428 | 0.474 | 0.909 | 0.848 | 0.876 | 0.812 | 0.181 | 0.082 | 0.96 0.84 0.91 | 0.996 | 1.69 | — | grupo de uma categoria rara |
| k=4 init=k-means++ | 0.264 | 0.288 | 0.889 | 0.815 | 0.937 | 0.663 | 0.162 | 0.073 | 0.76 0.88 0.89 0.78 | 0.994 | 1.86 | — | grupo de uma categoria rara |
| k=4 init=random | 0.264 | 0.288 | 0.889 | 0.815 | 0.937 | 0.664 | 0.162 | 0.073 | 0.85 0.72 0.86 0.72 | 0.994 | 1.86 | — | instável (Jaccard < 0.75) |
| k=5 init=k-means++ | 0.232 | 0.264 | 0.892 | 0.807 | 0.933 | 0.651 | 0.172 | 0.075 | 0.87 0.78 0.80 0.77 0.86 | 0.978 | 1.80 | — | grupo de uma categoria rara |
| k=5 init=random | 0.233 | 0.264 | 0.891 | 0.807 | 0.931 | 0.655 | 0.172 | 0.075 | 0.78 0.87 0.79 0.85 0.76 | 0.962 | 1.80 | — | grupo de uma categoria rara |
| k=6 init=k-means++ | 0.220 | 0.245 | 0.883 | 0.813 | 0.896 | 0.709 | 0.184 | 0.080 | 0.64 0.83 0.65 0.92 0.83 0.80 | 0.888 | 1.82 | — | instável (Jaccard < 0.75) |
| k=6 init=random | 0.223 | 0.249 | 0.883 | 0.813 | 0.899 | 0.706 | 0.184 | 0.080 | 0.83 0.72 0.92 0.89 0.87 0.71 | 0.920 | 1.82 | — | instável (Jaccard < 0.75) |
| k=7 init=k-means++ | 0.162 | 0.171 | 0.887 | 0.814 | 0.870 | 0.744 | 0.187 | 0.074 | 0.97 0.84 0.95 0.92 0.99 0.98 0.80 | 0.943 | 1.81 | — | grupo de uma categoria rara |
| k=7 init=random | 0.163 | 0.172 | 0.887 | 0.813 | 0.861 | 0.753 | 0.187 | 0.074 | 0.97 0.94 0.83 0.93 0.75 0.91 0.98 | 0.870 | 1.81 | — | instável (Jaccard < 0.75) |
| k=8 init=k-means++ | 0.151 | 0.162 | 0.891 | 0.820 | 0.799 | 0.847 | 0.197 | 0.071 | 0.98 0.97 0.94 0.96 0.87 0.88 0.99 0.98 | 0.987 | 1.81 | — | grupo de uma categoria rara |
| k=8 init=random | 0.149 | 0.160 | 0.890 | 0.818 | 0.803 | 0.836 | 0.195 | 0.071 | 0.83 0.76 0.99 0.98 0.98 0.88 0.94 0.95 | 0.956 | 1.81 | — | grupo de uma categoria rara |

- k=3 init=k-means++: grupo 2: 100% ST_Slope=Down (base 7%)
- k=3 init=random: grupo 1: 100% ST_Slope=Down (base 7%)
- k=4 init=k-means++: grupo 0: 100% RestingECG=ST (base 19%)
- k=5 init=k-means++: grupo 2: 100% RestingECG=ST (base 19%)
- k=5 init=random: grupo 2: 100% RestingECG=ST (base 19%)
- k=7 init=k-means++: grupo 2: 100% ChestPainType=ATA (base 19%)
- k=8 init=k-means++: grupo 0: 100% ChestPainType=ATA (base 19%)
- k=8 init=random: grupo 4: 100% ChestPainType=ATA (base 19%)

**Vencedora: k=2 init=k-means++** (gravada em vencedor.yaml).
