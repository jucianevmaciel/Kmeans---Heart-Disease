# Anotações para o artigo

Estado do pipeline em 23/11/2026: regra de decisão por bootstrap pareado, estabilidade
por grupo (Jaccard), travas de atalho e de categoria rara, ARI só nos pacientes com
colesterol registrado na R2.

## Decisões do grupo

- [x] **Critério principal:** ARI (opção A, "os grupos coincidem com a doença?") nas
      rodadas R1, R4 e R5. Registrar na metodologia que a seleção do pré-processamento
      é guiada pelo rótulo, embora o agrupamento não o use. (`decisao.criterio_principal`)
- [x] **R2 pelo ARI só nos pacientes com colesterol registrado** (746 de 918). Nesses
      pacientes o atalho do colesterol não tem como ajudar. O ARI total é relatado.
      (`criterio: ari_registrado` em configs/r02_dados.yaml)
- [x] **k pela silhueta, só entre os k com todos os grupos estáveis** (R3 e R5b).
      Empate pelo bootstrap pareado; entre os empatados, o menor k. A silhueta é
      relatada ao lado da silhueta nula (colunas embaralhadas).
- [x] **Empate por bootstrap pareado** (substitui o teste t do SVM e o critério
      antigo do desvio entre sementes): 100 reamostras, as mesmas para todas as opções;
      cada opção é reajustada na reamostra e avaliada nos pacientes que ficaram fora
      dela. Empata com a melhor se o IC 95% da diferença contém zero.
      (`decisao.bootstrap`, `decisao.nivel_ic`)
- [x] **Estabilidade por grupo:** Jaccard médio por bootstrap ≥ 0,75 em **todos** os
      grupos (Hennig, 2007). A estabilidade entre sementes virou só diagnóstico.
      (`decisao.jaccard_min`)
- [x] **n_init = 50** (era 10): com 50 inicializações, a semente quase não muda o
      resultado, e a variação entre sementes deixa de se confundir com a estrutura.
- [x] **Trava do atalho relativa:** % de colesterol ausente no grupo mais concentrado
      ÷ % na base (18,7%) ≤ 2,0. Substitui o limite absoluto de 50%, que nunca atuava
      com k ≤ 6 (o pior grupo ficava em 27–35%). (`decisao.trava_atalho_lift`)
- [x] **Trava de categoria rara:** nenhum grupo com ≥ 90% dos pacientes numa categoria
      que tenha < 20% da base (categóricas, FastingBS e colesterol ausente).
      (`decisao.trava_categoria`) Ver a sensibilidade abaixo.
- [x] **Número de sementes:** 20 (`sementes` em configs/base.yaml)
- [x] **Sem divisão treino/teste:** todas as rodadas usam os 918 pacientes. O K-Means
      não usa o diagnóstico para agrupar. A R8 (validação cruzada 5×5, protocolo do
      SVM) mede o otimismo de avaliar nos mesmos pacientes.
- [x] **Limite da trava de categoria rara mantido em 20%**: decide o k final (ver
      "Sensibilidade"). Resultado principal: k = 2. O k = 4 (o que a regra escolheria
      com 15% ou 10%) entra como análise de sensibilidade (docs/alternativa_k4.md).

## Regra de decisão (src/compare.py)

1. **Elegíveis:** não supervisionadas, fora da disputa = não, Jaccard ≥ 0,75 em todos
   os grupos, lift do colesterol ausente ≤ 2,0 e nenhum grupo de uma categoria rara.
2. **Melhor:** maior média do critério no ajuste da base inteira (20 sementes).
3. **Empate:** IC 95% da diferença pareada (bootstrap, pacientes fora da reamostra)
   para a melhor contém zero.
4. Entre as empatadas, vence a primeira na ordem do YAML (a mais simples; na grade do
   k, o menor k).

## Resultado da execução de verificação (23/11/2026)

R0–R8 completas (20 sementes, 100 reamostras), scikit-learn 1.9.1. Os números podem
variar um pouco em outra versão; refazer na máquina do grupo antes de usar no artigo.

| Rodada | Vencedora | Observação |
|---|---|---|
| R0 | — (referências) | K-Means k=2: ARI 0,318, AUC 0,858; LogReg 0,518 / 0,922; GBoost 0,532 / 0,922. GMM instável (Jaccard 0,59 e 0,63) |
| R1 | `standard_all` (ARI 0,498) | vence com folga: IC da diferença exclui zero para todas as outras (minmax: +0,088 [+0,023; +0,144]) |
| R2 | `mediana` | `mediana_flag` tem a maior média, mas todas empatam no ARI registrado (Δ ≈ 0, IC ±0,02); vence a mais simples |
| R3 | k = 2, k-means++ | o único k elegível: k = 3 isola os 63 pacientes ST_Slope = Down; k = 4, 5, 7, 8 têm um grupo 100% RestingECG = ST ou ChestPainType = ATA (19% da base); k = 6 instável |
| R4 | sem redução | PCA empata (IC contém zero); vence a mais simples |
| R5 | completa | retirar o `standard_all` custa 0,178 de ARI [+0,119; +0,245] |
| R5b | k = 2 | igual à R3 |

**Configuração final:** `standard_all` + `mediana` + Oldpeak mantido + sem redução +
K-Means k = 2 (k-means++, n_init = 50).

| Métrica | Valor |
|---|---|
| ARI / ARI registrado | 0,498 / 0,516 |
| Acurácia (pureza) · recall · especificidade | 0,853 · 0,878 · 0,822 |
| AUC do escore | 0,914 (LogReg 0,923; GBoost 0,925 nas mesmas dobras) |
| Silhueta / silhueta nula | 0,165 / 0,082 |
| Jaccard por grupo (bootstrap) | 0,98 e 0,98 |
| Estabilidade entre sementes | 1,000 |
| R7: ARI com a referência, fora da reamostra | 0,962 ± 0,023 |
| R8: otimismo (dentro − fora) | ≈ 0 em todas as métricas |
| R6: grupos | 519 pacientes (86% doentes) e 399 (16% doentes); 135 discordantes; árvore substituta com 95,2% de fidelidade, primeiro corte em ST_Slope = Up |

Comparação com a versão anterior da regra (k = 3, `mediana_flag`): ARI 0,446 → 0,498;
estabilidade entre sementes 0,884 → 1,000; bootstrap 0,75 ± 0,21 → 0,96 ± 0,02.

## Sensibilidade: o limite da trava de categoria rara decide o k

Refazendo só a decisão da R3 com outros valores de `trava_categoria.prevalencia_max`:

| Limite | Vencedor | Por quê |
|---|---|---|
| 20% (adotado) | k = 2 | todos os k ≥ 3 eliminados por trava |
| 15% ou 10% | k = 4 | RestingECG = ST e ChestPainType = ATA (19%) passam; a silhueta de k = 8 (0,197) supera a de k = 2 (0,165) com IC excluindo zero, e k = 4 é o menor k empatado |

Varredura de k = 2 a 8 em docs/variacoes_k.md: todo k > 2 tem ao menos um grupo de
categoria isolada (Down, ECG de repouso, tipos de dor torácica); o ARI cai de 0,498 para
0,151 (todas as diferenças significativas) e a silhueta sobe de 0,165 para 0,197, com a
nula parada em 0,07–0,08. Os grupos de alto e baixo risco do k = 2 persistem em todos os k.

Análise completa do k = 4 em docs/alternativa_k4.md: os dois grupos extras são todos
os pacientes com ECG de repouso = ST e todos com LVH; os outros dois repetem o k = 2
entre os de ECG normal. ARI 0,264 contra 0,498 (Δ = −0,214 [−0,286; −0,142]); a
silhueta não distingue os dois (Δ = −0,004 [−0,022; +0,030]). O grupo de LVH tem 20,5%
da base e passaria pela trava de 20% sozinho; o k = 4 é barrado pelo grupo de ECG = ST
(19,4%). Um limite de 25% barraria os dois com folga, sem mudar o k = 2.

Leitura: sob `standard_all`, a silhueta **cresce** com o k porque os grupos viram
"fatias" de uma categoria (grupos 100% de uma categoria), enquanto a silhueta nula
fica estável (~0,07–0,08). Isso é o artefato de escalonamento, não estrutura clínica.
Argumento para o artigo: um grupo formado inteiramente por uma categoria está
reproduzindo a codificação, não descobrindo um subtipo. Alternativa mais simples de
defender: declarar k = 2 como hipótese principal (pergunta do trabalho: doente ×
saudável) e analisar k > 2 de forma descritiva.

## Pontos de método para a metodologia e a discussão

- O K-Means não vê o `HeartDisease`. O rótulo só entra na avaliação (ARI, NMI,
  pureza, escore de risco) e, por decisão do grupo, como critério de escolha.
- **k pela silhueta, não pelo ARI (R3 e R5b):** com 2 classes, o ARI favorece k = 2 e
  a escolha seria circular. Por isso o reajuste do k depois da combinação foi
  separado da R5 (que é decidida pelo ARI) numa R5b pela silhueta.
- **Silhueta fraca, mas acima do acaso:** todos os k ficam entre 0,16 e 0,20, abaixo
  de 0,25 (Kaufman & Rousseeuw, 1990: sem estrutura substancial). A silhueta nula
  (cada coluna embaralhada; ideia da estatística gap, Tibshirani et al., 2001) fica
  em ~0,08: há estrutura acima do acaso, mas pouca.
- **Silhueta entre espaços diferentes não é comparável** (escalonamentos, PCA). Por
  isso R1 e R4 usam o ARI. Exemplo: sem escalonamento a silhueta é 0,395, mas a nula
  é 0,391 (nenhuma estrutura); no PCA com 2 componentes, 0,456 contra 0,453.
- **standard_all:** padroniza também as colunas 0/1 (a padronização escolhida muda
  os grupos encontrados; Milligan & Cooper, 1988). Uma categoria com prevalência p
  fica com distância 1/√(p(1−p)): ST_Slope = Down (7%) pesa 3,9, uma categoria comum
  pesa 2,0. Com k = 3, o terceiro grupo era exatamente os 63 pacientes Down. A trava
  de categoria rara impede isso. Pesos que igualam a contribuição de cada variável
  (Hennig & Liao, 2013) não resolvem sozinhos: com eles, a flag de colesterol ausente
  vira o grupo extra (168 de 171 pacientes).
- **Atalho do colesterol:** os zerados são majoritariamente doentes (88%), provável
  efeito do hospital de origem (pela documentação da UCI, a maior parte vem do
  subconjunto da Suíça; conferir antes de citar). É um caso de vazamento (Kaufman et
  al., 2012). A flag de ausência pode introduzir viés quando a falta está ligada ao
  desfecho (Groenwold et al., 2012). No teste, a flag não ganha nada nos pacientes com
  colesterol registrado.
- **Empate por bootstrap pareado:** o desvio entre sementes media só a convergência
  do otimizador (~0,001), não a variação de amostragem (~0,04 no ARI). Bootstrap:
  Efron & Tibshirani (1993). Alternativa coerente com o SVM: teste t corrigido de
  Nadeau & Bengio (2003) nas dobras 5×5.
- **Jaccard por grupo** (Hennig, 2007): < 0,5 o grupo se dissolve; ≥ 0,75 é válido;
  ≥ 0,85 é altamente estável. Estabilidade como validade: Ben-Hur et al. (2002); von
  Luxburg (2010).
- **kbest** usa o diagnóstico para escolher colunas: fica fora da disputa na R4.
- **Escore de risco pela distância aos centróides:** permite comparar a ROC-AUC do
  K-Means com a do SVM e das referências supervisionadas.
- **Categóricas com distância euclidiana** são uma aproximação; K-Prototypes (Huang,
  1998) ou Gower (1971) com PAM são alternativas (limitação).
- **Cruzamento com os erros do SVM (R6):** o SVM-Infarto não salva as previsões por
  paciente. Para usar `erros_svm` em configs/r06_perfil.yaml, é preciso exportar um
  CSV com a coluna `id` (linha no heart.csv) dos pacientes que o SVM errou
  (previsões fora da dobra da validação cruzada).
- **Limitação da decisão sem divisão:** os pacientes avaliados também participaram
  das escolhas das rodadas (pelo ARI). A R8 mede o otimismo do ajuste, não o da
  seleção. O bootstrap avalia cada opção nos pacientes fora da reamostra, o que
  reduz, mas não elimina, esse otimismo.
- **Comparação com o SVM:** a AUC "fora" da R8 usa as mesmas dobras (5×5, semente
  42) da validação cruzada do SVM-Infarto.

## Registro de decisões

| Data | Rodada | Decisão | Motivo |
|---|---|---|---|
| 21/11/2026 | todas | critério ARI; 20 sementes; estabilidade ≥ 0,80; trava do atalho 50% | definido antes de rodar os experimentos |
| 21/11/2026 | todas | sem divisão treino/teste; teste final e R8 80/20 removidos | o K-Means não usa o rótulo para agrupar; a nova R8 mede o otimismo por validação cruzada |
| 23/11/2026 | todas | empate por bootstrap pareado (IC 95%, 100 reamostras) no lugar do desvio entre sementes | o desvio entre sementes não mede a variação de amostragem; diferenças de 0,007 decidiam rodadas |
| 23/11/2026 | todas | estabilidade por Jaccard de cada grupo (≥ 0,75) no lugar do ARI entre sementes (≥ 0,80); n_init 10 → 50 | o limiar antigo dependia da semente (k = 4: 0,778 com k-means++, 0,845 com random) |
| 23/11/2026 | todas | trava do atalho relativa (lift ≤ 2,0) no lugar de 50% absoluto | a trava antiga nunca atuava com k ≤ 6 |
| 23/11/2026 | todas | nova trava de categoria rara (≥ 90% do grupo numa categoria com < 20% da base) | com standard_all, k = 3 isolava exatamente os 63 pacientes ST_Slope = Down |
| 23/11/2026 | R2 | critério ari_registrado | o atalho do colesterol não pode ajudar nos pacientes com colesterol registrado |
| 23/11/2026 | R3, R5b | só k com todos os grupos estáveis; silhueta com empate por bootstrap; menor k entre os empatados; silhueta nula relatada | a silhueta não separava os k (0,157–0,173) |
| 23/11/2026 | R3, R5b | trava de categoria rara mantida em 20%; resultado principal k = 2; k = 4 como análise de sensibilidade (configs/alternativa_k4.yaml) | com 15% ou 10% a regra escolheria k = 4, cujos grupos extras são categorias do ECG de repouso; mostrar a alternativa responde a "por que 20%?" |
| 23/11/2026 | complementar | varredura de k = 2 a 8 sobre a configuração final (configs/variacoes_k.yaml), mantendo k = 2 como resultado principal | mostrar no trabalho o que cada k encontra e por que nenhum supera o k = 2 |
| 23/11/2026 | todas | vencedor.yaml guarda só `pre` e `modelo` | antes, mudar `decisao` ou `sementes` no base.yaml não valia para as rodadas já rodadas |

## Referências

- Ben-Hur, A.; Elisseeff, A.; Guyon, I. (2002). A stability based method for discovering structure in clustered data. *Pacific Symposium on Biocomputing*, 7, 6–17.
- Efron, B.; Tibshirani, R. (1993). *An Introduction to the Bootstrap*. Chapman & Hall.
- Gower, J. C. (1971). A general coefficient of similarity and some of its properties. *Biometrics*, 27(4), 857–871.
- Groenwold, R. H. H. et al. (2012). Missing covariate data in clinical research: when and when not to use the missing-indicator method for analysis. *CMAJ*, 184(11), 1265–1269.
- Hennig, C. (2007). Cluster-wise assessment of cluster stability. *Computational Statistics & Data Analysis*, 52(1), 258–271.
- Hennig, C.; Liao, T. F. (2013). How to find an appropriate clustering for mixed-type variables with application to socio-economic stratification. *JRSS C*, 62(3), 309–369.
- Huang, Z. (1998). Extensions to the k-means algorithm for clustering large data sets with categorical values. *Data Mining and Knowledge Discovery*, 2(3), 283–304.
- Kaufman, L.; Rousseeuw, P. J. (1990). *Finding Groups in Data*. Wiley.
- Kaufman, S.; Rosset, S.; Perlich, C.; Stitelman, O. (2012). Leakage in data mining. *ACM TKDD*, 6(4).
- Milligan, G. W.; Cooper, M. C. (1988). A study of standardization of variables in cluster analysis. *Journal of Classification*, 5, 181–204.
- Nadeau, C.; Bengio, Y. (2003). Inference for the generalization error. *Machine Learning*, 52(3), 239–281.
- Tibshirani, R.; Walther, G.; Hastie, T. (2001). Estimating the number of clusters in a data set via the gap statistic. *JRSS B*, 63(2), 411–423.
- von Luxburg, U. (2010). Clustering stability: an overview. *Foundations and Trends in Machine Learning*, 2(3), 235–274.
