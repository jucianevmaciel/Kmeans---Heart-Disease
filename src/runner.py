"""Roda uma rodada: cada opção do YAML x cada semente, na base inteira (918 pacientes).

Uso:
    python -m src.runner configs/r01_escalonamento.yaml
    python -m src.runner configs/r01_escalonamento.yaml --sementes 3   # teste rápido

Saídas em results/<rodada>/:
    por_semente.csv   uma linha por opção x semente
    resumo.csv        média, desvio e estabilidade por opção
    decisao.md        aplicação da regra de decisão (src/compare.py)
    vencedor.yaml     configuração vencedora (herdada pela próxima rodada)
"""
import argparse
import time
import warnings

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.model_selection import StratifiedKFold, cross_val_predict

from . import compare, config, metricas
from .dados import carregar_base, separar
from .pipeline import construir, espaco, resumo_cfg, supervisionado

warnings.filterwarnings("ignore", category=UserWarning)

METRICAS = ["ari", "nmi", "pureza", "recall", "especificidade", "auc_escore",
            "silhueta", "davies_bouldin", "calinski_harabasz", "inercia", "atalho_colesterol", "menor_grupo"]


def avaliar_agrupamento(cfg, X, y, ausente, semente):
    pipe = construir(cfg, semente)
    pipe.fit(X, y)  # y só é usado pelo kbest (avisado no YAML da R4)
    Z = espaco(pipe, X)
    modelo = pipe.named_steps["modelo"]
    rot = modelo.labels_ if hasattr(modelo, "labels_") else modelo.predict(Z)
    rot = np.asarray(rot).astype(int)
    mapa = metricas.mapear(rot, y)
    lin = {**metricas.internas(Z, rot, modelo), **metricas.externas(rot, y, mapa),
           "auc_escore": metricas.auc(y, metricas.escore_risco(modelo, Z, mapa)),
           "atalho_colesterol": metricas.atalho_colesterol(rot, ausente),
           "menor_grupo": metricas.menor_grupo(rot)}
    return lin, rot


def avaliar_supervisionado(cfg, X, y, ausente, semente):
    """Referências da R0: previsões fora da dobra (validação cruzada 5 dobras)."""
    pipe = construir(cfg, semente)
    cv = StratifiedKFold(5, shuffle=True, random_state=semente)
    proba = cross_val_predict(clone(pipe), X, y, cv=cv, method="predict_proba")[:, 1]
    pred = (proba >= 0.5).astype(int)
    lin = {**metricas.externas(pred, y, {0: 0, 1: 1}), "auc_escore": metricas.auc(y, proba),
           "atalho_colesterol": metricas.atalho_colesterol(pred, ausente) if len(np.unique(pred)) > 1 else np.nan,
           "menor_grupo": metricas.menor_grupo(pred) if len(np.unique(pred)) > 1 else np.nan}
    return lin, pred


def executar(arq_yaml, n_sementes=None):
    rod, opcoes = config.carregar_rodada(arq_yaml)
    pasta = config.pasta_rodada(arq_yaml)
    pasta.mkdir(parents=True, exist_ok=True)
    n = n_sementes or rod["_partida"].get("sementes", 20)
    X, y, ausente, _ = separar(carregar_base())

    print(f"{rod.get('rodada', '?')}: {rod.get('pergunta', '')}")
    print(f"  {len(opcoes)} opções x {n} sementes, {len(X)} pacientes")
    linhas, rotulos = [], {}
    t0 = time.time()
    for op in opcoes:
        sup = op["meta"]["supervisionado"] or supervisionado(op["cfg"])
        for s in range(n):
            f = avaliar_supervisionado if sup else avaliar_agrupamento
            lin, rot = f(op["cfg"], X, y, ausente, s)
            linhas.append({"opcao": op["nome"], "semente": s, **lin})
            rotulos.setdefault(op["nome"], []).append(rot)
        print(f"  - {op['nome']:<40} ARI={np.nanmean([l['ari'] for l in linhas if l['opcao'] == op['nome']]):.3f}")

    df = pd.DataFrame(linhas)
    df.to_csv(pasta / "por_semente.csv", index=False)

    resumo = []
    for op in opcoes:
        d = df[df["opcao"] == op["nome"]]
        r = {"opcao": op["nome"], **resumo_cfg(op["cfg"]),
             "supervisionado": op["meta"]["supervisionado"] or supervisionado(op["cfg"]),
             "fora_da_disputa": op["meta"]["fora_da_disputa"]}
        for m in METRICAS:
            if m in d:
                r[f"{m}_media"] = d[m].mean()
                r[f"{m}_dp"] = d[m].std(ddof=1) if len(d) > 1 else 0.0
        r["estabilidade"] = metricas.estabilidade(rotulos[op["nome"]])
        resumo.append(r)
    resumo = pd.DataFrame(resumo)
    resumo.to_csv(pasta / "resumo.csv", index=False)

    compare.decidir(rod, opcoes, resumo, pasta)
    print(f"  pronto em {time.time() - t0:.0f}s -> {pasta.relative_to(config.RAIZ)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("yaml")
    ap.add_argument("--sementes", type=int, default=None, help="sobrescreve o número de sementes (teste rápido)")
    a = ap.parse_args()
    executar(config.caminho(a.yaml), a.sementes)


if __name__ == "__main__":
    main()
