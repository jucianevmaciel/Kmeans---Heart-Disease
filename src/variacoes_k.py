"""Análise complementar: a configuração final com outros valores de k.

Uso:  python -m src.variacoes_k [--yaml configs/variacoes_k.yaml] [--ks 2 3 4] [--bootstrap 100]

Não é uma rodada de decisão: o k principal continua sendo o vencedor da R5b. Para cada
k da lista, a configuração final é refeita só com o k trocado e avaliada:
  - na base inteira (semente 0): ARI, ARI registrado, acurácia, recall, especificidade,
    AUC do escore, silhueta e silhueta nula;
  - no bootstrap pareado (as mesmas reamostras para todos os k): ARI fora da
    reamostra, Jaccard de cada grupo e diferenças para o k de referência com IC 95%;
  - na validação cruzada 5x5 (protocolo da R8): ARI e AUC fora da amostra;
  - diante das travas da regra de decisão (o que a R3/R5b faria com esse k);
  - pela composição dos grupos: tamanho, % de doentes e categorias que dominam o grupo.

Saídas em results/variacoes_k/:
    resumo.md        tabelas para o relatório (uma seção por k com os grupos)
    metricas.csv     uma linha por k
    diferencas.csv   diferenças pareadas para o k de referência
    grupos.csv       uma linha por k x grupo
    bootstrap.csv    uma linha por k x reamostra
    cv.csv           uma linha por k x dobra
    variacoes_k.png  ARI, AUC, silhueta (com a nula) e Jaccard mínimo por k
"""
import argparse
import copy
import warnings

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.model_selection import RepeatedStratifiedKFold

from . import config, metricas
from .dados import BINARIAS, CATEGORICAS, carregar_base, separar
from .pipeline import ajustar, espaco
from .runner import avaliar_agrupamento, bootstrap_opcao, reamostras

warnings.filterwarnings("ignore")
PASTA = config.RESULTADOS / "variacoes_k"


def _tabela(df, index=False):
    try:
        return df.to_markdown(index=index)
    except ImportError:
        return df.to_string(index=index)


def situacao(lin, jac_min, dec):
    """O que a regra de decisão da R3/R5b diria deste k (sem considerar o empate)."""
    motivos = []
    if jac_min < dec.get("jaccard_min", 0.75):
        motivos.append(f"instável (Jaccard {jac_min:.2f})")
    if lin["atalho_lift"] > dec.get("trava_atalho_lift", 2.0):
        motivos.append(f"atalho do colesterol ({lin['atalho_lift']:.2f}x)")
    if lin["categoria_rara"]:
        motivos.append(f"categoria rara ({lin['categoria_rara_desc']})")
    return "elegível" if not motivos else "barrado: " + "; ".join(motivos)


def categorias_dominantes(X, ausente, m, limite):
    """Categorias com >= `limite` dos pacientes do grupo, com a prevalência na base."""
    cols = {v: X[v].astype(str).to_numpy() for v in CATEGORICAS + BINARIAS}
    cols["colesterol_ausente"] = ausente.astype(str)
    out = []
    for v, val in cols.items():
        for c in np.unique(val):
            g = (val[m] == c).mean()
            if g >= limite:
                out.append(f"{v}={c} {g:.0%} (base {(val == c).mean():.0%})")
    return "; ".join(out) or "—"


def validacao_cruzada(cfg, X, y, cv):
    linhas = []
    for i, (tr, te) in enumerate(cv.split(X, y)):
        pipe, _, rot_tr = ajustar(cfg, X.iloc[tr], y[tr], semente=i)
        mapa = metricas.mapear(rot_tr, y[tr])
        Zte = espaco(pipe, X.iloc[te])
        modelo = pipe.named_steps["modelo"]
        rot_te = np.asarray(modelo.predict(Zte)).astype(int)
        linhas.append({"dobra": i, **metricas.externas(rot_te, y[te], mapa),
                       "auc_escore": metricas.auc(y[te], metricas.escore_risco(modelo, Zte, mapa))})
    return pd.DataFrame(linhas)


def grafico(met, ref_k, arq):
    fig, eixos = plt.subplots(2, 2, figsize=(10, 7))
    k = met["k"]
    ax = eixos[0, 0]
    ax.plot(k, met["ari"], marker="o", label="base inteira")
    ax.errorbar(k, met["ari_cv"], yerr=met["ari_cv_dp"], marker="s", capsize=3, label="fora da amostra (CV 5x5)")
    ax.set_title("ARI com o diagnóstico", fontsize=10)
    ax.legend(fontsize=8)
    ax = eixos[0, 1]
    ax.plot(k, met["auc_escore"], marker="o", label="base inteira")
    ax.errorbar(k, met["auc_cv"], yerr=met["auc_cv_dp"], marker="s", capsize=3, label="fora da amostra (CV 5x5)")
    ax.set_title("AUC do escore", fontsize=10)
    ax.legend(fontsize=8)
    ax = eixos[1, 0]
    ax.plot(k, met["silhueta"], marker="o", label="silhueta")
    ax.plot(k, met["silhueta_nula"], marker=".", ls=":", label="silhueta nula (colunas embaralhadas)")
    ax.set_title("Silhueta", fontsize=10)
    ax.legend(fontsize=8)
    ax = eixos[1, 1]
    ax.plot(k, met["jaccard_min"], marker="o")
    ax.axhline(0.75, ls="--", c="gray", lw=1)
    ax.set_title("Jaccard do grupo menos estável (bootstrap)", fontsize=10)
    for ax in eixos.flat:
        ax.axvline(ref_k, c="k", lw=0.8, alpha=0.4)
        ax.set_xlabel("k")
        ax.set_xticks(list(k))
        ax.grid(alpha=0.3)
    fig.suptitle(f"Configuração final com outros k (linha vertical: k = {ref_k}, o principal)", fontsize=11)
    fig.tight_layout()
    fig.savefig(arq, dpi=150)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--yaml", default="configs/variacoes_k.yaml")
    ap.add_argument("--ks", type=int, nargs="+", default=None)
    ap.add_argument("--bootstrap", type=int, default=None)
    a = ap.parse_args()
    params = config.ler_yaml(a.yaml)
    cfg_final = config.config_final(params.get("herda_de", "final"))
    dec = config.base().get("decisao", {})
    ks = a.ks or params.get("ks", [2, 3, 4, 5, 6])
    ref_k = params.get("referencia_k", cfg_final["modelo"]["k"])
    if ref_k not in ks:
        ks = [ref_k] + list(ks)
    B = a.bootstrap or dec.get("bootstrap", 100)
    trava = dec.get("trava_categoria", {"concentracao": 0.90, "prevalencia_max": 0.20})
    vc = params.get("validacao_cruzada", {})
    cv = RepeatedStratifiedKFold(n_splits=vc.get("dobras", 5), n_repeats=vc.get("repeticoes", 5),
                                 random_state=vc.get("semente_cv", 42))
    PASTA.mkdir(parents=True, exist_ok=True)

    X, y, ausente, _ = separar(carregar_base())
    idxs = reamostras(len(X), B, dec.get("semente_bootstrap", 0))
    print(f"Variações de k {ks} (referência k = {ref_k}): {B} reamostras pareadas + CV "
          f"{vc.get('dobras', 5)}x{vc.get('repeticoes', 5)}")

    met, grupos, boots, cvs, rotulos = [], [], [], [], {}
    for k in ks:
        cfg = copy.deepcopy(cfg_final)
        cfg["modelo"]["k"] = k
        lin, rot, Z = avaliar_agrupamento(cfg, X, y, ausente, 0, trava)
        rotulos[k] = rot
        b = pd.DataFrame(bootstrap_opcao(f"k={k}", cfg, X, y, ausente, rot, idxs)).assign(k=k)
        boots.append(b)
        jac = b.filter(like="jaccard_g").mean()
        c = validacao_cruzada(cfg, X, y, cv).assign(k=k)
        cvs.append(c)
        met.append({"k": k, **{m: lin[m] for m in ["ari", "ari_registrado", "nmi", "pureza", "recall",
                                                  "especificidade", "auc_escore", "silhueta", "atalho_lift"]},
                    "silhueta_nula": metricas.silhueta_nula(Z, k, dec.get("permutacoes_nula", 10)),
                    "ari_boot": b["ari"].mean(), "ari_boot_dp": b["ari"].std(),
                    "ari_cv": c["ari"].mean(), "ari_cv_dp": c["ari"].std(),
                    "auc_cv": c["auc_escore"].mean(), "auc_cv_dp": c["auc_escore"].std(),
                    "jaccard_min": jac.min(), "jaccard_grupos": " · ".join(f"{v:.2f}" for v in jac),
                    "menor_grupo": lin["menor_grupo"], "situacao": situacao(lin, jac.min(), dec)})
        for g in np.unique(rot):
            m = rot == g
            grupos.append({"k": k, "grupo": int(g), "n": int(m.sum()), "% doentes": round(100 * y[m].mean(), 1),
                           "% colesterol ausente": round(100 * ausente[m].mean(), 1),
                           "jaccard": round(float(jac.get(f"jaccard_g{g}", np.nan)), 2),
                           "categorias dominantes": categorias_dominantes(X, ausente, m, trava["concentracao"])})
        print(f"  k={k}: ARI={lin['ari']:.3f}  CV={c['ari'].mean():.3f}  Jaccard mín.={jac.min():.2f}  "
              f"{met[-1]['situacao'][:60]}")

    met = pd.DataFrame(met)
    grupos = pd.DataFrame(grupos)
    boots = pd.concat(boots, ignore_index=True)
    cvs = pd.concat(cvs, ignore_index=True)

    # de onde vêm os pacientes de cada grupo: fração vinda do grupo "doente" do k de referência
    rr = rotulos[ref_k]
    mapa_r = metricas.mapear(rr, y)
    doente_ref = np.array([mapa_r[int(g)] for g in rr]) == 1
    grupos["% vindo do grupo 'doente' do k de referência"] = [
        round(100 * doente_ref[rotulos[r.k] == r.grupo].mean(), 1) for r in grupos.itertuples()]
    grupos = grupos.sort_values(["k", "% doentes"], ascending=[True, False])

    ref_b = boots[boots["k"] == ref_k].set_index("reamostra")
    dif = []
    for k in ks:
        if k == ref_k:
            continue
        bk = boots[boots["k"] == k].set_index("reamostra")
        lin = {"k": k}
        for m in ["ari", "ari_registrado", "silhueta"]:
            d = (bk[m] - ref_b[m]).dropna()
            lo, hi = np.quantile(d, [0.025, 0.975])
            lin[f"Δ {m}"] = round(d.mean(), 3)
            lin[f"IC95 {m}"] = f"[{lo:+.3f}; {hi:+.3f}]"
        dif.append(lin)
    dif = pd.DataFrame(dif)

    met.to_csv(PASTA / "metricas.csv", index=False)
    dif.to_csv(PASTA / "diferencas.csv", index=False)
    grupos.to_csv(PASTA / "grupos.csv", index=False)
    boots.to_csv(PASTA / "bootstrap.csv", index=False)
    cvs.to_csv(PASTA / "cv.csv", index=False)
    grafico(met, ref_k, PASTA / "variacoes_k.png")

    tab = met[["k", "ari", "ari_registrado", "ari_cv", "pureza", "recall", "especificidade", "auc_escore",
               "auc_cv", "silhueta", "silhueta_nula", "jaccard_min", "situacao"]].copy()
    tab.columns = ["k", "ARI", "ARI registr.", "ARI CV 5x5", "acurácia", "recall", "espec.", "AUC",
                   "AUC CV 5x5", "silhueta", "silh. nula", "Jaccard mín.", "situação na regra da R3/R5b"]
    txt = ["# Variações de k (análise complementar)", "",
           f"Configuração final (vencedor da R5b) com só o k trocado. **O k principal é {ref_k}**; os "
           "demais são complementares. Base inteira (semente 0), bootstrap com "
           f"{B} reamostras pareadas, validação cruzada {vc.get('dobras', 5)}x{vc.get('repeticoes', 5)} "
           f"(semente {vc.get('semente_cv', 42)}, protocolo da R8).", "",
           "## Métricas por k", "", _tabela(tab.round(3)), "",
           f"## Diferenças pareadas para o k = {ref_k} (bootstrap, pacientes fora da reamostra)", "",
           _tabela(dif), "",
           "## Grupos de cada k", "",
           f"Categorias dominantes: as que reúnem ≥ {trava['concentracao']:.0%} do grupo. "
           f"A última coluna diz quanto do grupo vem do grupo 'doente' do k = {ref_k}.", ""]
    for k in ks:
        g = grupos[grupos["k"] == k].drop(columns="k")
        txt += [f"### k = {k}", "", _tabela(g), ""]
    (PASTA / "resumo.md").write_text("\n".join(txt) + "\n", encoding="utf-8")
    print(f"-> {PASTA.relative_to(config.RAIZ)}")


if __name__ == "__main__":
    main()
