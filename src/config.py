"""Leitura dos YAML das rodadas, com herança e expansão das opções."""
import copy
import itertools
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[1]
CONFIGS = RAIZ / "configs"
RESULTADOS = RAIZ / "results"


def caminho(p):
    p = Path(p)
    return p if p.is_absolute() else RAIZ / p


def ler_yaml(p):
    with open(caminho(p), encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def mesclar(a, b):
    """Mescla b sobre a (recursivo para dicionários)."""
    out = copy.deepcopy(a)
    for k, v in (b or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = mesclar(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


def definir(cfg, chave, valor):
    """definir(cfg, 'modelo.k', 3) -> cfg['modelo']['k'] = 3"""
    partes = chave.split(".")
    alvo = cfg
    for p in partes[:-1]:
        alvo = alvo.setdefault(p, {})
    alvo[partes[-1]] = copy.deepcopy(valor)


def obter(cfg, chave, padrao=None):
    alvo = cfg
    for p in chave.split("."):
        if not isinstance(alvo, dict) or p not in alvo:
            return padrao
        alvo = alvo[p]
    return alvo


def base():
    return ler_yaml(CONFIGS / "base.yaml")


def pasta_rodada(nome_yaml):
    """configs/r01_escalonamento.yaml -> results/r01_escalonamento"""
    return RESULTADOS / Path(nome_yaml).stem


def config_herdada(herda_de):
    """Configuração de partida de uma rodada.

    - 'base'                -> configs/base.yaml
    - 'r01_escalonamento'   -> results/r01_escalonamento/vencedor.yaml
    - caminho para um .yaml -> o próprio arquivo (mesclado sobre a base)
    """
    if herda_de in (None, "base"):
        return base()
    if str(herda_de).endswith((".yaml", ".yml")):
        return mesclar(base(), ler_yaml(herda_de))
    arq = RESULTADOS / herda_de / "vencedor.yaml"
    if not arq.exists():
        raise FileNotFoundError(
            f"Não achei {arq.relative_to(RAIZ)}. Rode a rodada '{herda_de}' antes "
            f"(python -m src.runner configs/{herda_de}.yaml)."
        )
    return mesclar(base(), ler_yaml(arq))


def config_final(arg="final"):
    """'final' = vencedor da R5b; ou o nome de uma rodada, ou um caminho de YAML."""
    if arg in (None, "final"):
        return config_herdada("r05b_reajuste_k")
    return config_herdada(arg)


def carregar_rodada(arq_yaml):
    """Lê o YAML da rodada e devolve (rodada, lista de opções).

    Cada opção é um dict com: nome, cfg (configuração completa), meta.
    """
    rod = ler_yaml(arq_yaml)
    rod["_arquivo"] = str(arq_yaml)
    partida = config_herdada(rod.get("herda_de", "base"))
    partida = mesclar(partida, rod.get("fixo"))
    rod["_partida"] = partida

    opcoes = []
    for op in rod.get("opcoes", []) or []:
        op = copy.deepcopy(op)
        nome = op.pop("nome")
        meta = {
            "fora_da_disputa": bool(op.pop("fora_da_disputa", False)),
            "supervisionado": bool(op.pop("supervisionado", False)),
        }
        cfg = mesclar(partida, op)
        opcoes.append({"nome": nome, "cfg": cfg, "meta": meta})

    grade = rod.get("grade")
    if grade:
        chaves = list(grade)
        for valores in itertools.product(*(grade[c] for c in chaves)):
            cfg = copy.deepcopy(partida)
            partes = []
            for c, v in zip(chaves, valores):
                definir(cfg, c, v)
                partes.append(f"{c.split('.')[-1]}={v}")
            opcoes.append({"nome": " ".join(partes), "cfg": cfg,
                           "meta": {"fora_da_disputa": False, "supervisionado": False}})

    abl = rod.get("ablacao")
    if abl:
        # retiradas primeiro: no empate vence a versão com menos componentes
        ref = base()
        for nome, chaves in abl.items():
            cfg = copy.deepcopy(partida)
            mudou = False
            for c in chaves:
                if obter(cfg, c) != obter(ref, c):
                    definir(cfg, c, obter(ref, c))
                    mudou = True
            if not mudou:
                print(f"[ablação] '{nome}': o vencedor já usa o valor da base; opção ignorada.")
                continue
            opcoes.append({"nome": nome, "cfg": cfg,
                           "meta": {"fora_da_disputa": False, "supervisionado": False}})
        for k in rod.get("reajustar_k", [obter(partida, "modelo.k")]):
            cfg = copy.deepcopy(partida)
            definir(cfg, "modelo.k", k)
            opcoes.append({"nome": f"completa k={k}", "cfg": cfg,
                           "meta": {"fora_da_disputa": False, "supervisionado": False}})

    if not opcoes:
        raise ValueError(f"{arq_yaml}: nenhuma opção definida (use 'opcoes', 'grade' ou 'ablacao').")
    return rod, opcoes


def salvar_yaml(obj, arq):
    arq = caminho(arq)
    arq.parent.mkdir(parents=True, exist_ok=True)
    with open(arq, "w", encoding="utf-8") as f:
        yaml.safe_dump(obj, f, allow_unicode=True, sort_keys=False)
