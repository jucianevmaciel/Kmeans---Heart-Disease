"""Regra de decisão das rodadas (substitui o teste t do SVM-Infarto).

1. Elegíveis: não supervisionadas, fora_da_disputa = false e sem nenhuma trava:
   - estabilidade: Jaccard médio por bootstrap >= decisao.jaccard_min em TODOS os
     grupos (Hennig, 2007);
   - atalho do colesterol: % de ausentes no grupo mais concentrado / % na base
     <= decisao.trava_atalho_lift;
   - categoria rara: nenhum grupo com >= trava_categoria.concentracao dos pacientes
     numa categoria com prevalência < trava_categoria.prevalencia_max (na maioria
     das sementes).
2. Melhor: maior média do critério no ajuste da base inteira (menor no Davies-Bouldin).
3. Empate (bootstrap pareado): para cada elegível, a diferença do critério para a
   melhor é calculada em cada reamostra, nos pacientes fora dela (as mesmas
   reamostras para todas as opções). Empata se o intervalo de confiança
   (decisao.nivel_ic) da diferença contém zero.
4. Entre as empatadas, vence a primeira na ordem do YAML (a mais simples; na grade
   do k, o menor k).

Uso direto (refazer a decisão sem rodar de novo):
    python -m src.compare configs/r01_escalonamento.yaml
"""
import argparse

import numpy as np
import pandas as pd

from . import config

MENOR_MELHOR = {"davies_bouldin", "inercia"}


def _fmt(v, casas=3):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "—"
    return f"{v:.{casas}f}" if isinstance(v, (int, float, np.floating)) else str(v)


def _diferencas(boot, crit, melhor, outra, sinal):
    """Diferença pareada (melhor − outra) do critério em cada reamostra, no sentido 'maior é melhor'."""
    a = boot[boot["opcao"] == melhor].set_index("reamostra")[crit]
    b = boot[boot["opcao"] == outra].set_index("reamostra")[crit]
    d = (sinal * (a - b)).dropna()
    return d.to_numpy()


def decidir(rod, opcoes, resumo, boot, pasta):
    dec = rod["_partida"].get("decisao", {})
    crit = rod.get("criterio")
    if crit == "principal":  # definido em base.yaml -> decisao.criterio_principal
        crit = dec.get("criterio_principal", "ari")
    jac_min = dec.get("jaccard_min", 0.75)
    lift_max = dec.get("trava_atalho_lift", 2.0)
    tc = dec.get("trava_categoria", {"concentracao": 0.90, "prevalencia_max": 0.20})
    nivel = dec.get("nivel_ic", 0.95)
    alfa = (1 - nivel) / 2
    linhas = [f"# {rod.get('rodada', '')}: {rod.get('pergunta', '')}", ""]
    if rod.get("nota"):
        linhas += [str(rod["nota"]).strip(), ""]

    r = resumo.copy()
    for c in ["jaccard_min", "atalho_lift_media", "categoria_rara_media"]:
        if c not in r:
            r[c] = np.nan
    r["supervisionado"] = r["supervisionado"].astype(bool)
    r["fora_da_disputa"] = r["fora_da_disputa"].astype(bool)
    r["motivo"] = ""
    r["delta_ic"] = ""
    livre = lambda: r["motivo"] == ""  # noqa: E731
    r.loc[r["supervisionado"], "motivo"] = "referência supervisionada"
    r.loc[r["fora_da_disputa"] & livre(), "motivo"] = "fora da disputa"
    r.loc[livre() & (r["jaccard_min"] < jac_min), "motivo"] = f"instável (Jaccard < {jac_min})"
    r.loc[livre() & (r["atalho_lift_media"] > lift_max), "motivo"] = \
        f"atalho do colesterol (> {lift_max}x a base num grupo)"
    r.loc[livre() & (r["categoria_rara_media"] > 0.5), "motivo"] = "grupo de uma categoria rara"

    vencedor = None
    if crit:
        col = f"{crit}_media"
        sinal = -1 if crit in MENOR_MELHOR else 1
        eleg = r[livre()]
        pareado = len(boot) and crit in boot.columns
        if len(eleg):
            melhor = eleg.loc[(sinal * eleg[col]).idxmax()]
            empatadas = []
            for i, o in eleg.iterrows():
                if i == melhor.name:
                    empatadas.append(i)
                    continue
                if pareado:
                    d = _diferencas(boot, crit, melhor["opcao"], o["opcao"], sinal)
                    lo, hi = np.quantile(d, [alfa, 1 - alfa])
                    r.loc[i, "delta_ic"] = f"{d.mean():+.3f} [{lo:+.3f}; {hi:+.3f}]"
                    if lo <= 0:
                        empatadas.append(i)
                else:  # critério sem bootstrap: regra antiga (desvio entre sementes)
                    tol = max(o.get(f"{crit}_dp", 0) or 0, melhor.get(f"{crit}_dp", 0) or 0)
                    if abs(melhor[col] - o[col]) <= tol:
                        empatadas.append(i)
            vencedor = r.loc[min(empatadas)]  # ordem do YAML = ordem de simplicidade
            r.loc[empatadas, "motivo"] = "empatada com a melhor"
            r.loc[melhor.name, "motivo"] = "melhor média"
            r.loc[vencedor.name, "motivo"] = "VENCEDORA"
        regra = (f"empate se o IC {nivel:.0%} da diferença pareada (bootstrap, pacientes fora da "
                 f"reamostra) contém zero" if pareado else "empate pelo desvio entre sementes")
        linhas += [f"Critério: **{crit}** ({'menor' if crit in MENOR_MELHOR else 'maior'} é melhor); {regra}. "
                   f"Travas: Jaccard mínimo por grupo {jac_min}; atalho do colesterol até {lift_max}x a base; "
                   f"nenhum grupo com ≥ {tc['concentracao']:.0%} numa categoria com < "
                   f"{tc['prevalencia_max']:.0%} da base.", ""]
    else:
        linhas += ["Rodada sem escolha (referências).", ""]

    cab = ["opção", "ARI", "ARI registr.", "AUC escore", "pureza", "recall", "espec.", "silhueta",
           "silh. nula", "Jaccard por grupo", "estab. sementes", "lift ausente", "Δ para a melhor [IC]", "situação"]
    linhas += ["| " + " | ".join(cab) + " |", "|" + "---|" * len(cab)]
    for _, x in r.iterrows():
        linhas.append("| " + " | ".join([
            str(x["opcao"]), _fmt(x.get("ari_media")), _fmt(x.get("ari_registrado_media")),
            _fmt(x.get("auc_escore_media")), _fmt(x.get("pureza_media")), _fmt(x.get("recall_media")),
            _fmt(x.get("especificidade_media")), _fmt(x.get("silhueta_media")), _fmt(x.get("silhueta_nula")),
            _fmt(x.get("jaccard_grupos")) if isinstance(x.get("jaccard_grupos"), str) else "—",
            _fmt(x.get("estabilidade_sementes")), _fmt(x.get("atalho_lift_media"), 2),
            x["delta_ic"] or "—", x["motivo"] or "—"]) + " |")
    linhas.append("")
    raras = r[r["motivo"] == "grupo de uma categoria rara"]
    for _, x in raras.iterrows():
        linhas.append(f"- {x['opcao']}: {x.get('categoria_rara_desc', '')}")
    if len(raras):
        linhas.append("")

    if crit and vencedor is None:
        linhas.append("**Nenhuma opção elegível.** Revejam a rodada antes de seguir; vencedor.yaml não foi gravado.")
    elif vencedor is not None:
        cfg = next(o["cfg"] for o in opcoes if o["nome"] == vencedor["opcao"])
        config.salvar_yaml({k: cfg[k] for k in ("pre", "modelo")}, pasta / "vencedor.yaml")
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
    boot = pd.read_csv(pasta / "bootstrap.csv") if (pasta / "bootstrap.csv").exists() else pd.DataFrame()
    decidir(rod, opcoes, resumo.drop(columns=["motivo", "delta_ic"], errors="ignore"), boot, pasta)


if __name__ == "__main__":
    main()
