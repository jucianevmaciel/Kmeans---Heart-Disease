# Anotações para o artigo

## Decisões do grupo (fechadas antes de rodar)

- [x] **Critério principal:** ARI (opção A, "os grupos coincidem com a doença?").
      Registrar na metodologia que a seleção do pré-processamento é guiada pelo
      rótulo, embora o agrupamento não o use. (`decisao.criterio_principal`)
- [x] **Número de sementes:** 20 (`sementes` em configs/base.yaml)
- [x] **Estabilidade mínima:** ARI médio entre sementes ≥ 0,80 (`decisao.estabilidade_min`)
- [x] **Trava do atalho:** nenhum grupo com mais de 50% de colesterol ausente (`decisao.trava_atalho`)
- [x] **Sem divisão treino/teste:** todas as rodadas usam os 918 pacientes. O K-Means
      não usa o diagnóstico para agrupar. A R8 (validação cruzada 5×5, protocolo do
      SVM) mede o otimismo de avaliar nos mesmos pacientes. Num teste rápido, ele
      ficou em ~0,01–0,02 no ARI e ~0 na AUC do escore.

## Pontos de método para a metodologia e a discussão

- O K-Means não vê o `HeartDisease`. O rótulo só entra na avaliação (ARI, NMI,
  pureza, escore de risco) e, por decisão do grupo, como critério de escolha.
- **k pela silhueta, não pelo ARI (R3 e R5b):** com 2 classes, o ARI favorece k = 2 e
  a escolha seria circular. Por isso o reajuste do k depois da combinação foi
  separado da R5 (que é decidida pelo ARI) numa R5b pela silhueta.
- **Silhueta entre espaços diferentes não é comparável** (escalonamentos, PCA). Por
  isso R1 e R4 usam o ARI.
- **standard_all:** padroniza também as colunas 0/1. Categorias raras ficam com
  valores grandes e ganham peso extra na distância; conferir no perfil (R6).
- **Atalho do colesterol:** os zerados são majoritariamente doentes (88% no SVM),
  provável efeito do hospital de origem. O atalho aumenta o ARI; a trava impede
  que ele decida a R2.
- **kbest** usa o diagnóstico para escolher colunas: fica fora da disputa na R4.
- **Escore de risco pela distância aos centróides:** permite comparar a ROC-AUC do
  K-Means com a do SVM e das referências supervisionadas.
- **Categóricas com distância euclidiana** são uma aproximação; o K-Prototypes é a
  alternativa (limitação).
- Substituto do teste t do SVM: empate quando a diferença é menor que o desvio entre
  sementes.

- **Cruzamento com os erros do SVM (R6):** o SVM-Infarto não salva as previsões por
  paciente. Para usar `erros_svm` em configs/r06_perfil.yaml, é preciso exportar um
  CSV com a coluna `id` (linha no heart.csv) dos pacientes que o SVM errou
  (previsões fora da dobra da validação cruzada).

- **Limitação da decisão sem divisão:** os pacientes avaliados também participaram
  das escolhas das rodadas (pelo ARI). A R8 mede o otimismo do ajuste, não o da
  seleção. Argumento: cada rodada compara de 3 a 7 opções, então o otimismo da
  seleção deve ser pequeno.
- **Comparação com o SVM:** a AUC "fora" da R8 usa as mesmas dobras (5×5, semente
  42) da validação cruzada do SVM-Infarto.

## Registro de decisões

| Data | Rodada | Decisão | Motivo |
|---|---|---|---|
| 21/11/2026 | todas | critério ARI; 20 sementes; estabilidade ≥ 0,80; trava do atalho 50% | definido antes de rodar os experimentos |
| 21/11/2026 | todas | sem divisão treino/teste; teste final e R8 80/20 removidos | o K-Means não usa o rótulo para agrupar; a nova R8 mede o otimismo por validação cruzada |
