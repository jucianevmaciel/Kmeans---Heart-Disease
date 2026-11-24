# R2 — Tratamento dos dados

**Pergunta:** como tratar o colesterol registrado como zero (valor ausente ligado ao
diagnóstico), o Oldpeak negativo e a FastingBS? Alguma dessas escolhas melhora a
concordância dos grupos com o diagnóstico?

**Status:** decidida. **Vencedora: `mediana`** (o tratamento da base), gravada em
`results/r02_dados/vencedor.yaml` e herdada pela R3.
**Execução:** 23/11/2026 (6 opções × 20 sementes + 100 reamostras bootstrap).

## Configuração

- **Herda da R1:** `standard_all`, sem redução, K-Means k = 2, k-means++, n_init = 50.
- **O problema:** 172 pacientes (18,7%) têm colesterol registrado como 0, um valor
  impossível que na prática significa "não medido". Entre eles, 88,4% são doentes,
  contra 47,7% entre os 746 com colesterol registrado. É um **atalho**: a ausência
  do exame prevê o diagnóstico, provavelmente por causa do hospital de origem, e não
  por motivo clínico. Também há 13 pacientes com Oldpeak negativo e 1 com pressão
  em repouso igual a 0 (este sempre imputado pela mediana).
- **Opções, em ordem de desempate:**

| Opção | Colesterol 0 | Oldpeak negativo | Outras |
|---|---|---|---|
| `mediana` | imputado pela mediana | mantido | — |
| `sem_colesterol` | coluna removida | mantido | — |
| `sem_colesterol_fastingbs` | coluna removida | mantido | FastingBS removida |
| `mediana_flag` | mediana + coluna indicadora "colesterol ausente" | mantido | — |
| `oldpeak_zero` | mediana | negativos viram 0 | — |
| `oldpeak_abs` | mediana | valor absoluto | — |

- **Critério:** ARI **só nos pacientes com colesterol registrado** (`ari_registrado`),
  em quem o atalho não tem como ajudar. O ARI total é relatado.
- **Regra:** empate se o IC 95% da diferença pareada (bootstrap, pacientes fora da
  reamostra) contém zero; entre as empatadas, vence a primeira da lista. Travas:
  Jaccard ≥ 0,75; colesterol ausente ≤ 2× a base; nenhum grupo de categoria rara.

## Resultados

| Opção | ARI | **ARI registr.** | NMI | Acurácia | Recall | Espec. | AUC | Jaccard | Lift ausente | Situação |
|---|---|---|---|---|---|---|---|---|---|---|
| `mediana` | 0,498 | **0,516** | 0,394 | 0,853 | 0,878 | 0,822 | 0,914 | 0,98 · 0,98 | 1,44 | **vencedora** |
| `sem_colesterol` | 0,504 | 0,523 | 0,399 | 0,855 | 0,880 | 0,824 | 0,914 | 0,98 · 0,98 | 1,44 | empatada |
| `sem_colesterol_fastingbs` | 0,486 | 0,523 | 0,384 | 0,849 | 0,863 | 0,832 | 0,911 | 0,98 · 0,98 | 1,41 | empatada |
| `mediana_flag` | 0,529 | 0,527 | 0,422 | 0,864 | 0,894 | 0,827 | 0,918 | 0,99 · 0,98 | 1,51 | melhor média |
| `oldpeak_zero` | 0,495 | 0,516 | 0,391 | 0,852 | 0,876 | 0,822 | 0,914 | 0,98 · 0,98 | 1,43 | empatada |
| `oldpeak_abs` | 0,495 | 0,516 | 0,391 | 0,852 | 0,876 | 0,822 | 0,914 | 0,98 · 0,98 | 1,43 | empatada |

Todas as opções passam pelas travas: a maior concentração de uma categoria num grupo
é 40% (ChestPainType = ATA), e o lift do colesterol ausente vai de 1,41 a 1,51.

**Comparação pareada por bootstrap** (outra − `mediana`; pacientes fora da reamostra):

| Opção | Δ ARI registrado | IC 95% | Δ ARI total | IC 95% |
|---|---|---|---|---|
| `mediana_flag` | −0,000 | [−0,024; +0,021] | **+0,024** | [−0,008; +0,056] |
| `sem_colesterol` | −0,001 | [−0,027; +0,021] | −0,002 | [−0,025; +0,017] |
| `sem_colesterol_fastingbs` | +0,001 | [−0,031; +0,037] | −0,013 | [−0,055; +0,021] |
| `oldpeak_zero` | −0,001 | [−0,011; +0,010] | −0,000 | [−0,009; +0,013] |
| `oldpeak_abs` | −0,001 | [−0,011; +0,011] | −0,001 | [−0,017; +0,013] |

Todos os intervalos contêm zero. As seis opções empatam no critério, e vence a
primeira da lista, `mediana`.

**O que acontece com os 172 pacientes de colesterol ausente** (ajuste na base inteira):

| Opção | Ausentes no grupo "doente" | Acurácia nos ausentes | Acurácia nos registrados | Pacientes que mudam de grupo (vs. `mediana`) |
|---|---|---|---|---|
| `mediana` | 81,4% | 82,6% | 85,9% | — |
| `sem_colesterol` | 81,4% | 82,6% | 86,2% | 2 (nenhum ausente) |
| `sem_colesterol_fastingbs` | 77,9% | 79,1% | 86,2% | 16 (8 ausentes) |
| `mediana_flag` | **86,6%** | **86,6%** | 86,3% | 12 (**9 ausentes**) |
| `oldpeak_zero` / `oldpeak_abs` | 80,8% | 82,0% | 85,9% | 1 (1 ausente) |

## Achados

1. **Nenhum tratamento dos dados melhora a concordância com o diagnóstico.** No
   critério da rodada, as seis opções ficam entre 0,516 e 0,527, e todas as diferenças
   pareadas têm IC contendo zero. Vence a mais simples, `mediana`, que já era o
   tratamento da base. O ARI de referência continua 0,498 (0,516 registrado).
2. **A flag de colesterol ausente só ganha por causa do atalho.** A `mediana_flag` tem
   o maior ARI total (0,529; +0,024 no bootstrap, maior que a `mediana` em 89% das
   reamostras), mas ganho nenhum no ARI registrado (−0,000 [−0,024; +0,021]). O ganho
   inteiro vem dos ausentes: a flag leva 9 deles para o grupo "doente" (de 81,4% para
   86,6%), enquanto a acurácia nos registrados quase não muda (85,9% → 86,3%). É o
   atalho funcionando: a coluna diz "exame não feito", e quase todos os pacientes sem
   o exame são doentes. A flag também tem o maior lift de ausentes (1,51).
3. **O critério escolhido para a rodada funcionou como planejado.** Pelo ARI total, a
   `mediana_flag` teria a melhor média. Pelo ARI registrado, ela empata com as demais.
   Sem esse critério, o pipeline poderia ter adotado uma variável que reproduz um
   artefato da coleta.
4. **O colesterol não contribui para os grupos.** Remover a coluna (`sem_colesterol`)
   muda o grupo de só 2 pacientes e deixa o ARI praticamente igual (0,504 contra
   0,498). Sob `standard_all`, o colesterol é 1 de 18 colunas, e os grupos são
   definidos sobretudo por ST_Slope, angina no esforço e tipo de dor torácica (R1).
5. **A FastingBS ajuda um pouco a classificar os ausentes.** Removê-la junto com o
   colesterol muda o grupo de 16 pacientes, metade deles ausentes. A acurácia nos
   ausentes cai de 82,6% para 79,1%, e o ARI total fica 0,013 abaixo (IC contém
   zero). Nos registrados, nada muda.
6. **O Oldpeak negativo é irrelevante.** São 13 pacientes. Zerá-los ou usar o valor
   absoluto muda o grupo de 1 paciente, com diferenças de ARI de ±0,001.
7. **Todas as opções são estáveis.** Jaccard de 0,98–0,99 em todos os grupos;
   estabilidade entre sementes de 0,998 a 1,000.

## Implicações para as próximas rodadas

- **Nada muda nos arquivos.** O `vencedor.yaml` (`mediana`, `standard_all`, k = 2) é
  herdado pela R3.
- **Antes de rodar a R3, decidir a pendência da trava de categoria rara**
  (`decisao.trava_categoria.prevalencia_max`, hoje 20%; ver anotacoes_artigo.md,
  "Sensibilidade"). É a R3 que escolhe o k, e o resultado depende desse limite:
  - com **20%**, todos os k ≥ 3 são eliminados e a R3 escolhe k = 2;
  - com **15% ou 10%**, categorias com 19% da base (RestingECG = ST, ChestPainType =
    ATA) passam a formar grupos próprios e a R3 escolhe k = 4.

  Se o grupo mantiver 20%, a R3 pode ser rodada sem mudanças. Se preferir declarar
  k = 2 como hipótese principal, a R3 passa a ser descritiva.
- **Para a discussão do artigo:** o atalho do colesterol está contido. Nenhuma das
  configurações candidatas usa a ausência do exame como informação.

## Para o texto do artigo

> O colesterol registrado como zero (172 pacientes, 18,7%) corresponde a um exame não
> realizado e está fortemente associado ao diagnóstico: 88,4% desses pacientes são
> doentes, contra 47,7% entre os demais. Para que essa associação, provavelmente
> ligada à origem dos dados, não guiasse as escolhas, os tratamentos foram comparados
> pelo ARI calculado apenas nos 746 pacientes com colesterol registrado. Seis
> alternativas foram avaliadas: imputação pela mediana, remoção da variável, remoção
> também da glicemia de jejum, imputação com indicador de ausência e dois tratamentos
> do Oldpeak negativo. Nenhuma diferiu da imputação pela mediana (todas as diferenças
> pareadas com IC 95% contendo zero), que foi mantida. O indicador de ausência elevou o
> ARI na base inteira (0,529 contra 0,498), mas não nos pacientes com colesterol
> registrado (diferença de −0,000; IC 95% de −0,024 a +0,021): o ganho veio apenas de
> deslocar pacientes sem o exame para o grupo de doentes, o que caracteriza o uso do
> atalho, e não uma melhora do agrupamento.

## Cuidados

- **Não afirmar que o colesterol é irrelevante para a doença cardíaca.** O achado 4 diz
  que ele não contribui *para estes grupos*, sob este escalonamento. Isso não é uma
  afirmação clínica.
- **A origem dos zeros não está confirmada.** "Provavelmente o hospital de origem" é
  uma hipótese (pela documentação da UCI, a maior parte viria do subconjunto da
  Suíça). Conferir na documentação da base antes de afirmar no artigo.
- **Empate não é equivalência.** Os ICs contêm zero, mas têm largura de ±0,02 a ±0,04:
  diferenças desse tamanho não podem ser descartadas. O texto deve dizer "nenhuma
  diferença detectada", e não "os tratamentos são iguais".
- **Os 172 ausentes continuam na base.** A imputação pela mediana não remove o atalho
  da avaliação final. O ARI total (0,498) ainda inclui esses pacientes; relatar
  também o ARI registrado (0,516) ao lado.
- **A tabela dos ausentes vem de um único ajuste na base inteira** (semente 0), não do
  bootstrap. Ela explica o mecanismo; a significância vem da tabela pareada.

## Arquivos de origem

- `results/r02_dados/decisao.md`: tabela da rodada e regra aplicada
- `results/r02_dados/resumo.csv`: médias, desvios, travas e IC por opção
- `results/r02_dados/por_semente.csv`: uma linha por opção × semente
- `results/r02_dados/bootstrap.csv`: ARI, ARI registrado, silhueta e Jaccard fora da reamostra (100 reamostras pareadas)
- `results/r02_dados/vencedor.yaml`: configuração herdada pela R3
- `configs/r02_dados.yaml`: definição da rodada
- Comparações com o ARI total no bootstrap e a tabela dos 172 ausentes: calculadas à
  parte com o pipeline do projeto; não há arquivo em `results/`
