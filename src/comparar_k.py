"""Compara uma configuração alternativa (ex.: k = 4) com a configuração final (k = 2).

Uso:  python -m src.comparar_k --config configs/alternativa_k4.yaml [--referencia final] [--bootstrap 100]

As duas configurações são ajustadas na base inteira (semente 0) e avaliadas nas mesmas
reamostras bootstrap (comparação pareada). Também cruza os grupos: para onde vão os
pacientes de cada grupo do k = 2, e onde caem os discordantes do k = 2 (doentes no
grupo "saudável" e saudáveis no grupo "doente").

Saídas em results/<alt>/comparacao/:
    comparacao.md    tabelas de métricas, diferenças pareadas, perfil e cruzamento
    metricas.csv     métricas das duas configurações
    grupos.csv       perfil dos grupos da alternativa
    cruzamento.csv   grupos da referência x grupos da alternativa
"""
import argparse
import warnings

import numpy as np
import pandas as pd

from . import config, metricas
from .dados import CATEGORICAS, carregar_base, separar
from .runner import avaliar_agrupamento, bootstrap_opcao, reamostras

warnings.filterwarnings("ignore")

LINHAS = [("ari", "ARI"), ("ari_registrado", "ARI registrado"), ("nmi", "NMI"), ("pureza", "Acurácia (pureza)"),
          ("recall", "Recall"), ("especificidade", "Especificidade"), ("auc_escore", "AUC do escore"),
          ("silhueta", "Silhueta"), ("silhueta_nula", "Silhueta nula"), ("davies_bouldin", "Davies-Bouldin"),
          ("menor_grupo", "Menor grupo (fração)"), ("atalho_lift", "Lift do colesterol ausente"),
          ("jaccard_min", "Jaccard do grupo menos estável"), ("jaccard_grupos", "Jaccard por grupo"),
          ("ari_boot", "ARI fora da reamostra (média ± dp)"), ("categoria_rara_desc", "Maior concentração de categoria rara")]


def _tabela(df, index=True):
    try:
        return df.to_markdown(index=index)
    except ImportError:
        return df.to_string(index=index)


def avaliar(cfg, X, y, ausente, idxs, trava_cat, n_perm):
    lin, rot, Z = avaliar_agrupamento(cfg, X, y, ausente, 0, trava_cat)
    boot = pd.DataFrame(bootstrap_opcao("x", cfg, X, y, ausente, rot, idxs))
    jac = boot.filter(like="jaccard_g").mean()
    lin.update({"silhueta_nula": metricas.silhueta_nula(Z, len(np.unique(rot)), n_perm),
                "jaccard_min": jac.min(), "jaccard_grupos": " · ".join(f"{v:.2f}" for v in jac),
                "ari_boot": f"{boot['ari'].mean():.3f} ± {boot['ari'].std():.3f}"})
    return lin, rot, boot


def destaque(X, ausente, m):
    """Categoria mais sobrerrepresentada no grupo (share no grupo / share na base), entre as
    que têm pelo menos metade do grupo."""
    melhor, txt = 0, "-"
    cols = {v: X[v].astype(str).to_numpy() for v in CATEGORICAS + ["FastingBS"]}
    cols["colesterol_ausente"] = ausente.astype(str)
    for v, val in cols.items():
        for c in np.unique(val):
            g, b = (val[m] == c).mean(), (val == c).mean()
            if g >= 0.5 and g / b > melhor:
                melhor, txt = g / b, f"{v}={c}: {g:.0%} (base {b:.0%})"
    return txt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/alternativa_k4.yaml")
    ap.add_argument("--referencia", default="final")
    ap.add_argument("--bootstrap", type=int, default=None)
    ap.add_argument("--saida", default=None)
    a = ap.parse_args()
    ref_cfg, alt_cfg = config.config_final(a.referencia), config.config_final(a.config)
    dec = config.base().get("decisao", {})
    B = a.bootstrap or dec.get("bootstrap", 100)
    trava = dec.get("trava_categoria", {"concentracao": 0.90, "prevalencia_max": 0.20})
    pasta = config.pasta_analise(a.config, "comparacao", a.saida)
    kr, ka = ref_cfg["modelo"]["k"], alt_cfg["modelo"]["k"]
    nr, na = f"referência (k = {kr})", f"alternativa (k = {ka})"

    base = carregar_base()
    X, y, ausente, _ = separar(base)
    idxs = reamostras(len(X), B, dec.get("semente_bootstrap", 0))
    print(f"comparando {nr} x {na}: {B} reamostras pareadas")
    lr, rot_r, br = avaliar(ref_cfg, X, y, ausente, idxs, trava, dec.get("permutacoes_nula", 10))
    la, rot_a, ba = avaliar(alt_cfg, X, y, ausente, idxs, trava, dec.get("permutacoes_nula", 10))

    met = pd.DataFrame({nr: {n: lr.get(c) for c, n in LINHAS}, na: {n: la.get(c) for c, n in LINHAS}})
    met.to_csv(pasta / "metricas.csv")
    fmt = met.map(lambda v: f"{v:.3f}" if isinstance(v, (float, np.floating)) else v)

    dif = []
    for m, nome in [("ari", "ARI"), ("ari_registrado", "ARI registrado"), ("silhueta", "Silhueta")]:
        d = (ba[m] - br[m]).dropna()
        lo, hi = np.quantile(d, [0.025, 0.975])
        dif.append({"métrica": nome, "Δ (alternativa − referência)": f"{d.mean():+.3f}",
                    "IC 95%": f"[{lo:+.3f}; {hi:+.3f}]"})
    dif = pd.DataFrame(dif)

    mapa_r = metricas.mapear(rot_r, y)
    classe_r = np.array([mapa_r[int(g)] for g in rot_r])
    disc = classe_r != y
    rotulo_r = {g: f"k{kr} grupo {g} ({'doente' if c else 'saudável'})" for g, c in mapa_r.items()}

    grupos = []
    for g in np.unique(rot_a):
        m = rot_a == g
        grupos.append({"grupo": g, "n": int(m.sum()), "% doentes": round(100 * y[m].mean(), 1),
                       "% colesterol ausente": round(100 * ausente[m].mean(), 1),
                       "discordantes do k2 no grupo": int((disc & m).sum()),
                       "% do grupo que é discordante do k2": round(100 * disc[m].mean(), 1),
                       "destaque": destaque(X, ausente, m)})
    grupos = pd.DataFrame(grupos)
    grupos.to_csv(pasta / "grupos.csv", index=False)

    cruz = pd.crosstab(pd.Series(rot_r).map(rotulo_r).rename("referência"),
                       pd.Series(rot_a).rename(f"alternativa (k = {ka})"))
    cruz.to_csv(pasta / "cruzamento.csv")
    cruz_disc = pd.crosstab(pd.Series(np.where(disc, "discordante", "concordante")).rename("no k = 2"),
                            pd.Series(rot_a).rename(f"grupo na alternativa (k = {ka})"))

    txt = [f"# Comparação: {nr} × {na}", "",
           f"Ajuste na base inteira (semente 0); bootstrap com {B} reamostras pareadas "
           "(as mesmas para as duas configurações; avaliação nos pacientes fora da reamostra).", "",
           "## Métricas", "", _tabela(fmt), "",
           "## Diferenças pareadas (bootstrap)", "", _tabela(dif, index=False), "",
           f"## Grupos da alternativa (k = {ka})", "", _tabela(grupos, index=False), "",
           f"Discordantes do k = {kr}: {int(disc.sum())} de {len(y)} pacientes.", "",
           f"## Para onde vão os pacientes de cada grupo do k = {kr}", "", _tabela(cruz), "",
           f"## Onde caem os discordantes do k = {kr}", "", _tabela(cruz_disc)]
    (pasta / "comparacao.md").write_text("\n".join(txt) + "\n", encoding="utf-8")
    print(fmt.to_string())
    print(dif.to_string(index=False))
    print(grupos.to_string(index=False))
    print(f"-> {pasta}")


if __name__ == "__main__":
    main()
