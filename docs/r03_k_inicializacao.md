# R3 — Número de grupos (k) e inicialização

**Pergunta:** quantos grupos o K-Means deve formar, e qual inicialização usar?

**Status:** decidida. **Vencedora: k = 2 com k-means++**, gravada em
`results/r03_k_inicializacao/vencedor.yaml` e herdada pela R4.
**Execução:** 23/11/2026 (14 opções × 20 sementes + 100 reamostras bootstrap).

## Configuração

- **Herda da R2:** `standard_all`, zeros pela mediana, Oldpeak mantido, sem redução,
  n_init = 50.
- **Grade:** k de 2 a 8 × inicialização (k-means++ ou random), na ordem de desempate:
  menor k primeiro, e k-means++ antes de random.
- **Critério:** silhueta (separação geométrica dos grupos, sem usar o diagnóstico).
  **O k não é escolhido pelo ARI**: com 2 classes no diagnóstico, o ARI favorece k = 2,
  e a escolha seria circular. ARI, Davies-Bouldin, Calinski-Harabasz e inércia são só
  relatados.
- **Regra:** só concorrem os k que passam pelas travas (Jaccard ≥ 0,75 em todos os
  grupos; colesterol ausente ≤ 2× a base; nenhum grupo com ≥ 90% numa categoria com
  < 20% da base). Entre eles, decide a silhueta, com empate se o IC 95% da diferença
  pareada (bootstrap) contém zero; entre os empatados, vence o menor k. A silhueta nula
  (colunas embaralhadas) é relatada ao lado.

## Resultados

| k | Init | ARI | ARI registr. | AUC | Silhueta (nula) | Davies-B. | Calinski-H. | Inércia | Jaccard por grupo | Situação |
|---|---|---|---|---|---|---|---|---|---|---|
| **2** | **k-means++** | **0,498** | **0,516** | **0,914** | 0,165 (0,082) | 2,160 | 179,6 | 13.815 | 0,98 · 0,98 | **vencedora** |
| 2 | random | 0,497 | 0,516 | 0,914 | 0,165 (0,082) | 2,160 | 179,6 | 13.815 | 0,98 · 0,98 | empatada |
| 3 | k-means++ | 0,428 | 0,474 | 0,909 | 0,181 (0,082) | 1,928 | 136,4 | 12.728 | 0,92 · 0,96 · 0,85 | categoria rara |
| 3 | random | 0,428 | 0,474 | 0,909 | 0,181 (0,082) | 1,928 | 136,4 | 12.728 | 0,96 · 0,84 · 0,91 | categoria rara |
| 4 | k-means++ | 0,264 | 0,288 | 0,889 | 0,162 (0,073) | 1,972 | 122,7 | 11.779 | 0,76 · 0,88 · 0,89 · 0,78 | categoria rara |
| 4 | random | 0,264 | 0,288 | 0,889 | 0,162 (0,073) | 1,972 | 122,7 | 11.779 | 0,85 · 0,72 · 0,86 · 0,72 | instável |
| 5 | k-means++ | 0,232 | 0,264 | 0,892 | 0,172 (0,075) | 1,784 | 117,9 | 10.897 | mín. 0,77 | categoria rara |
| 5 | random | 0,233 | 0,264 | 0,891 | 0,172 (0,075) | 1,784 | 117,8 | 10.898 | mín. 0,76 | categoria rara |
| 6 | k-means++ | 0,220 | 0,245 | 0,883 | 0,184 (0,080) | 1,685 | 116,1 | 10.096 | mín. 0,64 | instável |
| 6 | random | 0,223 | 0,249 | 0,883 | 0,184 (0,080) | 1,677 | 116,3 | 10.090 | mín. 0,71 | instável |
| 7 | k-means++ | 0,162 | 0,171 | 0,887 | 0,187 (0,074) | 1,686 | 115,9 | 9.370 | mín. 0,80 | categoria rara |
| 7 | random | 0,163 | 0,172 | 0,887 | 0,187 (0,074) | 1,691 | 115,6 | 9.382 | mín. 0,75 | instável |
| 8 | k-means++ | 0,151 | 0,162 | 0,891 | 0,197 (0,071) | 1,642 | 112,6 | 8.854 | mín. 0,87 | categoria rara |
| 8 | random | 0,149 | 0,160 | 0,890 | 0,195 (0,071) | 1,641 | 112,4 | 8.863 | mín. 0,76 | categoria rara |

**Grupos que acionaram a trava de categoria rara** (100% dos pacientes do grupo numa
categoria):

| k | Categoria isolada | Prevalência na base |
|---|---|---|
| 3 | ST_Slope = Down | 7% |
| 4, 5 | RestingECG = ST | 19% |
| 7, 8 | ChestPainType = ATA | 19% |

Nas opções marcadas como "instável", a trava de estabilidade é checada antes e aparece
como motivo, mas elas também têm grupos de uma categoria só (no k = 6, por exemplo,
ChestPainType = TA, com 5% da base).

**Comparação pareada da silhueta com o k = 2** (bootstrap, pacientes fora da reamostra;
só descritiva, porque nenhum k ≥ 3 é elegível):

| k (k-means++) | Δ silhueta | IC 95% |
|---|---|---|
| 3 | +0,010 | [−0,030; +0,024] |
| 4 | −0,004 | [−0,022; +0,030] |
| 5 | +0,007 | [−0,014; +0,020] |
| 6 | +0,011 | [−0,010; +0,031] |
| 7 | +0,020 | [+0,005; +0,031] |
| 8 | +0,025 | [+0,004; +0,045] |

## Achados

1. **O k = 2 é o único elegível.** Todos os k de 3 a 8 são barrados: k = 3, 4, 5, 7 e 8
   por terem um grupo formado inteiramente por uma categoria, e k = 6 por
   instabilidade (Jaccard mínimo de 0,64). Como não há outro k na disputa, a silhueta
   não chega a decidir; o k = 2 vence pelas travas.
2. **Cada grupo a mais isola uma categoria.** O terceiro grupo são os 63 pacientes com
   ST descendente (Down, 7% da base). Com mais grupos, aparecem as categorias do ECG de
   repouso e os tipos de dor torácica. É o efeito do `standard_all` previsto na R1:
   categorias raras ganham peso na distância e viram grupos próprios.
3. **As métricas internas não apontam um k.** A silhueta fica entre 0,162 e 0,197 em
   todos os k, abaixo de 0,25 (faixa sem estrutura substancial; Kaufman & Rousseeuw,
   1990), e só k = 7 e 8 superam o k = 2 com IC excluindo zero. O Davies-Bouldin melhora
   com o k (2,16 → 1,64) e o Calinski-Harabasz piora (180 → 113): as duas discordam. A
   inércia cai de 5% a 8% a cada grupo adicional, sem dobra que indique um "cotovelo".
4. **A silhueta sobe com o k pelo motivo errado.** De 0,165 (k = 2) a 0,197 (k = 8),
   enquanto a silhueta nula fica estável em 0,07–0,08. Grupos de uma categoria só são
   bem separados por construção. Sem a trava, a silhueta escolheria o k = 8, com ARI de
   0,151.
5. **A concordância com o diagnóstico cai com o k.** O ARI vai de 0,498 (k = 2) a 0,151
   (k = 8), e a AUC do escore, de 0,914 a 0,88–0,89. O ARI não entra na decisão, mas
   confirma que os grupos a mais não acompanham a doença.
6. **A inicialização não faz diferença.** Com n_init = 50, k-means++ e random chegam à
   mesma solução em todos os k (silhueta e ARI iguais até a terceira casa; Δ = +0,000
   [+0,000; +0,000] no k = 2). Vence o k-means++ pela ordem de desempate. As diferenças
   de estabilidade entre as duas (k = 4, 7 e 8) vêm do bootstrap, não do ajuste.
7. **A escolha depende do limite da trava de categoria rara.** Com 20% (adotado), o k = 4
   é barrado pelo grupo de ECG = ST (19,4%). Com 15% ou 10%, as categorias de 19%
   passariam e a regra escolheria o k = 4 (ver anotacoes_artigo.md, "Sensibilidade", e
   docs/alternativa_k4.md). Por isso os outros k entram como análise complementar
   (docs/variacoes_k.md).

## Implicações para as próximas rodadas

- **Nada muda nos arquivos.** A R4 herda `standard_all`, `mediana`, k = 2 e k-means++.
- **A figura da rodada** está em `results/r03_k_inicializacao/cotovelo.png` (curvas
  de cada métrica por k).
- **Na R4 (redução de dimensão),** o critério volta a ser o ARI, com k = 2. Espera-se
  empate entre "sem redução" e as variantes de PCA.
- **A R5b refaz esta escolha** sobre a combinação final. Se a R4 e a R5 mantiverem a
  configuração atual, a R5b deve repetir o k = 2.
- **As análises complementares de k** (`variacoes_k` e `alternativa_k4`) podem ser
  rodadas depois da R5b.

## Para o texto do artigo

> O número de grupos foi escolhido sem usar o diagnóstico, para evitar circularidade:
> com duas classes, o ARI favorece k = 2. Foram avaliados k de 2 a 8, com inicialização
> k-means++ e aleatória (50 inicializações cada). Só concorreram os valores de k cujos
> grupos fossem estáveis sob reamostragem (Jaccard ≥ 0,75) e não formados por uma única
> categoria rara. Todos os valores de k ≥ 3 apresentaram ao menos um grupo composto
> inteiramente por uma categoria — a inclinação descendente do segmento ST (k = 3), as
> categorias do eletrocardiograma de repouso (k = 4 e 5) ou os tipos de dor torácica
> (k ≥ 6) — ou instabilidade, e k = 2 foi o único elegível. As métricas internas não
> indicaram um k superior: a silhueta variou entre 0,162 e 0,197, com a referência obtida
> pelas variáveis embaralhadas estável entre 0,07 e 0,08, e os índices de Davies-Bouldin
> e Calinski-Harabasz apontaram em direções opostas. As duas inicializações produziram
> soluções idênticas.

## Cuidados

- **Não dizer que a silhueta escolheu o k = 2.** Ela é a segunda menor entre os k
  testados. O k = 2 vence porque é o único que passa pelas travas.
- **Não dizer que os dados "têm 2 grupos naturais".** A silhueta é fraca em todos os k.
  O que se pode afirmar é que, entre os k testados, só o k = 2 forma grupos que não se
  reduzem a uma categoria.
- **O limite de 20% é uma escolha do grupo.** Explicar o motivo (os grupos que ele barra
  são 100% de uma categoria) e citar a análise de sensibilidade.
- **"Instável" e "categoria rara" não são exclusivos.** A tabela mostra o primeiro motivo
  checado; no k = 6, o grupo de ChestPainType = TA também é de uma categoria só.
- **A inicialização é irrelevante só com n_init = 50.** Com poucas inicializações, a
  random tende a variar mais. Registrar o n_init junto com a conclusão.

## Arquivos de origem

- `results/r03_k_inicializacao/decisao.md`: tabela da rodada, regra aplicada e grupos de categoria rara
- `results/r03_k_inicializacao/resumo.csv`: médias, desvios, travas e métricas internas por opção
- `results/r03_k_inicializacao/por_semente.csv`: uma linha por opção × semente
- `results/r03_k_inicializacao/bootstrap.csv`: ARI, ARI registrado, silhueta e Jaccard fora da reamostra (100 reamostras pareadas)
- `results/r03_k_inicializacao/vencedor.yaml`: configuração herdada pela R4
- `results/r03_k_inicializacao/cotovelo.png`: curvas por k (`python -m src.cotovelo`)
- `configs/r03_k_inicializacao.yaml`: definição da rodada
- Comparação pareada da silhueta com o k = 2: calculada à parte a partir do `bootstrap.csv`
