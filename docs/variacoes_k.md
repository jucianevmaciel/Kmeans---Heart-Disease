# Variações de k (k = 3 a 8) — análise complementar

> **Provisório.** Os números abaixo são da execução de verificação (23/11/2026, feita
> fora da máquina do grupo, scikit-learn 1.9.1). Refazer com `python -m src.variacoes_k`
> depois da R5b e conferir se batem.

**Pergunta:** o que o K-Means encontra se a configuração final usar mais de 2 grupos?
Algum outro k revela estrutura que o k = 2 esconde?

**Status:** análise complementar. **O resultado principal continua sendo k = 2**,
escolhido pela regra de decisão na R3/R5b. Os outros k mostram o que mais existe nos
dados e por que não foram escolhidos. O k = 4 tem uma análise detalhada à parte
(docs/alternativa_k4.md).

## Configuração

- **Definição:** `configs/variacoes_k.yaml`. Herda a configuração final
  (`r05b_reajuste_k`: `standard_all`, `mediana`, k-means++, n_init = 50) e troca só o
  k, para cada valor de 2 a 8. Não entra na cadeia de rodadas.
- **Comando:** `python -m src.variacoes_k` (cerca de 1 minuto). Saídas em
  `results/variacoes_k/`.
- **Avaliação de cada k:**
  - na base inteira (semente 0): ARI, ARI registrado, acurácia, recall, especificidade,
    AUC do escore, silhueta e silhueta nula;
  - no bootstrap pareado (100 reamostras, as mesmas para todos os k): Jaccard de cada
    grupo e diferença para o k = 2 com IC 95%;
  - na validação cruzada 5×5 com semente 42 (protocolo da R8): ARI e AUC fora da amostra;
  - diante das travas da regra de decisão: o que a R3/R5b faria com esse k;
  - pela composição dos grupos: categorias que reúnem ≥ 90% de cada grupo.

## Resultados

| k | ARI | ARI CV 5×5 | Acurácia | Recall | Espec. | AUC | Silhueta (nula) | Jaccard mín. | Na regra da R3/R5b |
|---|---|---|---|---|---|---|---|---|---|
| **2** | **0,498** | **0,498** | **0,853** | 0,878 | **0,822** | **0,914** | 0,165 (0,082) | **0,98** | **elegível (vence)** |
| 3 | 0,431 | 0,434 | 0,849 | 0,876 | 0,815 | 0,909 | 0,181 (0,082) | 0,85 | barrado: ST_Slope = Down (7%) |
| 4 | 0,264 | 0,273 | 0,815 | 0,937 | 0,663 | 0,889 | 0,162 (0,073) | 0,76 | barrado: RestingECG = ST (19%) |
| 5 | 0,231 | 0,233 | 0,807 | 0,935 | 0,649 | 0,892 | 0,172 (0,075) | 0,77 | barrado: RestingECG = ST (19%) |
| 6 | 0,225 | 0,222 | 0,809 | 0,904 | 0,693 | 0,882 | 0,186 (0,080) | 0,64 | barrado: instável e ChestPainType = TA (5%) |
| 7 | 0,157 | 0,165 | 0,805 | 0,872 | 0,722 | 0,882 | 0,185 (0,074) | 0,80 | barrado: ChestPainType = ATA (19%) |
| 8 | 0,151 | 0,152 | 0,820 | 0,799 | 0,846 | 0,891 | 0,197 (0,071) | 0,87 | barrado: ChestPainType = ATA (19%) |

**Diferenças pareadas para o k = 2** (bootstrap, pacientes fora da reamostra):

| k | Δ ARI | IC 95% | Δ silhueta | IC 95% |
|---|---|---|---|---|
| 3 | −0,084 | [−0,174; −0,024] | +0,010 | [−0,030; +0,024] |
| 4 | −0,214 | [−0,286; −0,142] | −0,004 | [−0,022; +0,030] |
| 5 | −0,247 | [−0,314; −0,175] | +0,007 | [−0,014; +0,020] |
| 6 | −0,286 | [−0,359; −0,203] | +0,011 | [−0,010; +0,031] |
| 7 | −0,329 | [−0,400; −0,266] | +0,020 | [+0,005; +0,031] |
| 8 | −0,346 | [−0,413; −0,281] | +0,025 | [+0,004; +0,045] |

**O que cada grupo novo isola:**

| k | Grupo que aparece (100% de uma categoria) | Pacientes | % doentes |
|---|---|---|---|
| 3 | ST_Slope = Down | 63 | 78% |
| 4 | RestingECG = ST · RestingECG = LVH (e o restante com ECG normal) | 146 · 181 | 80% · 59% |
| 5 | k = 4 + ST_Slope = Down | 63 | 78% |
| 6 | + ChestPainType = TA | 46 | 43% |
| 7 | + ChestPainType = ATA | 149 | 5% |
| 8 | os quatro tipos de dor torácica, cada um num grupo (ASY, NAP, ATA, TA) | 46 a 151 | 5% a 44% |

Em todos os k, dois grupos persistem: um de **alto risco** (86–91% doentes; ST_Slope =
Flat; 96–100% dos pacientes vindos do grupo "doente" do k = 2) e um de **baixo risco**
(5–16% doentes; ST_Slope = Up, sem angina no esforço; 0–2% vindos do grupo "doente").

Gráfico: `results/variacoes_k/variacoes_k.png` (ARI e AUC na base inteira e fora da
amostra, silhueta com a nula e Jaccard mínimo, por k).

## Achados

1. **Todo k acima de 2 isola categorias de uma variável.** Em todos os k de 3 a 8, há pelo
   menos um grupo com 100% dos pacientes numa única categoria: primeiro ST_Slope = Down
   (k = 3), depois as categorias do ECG de repouso (k = 4 e 5) e por fim os tipos de dor
   torácica (k = 6 a 8). No k = 8, o K-Means reproduz basicamente a tabela de tipo de dor
   × ECG de repouso (um grupo por tipo de dor, e os de ECG alterado à parte).
2. **A concordância com o diagnóstico só cai.** O ARI vai de 0,498 (k = 2) a 0,151 (k = 8),
   e todas as diferenças para o k = 2 são significativas (nenhum IC contém zero; a menor
   queda é a do k = 3, −0,084 [−0,174; −0,024]). As variáveis isoladas se relacionam
   menos com a doença que o eixo do k = 2 (inclinação do ST e angina no esforço). Por
   isso os grupos que elas formam misturam doentes e saudáveis.
3. **O núcleo do k = 2 sobrevive em todos os k.** Os grupos de alto risco (86–91% doentes)
   e de baixo risco (5–16%) aparecem em todas as soluções. Os grupos a mais saem das
   bordas desses dois. É a evidência mais direta de que a divisão doente/saudável é a
   estrutura principal desses dados.
4. **A silhueta sobe com o k pelo motivo errado.** De 0,165 (k = 2) a 0,197 (k = 8), com
   aumento significativo em k = 7 e 8 (+0,020 e +0,025, ICs excluem zero), enquanto a
   silhueta nula fica estável (0,07–0,08). Um grupo em que todos têm a mesma categoria é
   bem separado por construção, porque no `standard_all` a distância entre "tem" e "não
   tem" uma categoria rara é grande. Pela silhueta sozinha, o k escolhido seria 8, com
   ARI de 0,151. Isso justifica a trava de categoria rara.
5. **A estabilidade não ordena os k.** O Jaccard mínimo sobe e desce: 0,98, 0,85, 0,76,
   0,77, 0,64, 0,80, 0,87. Grupos definidos por uma categoria podem ser muito estáveis,
   porque a categoria está sempre lá. Por isso a estabilidade é uma trava, e não o
   critério de escolha.
6. **Nada disso é otimismo da avaliação.** O ARI e a AUC fora da amostra (validação
   cruzada 5×5) acompanham os da base inteira em todos os k: a maior diferença é 0,009
   no ARI (k = 4) e 0,005 na AUC (k = 8).
7. **O k = 3 é a alternativa "mais limpa", mas não é exceção.** Perde menos ARI (−0,084),
   todos os grupos são estáveis (Jaccard ≥ 0,85), e o grupo extra tem leitura clínica: o
   ST descendente é um marcador clássico de isquemia, e 78% desses pacientes são
   doentes. Mesmo assim, o grupo é a categoria inteira e só ela; a variável já estava na
   tabela. Esse k = 3 era o que a regra antiga escolhia, e foi o que motivou a criação
   da trava.
8. **Mais grupos trocam especificidade por sensibilidade, até k = 5.** Os grupos de
   categoria isolada costumam ter maioria de doentes e são mapeados como "doente": em
   k = 4 e 5, o recall sobe para 0,94 e a especificidade cai para 0,65–0,66. A AUC do
   escore cai de 0,914 para 0,88–0,89 em todos os k ≥ 4.

## Implicações

- **O k = 2 se confirma como resultado principal**, por todos os critérios ao mesmo
  tempo: maior ARI e AUC (dentro e fora da amostra), maior estabilidade, único k
  elegível pela regra e o único sem grupo de categoria isolada.
- **Resposta à pergunta do trabalho:** a estrutura natural dos pacientes coincide com a
  doença. Mais grupos não revelam subtipos; reproduzem a codificação das variáveis
  categóricas.
- **Para o artigo:** uma subseção curta ("Sensibilidade ao número de grupos") com a
  tabela de métricas e o gráfico. O k = 4 detalhado (docs/alternativa_k4.md) pode
  entrar como exemplo, ou só ser citado.
- **Para os slides:** o gráfico `variacoes_k.png` resume tudo num só quadro (o ARI cai, a
  silhueta sobe, a nula fica parada).

## Para o texto do artigo

> Para avaliar a sensibilidade ao número de grupos, a configuração final foi refeita
> com k de 3 a 8, mantidas as demais escolhas. Em todos os casos, ao menos um dos grupos
> adicionais foi formado inteiramente por uma única categoria de uma variável: a
> inclinação descendente do segmento ST (k = 3), as categorias do eletrocardiograma de
> repouso (k = 4 e 5) e os tipos de dor torácica (k = 6 a 8). A concordância com o
> diagnóstico caiu de forma monotônica, de ARI = 0,498 (k = 2) para 0,151 (k = 8), com
> todas as diferenças significativas na comparação pareada por bootstrap, e o mesmo
> padrão foi observado fora da amostra (validação cruzada 5×5). Em todas as soluções, os
> grupos de alto risco (86–91% de doentes) e de baixo risco (5–16%) se mantiveram, e os
> grupos adicionais surgiram das bordas desses dois. A silhueta aumentou com k (0,165
> para 0,197), enquanto a silhueta obtida com as variáveis embaralhadas permaneceu
> estável (0,07–0,08): sob padronização completa, isolar uma categoria produz grupos
> bem separados por construção, o que torna a silhueta inadequada como critério único
> para k nesta base.

## Cuidados

- **Não apresentar os outros k como resultados.** São análise de sensibilidade; o
  resultado do trabalho é o k = 2.
- **Não dizer que "os dados têm 2 grupos naturais"** de forma absoluta. A silhueta de
  todos os k é fraca (< 0,25) e a estrutura acima do acaso é pequena (~0,08). O que se
  pode afirmar é que, entre os k testados, só o k = 2 produz grupos que não se reduzem
  a uma categoria, e que esses grupos coincidem com o diagnóstico.
- **A composição dos grupos depende do `standard_all`.** Sob outro escalonamento, os
  grupos extras seriam outros (no `standard`, por exemplo, as numéricas pesam mais).
  O achado vale para a configuração final.
- **O grupo ST_Slope = Down (k = 3) tem leitura clínica, mas não é descoberta do
  agrupamento:** a variável já estava na base. Pode ser citado como curiosidade, não
  como achado.
- **Silhueta e Jaccard vêm de um ajuste por k (semente 0) e de 100 reamostras.** A
  ordem dos k pela silhueta (k = 3, 5, 6, 7 e 8 acima do k = 2) é robusta só em k = 7 e
  8, os únicos com IC excluindo zero.
- **Provisório:** refazer com os resultados da máquina do grupo.

## Arquivos de origem

- `configs/variacoes_k.yaml`: definição da análise (lista de k, k de referência, protocolo da CV)
- `src/variacoes_k.py`: script da análise
- `results/variacoes_k/resumo.md`: tabelas completas, incluindo os grupos de cada k
- `results/variacoes_k/metricas.csv`: uma linha por k
- `results/variacoes_k/diferencas.csv`: diferenças pareadas para o k = 2
- `results/variacoes_k/grupos.csv`: uma linha por k × grupo (tamanho, % doentes, Jaccard, categorias dominantes, origem no k = 2)
- `results/variacoes_k/bootstrap.csv` e `cv.csv`: dados por reamostra e por dobra
- `results/variacoes_k/variacoes_k.png`: gráfico para os slides
