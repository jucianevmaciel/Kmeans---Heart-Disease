# R4 — Redução de dimensão

**Pergunta:** reduzir o número de dimensões antes do K-Means melhora a concordância dos
grupos com o diagnóstico?

**Status:** decidida. **Vencedora: `sem_reducao`**, gravada em
`results/r04_reducao/vencedor.yaml` e herdada pela R5.
**Execução:** 23/11/2026 (7 opções × 20 sementes + 100 reamostras bootstrap).

## Configuração

- **Herda da R3:** `standard_all`, zeros pela mediana, Oldpeak mantido, K-Means k = 2,
  k-means++, n_init = 50. O espaço do K-Means tem 18 colunas (5 numéricas, FastingBS
  e 12 do one-hot).
- **Opções, em ordem de desempate:**

| Opção | O que faz | Dimensões | Variância mantida |
|---|---|---|---|
| `sem_reducao` | usa as 18 colunas | 18 | 100% |
| `pca_2` | PCA com 2 componentes | 2 | 31,3% |
| `pca_3` | PCA com 3 componentes | 3 | 39,3% |
| `pca_5` | PCA com 5 componentes | 5 | 54,1% |
| `pca_90pct` | PCA com os componentes que somam 90% da variância | 12 | 91,5% |
| `kbest_4` | as 4 colunas mais associadas ao diagnóstico (teste F) | 4 | — |
| `kbest_8` | as 8 colunas mais associadas ao diagnóstico (teste F) | 8 | — |

- **`kbest` fica fora da disputa:** ele escolhe as colunas **usando o diagnóstico**, o que
  contradiz a proposta de agrupar sem ver o rótulo. Aparece na tabela só como
  comparação. Colunas escolhidas:
  - `kbest_4`: ChestPainType = ASY, ExerciseAngina = Y, ST_Slope = Flat, ST_Slope = Up;
  - `kbest_8`: as 4 anteriores + MaxHR, Oldpeak, Sex = M, ChestPainType = ATA.
- **Critério:** ARI. A silhueta não serve aqui: cada redução cria um espaço diferente, e
  silhuetas de espaços diferentes não são comparáveis.
- **Regra:** empate se o IC 95% da diferença pareada de ARI (bootstrap, pacientes fora da
  reamostra) contém zero; entre as empatadas, vence a primeira da lista. Travas: Jaccard
  ≥ 0,75; colesterol ausente ≤ 2× a base; nenhum grupo de categoria rara.

## Resultados

| Opção | ARI | ARI registr. | NMI | Acurácia | Recall | Espec. | AUC | Silhueta (nula) | Jaccard | Situação |
|---|---|---|---|---|---|---|---|---|---|---|
| **`sem_reducao`** | **0,498** | **0,516** | 0,394 | 0,853 | 0,878 | 0,822 | **0,914** | 0,165 (0,082) | 0,98 · 0,98 | **vencedora** |
| `pca_2` | 0,473 | 0,493 | 0,373 | 0,844 | 0,852 | 0,834 | 0,903 | 0,456 (0,453) | 0,97 · 0,98 | empatada |
| `pca_3` | 0,488 | 0,500 | 0,385 | 0,850 | 0,872 | 0,822 | 0,906 | 0,378 (0,365) | 0,97 · 0,98 | empatada |
| `pca_5` | 0,492 | 0,504 | 0,388 | 0,851 | 0,872 | 0,824 | 0,908 | 0,290 (0,273) | 0,97 · 0,98 | empatada |
| `pca_90pct` | 0,501 | 0,516 | 0,397 | 0,854 | 0,880 | 0,822 | 0,913 | 0,181 (0,166) | 0,98 · 0,98 | melhor média |
| `kbest_4` | 0,407 | 0,438 | 0,314 | 0,819 | 0,839 | 0,795 | 0,884 | 0,543 (0,284) | 1,00 · 1,00 | fora da disputa |
| `kbest_8` | 0,476 | 0,508 | 0,375 | 0,845 | 0,868 | 0,817 | 0,905 | 0,319 (0,166) | 0,97 · 0,97 | fora da disputa |

Todas as opções passam pelas travas (maior concentração de uma categoria num grupo: 40%;
lift do colesterol ausente de 1,30 a 1,47).

**Comparação pareada por bootstrap** (outra − `sem_reducao`; pacientes fora da reamostra):

| Opção | Δ ARI | IC 95% | Δ ARI registrado | IC 95% |
|---|---|---|---|---|
| `pca_90pct` | +0,001 | [−0,021; +0,017] | −0,000 | [−0,011; +0,011] |
| `pca_5` | −0,008 | [−0,058; +0,030] | −0,009 | [−0,051; +0,022] |
| `pca_3` | −0,008 | [−0,054; +0,033] | −0,010 | [−0,056; +0,027] |
| `pca_2` | −0,014 | [−0,057; +0,030] | −0,017 | [−0,056; +0,027] |
| `kbest_8` (fora da disputa) | −0,024 | [−0,080; +0,030] | −0,015 | [−0,080; +0,040] |
| `kbest_4` (fora da disputa) | **−0,091** | **[−0,144; −0,026]** | **−0,081** | **[−0,155; −0,009]** |

Pela regra, a diferença é medida contra a opção de melhor média (`pca_90pct`); a tabela
usa `sem_reducao` como referência para facilitar a leitura. As conclusões são as mesmas:
todos os PCAs empatam, e vence a primeira opção da lista.

## Achados

1. **Reduzir a dimensão não melhora a concordância com o diagnóstico.** Todas as variantes
   de PCA empatam com `sem_reducao` (ICs contendo zero). Vence a mais simples,
   `sem_reducao`. O ARI de referência continua 0,498 (0,516 registrado).
2. **O PCA de 90% reproduz o espaço original.** Com 12 componentes (91,5% da variância),
   ele chega ao mesmo agrupamento: ARI 0,501 contra 0,498, Δ = +0,001 [−0,021; +0,017].
3. **Mesmo com poucas dimensões, o sinal da doença se mantém.** Com só 2 componentes (31%
   da variância), o ARI cai para 0,473, uma perda de 0,014 que não é significativa
   [−0,057; +0,030]. A direção doente/saudável está concentrada nos primeiros
   componentes principais, que capturam a maior variação dos dados sem usar o
   diagnóstico.
4. **A silhueta do PCA é alta, mas igual à nula.** O `pca_2` tem silhueta de 0,456,
   praticamente a mesma da referência com colunas embaralhadas (0,453); o mesmo vale
   para `pca_3` (0,378 contra 0,365) e `pca_5` (0,290 contra 0,273). A silhueta alta vem
   da baixa dimensão, não de grupos mais bem separados. Isso confirma que a silhueta não
   pode comparar espaços diferentes.
5. **Escolher colunas pelo diagnóstico não ajuda, e pode piorar.** O `kbest_4` usa as 4
   colunas mais associadas à doença (dor assintomática, angina no esforço e as duas
   inclinações de ST) e, mesmo assim, tem o pior ARI da rodada: 0,407, uma queda
   significativa de −0,091 [−0,144; −0,026]. Com só 4 colunas binárias, os pacientes se
   concentram em poucas combinações, e o K-Means perde a informação das outras
   variáveis. O `kbest_8` empata com `sem_reducao` (−0,024 [−0,080; +0,030]). Ou seja,
   mesmo trapaceando (usando o rótulo para escolher as colunas), não se ganha nada.
6. **A silhueta do kbest é a única que supera claramente a nula.** O `kbest_4` tem
   silhueta de 0,543 contra 0,284 da nula, e o `kbest_8`, 0,319 contra 0,166. Selecionar
   colunas pelo diagnóstico cria um espaço com grupos mais nítidos, mas esses grupos
   concordam *menos* com o diagnóstico. Separação geométrica e concordância com a
   doença são coisas diferentes.
7. **Todas as opções são estáveis.** Jaccard de 0,97 a 1,00 em todos os grupos;
   estabilidade entre sementes de 0,999 a 1,000.

## Implicações para as próximas rodadas

- **Nada muda nos arquivos.** A R5 herda a configuração atual: `standard_all`,
  `mediana`, sem redução, k = 2, k-means++.
- **Na R5 (combinação),** só duas retiradas acontecem: sem o `standard_all` (volta ao
  `standard`) e sem o tratamento de dados. Mas o tratamento vencedor (`mediana`) já é o
  da base, então essa retirada é ignorada. Redução e inicialização também já são os
  valores da base. Na prática, a R5 vai comparar a configuração completa com a versão
  sem `standard_all`. Espera-se que a completa vença com folga, repetindo a R1
  (+0,178 de ARI).
- **A R5b** deve repetir a R3 e confirmar o k = 2.

## Para o texto do artigo

> Avaliou-se se reduzir a dimensão antes do agrupamento melhoraria a concordância com o
> diagnóstico. Análise de componentes principais com 2, 3 e 5 componentes e com 90% da
> variância (12 componentes) não diferiu do espaço original (todas as diferenças de ARI
> com IC 95% contendo zero), e o espaço original foi mantido. Com apenas dois
> componentes (31% da variância), o ARI foi de 0,473, contra 0,498 sem redução,
> indicando que a direção que separa doentes e saudáveis está concentrada nos primeiros
> componentes. Como comparação, a seleção das colunas mais associadas ao diagnóstico
> (teste F), que usa o rótulo e por isso não concorreu, não trouxe ganho: com quatro
> colunas, o ARI caiu para 0,407 (diferença de −0,091; IC 95% de −0,144 a −0,026),
> embora a silhueta tenha sido a maior da rodada.

## Cuidados

- **Não comparar silhuetas entre opções desta rodada.** Cada redução cria um espaço com
  outra dimensão. A silhueta do PCA é alta porque o espaço é pequeno, como mostra a nula.
- **Não afirmar que "o PCA não serve".** O achado é que ele não melhora o ARI *aqui*. Com
  2 componentes, ele preserva quase toda a concordância e pode servir para
  visualização (é o que a R6 usa no gráfico 2D).
- **O kbest usa o diagnóstico.** Ele está na tabela só como comparação. Não apresentar
  seus números como alternativa possível ao K-Means não supervisionado.
- **Empate não é equivalência.** Os ICs têm largura de ±0,02 a ±0,06; diferenças desse
  tamanho não podem ser descartadas.

## Arquivos de origem

- `results/r04_reducao/decisao.md`: tabela da rodada e regra aplicada
- `results/r04_reducao/resumo.csv`: médias, desvios, travas e IC por opção
- `results/r04_reducao/por_semente.csv`: uma linha por opção × semente
- `results/r04_reducao/bootstrap.csv`: ARI, ARI registrado, silhueta e Jaccard fora da reamostra (100 reamostras pareadas)
- `results/r04_reducao/vencedor.yaml`: configuração herdada pela R5
- `configs/r04_reducao.yaml`: definição da rodada
- Variância mantida por cada PCA, colunas escolhidas pelo kbest e diferenças pareadas
  contra `sem_reducao`: calculadas à parte com o pipeline do projeto e o `bootstrap.csv`
