"""
Exceção padronizada usada em toda a aplicação para representar erros de
negócio (validação, recurso não encontrado, serviço externo indisponível).

Centralizar o formato do erro aqui garante que toda resposta de erro da API
siga exatamente o mesmo formato JSON, conforme exigido na especificação:

    {
        "erro": true,
        "codigo": "ALGUM_CODIGO",
        "mensagem": "Descrição legível do erro",
        ... campos extras específicos do erro ...
    }
"""
from __future__ import annotations

from typing import Any


class ApiError(Exception):
    """Erro de negócio conhecido, convertido em resposta HTTP pelo error handler do Flask."""

    def __init__(
        self,
        status_code: int,
        codigo: str,
        mensagem: str,
        campos_extra: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(mensagem)
        self.status_code = status_code
        self.codigo = codigo
        self.mensagem = mensagem
        self.campos_extra = campos_extra or {}

    def to_dict(self) -> dict[str, Any]:
        corpo: dict[str, Any] = {
            "erro": True,
            "codigo": self.codigo,
            "mensagem": self.mensagem,
        }
        corpo.update(self.campos_extra)
        return corpo
