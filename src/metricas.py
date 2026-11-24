"""Métricas internas (sem rótulo), externas (com rótulo, só para avaliar),
escore de risco pela distância aos centróides, estabilidade e travas."""
import itertools

import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import (adjusted_rand_score, calinski_harabasz_score, davies_bouldin_score,
                             normalized_mutual_info_score, roc_auc_score, silhouette_score)

from .dados import BINARIAS, CATEGORICAS
from .pipeline import centroides


def internas(Z, rot, modelo=None):
    if len(np.unique(rot)) < 2:
        return {"silhueta": np.nan, "davies_bouldin": np.nan, "calinski_harabasz": np.nan, "inercia": np.nan}
    if modelo is not None and hasattr(modelo, "inertia_"):
        inercia = float(modelo.inertia_)
    else:
        inercia = float(sum(((Z[rot == g] - Z[rot == g].mean(0)) ** 2).sum() for g in np.unique(rot)))
    return {"silhueta": silhouette_score(Z, rot), "davies_bouldin": davies_bouldin_score(Z, rot),
            "calinski_harabasz": calinski_harabasz_score(Z, rot), "inercia": inercia}


def mapear(rot, y):
    """Cada grupo recebe a classe majoritária dos seus pacientes (feito depois do agrupamento)."""
    return {int(g): int(round(y[rot == g].mean())) for g in np.unique(rot)}


def externas(rot, y, mapa=None):
    """ARI, NMI, pureza e recall/especificidade pelo mapeamento grupo -> classe.

    Com o mapeamento por maioria, a pureza é igual à acurácia do agrupamento.
    """
    mapa = mapa or mapear(rot, y)
    pred = np.array([mapa.get(int(g), 0) for g in rot])
    vp = ((pred == 1) & (y == 1)).sum()
    vn = ((pred == 0) & (y == 0)).sum()
    return {"ari": adjusted_rand_score(y, rot), "nmi": normalized_mutual_info_score(y, rot),
            "pureza": (pred == y).mean(),
            "recall": vp / max((y == 1).sum(), 1), "especificidade": vn / max((y == 0).sum(), 1)}


def escore_risco(modelo, Z, mapa):
    """Escore contínuo de risco a partir do agrupamento.

    K-Means/Ward: d_saudavel / (d_saudavel + d_doente), em que d_* é a distância ao
    centróide mais próximo dos grupos mapeados para aquela classe.
    GMM: soma das probabilidades dos grupos mapeados para 'doente'.
    Devolve None se todos os grupos forem mapeados para a mesma classe.
    """
    grupos_d = [g for g, c in mapa.items() if c == 1]
    grupos_s = [g for g, c in mapa.items() if c == 0]
    if not grupos_d or not grupos_s:
        return None
    if hasattr(modelo, "predict_proba") and hasattr(modelo, "means_"):
        return modelo.predict_proba(Z)[:, grupos_d].sum(1)
    C = centroides(modelo)
    d = np.sqrt(((Z[:, None, :] - C[None]) ** 2).sum(-1))
    d1, d0 = d[:, grupos_d].min(1), d[:, grupos_s].min(1)
    return d0 / (d0 + d1 + 1e-12)


def auc(y, escore):
    if escore is None or len(np.unique(y)) < 2:
        return np.nan
    return roc_auc_score(y, escore)


def estabilidade(lista_rotulos):
    """ARI médio entre todos os pares de execuções (sementes diferentes)."""
    if len(lista_rotulos) < 2:
        return np.nan
    return float(np.mean([adjusted_rand_score(a, b) for a, b in itertools.combinations(lista_rotulos, 2)]))


def atalho_colesterol(rot, ausente):
    """Maior % de colesterol ausente dentro de um grupo (a marca do atalho)."""
    return float(max(ausente[rot == g].mean() for g in np.unique(rot)))


def atalho_lift(rot, ausente):
    """Maior % de colesterol ausente num grupo dividido pelo % da base inteira (18,7%).

    1 = nenhum grupo concentra os ausentes; 5 = um grupo é quase só de ausentes.
    """
    base = ausente.mean()
    return atalho_colesterol(rot, ausente) / base if base > 0 else np.nan


def ari_registrado(rot, y, ausente):
    """ARI só nos pacientes com colesterol registrado (o atalho não pode ajudar neles)."""
    m = ausente == 0
    return adjusted_rand_score(y[m], rot[m])


def categoria_rara(rot, X, ausente, concentracao=0.90, prevalencia_max=0.20):
    """Procura um grupo formado por uma única categoria rara.

    Para cada grupo e cada categoria (categóricas, FastingBS = 1 e colesterol ausente):
    dispara se >= `concentracao` do grupo está numa categoria que tem < `prevalencia_max`
    na base. Devolve (disparou, descrição do pior caso).
    """
    colunas = {v: X[v].astype(str).to_numpy() for v in CATEGORICAS}
    for v in BINARIAS:
        colunas[v] = X[v].astype(str).to_numpy()
    colunas["colesterol_ausente"] = ausente.astype(str)
    pior, desc = 0.0, "-"
    for v, val in colunas.items():
        for cat in np.unique(val):
            prev = (val == cat).mean()
            if prev >= prevalencia_max:
                continue
            for g in np.unique(rot):
                conc = (val[rot == g] == cat).mean()
                if conc > pior:
                    pior, desc = conc, f"grupo {g}: {conc:.0%} {v}={cat} (base {prev:.0%})"
    return pior >= concentracao, desc


def jaccard_grupos(ref, rot_boot, idx):
    """Jaccard de cada grupo de referência com o grupo mais parecido da reamostra (Hennig, 2007).

    ref: grupos do ajuste na base inteira; rot_boot: grupos do ajuste na reamostra;
    idx: pacientes (sem repetição) que entraram na reamostra. Compara só nesses pacientes.
    """
    r, b = ref[idx], rot_boot[idx]
    out = []
    for g in np.unique(ref):
        A = r == g
        if not A.any():
            out.append(np.nan)
            continue
        out.append(max((A & (b == h)).sum() / (A | (b == h)).sum() for h in np.unique(b)))
    return out


def silhueta_nula(Z, k, n_perm=10, semente=0):
    """Silhueta média do K-Means em dados sem estrutura: cada coluna de Z embaralhada
    de forma independente (preserva as distribuições, destrói as relações). Ideia da
    estatística gap (Tibshirani et al., 2001)."""
    rng = np.random.default_rng(semente)
    vals = []
    for p in range(n_perm):
        Zp = np.column_stack([rng.permutation(Z[:, j]) for j in range(Z.shape[1])])
        rot = KMeans(n_clusters=k, n_init=10, random_state=p).fit_predict(Zp)
        if len(np.unique(rot)) > 1:
            vals.append(silhouette_score(Zp, rot))
    return float(np.mean(vals)) if vals else np.nan


def menor_grupo(rot):
    return float(np.bincount(rot).min() / len(rot)) if len(rot) else np.nan
