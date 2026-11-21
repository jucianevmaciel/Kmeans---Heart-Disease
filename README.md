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

Para um teste rápido, acrescente `--sementes 3` ao runner.

Cada rodada herda o `vencedor.yaml` da anterior (`herda_de` no YAML). Para mudar uma
escolha à mão, use o bloco `fixo:` do YAML da rodada seguinte. Para refazer só a
decisão de uma rodada sem rodar de novo: `python -m src.compare configs/<rodada>.yaml`.

## Rodadas

| Rodada | Pergunta | Critério | Desempate |
|---|---|---|---|
| R0 | Quais são as referências? | ARI, pureza e AUC do escore de todos | sem escolha |
| R1 | O escalonamento importa? | ARI | nenhum → standard → standard_all → minmax → robust |
| R2 | Zeros, atalho do colesterol e Oldpeak negativo | ARI, com a trava do atalho | a mais simples |
| R3 | Qual k e qual inicialização? | silhueta (ARI só relatado) | menor k; k-means++ |
| R4 | Reduzir a dimensão ajuda? | ARI; kbest fora da disputa | sem redução |
| R5 | Os vencedores funcionam juntos? | completa × retirada de cada vencedor (ARI) | menos componentes |
| R5b | O melhor k muda com a combinação? | silhueta (ARI só relatado) | menor k |
| R6 | Os grupos fazem sentido clínico? | perfil, árvore substituta, discordantes | teste de sanidade |
| R7 | Os grupos são estáveis? | sementes, bootstrap, subgrupos | análise descritiva |
| R8 | A avaliação sem divisão é otimista? | dentro × fora da amostra, validação cruzada 5×5 (protocolo do SVM) | não escolhe nada |

## Regra de decisão (`src/compare.py`)

1. **Elegíveis:** não supervisionadas, fora da disputa = não, estabilidade ≥
   `decisao.estabilidade_min` e nenhum grupo com mais de `decisao.trava_atalho` de
   colesterol ausente.
2. **Melhor:** maior média do critério entre as sementes (menor no Davies-Bouldin).
3. **Empate:** diferença para a melhor ≤ maior desvio-padrão entre sementes das duas.
4. Entre as empatadas, vence a primeira na ordem do YAML (a mais simples).

## Métricas

- **Internas** (sem rótulo): silhueta, Davies-Bouldin, Calinski-Harabasz, inércia.
- **Externas** (o rótulo só avalia): ARI, NMI, pureza (= acurácia pelo mapeamento
  grupo → classe majoritária), recall e especificidade.
- **Escore de risco:** d_saudável / (d_saudável + d_doente), com as distâncias aos
  centróides. Dá uma ROC-AUC comparável à do SVM e das referências supervisionadas.
- **Estabilidade:** ARI médio entre pares de sementes.

## Estrutura

```
configs/      base.yaml + um YAML por rodada
data/         raw/heart.csv (base usada); split/ = splits do SVM-Infarto, só como referência
src/
  config.py        herança dos YAML e expansão das opções
  dados.py         leitura da base e dos splits
  pipeline.py      tratamento → codificação/escala → redução → agrupamento
  metricas.py      internas, externas, escore de risco, estabilidade
  runner.py        roda uma rodada (opções × sementes)
  compare.py       regra de decisão → decisao.md e vencedor.yaml
  cotovelo.py      curvas por k (R3)
  perfil_grupos.py perfil, árvore substituta, discordantes, silhueta (R6)
  clusters_2d.py   grupos em 2D pelo PCA (R6)
  robustez.py      sementes, bootstrap (com pacientes fora da reamostragem), subgrupos (R7)
  generalizacao.py dentro × fora da amostra e comparação com modelos supervisionados (R8)
results/      uma pasta por rodada
docs/         anotacoes_artigo.md (decisões do grupo)
```
