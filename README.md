# K-Means na base de doença cardíaca

Agrupamento não supervisionado com K-Means na base Heart Failure Prediction (Kaggle),
na mesma estrutura de rodadas do SVM-Infarto. Trabalho da disciplina de Aprendizado
de Máquina – PPGCC/UFPI.

**Pergunta do trabalho:** até que ponto a doença cardíaca aparece nos grupos naturais
dos pacientes, sem que o algoritmo veja o diagnóstico?

## Como rodar

Todas as rodadas usam a base inteira (918 pacientes). Não há divisão treino/teste:
o K-Means não usa o diagnóstico para agrupar. A R8 confere se isso deixa a
avaliação otimista.

```bash
pip install -r requirements.txt

python -m src.runner configs/r00_referencias.yaml
python -m src.runner configs/r01_escalonamento.yaml
python -m src.runner configs/r02_dados.yaml
python -m src.runner configs/r03_k_inicializacao.yaml
python -m src.cotovelo                                     # curvas por k (R3)
python -m src.runner configs/r04_reducao.yaml
python -m src.runner configs/r05_combinacao.yaml
python -m src.runner configs/r05b_reajuste_k.yaml          # define a configuração final
python -m src.cotovelo --rodada r05b_reajuste_k

python -m src.perfil_grupos                                # R6
python -m src.clusters_2d                                  # R6
python -m src.robustez                                     # R7
python -m src.generalizacao                                # R8
```

**Análise de sensibilidade (k = 4).** Depois da R5b, as análises da configuração final
podem ser refeitas com outro k, sem entrar na cadeia de rodadas. A alternativa herda a
configuração final e muda só o k (`configs/alternativa_k4.yaml`); as saídas vão para
`results/alternativa_k4/`, sem sobrescrever as da configuração final:

```bash
python -m src.perfil_grupos --config configs/alternativa_k4.yaml
python -m src.clusters_2d   --config configs/alternativa_k4.yaml
python -m src.robustez      --config configs/alternativa_k4.yaml
python -m src.generalizacao --config configs/alternativa_k4.yaml
python -m src.comparar_k    --config configs/alternativa_k4.yaml   # k = 2 x k = 4, pareado
```

**Variações de k (complementar).** A configuração final refeita com k de 2 a 8
(`configs/variacoes_k.yaml`): métricas, bootstrap pareado contra o k = 2, validação
cruzada 5×5, composição dos grupos e o que a regra de decisão faria com cada k. O k
principal continua sendo o da R5b. Saídas em `results/variacoes_k/` (inclui o gráfico
`variacoes_k.png`):

```bash
python -m src.variacoes_k
```

Para um teste rápido, acrescente `--sementes 3 --bootstrap 20` ao runner. O teste rápido
também grava o `vencedor.yaml`: rode de novo sem as opções antes de seguir para a
próxima rodada.

Cada rodada herda o `vencedor.yaml` da anterior (`herda_de` no YAML). Do vencedor só
se herdam `pre` e `modelo`; `sementes`, `dados` e `decisao` vêm sempre do `base.yaml`.
Para mudar uma escolha à mão, use o bloco `fixo:` do YAML da rodada seguinte. Para refazer só a
decisão de uma rodada sem rodar de novo: `python -m src.compare configs/<rodada>.yaml`.

## Rodadas

| Rodada | Pergunta | Critério | Desempate |
|---|---|---|---|
| R0 | Quais são as referências? | ARI, pureza e AUC do escore de todos | sem escolha |
| R1 | O escalonamento importa? | ARI | nenhum → standard → standard_all → minmax → robust |
| R2 | Zeros, atalho do colesterol e Oldpeak negativo | ARI só nos pacientes com colesterol registrado | a mais simples |
| R3 | Qual k e qual inicialização? | silhueta entre os k estáveis (silhueta nula e ARI relatados) | menor k; k-means++ |
| R4 | Reduzir a dimensão ajuda? | ARI; kbest fora da disputa | sem redução |
| R5 | Os vencedores funcionam juntos? | completa × retirada de cada vencedor (ARI) | menos componentes |
| R5b | O melhor k muda com a combinação? | igual à R3 | menor k |
| R6 | Os grupos fazem sentido clínico? | perfil, árvore substituta, discordantes | teste de sanidade |
| R7 | Os grupos são estáveis? | sementes, bootstrap (ARI e Jaccard por grupo), subgrupos | análise descritiva |
| R8 | A avaliação sem divisão é otimista? | dentro × fora da amostra, validação cruzada 5×5 (protocolo do SVM) | não escolhe nada |

## Regra de decisão (`src/compare.py`)

1. **Elegíveis:** não supervisionadas, fora da disputa = não e sem nenhuma trava:
   - Jaccard médio por bootstrap ≥ `decisao.jaccard_min` (0,75) em **todos** os grupos;
   - % de colesterol ausente no grupo mais concentrado ÷ % na base ≤
     `decisao.trava_atalho_lift` (2,0);
   - nenhum grupo com ≥ 90% dos pacientes numa categoria com < 20% da base
     (`decisao.trava_categoria`).
2. **Melhor:** maior média do critério no ajuste da base inteira (menor no Davies-Bouldin).
3. **Empate (bootstrap pareado):** 100 reamostras, as mesmas para todas as opções. Cada
   opção é reajustada na reamostra e avaliada nos pacientes fora dela. Empata com a
   melhor se o IC 95% da diferença contém zero.
4. Entre as empatadas, vence a primeira na ordem do YAML (a mais simples; na grade do
   k, o menor k).

## Métricas

- **Internas** (sem rótulo): silhueta, Davies-Bouldin, Calinski-Harabasz, inércia.
  **Silhueta nula:** a do K-Means com cada coluna embaralhada (referência sem estrutura).
- **Externas** (o rótulo só avalia): ARI, NMI, pureza (= acurácia pelo mapeamento
  grupo → classe majoritária), recall e especificidade. **ARI registrado:** ARI só
  nos pacientes com colesterol registrado.
- **Escore de risco:** d_saudável / (d_saudável + d_doente), com as distâncias aos
  centróides. Dá uma ROC-AUC comparável à do SVM e das referências supervisionadas.
- **Estabilidade:** Jaccard de cada grupo por bootstrap (decide); ARI médio entre
  pares de sementes (só diagnóstico).

## Estrutura

```
configs/      base.yaml + um YAML por rodada + alternativa_k4.yaml e variacoes_k.yaml (sensibilidade)
data/         raw/heart.csv (base usada); split/ = splits do SVM-Infarto, só como referência
src/
  config.py        herança dos YAML e expansão das opções
  dados.py         leitura da base
  pipeline.py      tratamento → codificação/escala → redução → agrupamento
  metricas.py      internas, externas, escore de risco, estabilidade, travas
  runner.py        roda uma rodada (opções × sementes + bootstrap pareado)
  compare.py       regra de decisão → decisao.md e vencedor.yaml
  cotovelo.py      curvas por k (R3)
  perfil_grupos.py perfil, árvore substituta, discordantes, silhueta (R6)
  clusters_2d.py   grupos em 2D pelo PCA (R6)
  robustez.py      sementes, bootstrap (com pacientes fora da reamostragem), subgrupos (R7)
  generalizacao.py dentro × fora da amostra e comparação com modelos supervisionados (R8)
  comparar_k.py    configuração final × alternativa (métricas pareadas e cruzamento dos grupos)
  variacoes_k.py   configuração final com k de 2 a 8 (análise complementar)
results/      uma pasta por rodada; alternativa_k4/ e variacoes_k/ para as análises de sensibilidade
docs/         anotacoes_artigo.md (decisões do grupo); rNN_<rodada>.md (resumo de cada rodada para o artigo)
```
