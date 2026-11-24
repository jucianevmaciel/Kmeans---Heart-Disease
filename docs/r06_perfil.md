# R6 — Perfil clínico dos grupos

**Pergunta:** os grupos da configuração final fazem sentido clínico? O que os diferencia,
e quem são os pacientes que o agrupamento coloca no grupo "errado"?

**Status:** concluída. Rodada descritiva, sem escolha. É o teste de sanidade da
configuração final.
**Execução:** 23/11/2026 (configuração final da R5b, ajuste na base inteira, semente 0).

## Configuração

- **Configuração analisada:** a final (`results/r05b_reajuste_k/vencedor.yaml`):
  `standard_all`, zeros pela mediana, sem redução, K-Means k = 2, k-means++, n_init = 50.
- **Análises:**
  - **perfil dos grupos:** médias das numéricas na escala original e % de cada
    categoria, por grupo;
  - **árvore substituta:** árvore de decisão de profundidade 3 que prevê o *grupo* (não a
    doença) a partir das variáveis originais. Mostra quais variáveis definem os grupos;
  - **discordantes:** doentes no grupo de baixo risco e saudáveis no grupo de alto risco
    (o grupo recebe a classe majoritária dos seus pacientes);
  - **silhueta por paciente:** o quanto cada paciente está mais perto do próprio grupo
    do que do outro;
  - **gráficos 2D:** projeção por PCA, só para visualização.
- **Cruzamento com os erros do SVM:** não feito (`erros_svm: null` em
  `configs/r06_perfil.yaml`).

## Resultados

**Perfil dos grupos** (escala original):

| Variável | Grupo 0: alto risco | Grupo 1: baixo risco | Base |
|---|---|---|---|
| Pacientes | 519 (56,5%) | 399 (43,5%) | 918 |
| **% doentes** | **85,9%** | **15,5%** | 55,3% |
| ST_Slope = Up | 7,3% | 89,5% | 43,0% |
| ST_Slope = Flat | 81,7% | 9,0% | 50,1% |
| ST_Slope = Down | 11,0% | 1,5% | 6,9% |
| Angina no esforço (ExerciseAngina = Y) | 66,1% | 7,0% | 40,4% |
| Dor assintomática (ChestPainType = ASY) | 77,1% | 24,1% | 54,0% |
| Dor atípica (ChestPainType = ATA) | 2,9% | 39,6% | 18,9% |
| Oldpeak (média) | 1,34 | 0,30 | 0,89 |
| Frequência cardíaca máxima (média) | 125,6 | 151,4 | 136,8 |
| Idade (média) | 56,6 | 49,5 | 53,5 |
| Homens | 88,1% | 67,2% | 79,0% |
| Glicemia de jejum alta (FastingBS = 1) | 32,2% | 11,8% | 23,3% |
| Pressão em repouso (média) | 135,1 | 129,2 | 132,5 |
| Colesterol (média, só registrados) | 252,5 | 236,5 | 244,6 |
| ECG de repouso normal | 53,4% | 68,9% | 60,1% |
| Colesterol ausente | 27,0% | 8,0% | 18,7% |

**Árvore substituta** (`arvore_substituta.png`): profundidade 3, acerta o grupo de
**95,2%** dos pacientes.

| Caminho | Pacientes | % doentes | Grupo previsto |
|---|---|---|---|
| ST_Slope ≠ Up → dor ≠ ATA → FC máx. ≤ 155,5 | 436 | 87% | alto risco (99% dos pacientes) |
| ST_Slope = Up → sem angina no esforço → FC máx. > 88 | 334 | 13% | baixo risco (99%) |
| ST_Slope ≠ Up → dor ≠ ATA → FC máx. > 155,5 | 52 | 60% | alto risco (65%) |
| ST_Slope = Up → com angina → FC máx. ≤ 150,5 | 37 | 65% | alto risco (78%) |
| ST_Slope ≠ Up → dor = ATA → sem angina | 24 | 42% | baixo risco (79%) |
| ST_Slope = Up → com angina → FC máx. > 150,5 | 21 | 38% | baixo risco (90%) |
| outras duas folhas | 14 | — | — |

**Discordantes** (135 de 918 pacientes, 14,7%):

| | Saudáveis no grupo de alto risco | Doentes no grupo de baixo risco |
|---|---|---|
| Pacientes | 73 (17,8% dos saudáveis) | 62 (12,2% dos doentes) |
| Idade (média) | 57,4 (concordantes: 49,1) | 51,5 (concordantes: 56,5) |
| FC máxima (média) | 134,0 (concordantes: 151,2) | 152,4 (concordantes: 124,2) |
| Oldpeak (média) | 1,22 (concordantes: 0,23) | 0,65 (concordantes: 1,36) |
| ST_Slope = Up | 12% | 79% |
| ST_Slope = Flat | 75% | 19% |
| Angina no esforço | 47% | 11% |
| Colesterol ausente | 12,3% | 33,9% |

**Silhueta por paciente** (`silhueta_por_paciente.png`):

| | Silhueta média | Pacientes com silhueta negativa |
|---|---|---|
| Todos | 0,165 | 2,6% |
| Grupo 0 (alto risco) | 0,145 | 4,6% |
| Grupo 1 (baixo risco) | 0,192 | 0,0% |
| Discordantes | 0,099 | 6,7% |
| Concordantes | 0,177 | — |

## Achados

1. **Os grupos são um grupo de alto risco e um de baixo risco.** O grupo 0 tem 85,9% de
   doentes; o grupo 1, 15,5%. O K-Means não viu o diagnóstico, mas a divisão que ele
   encontrou separa a doença com acurácia de 85,3%.
2. **O que separa os grupos são os achados do teste de esforço e o tipo de dor.** As
   maiores diferenças estão na inclinação do segmento ST (Up: 7% contra 89%), na angina
   no esforço (66% contra 7%), na dor assintomática (77% contra 24%), no Oldpeak (1,34
   contra 0,30) e na frequência cardíaca máxima (126 contra 151). São marcadores
   conhecidos de doença coronariana na literatura clínica, o que dá coerência ao
   agrupamento.
3. **Uma única variável explica quase tudo.** A árvore substituta começa por "ST_Slope =
   Up?": quem tem inclinação Up vai quase todo para o grupo de baixo risco. Com mais duas
   perguntas (angina no esforço ou dor ATA, e frequência máxima), a árvore acerta o grupo
   de 95,2% dos pacientes. As duas maiores folhas reúnem 770 pacientes (84% da base), com
   99% de acerto do grupo cada uma.
4. **Pressão, colesterol e ECG de repouso quase não diferenciam os grupos.** Pressão em
   repouso de 135 contra 129; colesterol de 253 contra 236; ECG normal em 53% contra 69%.
   É coerente com as rodadas anteriores: o colesterol não contribui para os grupos (R2),
   e isolar o ECG de repouso piora o agrupamento (alternativa k = 4).
5. **Os discordantes têm o perfil do outro grupo.** Os 73 saudáveis no grupo de alto risco
   são mais velhos (57 contra 49 anos), com frequência máxima menor (134 contra 151),
   Oldpeak maior (1,22 contra 0,23) e ST plano (75%): clinicamente, parecem doentes. Os 62
   doentes no grupo de baixo risco são o oposto: mais jovens, frequência máxima alta
   (152), ST Up (79%) e pouca angina no esforço (11%). O agrupamento não erra ao acaso:
   coloca esses pacientes junto de quem eles se parecem.
6. **Os discordantes estão na fronteira.** A silhueta deles é menor (0,099 contra 0,177 dos
   concordantes), e 6,7% têm silhueta negativa, contra 2,6% da base.
7. **Entre os doentes no grupo de baixo risco, o colesterol ausente é frequente.** 33,9%
   deles têm colesterol registrado como 0, contra 18,7% da base. São pacientes cujo
   diagnóstico de doença não se apoia nos marcadores do teste de esforço; parte deles
   pode refletir o mesmo efeito de origem dos dados que gera o atalho do colesterol (R2).
8. **O grupo de baixo risco é mais coeso.** Silhueta de 0,192 e nenhum paciente com valor
   negativo, contra 0,145 e 4,6% no grupo de alto risco. O grupo de alto risco é mais
   heterogêneo; é nele que a análise de k > 2 encontrou as subdivisões por categoria
   (ST descendente, ECG de repouso).
9. **O grupo de alto risco concentra os pacientes sem colesterol registrado.** 27,0%
   contra 8,0% (lift de 1,44, abaixo da trava de 2×). Isso acompanha a proporção de
   doentes, e a R2 mostrou que o agrupamento não depende dessa variável.

## Implicações para as próximas rodadas

- **Nada muda nos arquivos.** A R7 (robustez) e a R8 (generalização) usam a mesma
  configuração final.
- **R7:** verificar se a estabilidade se mantém em subgrupos (sexo, colesterol ausente).
  Os achados 7 e 9 tornam o subgrupo "colesterol ausente" o mais importante de olhar.
- **R8:** a acurácia de 85,3% e o ARI de 0,498 vêm do ajuste na base inteira; a R8 diz se
  eles se mantêm fora da amostra.
- **Opcional:** o cruzamento com os erros do SVM diria se os 135 discordantes são os
  mesmos pacientes que o SVM erra. Precisa de um CSV com o `id` desses pacientes (ver
  anotacoes_artigo.md).

## Para o texto do artigo

> Os dois grupos encontrados pelo K-Means corresponderam a perfis de alto e baixo risco,
> com 85,9% e 15,5% de doentes. As maiores diferenças entre eles estiveram nas variáveis
> do teste de esforço e no tipo de dor torácica: inclinação ascendente do segmento ST
> (7,3% contra 89,5%), angina induzida pelo esforço (66,1% contra 7,0%), dor
> assintomática (77,1% contra 24,1%), depressão do segmento ST (Oldpeak médio de 1,34
> contra 0,30) e frequência cardíaca máxima (125,6 contra 151,4 bpm). Pressão arterial,
> colesterol e eletrocardiograma de repouso pouco diferiram. Uma árvore de decisão de
> profundidade 3 reproduziu o grupo de 95,2% dos pacientes, com a inclinação do segmento
> ST como primeira divisão. Os 135 pacientes cujo diagnóstico discordou do grupo (14,7%)
> apresentaram o perfil clínico do grupo em que foram colocados: os saudáveis do grupo de
> alto risco eram mais velhos, com menor frequência cardíaca máxima e maior depressão do
> segmento ST, e os doentes do grupo de baixo risco, o contrário. Esses pacientes ficaram
> na fronteira entre os grupos (silhueta média de 0,099, contra 0,177 dos demais).

## Cuidados

- **Não chamar os grupos de "doentes" e "saudáveis".** São grupos de alto e baixo risco: o
  de alto risco tem 14% de saudáveis, e o de baixo risco, 16% de doentes.
- **Não afirmar relação causal.** O perfil descreve quem está em cada grupo; não diz que
  ST plano ou angina causam a doença.
- **A coerência clínica (achado 2) deve vir com referência.** Citar literatura de
  cardiologia sobre teste ergométrico e sintomas antes de afirmar no artigo.
- **A árvore explica o grupo, não a doença.** A fidelidade de 95,2% é acerto do grupo; a
  % de doentes nas folhas é só para leitura.
- **Os discordantes não são "erros" do K-Means** no sentido supervisionado. O K-Means não
  tenta prever o diagnóstico; os discordantes são pacientes cujo perfil não segue o
  padrão do próprio diagnóstico.
- **O achado 7 é uma hipótese.** A relação entre colesterol ausente e origem dos dados não
  está confirmada (ver R2).
- **Os gráficos 2D são projeções.** O PCA mostra só 31% da variância (21% + 10%); a
  sobreposição que aparece neles é maior do que a real nas 18 dimensões.

## Arquivos de origem

- `results/r06_perfil/perfil_grupos.csv`: médias e % de cada categoria por grupo
- `results/r06_perfil/arvore_substituta.txt` e `.png`: árvore substituta (texto e desenho)
- `results/r06_perfil/discordantes.csv`: os 135 pacientes discordantes, com o `id`
- `results/r06_perfil/discordantes_resumo.csv`: médias de discordantes × concordantes por diagnóstico
- `results/r06_perfil/silhueta_por_paciente.png`: silhueta de cada paciente por grupo
- `results/r06_perfil/clusters_2d.png`: grupos (cor) e diagnóstico (forma) na projeção PCA
- `results/r06_perfil/grupos_kmeans_vs_diagnostico.png`: grupos e diagnóstico lado a lado
  (gerado à parte, fora dos scripts, para os slides)
- `configs/r06_perfil.yaml`: parâmetros da rodada
- Composição categórica dos discordantes, silhueta por grupo e por discordância e o
  resumo das folhas da árvore: calculados à parte com o pipeline do projeto
