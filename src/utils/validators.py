"""Validações de entrada dos endpoints, isoladas dos handlers do Flask."""
from __future__ import annotations

import re

from src.errors import ApiError

_PADRAO_SIGLA_UF = re.compile(r"^[A-Za-z]{2}$")
_TAMANHO_MINIMO_NOME_CIDADE = 2


def validar_nome_cidade(nome_cidade: str) -> str:
    """Garante que o nome da cidade tenha pelo menos 2 caracteres (após remover espaços)."""
    nome = (nome_cidade or "").strip()
    if len(nome) < _TAMANHO_MINIMO_NOME_CIDADE:
        raise ApiError(
            status_code=400,
            codigo="NOME_INVALIDO",
            mensagem="O nome da cidade deve conter pelo menos 2 caracteres",
            campos_extra={"nome_informado": nome_cidade},
        )
    return nome


def validar_sigla_uf(sigla_uf: str) -> str:
    """Garante que a sigla da UF tenha exatamente 2 letras (ex.: CE, SP, RJ)."""
    if not _PADRAO_SIGLA_UF.match(sigla_uf or ""):
        raise ApiError(
            status_code=400,
            codigo="SIGLA_UF_INVALIDA",
            mensagem="A sigla do estado deve conter exatamente 2 letras",
            campos_extra={"sigla_uf_informada": sigla_uf},
        )
    return sigla_uf.upper()
