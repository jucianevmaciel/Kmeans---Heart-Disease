# R1 — Escalonamento

**Pergunta:** o escalonamento das variáveis muda o quanto os grupos do K-Means
coincidem com o diagnóstico? Qual escalonamento usar?

**Status:** decidida. **Vencedora: `standard_all`**, gravada em
`results/r01_escalonamento/vencedor.yaml` e herdada pela R2.
**Execução:** 23/11/2026 (5 opções × 20 sementes + 100 reamostras bootstrap).

## Configuração

- **Parte do `base.yaml`:** zeros pela mediana, Oldpeak mantido, sem redução,
  K-Means k = 2, k-means++, n_init = 50.
- **Opções, em ordem de desempate:**

| Opção | O que faz |
|---|---|
| `nenhum` | sem escalonamento; numéricas na escala original, categóricas 0/1 |
| `standard` | numéricas padronizadas (média 0, desvio 1); categóricas e FastingBS em 0/1 |
| `standard_all` | padroniza **todas** as colunas, inclusive as 0/1 do one-hot e FastingBS |
| `minmax` | numéricas reescaladas para [0, 1]; categóricas em 0/1 |
| `robust` | numéricas centradas na mediana e divididas pelo intervalo interquartil |

- **Critério:** ARI. A silhueta não serve aqui porque cada escalonamento cria um
  espaço diferente, e silhuetas de espaços diferentes não são comparáveis.
- **Regra:** empate se o IC 95% da diferença pareada de ARI (bootstrap, pacientes fora
  da reamostra) contém zero. Travas: Jaccard ≥ 0,75 em todos os grupos; colesterol
  ausente ≤ 2× a base; nenhum grupo de uma categoria rara.

## Resultados

| Opção | ARI | ARI registr. | NMI | Acurácia | Recall | Espec. | AUC | Silhueta (nula) | Jaccard | Lift ausente |
|---|---|---|---|---|---|---|---|---|---|---|
| `nenhum` | −0,001 | 0,011 | 0,000 | 0,553 | 1,000 | 0,000 | — | 0,395 (0,391) | 0,98 · 0,94 | 1,35 |
| `standard` | 0,318 | 0,344 | 0,244 | 0,782 | 0,774 | 0,793 | 0,858 | 0,176 (0,102) | 0,97 · 0,97 | 1,43 |
| **`standard_all`** | **0,498** | **0,516** | **0,394** | **0,853** | **0,878** | **0,822** | **0,914** | 0,165 (0,082) | 0,98 · 0,98 | 1,44 |
| `minmax` | 0,410 | 0,438 | 0,316 | 0,820 | 0,843 | 0,793 | 0,902 | 0,234 (0,105) | 1,00 · 1,00 | 1,30 |
| `robust` | 0,348 | 0,410 | 0,273 | 0,795 | 0,772 | 0,824 | 0,882 | 0,158 (0,110) | 0,96 · 0,96 | 1,36 |

Todas as opções passam pelas três travas. A maior concentração de uma categoria num
grupo é 40% (ChestPainType = ATA, no `standard_all`), longe do limite de 90%.

**Comparação pareada por bootstrap** (`standard_all` − outra; ARI fora da reamostra):

| Comparação | Δ ARI | IC 95% | Δ ARI registrado | IC 95% |
|---|---|---|---|---|
| − `minmax` | +0,088 | [+0,023; +0,144] | +0,080 | [+0,009; +0,150] |
| − `robust` | +0,134 | [+0,056; +0,221] | +0,099 | [+0,021; +0,192] |
| − `standard` | +0,178 | [+0,119; +0,245] | +0,167 | [+0,081; +0,241] |
| − `nenhum` | +0,493 | [+0,417; +0,570] | +0,498 | [+0,396; +0,589] |

Nenhum intervalo contém zero: o `standard_all` vence todas as outras opções, sem
empate. Ele também fica à frente da `minmax` em 99% das reamostras.

**Peso de cada bloco de variáveis na distância** (fração da variância total das
colunas no espaço do K-Means):

| Opção | Peso das 5 numéricas | Colunas que mais pesam | ARI |
|---|---|---|---|
| `nenhum` | 100% | Cholesterol (73%), MaxHR (17%) | −0,001 |
| `standard` | 68% | RestingBP, Cholesterol, MaxHR (14% cada) | 0,318 |
| `robust` | 59% | Cholesterol (18%), RestingBP (14%) | 0,348 |
| `standard_all` | 28% | todas as 18 colunas com o mesmo peso (~6%) | 0,498 |
| `minmax` | 5% | ST_Slope, ChestPainType (10% cada) | 0,410 |

## Achados

1. **O escalonamento é a decisão que mais pesa até aqui.** Sozinho, ele leva o ARI de
   0,318 (`standard`, a configuração da R0) para 0,498 (`standard_all`). O ganho de
   +0,178 [+0,119; +0,245] é a maior parte da distância até o teto supervisionado da
   R0 (regressão logística: 0,518). A AUC do escore sobe de 0,858 para 0,914, contra
   0,922 da regressão logística.
2. **Sem escalonamento, o K-Means não encontra a doença.** ARI = −0,001: o colesterol
   ocupa 73% da variância e decide os grupos sozinho. Os dois grupos separam
   colesterol médio de 160 e de 309 mg/dL, com 55% de doentes em cada um (a mesma
   proporção da base). A silhueta é a maior da rodada (0,395), mas igual à nula
   (0,391): estrutura de uma única variável, que não tem relação com o diagnóstico.
3. **O ganho vem de dar mais peso às variáveis categóricas.** No `standard`, as 5
   numéricas ficam com 68% do peso. As colunas 0/1 têm variância p(1 − p) ≤ 0,25,
   contra 1 das numéricas padronizadas, então pesam pouco. O `standard_all` dá peso
   igual às 18 colunas, e as categóricas passam a 72%. São justamente elas que mais
   separam doentes de saudáveis. Os grupos vencedores diferem sobretudo em
   ST_Slope = Up (7% contra 89%) e angina no esforço (66% contra 7%); o colesterol
   médio quase não muda (184 contra 218).
4. **A relação não é só "quanto mais categórica, melhor".** O `minmax` deixa só 5% do
   peso para as numéricas e fica abaixo do `standard_all` (0,410 contra 0,498). O
   melhor resultado combina categóricas dominantes com as numéricas ainda
   contribuindo.
5. **O ganho não vem do atalho do colesterol.** O `standard_all` vence também no ARI
   só dos pacientes com colesterol registrado (0,516; todos os ICs pareados excluem
   zero). A concentração de colesterol ausente é praticamente a mesma em todas as
   opções (lift de 1,30 a 1,44).
6. **Todas as opções são estáveis.** O Jaccard fica entre 0,94 e 1,00 em todos os
   grupos. A escolha é decidida só pela concordância com o diagnóstico, não por
   instabilidade.
7. **A silhueta engana entre escalonamentos.** Ela ordena as opções ao contrário do
   ARI: `nenhum` 0,395 > `minmax` 0,234 > `standard` 0,176 > `standard_all` 0,165.
   Isso confirma a nota da rodada: a silhueta não pode ser critério aqui.
8. **O vencedor tem um efeito colateral conhecido.** No `standard_all`, uma categoria
   com prevalência p fica com distância 1/√(p(1 − p)) entre "tem" e "não tem", e as
   raras ganham peso: ST_Slope = Down (7%) pesa 3,9, contra 2,0 de uma categoria
   comum. Com k = 2 isso não cria problema (a maior concentração é 40%). Com k ≥ 3, é
   o que faz surgir grupos de uma categoria só; a trava de categoria rara (R3/R5b)
   trata disso.

## Implicações para as próximas rodadas

- **A R2 herda `standard_all`** automaticamente. Não é preciso mudar nada nos
  arquivos.
- **Na R2, a opção `mediana_flag` cria a coluna `Cholesterol_ausente`**, que tem 19% da
  base. Sob `standard_all`, essa coluna ganha peso maior que o de uma categoria comum
  (≈ 2,6). O critério da R2 (ARI só nos pacientes com colesterol registrado) e a trava
  do atalho existem para isso. Vale olhar o lift dessa opção com atenção.
- **Nas rodadas do k (R3/R5b),** o efeito do item 8 deve aparecer: esperar opções
  eliminadas pela trava de categoria rara.
- **Nova referência de ARI:** 0,498. As próximas rodadas medem se o tratamento dos
  dados (R2), o k (R3) ou a redução (R4) acrescentam algo a esse valor.

## Para o texto do artigo

> Cinco escalonamentos foram comparados, todos com K-Means k = 2: sem escalonamento,
> padronização das variáveis numéricas (z-score), padronização de todas as colunas
> (incluindo as indicadoras do one-hot), min-max e escalonamento robusto. A
> padronização de todas as colunas obteve o maior ARI (0,498; AUC do escore = 0,914),
> superior a todas as alternativas na comparação pareada por bootstrap (diferença para
> a padronização só das numéricas: +0,178, IC 95% de +0,119 a +0,245). Sem
> escalonamento, o colesterol concentrou 73% da variância e determinou sozinho os
> grupos, que não tiveram relação com o diagnóstico (ARI = −0,001). O ganho da
> padronização completa vem de igualar o peso das variáveis categóricas ao das
> numéricas: na padronização só das numéricas, elas respondiam por 68% da variância;
> na completa, por 28%. Os grupos resultantes diferem sobretudo pela inclinação do
> segmento ST e pela angina induzida pelo esforço. O resultado se manteve quando a
> avaliação foi restrita aos pacientes com colesterol registrado (ARI = 0,516).

## Cuidados

- **Não afirmar que "padronizar sempre melhora o K-Means".** O resultado vale para esta
  base, em que as categóricas carregam a informação mais ligada ao diagnóstico. Em
  outra base, o mesmo peso extra poderia piorar o resultado.
- **A escolha usou o diagnóstico.** O critério é o ARI. O agrupamento não vê o rótulo,
  mas a escolha do escalonamento sim. Isso está registrado como decisão do grupo e
  deve aparecer na metodologia.
- **Não usar a silhueta para defender o vencedor.** A do `standard_all` (0,165) é a
  segunda menor da rodada. O argumento é a concordância com o diagnóstico, não a
  separação geométrica.
- **Distância euclidiana em dados mistos é uma aproximação.** O `standard_all` é uma
  forma de ponderar as categóricas, não um tratamento próprio para elas (K-Prototypes
  ou distância de Gower seriam as alternativas; ver anotacoes_artigo.md).
- **O peso das raras é conhecido e documentado** (achado 8). Não omitir: é o que
  explica as eliminações das rodadas do k.

## Arquivos de origem

- `results/r01_escalonamento/decisao.md`: tabela da rodada e regra aplicada
- `results/r01_escalonamento/resumo.csv`: médias, desvios, travas e IC por opção
- `results/r01_escalonamento/por_semente.csv`: uma linha por opção × semente
- `results/r01_escalonamento/bootstrap.csv`: ARI, ARI registrado, silhueta e Jaccard fora da reamostra (100 reamostras pareadas)
- `results/r01_escalonamento/vencedor.yaml`: configuração herdada pela R2
- `configs/r01_escalonamento.yaml`: definição da rodada
- Peso de cada bloco de variáveis e perfil dos grupos (tabela "Peso de cada bloco" e
  achados 2 e 3): calculados à parte com o pipeline do projeto; não há arquivo em
  `results/`
