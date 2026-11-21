"""Métricas internas (sem rótulo), externas (com rótulo, só para avaliar),
escore de risco pela distância aos centróides e estabilidade."""
import itertools

import numpy as np
from sklearn.metrics import (adjusted_rand_score, calinski_harabasz_score, davies_bouldin_score,
                             normalized_mutual_info_score, roc_auc_score, silhouette_score)

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


def menor_grupo(rot):
    return float(np.bincount(rot).min() / len(rot)) if len(rot) else np.nan
