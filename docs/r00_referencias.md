# R0 — Referências

**Pergunta:** quais são os valores de referência para avaliar o K-Means? Qual é o
teto (modelos supervisionados) e o piso (classificador trivial), e como o K-Means se
compara a outros algoritmos de agrupamento?

**Status:** rodada sem escolha. Nada é herdado pela R1, que parte do `base.yaml`.
**Execução:** 23/11/2026, `results/r00_referencias/` (20 sementes, 100 reamostras bootstrap).

## Configuração

- **Base:** 918 pacientes, sem divisão treino/teste; 55,3% doentes.
- **Pré-processamento** (o do `base.yaml`, igual para todos): zeros pela mediana,
  Oldpeak mantido, numéricas padronizadas, categóricas em one-hot, sem redução.
- **Referências supervisionadas** (usam o diagnóstico no treino): classificador
  trivial (`dummy`, prevê sempre a classe majoritária), regressão logística e
  gradient boosting. Previsões fora da dobra numa validação cruzada estratificada de
  5 dobras, repetida com 20 sementes.
- **Agrupamentos com k = 2** (não veem o diagnóstico): K-Means, mistura de gaussianas
  (GMM) e hierárquico de Ward. O diagnóstico só entra depois, para avaliar.
- **Métricas comuns:** ARI, pureza (= acurácia com cada grupo mapeado para a classe
  majoritária), recall, especificidade e AUC do escore. Nos agrupamentos, o escore é
  a distância relativa aos centróides; no GMM, a probabilidade do grupo "doente".

## Resultados

| Modelo | ARI | ARI registr. | NMI | Acurácia | Recall | Espec. | AUC | Silhueta (nula) | Jaccard por grupo |
|---|---|---|---|---|---|---|---|---|---|
| Dummy | 0,000 | 0,000 | 0,000 | 0,553 | 1,000 | 0,000 | 0,499 | — | — |
| Regressão logística | 0,518 ± 0,010 | 0,519 | 0,412 | 0,860 | 0,887 | 0,826 | 0,922 | — | — |
| Gradient boosting | 0,531 ± 0,013 | 0,520 | 0,425 | 0,865 | 0,891 | 0,832 | 0,922 | — | — |
| **K-Means k=2** | **0,318** | 0,344 | 0,244 | 0,782 | 0,774 | 0,793 | 0,858 | 0,176 (0,102) | 0,97 · 0,97 |
| GMM k=2 | 0,340 | 0,386 | 0,291 | 0,792 | 0,713 | 0,890 | 0,849 | 0,112 (0,102) | **0,59 · 0,63** |
| Ward k=2 | 0,345 | 0,338 | 0,262 | 0,794 | 0,829 | 0,751 | 0,870 | 0,152 (0,102) | 0,81 · 0,77 |

Nos agrupamentos, o ± é zero porque a base inteira dá sempre o mesmo resultado (o
K-Means com n_init = 50; Ward e GMM são praticamente determinísticos). A variação de
amostragem aparece no bootstrap: o ARI fora da reamostra é 0,314 ± 0,037 no K-Means,
0,317 ± 0,053 no Ward e 0,171 ± 0,150 no GMM.

Comparação pareada por bootstrap (diferença de ARI fora da reamostra, IC 95%):

| Comparação | Δ ARI | IC 95% |
|---|---|---|
| Ward − K-Means | +0,003 | [−0,075; +0,076] |
| GMM − K-Means | −0,143 | [−0,367; +0,137] |
| Ward − GMM | +0,146 | [−0,108; +0,381] |

## Achados

1. **Há um sinal de doença nos grupos naturais, mas parcial.** Sem ver o diagnóstico,
   o K-Means acerta 78,2% dos pacientes (pela classe majoritária do grupo), contra
   55,3% do classificador trivial e 86,0% da regressão logística. O ARI (0,318) fica
   em cerca de 61% do da regressão logística (0,518). A AUC do escore (0,858) fica
   0,064 abaixo das supervisionadas (0,922).
2. **Os três algoritmos de agrupamento empatam na concordância com o diagnóstico.** O
   ARI vai de 0,318 a 0,345, e nenhuma diferença é significativa: o IC 95% de
   Ward − K-Means vai de −0,075 a +0,076.
3. **O K-Means é o único agrupamento claramente estável.** Jaccard de 0,97 nos dois
   grupos, contra 0,81 e 0,77 do Ward (no limite) e 0,59 e 0,63 do GMM (abaixo de
   0,75: instável pelo critério de Hennig, 2007). O ARI de 0,340 do GMM na base
   inteira não se repete nas reamostras (0,171 ± 0,150). Isso sustenta o K-Means como
   algoritmo do trabalho também por critério empírico.
4. **Os algoritmos erram de jeitos diferentes.** O GMM é o mais específico (0,890) e
   o menos sensível (0,713); o Ward é o mais sensível (0,829) e o menos específico
   (0,751); o K-Means fica equilibrado (0,774 e 0,793). Com acurácia parecida, a
   escolha do algoritmo muda o tipo de erro.
5. **A estrutura de grupos é fraca.** A silhueta do K-Means (0,176) fica abaixo de
   0,25, faixa que Kaufman & Rousseeuw (1990) associam a ausência de estrutura
   substancial. Mesmo assim, fica acima da silhueta nula (0,102, com as colunas
   embaralhadas). No GMM, a silhueta (0,112) praticamente não supera a nula.
6. **O atalho do colesterol não infla o resultado.** O ARI nos pacientes com
   colesterol registrado é maior que o ARI total no K-Means (0,344 contra 0,318) e no
   GMM (0,386 contra 0,340), e quase igual no Ward (0,338 contra 0,345). A concentração de colesterol ausente no pior grupo
   fica entre 1,43× e 1,52× a da base, abaixo da trava de 2×. Os modelos
   supervisionados concentram parecido: 1,49× e 1,56×.
7. **Nenhum grupo é formado por uma única categoria.** A maior concentração é 37% de
   ChestPainType = ATA num grupo do Ward, longe do limite de 90%.
8. **A variação entre sementes subestima a incerteza.** O desvio do ARI do K-Means é
   0,000 entre sementes e 0,037 no bootstrap. Isso justifica a regra de empate por
   bootstrap pareado adotada nas rodadas seguintes.

## Implicações para as próximas rodadas

- **Faixa de referência para o ARI:** 0,32 (K-Means sem ajustes) a 0,52–0,53 (teto
  supervisionado). As rodadas R1–R5b medem quanto do caminho até o teto o
  pré-processamento recupera.
- **Faixa de referência para a AUC:** 0,858 a 0,922. É a métrica que se compara com o
  SVM.
- **Foco no K-Means:** os outros algoritmos não superam o K-Means em concordância e são
  menos estáveis. GMM e Ward ficam como referência e não voltam nas rodadas seguintes.

## Para o texto do artigo

> Como referência, a base foi avaliada por três modelos supervisionados (classificador
> trivial, regressão logística e gradient boosting; validação cruzada estratificada de
> 5 dobras) e por três algoritmos de agrupamento com k = 2 (K-Means, GMM e Ward),
> todos com o mesmo pré-processamento. Sem acesso ao diagnóstico, o K-Means agrupou
> corretamente 78,2% dos pacientes (ARI = 0,318; AUC do escore = 0,858), contra 86,0%
> da regressão logística (ARI = 0,518; AUC = 0,922) e 55,3% do classificador trivial.
> Os três algoritmos de agrupamento não diferiram na concordância com o diagnóstico
> (ARI entre 0,318 e 0,345; IC 95% da diferença Ward − K-Means: −0,075 a +0,076). O
> K-Means, porém, foi o único com os dois grupos estáveis sob reamostragem (Jaccard =
> 0,97); o GMM ficou abaixo do limiar de 0,75 (0,59 e 0,63). A silhueta do K-Means
> (0,176) indica estrutura fraca, embora acima da obtida com as variáveis embaralhadas
> (0,102).

## Cuidados

- **Teto do ARI:** as referências supervisionadas não são um teto absoluto. Elas usam
  o mesmo pré-processamento básico, que a R1 em diante modifica. Um K-Means com melhor
  pré-processamento pode se aproximar delas.
- **Protocolo diferente da R8:** nesta rodada, a validação cruzada das supervisionadas
  muda de semente a cada repetição. A comparação com o SVM deve usar a R8 (5×5,
  semente 42).
- **Pureza como acurácia:** o mapeamento grupo → classe usa o próprio diagnóstico,
  então a "acurácia" do agrupamento é otimista por construção. A R8 mede esse otimismo.

## Arquivos de origem

- `results/r00_referencias/decisao.md`: tabela da rodada
- `results/r00_referencias/resumo.csv`: médias e desvios por opção
- `results/r00_referencias/por_semente.csv`: uma linha por opção × semente
- `results/r00_referencias/bootstrap.csv`: métricas fora da reamostra e Jaccard por grupo
- `configs/r00_referencias.yaml`: definição da rodada
