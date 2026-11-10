"""
Integração com a Brasil API - IBGE (https://brasilapi.com.br/docs#tag/IBGE).

Usada para listar os municípios de um estado brasileiro a partir da sigla (UF).

Endpoint utilizado:
  GET /api/ibge/municipios/v1/{uf} -> lista de municípios [{"nome", "codigo_ibge"}, ...]

Observação sobre o comportamento da API para uma UF inexistente: em testes
manuais e relatos da comunidade, esse endpoint ora responde 400, ora 404, e em
alguns casos responde 200 com uma lista vazia. Por isso tratamos todos esses
três casos como "UF não encontrada" (ver `listar_municipios` abaixo), em vez
de confiar em um único status HTTP.
"""
from __future__ import annotations

from typing import Any

import requests

from src.errors import ApiError

BASE_URL = "https://brasilapi.com.br/api/ibge"
TIMEOUT_SEGUNDOS = 8
TIMEOUT_HEALTH_CHECK_SEGUNDOS = 3
NOME_SERVICO = "IBGE"


def _erro_servico_indisponivel() -> ApiError:
    return ApiError(
        status_code=503,
        codigo="SERVICO_EXTERNO_INDISPONIVEL",
        mensagem="Não foi possível obter dados do serviço externo. Tente novamente em alguns instantes",
        campos_extra={"servico": NOME_SERVICO},
    )


def _erro_uf_nao_encontrada(sigla_uf: str) -> ApiError:
    return ApiError(
        status_code=404,
        codigo="UF_NAO_ENCONTRADA",
        mensagem="Estado com a sigla informada não foi encontrado",
        campos_extra={"sigla_uf_informada": sigla_uf},
    )


def listar_municipios(sigla_uf: str) -> list[dict[str, Any]]:
    """Lista os municípios (nome + código IBGE) de um estado a partir da sigla (UF)."""
    try:
        resposta = requests.get(f"{BASE_URL}/municipios/v1/{sigla_uf}", timeout=TIMEOUT_SEGUNDOS)
    except requests.RequestException as exc:
        raise _erro_servico_indisponivel() from exc

    if resposta.status_code in (400, 404):
        raise _erro_uf_nao_encontrada(sigla_uf)

    if not resposta.ok:
        raise _erro_servico_indisponivel()

    try:
        dados = resposta.json()
    except ValueError as exc:
        raise _erro_servico_indisponivel() from exc

    if not dados:
        raise _erro_uf_nao_encontrada(sigla_uf)

    return dados


def verificar_disponibilidade() -> None:
    """
    Usada apenas pelo /api/v1/health para saber se a BrasilAPI está no ar.
    Levanta uma exceção se a chamada falhar; quem chama decide o que fazer.
    """
    resposta = requests.get(f"{BASE_URL}/uf/v1", timeout=TIMEOUT_HEALTH_CHECK_SEGUNDOS)
    resposta.raise_for_status()
