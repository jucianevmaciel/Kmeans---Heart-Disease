# O que é o ARI (Adjusted Rand Index)

Métrica principal do trabalho para medir o quanto os grupos do K-Means coincidem com
o diagnóstico (`HeartDisease`). Proposta por Hubert & Arabie (1985), a partir do
índice de Rand (Rand, 1971).

## A ideia: comparar pares de pacientes

O ARI não avalia cada paciente sozinho, e sim **pares** de pacientes. Com 918
pacientes, são 918 × 917 / 2 = **420.903 pares**. Para cada par, duas perguntas:

- O K-Means colocou os dois no **mesmo grupo**?
- O diagnóstico coloca os dois na **mesma classe**?

As duas divisões **concordam** sobre o par quando as respostas são iguais: ou os dois
respondem "juntos", ou os dois respondem "separados". A proporção de pares em que há
concordância é o **índice de Rand (RI)**.

## Por que "ajustado"

Mesmo um agrupamento sorteado ao acaso concorda em muitos pares, então o RI puro
parece bom à toa. O ARI desconta a concordância esperada por acaso, mantendo o tamanho
dos grupos e das classes:

    ARI = (RI − RI esperado ao acaso) / (RI máximo − RI esperado ao acaso)

| Valor | Significado |
|---|---|
| 1 | as duas divisões são idênticas |
| 0 | concordância igual à esperada por acaso |
| < 0 | pior que o acaso (raro) |

### Fórmula pela tabela de contingência

Com n_ij = número de pacientes da classe i no grupo j, a_i = total da classe i,
b_j = total do grupo j e n = total de pacientes:

    índice   = Σ_ij C(n_ij, 2)
    esperado = [Σ_i C(a_i, 2) · Σ_j C(b_j, 2)] / C(n, 2)
    máximo   = ½ [Σ_i C(a_i, 2) + Σ_j C(b_j, 2)]
    ARI      = (índice − esperado) / (máximo − esperado)

em que C(m, 2) = m(m − 1)/2 é o número de pares entre m pacientes. No código:
`sklearn.metrics.adjusted_rand_score` (src/metricas.py).

## Exemplo com 4 pacientes

A e B estão doentes; C e D, saudáveis. O K-Means formou os grupos {A, B, C} e {D}.

| Par | Mesmo grupo? | Mesma classe? | Concordam? |
|---|---|---|---|
| A-B | sim | sim | ✓ |
| A-C | sim | não | ✗ |
| A-D | não | não | ✓ |
| B-C | sim | não | ✗ |
| B-D | não | não | ✓ |
| C-D | não | sim | ✗ |

- RI = 3/6 = **0,5**.
- Pela fórmula: índice = 1 (só o par A-B); esperado = (2 × 3) / 6 = 1;
  máximo = (2 + 3) / 2 = 2,5. ARI = (1 − 1) / (2,5 − 1) = **0**.
- Se cada grupo for mapeado para a sua classe majoritária ({A, B, C} → doente;
  {D} → saudável), a "acurácia" é **75%** (A, B e D certos).

**Lição:** uma acurácia que parece razoável pode corresponder a um agrupamento que não
captura nada além do acaso. O ARI mostra isso; a acurácia, não.

## Por que o ARI é a métrica principal do trabalho

1. **Não depende do nome dos grupos.** Trocar "grupo 0" por "grupo 1" não muda o ARI.
   Ele dispensa o mapeamento grupo → classe que a pureza (acurácia) usa, e esse
   mapeamento usa o próprio diagnóstico.
2. **Corrige o acaso.** Zero tem o mesmo significado em qualquer base, com qualquer
   proporção de doentes. A acurácia não: o classificador trivial já acerta 55,3% aqui.
3. **Funciona com k diferente do número de classes.** Se o K-Means divide os doentes
   em dois grupos, os pares de doentes separados contam como discordância. Por isso o
   ARI favorece k = 2, e **o k não é escolhido por ele** (seria circular; R3 e R5b
   usam a silhueta).

## Como ler os valores do trabalho

O ARI conta pares, então cai mais rápido que a acurácia e **não é uma porcentagem**.

| Modelo | ARI | Acurácia |
|---|---|---|
| Classificador trivial (R0) | 0,000 | 55,3% |
| K-Means sem ajustes (R0) | 0,318 | 78,2% |
| K-Means configuração final | 0,498 | 85,3% |
| Regressão logística (R0, supervisionada) | 0,518 | 86,0% |
| Gradient boosting (R0, supervisionado) | 0,531 | 86,5% |

Com duas classes, um ARI perto de 0,5 já é um resultado bom: fica próximo do teto dos
modelos supervisionados.

## Variante usada no trabalho: ARI registrado

O mesmo cálculo feito só nos **746 pacientes com colesterol registrado**. Nesses
pacientes, o atalho do colesterol ausente (88% dos zerados são doentes) não tem como
inflar o valor. É o critério da R2 e aparece em todas as tabelas.

## Para o slide

**Título:** Como medimos se os grupos coincidem com a doença: o ARI

- Compara **pares de pacientes**: os dois estão juntos no grupo *e* juntos no
  diagnóstico? (ou separados nos dois?)
- **Ajustado ao acaso:** 0 = acaso, 1 = coincidência perfeita
- Não depende do nome dos grupos e **não é porcentagem**
- No nosso caso: 0,32 (K-Means sem ajustes) → **0,50** (configuração final);
  teto supervisionado: 0,52–0,53

**Visual sugerido:** o exemplo dos 4 pacientes (tabela de pares), terminando em
"acurácia 75%, ARI = 0". Mostra numa só imagem por que a acurácia engana e o ARI não.

**Frase para a fala:** "Um agrupamento pode acertar 75% dos pacientes e ainda assim
não ser melhor que o acaso. O ARI desconta essa concordância por sorte."

## Referências

- Hubert, L.; Arabie, P. (1985). Comparing partitions. *Journal of Classification*, 2(1), 193–218.
- Rand, W. M. (1971). Objective criteria for the evaluation of clustering methods. *Journal of the American Statistical Association*, 66(336), 846–850.
