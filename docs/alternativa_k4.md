# Alternativa k = 4 — análise de sensibilidade

> **Provisório.** Os números abaixo são da execução de verificação (23/11/2026, feita
> fora da máquina do grupo, scikit-learn 1.9.1). Refazer depois de rodar R3–R5b e os
> comandos abaixo, e conferir se batem.

**Pergunta:** o que aparece nos dados se o K-Means usar 4 grupos em vez de 2? Vale
como alternativa ao resultado principal?

**Status:** análise complementar. **Não é um segundo resultado.** O resultado principal
continua sendo k = 2, escolhido pela regra de decisão na R3/R5b. O k = 4 é a
configuração que a mesma regra escolheria se a trava de categoria rara fosse de 15% ou
10%, em vez dos 20% adotados.

## Configuração

- **Definição:** `configs/alternativa_k4.yaml`. Herda a configuração final
  (`r05b_reajuste_k`: `standard_all`, `mediana`, k-means++, n_init = 50) e muda só o
  k para 4. Não entra na cadeia de rodadas.
- **Saídas:** `results/alternativa_k4/`, sem sobrescrever as da configuração final.
- **Comandos:**

```bash
python -m src.perfil_grupos --config configs/alternativa_k4.yaml   # R6
python -m src.clusters_2d   --config configs/alternativa_k4.yaml   # R6
python -m src.robustez      --config configs/alternativa_k4.yaml   # R7
python -m src.generalizacao --config configs/alternativa_k4.yaml   # R8
python -m src.comparar_k    --config configs/alternativa_k4.yaml   # k = 2 x k = 4
```

- **Comparação:** `src/comparar_k.py` ajusta as duas configurações na base inteira e as
  avalia nas mesmas 100 reamostras bootstrap (pareado). Também cruza os grupos das
  duas.

## Resultados

| Métrica | k = 2 (principal) | k = 4 (alternativa) |
|---|---|---|
| ARI | **0,498** | 0,264 |
| ARI registrado | **0,516** | 0,288 |
| NMI | 0,394 | 0,246 |
| Acurácia (pureza) | **0,853** | 0,815 |
| Recall | 0,878 | **0,937** |
| Especificidade | **0,822** | 0,663 |
| AUC do escore | **0,914** | 0,889 |
| Silhueta (nula) | 0,165 (0,082) | 0,162 (0,073) |
| Jaccard por grupo | 0,98 · 0,98 | 0,76 · 0,88 · 0,89 · 0,78 |
| ARI fora da reamostra | 0,492 ± 0,038 | 0,277 ± 0,044 |
| Lift do colesterol ausente | 1,44 | 1,86 |
| R8: AUC fora da amostra (5×5) | 0,914 | 0,888 |
| R8: otimismo no ARI | ≈ 0 | −0,009 |

**Diferenças pareadas por bootstrap** (k = 4 − k = 2):

| Métrica | Δ | IC 95% |
|---|---|---|
| ARI | −0,214 | [−0,286; −0,142] |
| ARI registrado | −0,211 | [−0,281; −0,121] |
| Silhueta | −0,004 | [−0,022; +0,030] |

**Os 4 grupos:**

| Grupo | Pacientes | % doentes | RestingECG | ST_Slope | Leitura |
|---|---|---|---|---|---|
| 0 | 146 | 79,5% | **100% ST** (146 dos 178 com ECG = ST) | misto | todos com ECG = ST |
| 1 | 287 | 88,5% | 100% Normal | 84% Flat | "doente" com ECG normal |
| 2 | 304 | 10,5% | 87% Normal | 91% Up | "saudável" |
| 3 | 181 | 58,6% | **100% LVH** (181 dos 188 com LVH) | misto | todos com LVH |

Árvore substituta (profundidade 3, fidelidade de 91,0%): o primeiro corte é
`RestingECG = LVH`, e o segundo nível usa `ST_Slope = Up` e `RestingECG = Normal/ST`.

**Cruzamento com o k = 2:**

| Grupo no k = 2 | → grupo 0 | → grupo 1 | → grupo 2 | → grupo 3 |
|---|---|---|---|---|
| "doente" (519) | 124 | 277 | 0 | 118 |
| "saudável" (399) | 22 | 10 | 304 | 63 |
| discordantes do k = 2 (135) | 20 | 39 | 32 | 44 |

## Achados

1. **Com 4 grupos, o K-Means separa o ECG de repouso, e não subtipos da doença.** Os
   dois grupos extras são formados por uma categoria só: o grupo 0 tem 100% de
   pacientes com ECG = ST e o grupo 3, 100% com LVH. Os grupos 1 e 2 repetem a divisão
   doente/saudável do k = 2 entre os pacientes com ECG normal. Na prática, o k = 4
   reproduz o k = 2 cruzado com a variável RestingECG.
2. **O ECG de repouso quase não se relaciona com o diagnóstico.** A proporção de doentes
   é de 52% (Normal), 56% (LVH) e 66% (ST). Por isso os grupos 0 e 3 misturam doentes e
   saudáveis (79,5% e 58,6% de doentes), e a concordância geral cai: o ARI vai de 0,498
   para 0,264 (Δ = −0,214 [−0,286; −0,142]), com a mesma queda no ARI registrado.
3. **O "grupo intermediário" não é um achado clínico.** O grupo 3, com 58,6% de doentes,
   parecia sugerir uma faixa de risco intermediário. O cruzamento mostra que ele é
   simplesmente o conjunto dos pacientes com LVH. Os discordantes do k = 2 não se
   concentram nele: 44 dos 135 (33%), num grupo que tem 20% da base.
4. **Dentro dos pacientes com ECG normal, a separação é até mais nítida.** Nos grupos 1 e
   2 (591 pacientes), o ARI é 0,608, maior que o do k = 2 na base inteira. Isso reforça
   que o eixo doente/saudável do k = 2 (ST_Slope e angina no esforço) é a estrutura
   relevante, e que o ECG de repouso só a mistura.
5. **A silhueta não distingue k = 2 de k = 4.** 0,165 contra 0,162, com Δ = −0,004
   [−0,022; +0,030]. As duas ficam ~0,08 acima da silhueta nula. Só a silhueta não
   justificaria o k = 4.
6. **O k = 4 é menos estável.** Jaccard de 0,76 a 0,89, contra 0,98 nos dois grupos do
   k = 2. Os grupos 0 e 3, os definidos pelo ECG, são os menos estáveis (0,76 e 0,78),
   perto do limite de 0,75.
7. **O k = 4 troca especificidade por sensibilidade.** Recall de 0,937 (contra 0,878),
   mas especificidade de 0,663 (contra 0,822): os grupos 0 e 3 são mapeados como
   "doente" e levam junto os saudáveis com ECG alterado. A AUC do escore fica 0,025
   menor (0,889 contra 0,914).
8. **A trava de categoria rara barrou o artefato por pouco.** Com o limite de 20%, o
   k = 4 foi eliminado pelo grupo de ECG = ST (19,4% da base). O grupo de LVH (20,5%)
   passaria sozinho, por 0,5 ponto. O artefato é o mesmo nos dois grupos, e o limite
   escolhido o barra só por estar logo acima de 19,4%.

## Implicações

- **O k = 2 se confirma como resultado principal**, por concordância (ARI 0,498 contra
  0,264), estabilidade (Jaccard 0,98 contra mínimo de 0,76) e interpretação.
- **A trava de categoria rara se justifica com um exemplo concreto:** sem ela, a regra
  aceitaria grupos que são uma variável da tabela. No artigo, isso responde à pergunta
  "por que 20%?" melhor do que o número sozinho.
- **Sobre o limite da trava:** o achado 8 mostra que 20% fica perto das prevalências de
  RestingECG (19,4% e 20,5%). Um limite de 25% barraria as duas categorias com folga
  e não mudaria o k = 2. Fica registrado como possibilidade; a decisão do grupo
  continua 20%.

## Para o texto do artigo

> Como análise de sensibilidade, avaliou-se a configuração que a regra de decisão
> escolheria com um limite menos restritivo para a trava de categoria rara (k = 4).
> Os dois grupos adicionais foram formados inteiramente por uma categoria do
> eletrocardiograma de repouso: um com todos os pacientes com alteração de ST e outro
> com os pacientes com hipertrofia ventricular esquerda. Os demais pacientes se
> dividiram como no k = 2. Como o eletrocardiograma de repouso tem pouca relação com o
> diagnóstico nesta base (52% a 66% de doentes entre as categorias), esses grupos
> misturaram doentes e saudáveis, e a concordância caiu de ARI = 0,498 para 0,264
> (diferença pareada de −0,214; IC 95% de −0,286 a −0,142), com especificidade de
> 0,663 contra 0,822. A silhueta não distinguiu as duas soluções (diferença de −0,004;
> IC 95% de −0,022 a +0,030), e os grupos do k = 4 foram menos estáveis (Jaccard de
> 0,76 a 0,89, contra 0,98). O resultado indica que, sob padronização completa, grupos
> adicionais tendem a reproduzir categorias isoladas, e não subtipos clínicos, o que
> justifica a trava e a escolha de k = 2.

## Cuidados

- **Não apresentar o k = 4 como resultado.** Ele entra como sensibilidade, numa
  subseção curta e num slide.
- **Não afirmar que o ECG de repouso é irrelevante clinicamente.** O achado é que ele
  pouco se relaciona com o diagnóstico *nesta base* e que separá-lo não ajuda o
  agrupamento.
- **A fidelidade da árvore (91%) não torna os grupos "explicáveis" no sentido clínico.**
  Ela é alta justamente porque os grupos seguem uma variável.
- **O k = 4 depende do `standard_all`.** Sob outro escalonamento, os grupos extras seriam
  outros. O achado vale para a configuração final, não para "k = 4" em geral.
- **Provisório:** refazer com os resultados da máquina do grupo.

## Arquivos de origem

- `configs/alternativa_k4.yaml`: definição da alternativa
- `results/alternativa_k4/comparacao/comparacao.md`: métricas, diferenças pareadas, grupos e cruzamento
- `results/alternativa_k4/comparacao/{metricas,grupos,cruzamento}.csv`
- `results/alternativa_k4/r06_perfil/`: perfil dos grupos, árvore substituta, discordantes, gráficos
- `results/alternativa_k4/r07_robustez/`: sementes, bootstrap (Jaccard por grupo), subgrupos
- `results/alternativa_k4/r08_generalizacao/`: dentro × fora da amostra e referências supervisionadas
- Composição dos grupos por RestingECG e ST_Slope e ARI nos grupos 1 e 2 (achados 1 e 4):
  calculados à parte com o pipeline do projeto; não há arquivo em `results/`
