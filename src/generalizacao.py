"""R8: a avaliação sem divisão é otimista?

Uso:  python -m src.generalizacao [--config final]

Compara a configuração final avaliada nos próprios pacientes ("dentro") com a
avaliação em pacientes que ficaram de fora do ajuste ("fora"), por validação
cruzada estratificada 5x5 com semente 42 (o mesmo protocolo do SVM-Infarto).
Em cada dobra, o K-Means é ajustado em 4/5 da base, o mapeamento grupo -> classe
vem desses 4/5, e o 1/5 restante vai para o centróide mais próximo (predict).

As referências supervisionadas (regressão logística e gradient boosting) rodam
nas mesmas dobras, então a AUC "fora" do K-Means é comparável com a delas e com
a AUC da validação cruzada do SVM.

Limitação (registrar na metodologia): os pacientes "fora" participaram das
escolhas das rodadas R1–R5b. A R8 mede o otimismo do ajuste, não o da seleção.

Saídas em results/r08_generalizacao/: por_dobra.csv, resumo.csv, resumo.md
(com --config configs/<alt>.yaml: results/<alt>/r08_generalizacao/)
"""
import argparse
import copy

import numpy as np
import pandas as pd
from sklearn.model_selection import RepeatedStratifiedKFold

from . import config, metricas
from .dados import carregar_base, separar
from .pipeline import ajustar, construir, espaco

METRICAS = ["ari", "pureza", "recall", "especificidade", "auc_escore"]
NOMES = {"ari": "ARI", "pureza": "Acurácia (pureza)", "recall": "Recall", "especificidade": "Especificidade",
         "auc_escore": "AUC do escore"}


def _tabela(df):
    try:
        return df.to_markdown()
    except ImportError:
        return df.to_string()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="final",
                    help="final (vencedor da R5b) ou um YAML, ex.: configs/alternativa_k4.yaml")
    ap.add_argument("--saida", default=None,
                    help="pasta raiz das saídas (padrão: results/, ou results/<yaml>/ com --config <yaml>)")
    a = ap.parse_args()
    PASTA = config.pasta_analise(a.config, "r08_generalizacao", a.saida)
    cfg = config.config_final(a.config)
    params = config.ler_yaml("configs/r08_generalizacao.yaml")

    X, y, _, _ = separar(carregar_base())
    cv = RepeatedStratifiedKFold(n_splits=params.get("dobras", 5), n_repeats=params.get("repeticoes", 5),
                                 random_state=params.get("semente_cv", 42))

    linhas = []
    for i, (tr, te) in enumerate(cv.split(X, y)):
        pipe, _, rot_tr = ajustar(cfg, X.iloc[tr], y[tr], semente=i)
        mapa = metricas.mapear(rot_tr, y[tr])
        Zte = espaco(pipe, X.iloc[te])
        modelo = pipe.named_steps["modelo"]
        rot_te = np.asarray(modelo.predict(Zte)).astype(int)
        linhas.append({"modelo": "kmeans_final", "dobra": i, **metricas.externas(rot_te, y[te], mapa),
                       "auc_escore": metricas.auc(y[te], metricas.escore_risco(modelo, Zte, mapa))})
        for ref in params.get("referencias", ["logreg", "gboost"]):
            c = copy.deepcopy(config.base())
            c["modelo"] = {"algoritmo": ref}
            proba = construir(c, i).fit(X.iloc[tr], y[tr]).predict_proba(X.iloc[te])[:, 1]
            pred = (proba >= 0.5).astype(int)
            linhas.append({"modelo": ref, "dobra": i, **metricas.externas(pred, y[te], {0: 0, 1: 1}),
                           "auc_escore": metricas.auc(y[te], proba)})
    dobras = pd.DataFrame(linhas)
    dobras.to_csv(PASTA / "por_dobra.csv", index=False)

    dentro = []
    for s in range(cfg.get("sementes", 20)):
        pipe, Z, rot = ajustar(cfg, X, y, semente=s)
        mapa = metricas.mapear(rot, y)
        dentro.append({**metricas.externas(rot, y, mapa),
                       "auc_escore": metricas.auc(y, metricas.escore_risco(pipe.named_steps["modelo"], Z, mapa))})
    dentro = pd.DataFrame(dentro)

    km = dobras[dobras["modelo"] == "kmeans_final"]
    comp = pd.DataFrame({
        "dentro (base inteira)": dentro[METRICAS].mean(),
        "fora (média das dobras)": km[METRICAS].mean(),
        "dp entre dobras": km[METRICAS].std(),
    })
    comp["otimismo (dentro − fora)"] = comp["dentro (base inteira)"] - comp["fora (média das dobras)"]
    comp = comp.rename(index=NOMES).round(3)

    refs = dobras.groupby("modelo", sort=False)[METRICAS].agg(["mean", "std"]).round(3)
    refs.columns = [f"{NOMES[m]} {'média' if e == 'mean' else 'dp'}" for m, e in refs.columns]
    resumo = pd.concat({"comparacao": comp}, names=["tabela"])
    resumo.to_csv(PASTA / "resumo.csv")
    refs.to_csv(PASTA / "referencias.csv")

    nome = "configuração final" if a.config in (None, "final") else a.config
    txt = [f"# R8: a avaliação sem divisão é otimista? ({nome})", "",
           f"Validação cruzada estratificada {params.get('dobras', 5)}x{params.get('repeticoes', 5)}, "
           f"semente {params.get('semente_cv', 42)} (mesmo protocolo do SVM-Infarto). "
           f"{len(X)} pacientes.", "",
           "## K-Means: dentro x fora da amostra", "", _tabela(comp), "",
           "## Mesmas dobras: K-Means x modelos supervisionados (avaliação fora da amostra)", "",
           _tabela(refs), "",
           "Os pacientes 'fora' participaram das escolhas das rodadas R1–R5b: a R8 mede o "
           "otimismo do ajuste, não o da seleção."]
    (PASTA / "resumo.md").write_text("\n".join(txt) + "\n", encoding="utf-8")
    print(comp.to_string())
    print()
    print(refs.to_string())


if __name__ == "__main__":
    main()
