"""R6: grupos em 2D (PCA do espaço do agrupamento), com o diagnóstico real.

Uso:  python -m src.clusters_2d [--config final]
Saída: results/r06_perfil/clusters_2d.png
       (com --config configs/<alt>.yaml: results/<alt>/r06_perfil/clusters_2d.png)

O PCA aqui é só para desenhar; o agrupamento foi feito no espaço completo.
"""
import argparse

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.decomposition import PCA

from . import config
from .dados import carregar_base, separar
from .pipeline import ajustar, centroides


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="final",
                    help="final (vencedor da R5b) ou um YAML, ex.: configs/alternativa_k4.yaml")
    ap.add_argument("--saida", default=None,
                    help="pasta raiz das saídas (padrão: results/, ou results/<yaml>/ com --config <yaml>)")
    a = ap.parse_args()
    cfg = config.config_final(a.config)
    pasta = config.pasta_analise(a.config, "r06_perfil", a.saida)

    X, y, _, _ = separar(carregar_base())
    pipe, Z, rot = ajustar(cfg, X, y, semente=0)
    pca = PCA(2, random_state=0).fit(Z)
    P = pca.transform(Z)
    C = centroides(pipe.named_steps["modelo"])

    fig, ax = plt.subplots(figsize=(8, 6))
    cores = plt.cm.tab10.colors
    for g in np.unique(rot):
        for diag, marca, nome in [(0, "o", "saudável"), (1, "^", "doente")]:
            m = (rot == g) & (y == diag)
            ax.scatter(P[m, 0], P[m, 1], s=18, marker=marca, color=cores[g % 10], alpha=0.6,
                       edgecolor="none", label=f"grupo {g} · {nome}")
    if C is not None:
        Cp = pca.transform(C)
        ax.scatter(Cp[:, 0], Cp[:, 1], s=220, marker="X", c="k", label="centróides")
    v = pca.explained_variance_ratio_
    ax.set_xlabel(f"PC1 ({v[0]:.0%} da variância)")
    ax.set_ylabel(f"PC2 ({v[1]:.0%} da variância)")
    ax.set_title("Grupos do K-Means (cor) e diagnóstico real (forma)")
    ax.legend(fontsize=8, ncol=2)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(pasta / "clusters_2d.png", dpi=150)
    print(f"salvo: {pasta / 'clusters_2d.png'}")


if __name__ == "__main__":
    main()
