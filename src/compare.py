"""Regra de decisão das rodadas (substitui o teste t do SVM-Infarto).

1. Elegíveis: não supervisionadas, fora_da_disputa = false,
   estabilidade >= decisao.estabilidade_min e
   atalho_colesterol (maior % de colesterol ausente num grupo) <= decisao.trava_atalho.
2. Melhor: maior média do critério (menor, no caso de davies_bouldin).
3. Empate: diferença para a melhor <= maior desvio-padrão entre sementes das duas.
4. Entre as empatadas, vence a primeira na ordem do YAML (a mais simples).

Uso direto (refazer a decisão sem rodar de novo):
    python -m src.compare configs/r01_escalonamento.yaml
"""
import argparse

import numpy as np
import pandas as pd

from . import config

MENOR_MELHOR = {"davies_bouldin", "inercia"}


def _fmt(v, casas=3):
    return "—" if v is None or (isinstance(v, float) and np.isnan(v)) else f"{v:.{casas}f}"


def decidir(rod, opcoes, resumo, pasta):
    dec = rod["_partida"].get("decisao", {})
    crit = rod.get("criterio")
    if crit == "principal":  # definido em base.yaml -> decisao.criterio_principal
        crit = dec.get("criterio_principal", "ari")
    est_min = dec.get("estabilidade_min", 0.80)
    trava = dec.get("trava_atalho", 0.50)
    linhas = [f"# {rod.get('rodada', '')}: {rod.get('pergunta', '')}", ""]
    if rod.get("nota"):
        linhas += [str(rod["nota"]).strip(), ""]

    r = resumo.copy()
    r["motivo"] = ""
    r.loc[r["supervisionado"], "motivo"] = "referência supervisionada"
    r.loc[r["fora_da_disputa"] & (r["motivo"] == ""), "motivo"] = "fora da disputa"
    r.loc[(r["motivo"] == "") & (r["estabilidade"] < est_min), "motivo"] = f"instável (< {est_min})"
    if "atalho_colesterol_media" in r:
        r.loc[(r["motivo"] == "") & (r["atalho_colesterol_media"] > trava), "motivo"] = \
            f"atalho do colesterol (> {trava:.0%} num grupo)"

    vencedor = None
    if crit:
        col, dp = f"{crit}_media", f"{crit}_dp"
        eleg = r[r["motivo"] == ""]
        if len(eleg):
            sinal = -1 if crit in MENOR_MELHOR else 1
            melhor = eleg.loc[(sinal * eleg[col]).idxmax()]
            tol = np.maximum(eleg[dp].fillna(0), melhor[dp] if not np.isnan(melhor[dp]) else 0)
            empate = eleg[(sinal * (melhor[col] - eleg[col])).abs() <= tol]
            vencedor = empate.iloc[0]  # ordem do YAML = ordem de simplicidade
            r.loc[empate.index, "motivo"] = "empatada com a melhor"
            r.loc[melhor.name, "motivo"] = "melhor média"
            r.loc[vencedor.name, "motivo"] = "VENCEDORA"
        linhas += [f"Critério: **{crit}** ({'menor' if crit in MENOR_MELHOR else 'maior'} é melhor). "
                   f"Estabilidade mínima {est_min}; trava do atalho {trava:.0%}.", ""]
    else:
        linhas += ["Rodada sem escolha (referências).", ""]

    cab = ["opção", "ARI", "dp", "AUC escore", "pureza", "recall", "espec.", "silhueta",
           "Davies-B.", "estab.", "% ausente máx.", "situação"]
    linhas += ["| " + " | ".join(cab) + " |", "|" + "---|" * len(cab)]
    for _, x in r.iterrows():
        linhas.append("| " + " | ".join([
            str(x["opcao"]), _fmt(x.get("ari_media")), _fmt(x.get("ari_dp")), _fmt(x.get("auc_escore_media")),
            _fmt(x.get("pureza_media")), _fmt(x.get("recall_media")), _fmt(x.get("especificidade_media")),
            _fmt(x.get("silhueta_media")), _fmt(x.get("davies_bouldin_media")), _fmt(x.get("estabilidade")),
            _fmt(x.get("atalho_colesterol_media"), 2), x["motivo"] or "—"]) + " |")
    linhas.append("")

    if crit and vencedor is None:
        linhas.append("**Nenhuma opção elegível.** Revejam a rodada antes de seguir; vencedor.yaml não foi gravado.")
    elif vencedor is not None:
        cfg = next(o["cfg"] for o in opcoes if o["nome"] == vencedor["opcao"])
        salvar = {k: v for k, v in cfg.items() if not k.startswith("_")}
        config.salvar_yaml(salvar, pasta / "vencedor.yaml")
        linhas.append(f"**Vencedora: {vencedor['opcao']}** (gravada em vencedor.yaml).")
    (pasta / "decisao.md").write_text("\n".join(linhas) + "\n", encoding="utf-8")
    r.to_csv(pasta / "resumo.csv", index=False)
    if vencedor is not None:
        print(f"  vencedora: {vencedor['opcao']}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("yaml")
    a = ap.parse_args()
    rod, opcoes = config.carregar_rodada(config.caminho(a.yaml))
    pasta = config.pasta_rodada(a.yaml)
    resumo = pd.read_csv(pasta / "resumo.csv")
    decidir(rod, opcoes, resumo.drop(columns=["motivo"], errors="ignore"), pasta)


if __name__ == "__main__":
    main()
