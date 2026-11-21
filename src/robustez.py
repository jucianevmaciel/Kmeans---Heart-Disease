"""R7: estabilidade da configuração final (base inteira).

Uso:  python -m src.robustez [--config final]

Saídas em results/r07_robustez/:
    sementes.csv    ARI entre pares de sementes (os grupos se repetem?)
    bootstrap.csv   ARI entre o agrupamento de referência e o de cada reamostragem,
                    em todos os pacientes e só nos que ficaram de fora da reamostragem
    subgrupos.csv   ARI com o diagnóstico e distribuição dos grupos por subgrupo
    resumo.md
"""
import argparse
import itertools

import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score

from . import config, metricas
from .dados import carregar_base, separar
from .pipeline import ajustar, construir

PASTA = config.RESULTADOS / "r07_robustez"


def _tabela(df):
    try:
        return df.to_markdown(index=False)
    except ImportError:  # pacote tabulate ausente
        return df.to_string(index=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="final")
    ap.add_argument("--bootstrap", type=int, default=None)
    a = ap.parse_args()
    cfg = config.config_final(a.config)
    params = config.ler_yaml("configs/r07_robustez.yaml")
    B = a.bootstrap or params.get("bootstrap", 100)
    n = cfg.get("sementes", 20)
    PASTA.mkdir(parents=True, exist_ok=True)

    base = carregar_base()
    X, y, ausente, _ = separar(base)

    rot_s = [ajustar(cfg, X, y, s)[2] for s in range(n)]
    pares = pd.DataFrame([{"semente_a": i, "semente_b": j, "ari": adjusted_rand_score(rot_s[i], rot_s[j])}
                          for i, j in itertools.combinations(range(n), 2)])
    pares.to_csv(PASTA / "sementes.csv", index=False)

    ref = rot_s[0]
    rng = np.random.default_rng(0)
    boot = []
    for b in range(B):
        idx = rng.integers(0, len(X), len(X))
        pipe = construir(cfg, b)
        pipe.fit(X.iloc[idx], y[idx])
        rot_b = pipe.predict(X)
        fora = np.setdiff1d(np.arange(len(X)), idx)  # ~1/3 dos pacientes, não usados no ajuste
        boot.append({"reamostragem": b, "ari_com_referencia": adjusted_rand_score(ref, rot_b),
                     "ari_com_referencia_fora": adjusted_rand_score(ref[fora], rot_b[fora]),
                     "ari_com_diagnostico": adjusted_rand_score(y, rot_b),
                     "ari_com_diagnostico_fora": adjusted_rand_score(y[fora], rot_b[fora])})
    boot = pd.DataFrame(boot)
    boot.to_csv(PASTA / "bootstrap.csv", index=False)

    sub = []
    variaveis = {"Sex": base["Sex"].to_numpy(), "colesterol_ausente": ausente}
    for v in params.get("subgrupos", list(variaveis)):
        valores = variaveis[v] if v in variaveis else base[v].to_numpy()
        for val in np.unique(valores):
            m = valores == val
            lin = {"variavel": v, "valor": val, "n": int(m.sum()), "% doentes": 100 * y[m].mean(),
                   "ari_com_diagnostico": adjusted_rand_score(y[m], ref[m]) if m.sum() > 1 else np.nan,
                   "pureza": metricas.externas(ref[m], y[m], metricas.mapear(ref, y))["pureza"]}
            for g in np.unique(ref):
                lin[f"% no grupo {g}"] = 100 * (ref[m] == g).mean()
            sub.append(lin)
    sub = pd.DataFrame(sub).round(3)
    sub.to_csv(PASTA / "subgrupos.csv", index=False)

    txt = ["# R7: robustez da configuração final", "",
           f"- Sementes ({n}): ARI médio entre pares = {pares['ari'].mean():.3f} "
           f"(mín. {pares['ari'].min():.3f})",
           f"- Bootstrap ({B}), pacientes fora da reamostragem: ARI com a referência = "
           f"{boot['ari_com_referencia_fora'].mean():.3f} ± {boot['ari_com_referencia_fora'].std():.3f}",
           f"- Bootstrap ({B}), todos os pacientes: ARI com a referência = {boot['ari_com_referencia'].mean():.3f} "
           f"± {boot['ari_com_referencia'].std():.3f}; ARI com o diagnóstico = "
           f"{boot['ari_com_diagnostico'].mean():.3f} ± {boot['ari_com_diagnostico'].std():.3f}",
           "", "## Subgrupos", "", _tabela(sub)]
    (PASTA / "resumo.md").write_text("\n".join(txt) + "\n", encoding="utf-8")
    print("\n".join(txt[:5]))


if __name__ == "__main__":
    main()
