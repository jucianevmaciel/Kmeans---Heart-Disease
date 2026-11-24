"""Roda uma rodada: cada opção do YAML x cada semente, na base inteira (918 pacientes),
mais o bootstrap pareado usado na regra de decisão.

Uso:
    python -m src.runner configs/r01_escalonamento.yaml
    python -m src.runner configs/r01_escalonamento.yaml --sementes 3 --bootstrap 20   # teste rápido

Saídas em results/<rodada>/:
    por_semente.csv   uma linha por opção x semente (ajuste na base inteira)
    bootstrap.csv     uma linha por opção x reamostra: métricas nos pacientes fora da
                      reamostra e Jaccard de cada grupo (as mesmas reamostras em todas
                      as opções, para comparar de forma pareada)
    resumo.csv        média, desvio, estabilidade e travas por opção
    decisao.md        aplicação da regra de decisão (src/compare.py)
    vencedor.yaml     configuração vencedora (só 'pre' e 'modelo'; herdada pela próxima rodada)

Atenção: um teste rápido também grava vencedor.yaml. Rode de novo sem as opções antes
de seguir para a próxima rodada.
"""
import argparse
import time
import warnings

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict

from . import compare, config, metricas
from .dados import carregar_base, separar
from .pipeline import construir, espaco, resumo_cfg, supervisionado

warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

METRICAS = ["ari", "ari_registrado", "nmi", "pureza", "recall", "especificidade", "auc_escore",
            "silhueta", "davies_bouldin", "calinski_harabasz", "inercia",
            "atalho_colesterol", "atalho_lift", "categoria_rara", "menor_grupo"]
METRICAS_BOOT = ["ari", "ari_registrado", "silhueta"]


def avaliar_agrupamento(cfg, X, y, ausente, semente, trava_cat):
    pipe = construir(cfg, semente)
    pipe.fit(X, y)  # y só é usado pelo kbest (avisado no YAML da R4)
    Z = espaco(pipe, X)
    modelo = pipe.named_steps["modelo"]
    rot = modelo.labels_ if hasattr(modelo, "labels_") else modelo.predict(Z)
    rot = np.asarray(rot).astype(int)
    mapa = metricas.mapear(rot, y)
    cat, desc = metricas.categoria_rara(rot, X, ausente, **trava_cat)
    lin = {**metricas.internas(Z, rot, modelo), **metricas.externas(rot, y, mapa),
           "ari_registrado": metricas.ari_registrado(rot, y, ausente),
           "auc_escore": metricas.auc(y, metricas.escore_risco(modelo, Z, mapa)),
           "atalho_colesterol": metricas.atalho_colesterol(rot, ausente),
           "atalho_lift": metricas.atalho_lift(rot, ausente),
           "categoria_rara": float(cat), "categoria_rara_desc": desc,
           "menor_grupo": metricas.menor_grupo(rot)}
    return lin, rot, Z


def avaliar_supervisionado(cfg, X, y, ausente, semente, trava_cat):
    """Referências da R0: previsões fora da dobra (validação cruzada 5 dobras)."""
    pipe = construir(cfg, semente)
    cv = StratifiedKFold(5, shuffle=True, random_state=semente)
    proba = cross_val_predict(clone(pipe), X, y, cv=cv, method="predict_proba")[:, 1]
    pred = (proba >= 0.5).astype(int)
    dois = len(np.unique(pred)) > 1
    lin = {**metricas.externas(pred, y, {0: 0, 1: 1}), "auc_escore": metricas.auc(y, proba),
           "ari_registrado": metricas.ari_registrado(pred, y, ausente),
           "atalho_colesterol": metricas.atalho_colesterol(pred, ausente) if dois else np.nan,
           "atalho_lift": metricas.atalho_lift(pred, ausente) if dois else np.nan,
           "menor_grupo": metricas.menor_grupo(pred) if dois else np.nan}
    return lin, pred, None


def reamostras(n, B, semente):
    """Índices das B reamostras bootstrap (os mesmos para todas as opções = pareado)."""
    rng = np.random.default_rng(semente)
    return [rng.integers(0, n, n) for _ in range(B)]


def bootstrap_opcao(nome, cfg, X, y, ausente, ref, idxs):
    """Reajusta a opção em cada reamostra; avalia nos pacientes fora dela e mede o
    Jaccard de cada grupo de referência (ajuste na base inteira, semente 0)."""
    n = len(X)
    linhas = []
    for b, idx in enumerate(idxs):
        pipe = construir(cfg, b)
        pipe.fit(X.iloc[idx], y[idx])
        Z = espaco(pipe, X)
        rot = np.asarray(pipe.named_steps["modelo"].predict(Z)).astype(int)
        fora = np.setdiff1d(np.arange(n), idx)
        reg = fora[ausente[fora] == 0]
        sil = silhouette_score(Z[fora], rot[fora]) if len(np.unique(rot[fora])) > 1 else np.nan
        jac = metricas.jaccard_grupos(ref, rot, np.unique(idx))
        lin = {"opcao": nome, "reamostra": b,
               "ari": adjusted_rand_score(y[fora], rot[fora]),
               "ari_registrado": adjusted_rand_score(y[reg], rot[reg]),
               "silhueta": sil}
        lin.update({f"jaccard_g{g}": j for g, j in enumerate(jac)})
        linhas.append(lin)
    return linhas


def executar(arq_yaml, n_sementes=None, n_boot=None):
    rod, opcoes = config.carregar_rodada(arq_yaml)
    pasta = config.pasta_rodada(arq_yaml)
    pasta.mkdir(parents=True, exist_ok=True)
    partida = rod["_partida"]
    dec = partida.get("decisao", {})
    n = n_sementes or partida.get("sementes", 20)
    B = n_boot if n_boot is not None else dec.get("bootstrap", 100)
    trava_cat = dec.get("trava_categoria", {"concentracao": 0.90, "prevalencia_max": 0.20})
    X, y, ausente, _ = separar(carregar_base())
    idxs = reamostras(len(X), B, dec.get("semente_bootstrap", 0))

    print(f"{rod.get('rodada', '?')}: {rod.get('pergunta', '')}")
    print(f"  {len(opcoes)} opções x {n} sementes + {B} reamostras bootstrap, {len(X)} pacientes")
    linhas, rotulos, boot, extra = [], {}, [], {}
    t0 = time.time()
    for op in opcoes:
        sup = op["meta"]["supervisionado"] or supervisionado(op["cfg"])
        f = avaliar_supervisionado if sup else avaliar_agrupamento
        Z0 = None
        for s in range(n):
            lin, rot, Z = f(op["cfg"], X, y, ausente, s, trava_cat)
            linhas.append({"opcao": op["nome"], "semente": s, **lin})
            rotulos.setdefault(op["nome"], []).append(rot)
            if s == 0:
                Z0 = Z
        ex = {}
        if not sup:
            ref = rotulos[op["nome"]][0]
            boot += bootstrap_opcao(op["nome"], op["cfg"], X, y, ausente, ref, idxs)
            k = len(np.unique(ref))
            ex["silhueta_nula"] = metricas.silhueta_nula(Z0, k, dec.get("permutacoes_nula", 10)) if k > 1 else np.nan
            ex["categoria_rara_desc"] = linhas[-n]["categoria_rara_desc"]
        extra[op["nome"]] = ex
        ari_m = np.nanmean([l["ari"] for l in linhas if l["opcao"] == op["nome"]])
        print(f"  - {op['nome']:<40} ARI={ari_m:.3f}")

    df = pd.DataFrame(linhas)
    df.to_csv(pasta / "por_semente.csv", index=False)
    boot = pd.DataFrame(boot)
    boot.to_csv(pasta / "bootstrap.csv", index=False)

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
        r["estabilidade_sementes"] = metricas.estabilidade(rotulos[op["nome"]])
        r.update(extra[op["nome"]])
        if "silhueta_nula" in r:
            r["silhueta_excesso"] = r.get("silhueta_media", np.nan) - r["silhueta_nula"]
        db = boot[boot["opcao"] == op["nome"]] if len(boot) else boot
        if len(db):
            jac = db.filter(like="jaccard_g").mean()
            r["jaccard_min"] = jac.min()
            r["jaccard_grupos"] = " ".join(f"{v:.2f}" for v in jac.dropna())
            for m in METRICAS_BOOT:
                r[f"{m}_boot_dp"] = db[m].std(ddof=1)
        resumo.append(r)
    resumo = pd.DataFrame(resumo)
    resumo.to_csv(pasta / "resumo.csv", index=False)

    compare.decidir(rod, opcoes, resumo, boot, pasta)
    print(f"  pronto em {time.time() - t0:.0f}s -> {pasta.relative_to(config.RAIZ)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("yaml")
    ap.add_argument("--sementes", type=int, default=None, help="sobrescreve o número de sementes (teste rápido)")
    ap.add_argument("--bootstrap", type=int, default=None, help="sobrescreve o número de reamostras (teste rápido)")
    a = ap.parse_args()
    executar(config.caminho(a.yaml), a.sementes, a.bootstrap)


if __name__ == "__main__":
    main()
