"""Leitura da base Heart Failure Prediction.

Todas as rodadas usam a base inteira (918 pacientes): o K-Means não usa o
diagnóstico para agrupar, então não há divisão treino/teste. A pergunta
"os grupos se repetem em pacientes novos?" é respondida pela R8
(validação cruzada 5x5, src/generalizacao.py).

Cada paciente tem um 'id' = número da linha no data/raw/heart.csv (começando em 0).
Os arquivos em data/split/ são os do SVM-Infarto, guardados só como referência.
"""
import pandas as pd

from .config import RAIZ

NUMERICAS = ["Age", "RestingBP", "Cholesterol", "MaxHR", "Oldpeak"]
BINARIAS = ["FastingBS"]
CATEGORICAS = ["Sex", "ChestPainType", "RestingECG", "ExerciseAngina", "ST_Slope"]
ALVO = "HeartDisease"
COLUNAS = NUMERICAS + BINARIAS + CATEGORICAS

RAW_CSV = RAIZ / "data" / "raw" / "heart.csv"


def carregar_base():
    """Base inteira, sem duplicatas, com a coluna 'id'."""
    if not RAW_CSV.exists():
        raise FileNotFoundError(f"Não achei {RAW_CSV}. Copie o heart.csv do Kaggle para data/raw/.")
    df = pd.read_csv(RAW_CSV)
    faltando = [c for c in COLUNAS + [ALVO] if c not in df.columns]
    if faltando:
        raise ValueError(f"Colunas ausentes no heart.csv: {faltando}")
    df = df[COLUNAS + [ALVO]].copy()
    df.insert(0, "id", range(len(df)))
    df = df.drop_duplicates(subset=COLUNAS + [ALVO]).reset_index(drop=True)
    return df


def colesterol_ausente(df):
    """1 = colesterol registrado como 0 (valor ausente na prática)."""
    return (df["Cholesterol"] == 0).astype(int)


def separar(df):
    """(X, y, ausente, ids)"""
    return df[COLUNAS].copy(), df[ALVO].to_numpy(), colesterol_ausente(df).to_numpy(), df["id"].to_numpy()
