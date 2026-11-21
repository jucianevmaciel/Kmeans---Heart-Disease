"""Pipeline: tratamento dos dados -> codificação/escala -> redução -> agrupamento.

O ajuste (pipe.fit) aprende medianas, escalas e centróides a partir dos dados recebidos.
"""
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, ClusterMixin, TransformerMixin
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.compose import ColumnTransformer
from sklearn.decomposition import PCA
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.linear_model import LogisticRegression
from sklearn.mixture import GaussianMixture
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MinMaxScaler, OneHotEncoder, RobustScaler, StandardScaler

from .dados import BINARIAS, CATEGORICAS, NUMERICAS

SUPERVISIONADOS = {"dummy", "logreg", "gboost"}


class TratarDados(BaseEstimator, TransformerMixin):
    """Zeros impossíveis, Oldpeak negativo e colunas removidas.

    zeros:   mediana | mediana_flag | remover_colesterol
    oldpeak: manter | abs | zero
    """

    def __init__(self, zeros="mediana", oldpeak="manter", drop_cols=()):
        self.zeros = zeros
        self.oldpeak = oldpeak
        self.drop_cols = drop_cols

    def _limpar(self, X):
        X = X.copy()
        X["RestingBP"] = X["RestingBP"].replace(0, np.nan)
        if self.zeros == "mediana_flag":
            X["Cholesterol_ausente"] = (X["Cholesterol"] == 0).astype(int)
        X["Cholesterol"] = X["Cholesterol"].replace(0, np.nan)
        if self.zeros == "remover_colesterol":
            X = X.drop(columns="Cholesterol")
        if self.oldpeak == "abs":
            X["Oldpeak"] = X["Oldpeak"].abs()
        elif self.oldpeak == "zero":
            X["Oldpeak"] = X["Oldpeak"].clip(lower=0)
        elif self.oldpeak != "manter":
            raise ValueError(f"oldpeak inválido: {self.oldpeak}")
        if self.zeros not in ("mediana", "mediana_flag", "remover_colesterol"):
            raise ValueError(f"zeros inválido: {self.zeros}")
        return X.drop(columns=[c for c in (self.drop_cols or []) if c in X.columns])

    def fit(self, X, y=None):
        L = self._limpar(X)
        self.medianas_ = L.select_dtypes("number").median()
        return self

    def transform(self, X):
        L = self._limpar(X)
        return L.fillna(self.medianas_)


def _num(df):
    return [c for c in NUMERICAS if c in df.columns]


def _bin(df):
    return [c for c in BINARIAS + ["Cholesterol_ausente"] if c in df.columns]


def _cat(df):
    return [c for c in CATEGORICAS if c in df.columns]


def _escalador(nome):
    return {"none": "passthrough", "standard": StandardScaler(), "standard_all": StandardScaler(),
            "minmax": MinMaxScaler(), "robust": RobustScaler()}[nome]


def _reducao(nome, semente):
    """none | pca_<n> (n inteiro ou fração da variância) | kbest_<n>"""
    if nome in (None, "none"):
        return "passthrough"
    tipo, n = str(nome).split("_")
    n = float(n) if "." in n else int(n)
    if tipo == "pca":
        return PCA(n_components=n, random_state=semente)
    if tipo == "kbest":
        return SelectKBest(f_classif, k=n)
    raise ValueError(f"reducao inválida: {nome}")


class WardPredict(BaseEstimator, ClusterMixin):
    """Hierárquico (Ward) com predict pelo centróide mais próximo."""

    def __init__(self, n_clusters=2):
        self.n_clusters = n_clusters

    def fit(self, X, y=None):
        X = np.asarray(X)
        self.labels_ = AgglomerativeClustering(n_clusters=self.n_clusters, linkage="ward").fit_predict(X)
        self.cluster_centers_ = np.vstack([X[self.labels_ == g].mean(0) for g in range(self.n_clusters)])
        return self

    def predict(self, X):
        d = ((np.asarray(X)[:, None, :] - self.cluster_centers_[None]) ** 2).sum(-1)
        return d.argmin(1)

    def fit_predict(self, X, y=None):
        return self.fit(X).labels_


def _modelo(m, semente):
    alg = m["algoritmo"]
    if alg == "kmeans":
        return KMeans(n_clusters=m["k"], init=m.get("init", "k-means++"),
                      n_init=m.get("n_init", 10), random_state=semente)
    if alg == "gmm":
        return GaussianMixture(n_components=m["k"], n_init=m.get("n_init", 10),
                               reg_covar=1e-4, random_state=semente)
    if alg == "ward":
        return WardPredict(n_clusters=m["k"])
    if alg == "dummy":
        return DummyClassifier(strategy="prior")
    if alg == "logreg":
        return LogisticRegression(max_iter=2000)
    if alg == "gboost":
        return GradientBoostingClassifier(random_state=semente)
    raise ValueError(f"algoritmo inválido: {alg}")


def construir(cfg, semente=0):
    pre, m = cfg["pre"], cfg["modelo"]
    esc = pre.get("scaler", "standard")
    num = _escalador(esc)
    if esc == "standard_all":
        num = "passthrough"  # padroniza tudo depois, no passo 'global'
    ct = ColumnTransformer([
        ("num", num, _num),
        ("bin", "passthrough", _bin),
        ("cat", OneHotEncoder(drop="if_binary", handle_unknown="ignore", sparse_output=False), _cat),
    ], verbose_feature_names_out=False)
    return Pipeline([
        ("dados", TratarDados(pre.get("zeros", "mediana"), pre.get("oldpeak", "manter"),
                              tuple(pre.get("drop_cols") or ()))),
        ("prep", ct),
        ("global", StandardScaler() if esc == "standard_all" else "passthrough"),
        ("red", _reducao(pre.get("reducao", "none"), semente)),
        ("modelo", _modelo(m, semente)),
    ])


def supervisionado(cfg):
    return cfg["modelo"]["algoritmo"] in SUPERVISIONADOS


def espaco(pipe, X):
    """Dados no espaço em que o agrupamento trabalha (após escala/redução)."""
    return np.asarray(pipe[:-1].transform(X), dtype=float)


def nomes_colunas(pipe):
    try:
        nomes = list(pipe.named_steps["prep"].get_feature_names_out())
    except Exception:
        return None
    red = pipe.named_steps["red"]
    if isinstance(red, SelectKBest):
        return [n for n, s in zip(nomes, red.get_support()) if s]
    if isinstance(red, PCA):
        return [f"PC{i + 1}" for i in range(red.n_components_)]
    return nomes


def centroides(modelo):
    if hasattr(modelo, "cluster_centers_"):
        return modelo.cluster_centers_
    if hasattr(modelo, "means_"):
        return modelo.means_
    return None


def resumo_cfg(cfg):
    """Campos curtos para as tabelas de resultado."""
    p, m = cfg["pre"], cfg["modelo"]
    return {"algoritmo": m["algoritmo"], "k": m.get("k"), "init": m.get("init"),
            "scaler": p.get("scaler"), "zeros": p.get("zeros"), "oldpeak": p.get("oldpeak"),
            "drop_cols": ",".join(p.get("drop_cols") or []) or "-", "reducao": p.get("reducao")}


def ajustar(cfg, X, y=None, semente=0):
    """Ajusta o pipeline nos dados recebidos e devolve (pipe, Z, rotulos)."""
    pipe = construir(cfg, semente)
    pipe.fit(X, y)
    Z = espaco(pipe, X)
    modelo = pipe.named_steps["modelo"]
    rot = modelo.labels_ if hasattr(modelo, "labels_") else modelo.predict(Z)
    return pipe, Z, np.asarray(rot).astype(int)
