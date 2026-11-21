"""R6: perfil clínico dos grupos da configuração final (base inteira).

Uso:  python -m src.perfil_grupos [--config final]

Saídas em results/r06_perfil/:
    perfil_grupos.csv          médias (escala original), % de cada categoria, % de doentes
                               e % de colesterol ausente por grupo
    arvore_substituta.txt      árvore rasa que prevê o grupo a partir das variáveis originais
    discordantes.csv           doentes no grupo "saudável" e saudáveis no grupo "doente"
    discordantes_resumo.csv    médias dos discordantes x concordantes, por diagnóstico
    cruzamento_svm.md          (se erros_svm estiver no YAML) sobreposição com os erros do SVM
    silhueta_por_paciente.png  gráfico de silhueta por grupo
"""
import argparse

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import silhouette_samples
from sklearn.tree import DecisionTreeClassifier, export_text

from . import config, metricas
from .dados import ALVO, BINARIAS, CATEGORICAS, COLUNAS, NUMERICAS, carregar_base, separar
from .pipeline import ajustar

PASTA = config.RESULTADOS / "r06_perfil"


def bruto(df):
    """Variáveis na escala original, com os zeros impossíveis como ausentes."""
    b = df[COLUNAS].copy()
    b["Cholesterol"] = b["Cholesterol"].replace(0, np.nan)
    b["RestingBP"] = b["RestingBP"].replace(0, np.nan)
    return b


def perfil(df, rot, ausente):
    b = bruto(df)
    grupos = {f"grupo {g}": rot == g for g in np.unique(rot)}
    grupos["todos"] = np.ones(len(df), bool)
    linhas = {}
    for nome, m in grupos.items():
        c = {"n pacientes": m.sum(), "% dos pacientes": 100 * m.mean(),
             "% doentes": 100 * df.loc[m, ALVO].mean(), "% colesterol ausente": 100 * ausente[m].mean()}
        for v in NUMERICAS:
            c[f"{v} (média)"] = b.loc[m, v].mean()
        for v in BINARIAS:
            c[f"{v} = 1 (%)"] = 100 * b.loc[m, v].mean()
        for v in CATEGORICAS:
            for cat in sorted(b[v].unique()):
                c[f"{v} = {cat} (%)"] = 100 * (b.loc[m, v] == cat).mean()
        linhas[nome] = c
    return pd.DataFrame(linhas).round(2)


def arvore(df, rot, prof):
    Xa = pd.get_dummies(bruto(df), columns=CATEGORICAS, dtype=int)
    t = DecisionTreeClassifier(max_depth=prof, random_state=0).fit(Xa, rot)
    fid = (t.predict(Xa) == rot).mean()
    txt = export_text(t, feature_names=list(Xa.columns), class_names=[f"grupo {g}" for g in t.classes_])
    return f"Fidelidade (acerto da árvore ao prever o grupo): {fid:.1%}\n\n{txt}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="final")
    a = ap.parse_args()
    cfg = config.config_final(a.config)
    params = config.ler_yaml("configs/r06_perfil.yaml")
    PASTA.mkdir(parents=True, exist_ok=True)

    base = carregar_base()
    X, y, ausente, ids = separar(base)
    pipe, Z, rot = ajustar(cfg, X, y, semente=0)
    mapa = metricas.mapear(rot, y)

    p = perfil(base, rot, ausente)
    p.to_csv(PASTA / "perfil_grupos.csv")
    (PASTA / "arvore_substituta.txt").write_text(arvore(base, rot, params.get("profundidade_arvore", 3)),
                                                 encoding="utf-8")

    classe_grupo = np.array([mapa[int(g)] for g in rot])
    disc = base.assign(grupo=rot, classe_do_grupo=classe_grupo)
    disc = disc[disc["classe_do_grupo"] != disc[ALVO]]
    disc.to_csv(PASTA / "discordantes.csv", index=False)

    b = bruto(base).assign(diagnostico=y, discordante=classe_grupo != y)
    num = NUMERICAS + BINARIAS
    res = b.groupby(["diagnostico", "discordante"])[num].mean().round(2)
    res.insert(0, "n", b.groupby(["diagnostico", "discordante"]).size())
    res.to_csv(PASTA / "discordantes_resumo.csv")

    if params.get("erros_svm"):
        err = set(pd.read_csv(config.caminho(params["erros_svm"]))["id"])
        no_treino = np.isin(ids, list(err))
        d = classe_grupo != y
        txt = [f"Erros do SVM encontrados na base: {no_treino.sum()}",
               f"% discordantes entre os erros do SVM: {100 * d[no_treino].mean():.1f}%",
               f"% discordantes entre os acertos do SVM: {100 * d[~no_treino].mean():.1f}%",
               "Se a primeira for bem maior, os erros do SVM são casos que se parecem com o outro grupo."]
        (PASTA / "cruzamento_svm.md").write_text("\n\n".join(txt) + "\n", encoding="utf-8")

    if len(np.unique(rot)) > 1:
        s = silhouette_samples(Z, rot)
        fig, ax = plt.subplots(figsize=(7, 5))
        y0 = 0
        for g in np.unique(rot):
            sg = np.sort(s[rot == g])
            ax.fill_betweenx(np.arange(y0, y0 + len(sg)), 0, sg, alpha=0.7, label=f"grupo {g}")
            y0 += len(sg) + 10
        ax.axvline(s.mean(), ls="--", c="k", lw=1, label=f"média = {s.mean():.2f}")
        ax.set_xlabel("silhueta")
        ax.set_yticks([])
        ax.set_title(f"Silhueta por paciente ({(s < 0).mean():.1%} com valor negativo)")
        ax.legend()
        fig.tight_layout()
        fig.savefig(PASTA / "silhueta_por_paciente.png", dpi=150)

    print(p.loc[["n pacientes", "% doentes", "% colesterol ausente"]].to_string())
    print(f"discordantes: {len(disc)} de {len(base)}  ->  {PASTA.relative_to(config.RAIZ)}")


if __name__ == "__main__":
    main()
