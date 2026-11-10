"""
Integração com a Brasil API - CPTEC (https://brasilapi.com.br/docs#tag/CPTEC).

Usada para duas coisas:
  1. Encontrar o código de cidade do CPTEC a partir do NOME digitado pelo
     usuário (sem usar nenhuma coordenada fixa no código).
  2. Buscar a previsão do tempo (temperatura mínima/máxima e condição) a
     partir desse código de cidade.

Endpoints utilizados:
  GET /api/cptec/v1/cidade/{nome}            -> lista de cidades que combinam com o nome
  GET /api/cptec/v1/clima/previsao/{codigo}  -> previsão do tempo (dia atual + próximos dias)
"""
from __future__ import annotations

from typing import Any

import requests

from src.errors import ApiError

BASE_URL = "https://brasilapi.com.br/api/cptec/v1"
TIMEOUT_SEGUNDOS = 8
NOME_SERVICO = "CPTEC"


def _erro_servico_indisponivel() -> ApiError:
    return ApiError(
        status_code=503,
        codigo="SERVICO_EXTERNO_INDISPONIVEL",
        mensagem="Não foi possível obter dados do serviço externo. Tente novamente em alguns instantes",
        campos_extra={"servico": NOME_SERVICO},
    )


def buscar_cidade(nome_cidade: str) -> list[dict[str, Any]]:
    """
    Busca cidades no CPTEC pelo nome (aceita nome parcial).

    Retorna uma lista (pode ser vazia, o que significa "nenhuma cidade
    encontrada") de dicionários no formato {"nome": ..., "estado": ..., "id": ...}.
    """
    try:
        resposta = requests.get(f"{BASE_URL}/cidade/{nome_cidade}", timeout=TIMEOUT_SEGUNDOS)
    except requests.RequestException as exc:
        raise _erro_servico_indisponivel() from exc

    # A Brasil API responde 404 quando nenhuma cidade combina com o nome.
    if resposta.status_code == 404:
        return []

    if not resposta.ok:
        raise _erro_servico_indisponivel()

    try:
        return resposta.json()
    except ValueError as exc:
        raise _erro_servico_indisponivel() from exc


def obter_previsao(codigo_cidade: int | str) -> dict[str, Any]:
    """
    Busca a previsão do tempo para um código de cidade do CPTEC.

    Retorna o dicionário completo {"cidade", "estado", "atualizado_em", "clima": [...]}.
    """
    try:
        resposta = requests.get(
            f"{BASE_URL}/clima/previsao/{codigo_cidade}", timeout=TIMEOUT_SEGUNDOS
        )
    except requests.RequestException as exc:
        raise _erro_servico_indisponivel() from exc

    if not resposta.ok:
        raise _erro_servico_indisponivel()

    try:
        dados = resposta.json()
    except ValueError as exc:
        raise _erro_servico_indisponivel() from exc

    if not dados.get("clima"):
        # Cidade existe, mas o CPTEC não retornou previsão para ela.
        raise _erro_servico_indisponivel()

    return dados
