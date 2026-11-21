"""Curvas de cada métrica por k (R3).

Uso:  python -m src.cotovelo                            (R3)
      python -m src.cotovelo --rodada r05b_reajuste_k    (R5b)
Saída: results/<rodada>/cotovelo.png
"""
import argparse

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from .config import RESULTADOS

PAINEIS = [("silhueta", "Silhueta (maior é melhor)"), ("davies_bouldin", "Davies-Bouldin (menor é melhor)"),
           ("calinski_harabasz", "Calinski-Harabasz (maior é melhor)"), ("inercia", "Inércia (cotovelo)"),
           ("ari", "ARI com o diagnóstico (só relatado)"), ("estabilidade", "Estabilidade entre sementes")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rodada", default="r03_k_inicializacao")
    a = ap.parse_args()
    pasta = RESULTADOS / a.rodada
    r = pd.read_csv(pasta / "resumo.csv")
    fig, eixos = plt.subplots(2, 3, figsize=(13, 7))
    for ax, (m, titulo) in zip(eixos.flat, PAINEIS):
        for init, d in r.groupby(r["init"].fillna("k-means++")):
            d = d.sort_values("k")
            if m == "estabilidade":
                ax.plot(d["k"], d[m], marker="o", label=init)
            else:
                ax.errorbar(d["k"], d[f"{m}_media"], yerr=d[f"{m}_dp"], marker="o", capsize=3, label=init)
        ax.set_title(titulo, fontsize=10)
        ax.set_xlabel("k")
        ax.grid(alpha=0.3)
    eixos.flat[0].legend(title="inicialização", fontsize=8)
    fig.tight_layout()
    fig.savefig(pasta / "cotovelo.png", dpi=150)
    print(f"salvo: {pasta / 'cotovelo.png'}")


if __name__ == "__main__":
    main()
