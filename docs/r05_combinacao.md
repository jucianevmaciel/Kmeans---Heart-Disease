# R5 — Combinação dos vencedores

**Pergunta:** os vencedores das rodadas R1 a R4 funcionam juntos? Cada componente
escolhido ainda contribui quando os outros estão presentes?

**Status:** decidida. **Vencedora: a configuração completa** (`standard_all` +
`mediana` + sem redução + k = 2 + k-means++), gravada em
`results/r05_combinacao/vencedor.yaml` e herdada pela R5b.
**Execução:** 23/11/2026 (2 opções × 20 sementes + 100 reamostras bootstrap).

## Configuração

- **Ponto de partida:** o vencedor acumulado de R1 a R4: `standard_all` (R1), zeros pela
  mediana e Oldpeak mantido (R2), k = 2 e k-means++ (R3), sem redução (R4); n_init = 50.
- **Método (ablação):** a configuração completa é comparada com versões em que um
  vencedor por vez volta ao valor do `base.yaml`. As retiradas vêm antes na ordem de
  desempate: se uma delas empatar com a completa, vence a versão com menos componentes.
- **Retiradas previstas e o que aconteceu:**

| Retirada | Volta para | Situação |
|---|---|---|
| `sem_escalonamento_vencedor` | `standard` | **rodada** |
| `sem_tratamento_dados` | mediana, Oldpeak mantido | ignorada: o vencedor da R2 já era o valor da base |
| `sem_reducao` | sem redução | ignorada: o vencedor da R4 já era o valor da base |
| `sem_inicializacao_vencedora` | k-means++ | ignorada: o vencedor da R3 já era o valor da base |

- **Critério:** ARI. O k não é reajustado aqui; isso fica para a R5b, pela silhueta.
- **Regra:** empate se o IC 95% da diferença pareada de ARI (bootstrap, pacientes fora da
  reamostra) contém zero. Travas: Jaccard ≥ 0,75; colesterol ausente ≤ 2× a base;
  nenhum grupo de categoria rara.

## Resultados

| Opção | Escalonamento | ARI | ARI registr. | NMI | Acurácia | Recall | Espec. | AUC | Jaccard | Situação |
|---|---|---|---|---|---|---|---|---|---|---|
| `sem_escalonamento_vencedor` | `standard` | 0,318 | 0,344 | 0,244 | 0,782 | 0,774 | 0,793 | 0,858 | 0,97 · 0,97 | — |
| **completa** | **`standard_all`** | **0,498** | **0,516** | **0,394** | **0,853** | **0,878** | **0,822** | **0,914** | 0,98 · 0,98 | **vencedora** |

Ambas passam pelas travas (maior concentração de uma categoria num grupo: 40%; lift do
colesterol ausente de 1,43 e 1,44).

**Comparação pareada por bootstrap** (completa − retirada; pacientes fora da reamostra):

| Métrica | Δ | IC 95% | Reamostras em que a completa é melhor |
|---|---|---|---|
| ARI | +0,178 | [+0,119; +0,245] | 100% |
| ARI registrado | +0,167 | [+0,081; +0,241] | 100% |

## Achados

1. **A configuração completa vence com folga.** Retirar o `standard_all` faz o ARI cair de
   0,498 para 0,318 (Δ = +0,178 [+0,119; +0,245]), e a completa é melhor em todas as
   100 reamostras. O ganho se mantém nos pacientes com colesterol registrado (+0,167
   [+0,081; +0,241]).
2. **A configuração final só difere da base no escalonamento.** Das quatro retiradas
   previstas, três foram ignoradas porque os vencedores da R2, R3 e R4 já eram os valores
   do `base.yaml`. A configuração final é a da base com `standard_all` no lugar de
   `standard`.
3. **Todo o ganho do pipeline vem do escalonamento.** O ARI da versão sem `standard_all`
   (0,318) é exatamente o do K-Means da R0. Entre a R0 e a configuração final, a única
   mudança que alterou o resultado foi padronizar também as colunas 0/1, que dá às
   variáveis categóricas o mesmo peso das numéricas na distância (R1). As outras rodadas
   confirmaram as escolhas mais simples: tratar os zeros pela mediana (R2), k = 2 (R3) e
   não reduzir a dimensão (R4).
4. **A combinação não cria interação inesperada.** O resultado da completa (0,498) é o
   mesmo da R1, R2, R3 e R4. Isso era esperado: como os outros componentes são os da base,
   a R5 repete a comparação da R1 (`standard_all` × `standard`) e chega à mesma
   diferença (+0,178).
5. **As duas versões são estáveis.** Jaccard de 0,97 a 0,98 nos dois grupos; estabilidade
   entre sementes de 1,000 nas duas.

## Implicações para as próximas rodadas

- **Nada muda nos arquivos.** A R5b herda a configuração completa.
- **A R5b refaz a escolha do k sobre a combinação final.** Como a configuração é a mesma
  da R3, o resultado deve repetir o k = 2 (os k ≥ 3 barrados pelas mesmas travas). O
  vencedor da R5b é a **configuração final**, usada em R6, R7, R8 e nas análises
  complementares de k.
- **Para o artigo:** a sequência de rodadas pode ser apresentada de forma enxuta. Uma
  única decisão (o escalonamento) foi responsável por todo o ganho; as demais rodadas
  são a evidência de que as alternativas não ajudam.

## Para o texto do artigo

> Para verificar se as escolhas das rodadas anteriores funcionam em conjunto, a
> configuração final foi comparada com versões em que cada componente escolhido volta ao
> valor de partida. Como o tratamento dos dados, o número de grupos, a inicialização e a
> ausência de redução de dimensão coincidiram com os valores de partida, apenas a
> retirada da padronização completa pôde ser avaliada. Sem ela, o ARI caiu de 0,498 para
> 0,318 (diferença pareada de +0,178; IC 95% de +0,119 a +0,245), com a configuração
> completa superior em todas as reamostras. Assim, a padronização de todas as colunas foi
> a única escolha que alterou o resultado em relação ao K-Means de partida; as demais
> rodadas indicaram que as alternativas avaliadas não trazem ganho.

## Cuidados

- **Não chamar a R5 de "ablação completa".** Só um componente pôde ser retirado; as outras
  três retiradas não existiam, porque os vencedores eram os valores da base. Dizer isso
  explicitamente na metodologia.
- **Não dizer que as outras rodadas "não serviram".** Elas são a evidência de que tratar
  os zeros de outro jeito, usar outro k ou reduzir a dimensão não ajuda. Sem elas, a
  configuração final seria uma suposição, não uma conclusão.
- **O ganho do escalonamento vale para esta base.** Ele vem de dar mais peso às
  categóricas, que aqui carregam a informação mais ligada ao diagnóstico (R1).
- **A escolha foi guiada pelo ARI**, que usa o diagnóstico. Registrar na metodologia
  (decisão do grupo, ver anotacoes_artigo.md).

## Arquivos de origem

- `results/r05_combinacao/decisao.md`: tabela da rodada e regra aplicada
- `results/r05_combinacao/resumo.csv`: médias, desvios, travas e IC por opção
- `results/r05_combinacao/por_semente.csv`: uma linha por opção × semente
- `results/r05_combinacao/bootstrap.csv`: ARI, ARI registrado, silhueta e Jaccard fora da reamostra (100 reamostras pareadas)
- `results/r05_combinacao/vencedor.yaml`: configuração herdada pela R5b
- `configs/r05_combinacao.yaml`: definição da rodada (bloco `ablacao`)
- Retiradas ignoradas: mensagens `[ablação]` no terminal ao rodar a rodada
- Proporção de reamostras em que a completa é melhor: calculada à parte a partir do `bootstrap.csv`
