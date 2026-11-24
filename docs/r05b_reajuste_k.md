# R5b — Reajuste do k sobre a combinação final

**Pergunta:** com a combinação vencedora da R5, o melhor número de grupos continua o
mesmo?

**Status:** decidida. **Vencedora: k = 2.** Esta é a **configuração final** do trabalho,
gravada em `results/r05b_reajuste_k/vencedor.yaml` e usada por R6, R7, R8 e pelas
análises complementares de k.
**Execução:** 23/11/2026 (5 opções × 20 sementes + 100 reamostras bootstrap).

## Configuração

- **Herda da R5:** `standard_all`, zeros pela mediana, Oldpeak mantido, sem redução,
  k-means++, n_init = 50.
- **Grade:** k de 2 a 6, na ordem de desempate (menor k primeiro). A inicialização não
  varia (a R3 mostrou que ela não faz diferença com n_init = 50).
- **Critério e regra:** os mesmos da R3. Só concorrem os k que passam pelas travas
  (Jaccard ≥ 0,75 em todos os grupos; colesterol ausente ≤ 2× a base; nenhum grupo com
  ≥ 90% numa categoria com < 20% da base). Entre eles, decide a silhueta, com empate se o
  IC 95% da diferença pareada (bootstrap) contém zero; entre os empatados, vence o menor
  k. O ARI só é relatado.
- **Por que repetir a escolha do k:** a R5 é decidida pelo ARI, que favorece k = 2.
  Reajustar o k ali tornaria a escolha circular; por isso ela foi separada nesta rodada,
  decidida pela silhueta.

## Resultados

| k | ARI | ARI registr. | NMI | AUC | Silhueta (nula) | Davies-B. | Calinski-H. | Inércia | Jaccard por grupo | Situação |
|---|---|---|---|---|---|---|---|---|---|---|
| **2** | **0,498** | **0,516** | **0,394** | **0,914** | 0,165 (0,082) | 2,160 | 179,6 | 13.815 | 0,98 · 0,98 | **vencedora** |
| 3 | 0,428 | 0,474 | 0,332 | 0,909 | 0,181 (0,082) | 1,928 | 136,4 | 12.728 | 0,92 · 0,96 · 0,85 | categoria rara (ST_Slope = Down, 7%) |
| 4 | 0,264 | 0,288 | 0,246 | 0,889 | 0,162 (0,073) | 1,972 | 122,7 | 11.779 | 0,76 · 0,88 · 0,89 · 0,78 | categoria rara (RestingECG = ST, 19%) |
| 5 | 0,232 | 0,264 | 0,218 | 0,892 | 0,172 (0,075) | 1,784 | 117,9 | 10.897 | 0,87 · 0,78 · 0,80 · 0,77 · 0,86 | categoria rara (RestingECG = ST, 19%) |
| 6 | 0,220 | 0,245 | 0,214 | 0,883 | 0,184 (0,080) | 1,685 | 116,1 | 10.096 | mín. 0,64 | instável |

**Comparação pareada com o k = 2** (bootstrap, pacientes fora da reamostra; só
descritiva, porque nenhum k ≥ 3 é elegível):

| k | Δ silhueta | IC 95% | Δ ARI | IC 95% |
|---|---|---|---|---|
| 3 | +0,010 | [−0,030; +0,024] | −0,084 | [−0,174; −0,024] |
| 4 | −0,004 | [−0,022; +0,030] | −0,214 | [−0,286; −0,142] |
| 5 | +0,007 | [−0,014; +0,020] | −0,247 | [−0,314; −0,175] |
| 6 | +0,011 | [−0,010; +0,031] | −0,286 | [−0,359; −0,203] |

**Configuração final:**

| Componente | Valor | Rodada |
|---|---|---|
| Escalonamento | `standard_all` (todas as colunas padronizadas, inclusive as 0/1) | R1 |
| Colesterol = 0 | imputado pela mediana | R2 |
| Oldpeak negativo | mantido | R2 |
| Redução de dimensão | nenhuma (18 colunas) | R4 |
| Algoritmo | K-Means, k = 2, k-means++, n_init = 50 | R3 / R5b |

| Métrica (base inteira) | Valor |
|---|---|
| ARI / ARI registrado | 0,498 / 0,516 |
| NMI | 0,394 |
| Acurácia · recall · especificidade | 0,853 · 0,878 · 0,822 |
| AUC do escore | 0,914 |
| Silhueta (nula) | 0,165 (0,082) |
| Jaccard por grupo | 0,98 · 0,98 |
| Lift do colesterol ausente | 1,44 |

## Achados

1. **O k = 2 se confirma.** É o único k elegível, como na R3: k = 3, 4 e 5 são barrados por
   terem um grupo formado inteiramente por uma categoria, e k = 6 por instabilidade
   (Jaccard mínimo de 0,64).
2. **A R5b reproduz a R3 exatamente.** ARI, silhueta e Jaccard de cada k são idênticos aos
   da R3 com k-means++ (diferença máxima de 0,000). Era o esperado: a R5 manteve a
   mesma configuração da R3, então o espaço do K-Means é o mesmo.
3. **A silhueta não decide.** Nenhum k de 3 a 6 tem silhueta significativamente diferente
   da do k = 2 (todos os ICs contêm zero). A escolha vem das travas, não da silhueta.
4. **Os k maiores perdem concordância com a doença de forma significativa.** A queda de
   ARI em relação ao k = 2 vai de −0,084 (k = 3) a −0,286 (k = 6), com todos os ICs
   excluindo zero. A configuração final é também a de maior ARI, AUC e estabilidade
   entre os k testados.
5. **A cadeia de decisões termina na configuração da base com um único ajuste.** O
   K-Means final é o do `base.yaml` com `standard_all` no lugar de `standard`, e
   recupera 96% do ARI da regressão logística da R0 (0,498 contra 0,518), sem ver o
   diagnóstico para agrupar.

## Implicações para as próximas rodadas

- **Nada muda nos arquivos.** R6, R7, R8 e as análises complementares leem o
  `vencedor.yaml` desta rodada automaticamente.
- **Ordem de execução:**

```bash
python -m src.perfil_grupos                                  # R6
python -m src.clusters_2d                                    # R6
python -m src.robustez                                       # R7
python -m src.generalizacao                                  # R8
python -m src.variacoes_k                                    # complementar: k de 2 a 8
python -m src.perfil_grupos --config configs/alternativa_k4.yaml
python -m src.clusters_2d   --config configs/alternativa_k4.yaml
python -m src.robustez      --config configs/alternativa_k4.yaml
python -m src.generalizacao --config configs/alternativa_k4.yaml
python -m src.comparar_k    --config configs/alternativa_k4.yaml
```

- **Opcional na R6:** o cruzamento com os erros do SVM só roda se
  `configs/r06_perfil.yaml` tiver `erros_svm` apontando para um CSV com a coluna `id`
  dos pacientes que o SVM errou. Hoje está `null`, e a R6 roda sem ele.

## Para o texto do artigo

> Depois de combinar as escolhas das rodadas anteriores, o número de grupos foi
> reavaliado com o mesmo critério da escolha inicial (silhueta, entre os valores de k
> com grupos estáveis e não formados por uma única categoria rara). O resultado repetiu
> o da escolha inicial: k = 2 foi o único valor elegível, e nenhum outro diferiu dele na
> silhueta (IC 95% das diferenças contendo zero), enquanto todos apresentaram ARI
> significativamente menor. A configuração final — K-Means com k = 2 sobre todas as
> colunas padronizadas, com o colesterol ausente imputado pela mediana e sem redução de
> dimensão — obteve ARI = 0,498, acurácia de 85,3% e AUC do escore de 0,914, contra
> ARI = 0,518 e AUC = 0,922 da regressão logística supervisionada.

## Cuidados

- **Não dizer que a R5b "confirmou independentemente" o k = 2.** Como a configuração é a
  mesma da R3, a R5b repete a R3 por construção. O papel dela é garantir que a
  combinação não mudou o k, não trazer uma evidência nova.
- **Não comparar diretamente com o teto supervisionado como "quase igual".** A regressão
  logística foi avaliada fora da dobra (validação cruzada), e o K-Means na base inteira.
  A comparação justa, nas mesmas dobras, é a da R8.
- **A acurácia de 85,3% depende do mapeamento grupo → classe pelo diagnóstico.** Ela é
  otimista por construção; a R8 mede esse otimismo fora da amostra.
- **A silhueta da configuração final é fraca (0,165).** Os grupos concordam com a doença,
  mas não são bem separados geometricamente. Dizer as duas coisas.

## Arquivos de origem

- `results/r05b_reajuste_k/decisao.md`: tabela da rodada, regra aplicada e grupos de categoria rara
- `results/r05b_reajuste_k/resumo.csv`: médias, desvios, travas e métricas internas por k
- `results/r05b_reajuste_k/por_semente.csv`: uma linha por k × semente
- `results/r05b_reajuste_k/bootstrap.csv`: ARI, ARI registrado, silhueta e Jaccard fora da reamostra (100 reamostras pareadas)
- `results/r05b_reajuste_k/cotovelo.png`: curvas de cada métrica por k
- `results/r05b_reajuste_k/vencedor.yaml`: **configuração final**
- `configs/r05b_reajuste_k.yaml`: definição da rodada
- Comparação pareada com o k = 2 e a comparação com a R3: calculadas à parte a partir
  dos `bootstrap.csv` e `resumo.csv` das duas rodadas
