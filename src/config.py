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

    Do vencedor só se herdam 'pre' e 'modelo'. 'sementes', 'dados' e 'decisao' vêm
    sempre do base.yaml, então mudar esses valores vale para todas as rodadas.
    """
    if herda_de in (None, "base"):
        return base()
    if str(herda_de).endswith((".yaml", ".yml")):
        arq = caminho(herda_de)
    else:
        arq = RESULTADOS / herda_de / "vencedor.yaml"
    if not arq.exists():
        raise FileNotFoundError(
            f"Não achei {arq.relative_to(RAIZ) if arq.is_relative_to(RAIZ) else arq}. Rode a rodada "
            f"'{herda_de}' antes (python -m src.runner configs/{herda_de}.yaml)."
        )
    v = ler_yaml(arq)
    if v.get("herda_de"):  # análise alternativa: parte de outra configuração e muda só o 'fixo'
        partida = config_herdada(v["herda_de"])
        return mesclar(partida, {k: v["fixo"][k] for k in ("pre", "modelo") if k in (v.get("fixo") or {})})
    return mesclar(base(), {k: v[k] for k in ("pre", "modelo") if k in v})


def config_final(arg="final"):
    """'final' = vencedor da R5b; ou o nome de uma rodada, ou um caminho de YAML
    (por exemplo, configs/alternativa_k4.yaml, que herda a final e muda o k)."""
    if arg in (None, "final"):
        return config_herdada("r05b_reajuste_k")
    return config_herdada(arg)


def pasta_analise(arg_config, nome, saida=None):
    """Pasta de saída das análises da configuração final (R6–R8).

    - configuração final           -> results/<nome>                 (ex.: results/r06_perfil)
    - --config configs/<alt>.yaml  -> results/<alt>/<nome>           (ex.: results/alternativa_k4/r06_perfil)
    - --saida <pasta>              -> <pasta>/<nome>
    Assim, uma análise alternativa nunca sobrescreve os resultados da configuração final.
    """
    if saida:
        raiz = caminho(saida)
    elif arg_config not in (None, "final") and str(arg_config).endswith((".yaml", ".yml")):
        raiz = RESULTADOS / Path(arg_config).stem
    else:
        raiz = RESULTADOS
    p = raiz / nome
    p.mkdir(parents=True, exist_ok=True)
    return p


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
