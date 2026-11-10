"""
API de Agregação de Dados Climáticos e Geográficos
Disciplina: Técnicas de Integração de Sistemas (N703)

O usuário informa apenas o NOME de uma cidade (ou a SIGLA de um estado);
toda a resolução de identidade geográfica e coordenadas é feita
dinamicamente chamando APIs públicas — nenhuma coordenada é fixada no
código, conforme exigido na proposta da atividade.
"""
from __future__ import annotations

from datetime import datetime, timezone

from flask import Flask, jsonify, request
from flask_cors import CORS

from src.errors import ApiError
from src.services import cptec_service, ibge_service
from src.utils.validators import validar_nome_cidade, validar_sigla_uf

VERSAO_API = "1.0.0"
LIMITE_PADRAO = 10
LIMITE_MINIMO = 1
LIMITE_MAXIMO = 100
MAX_CANDIDATOS_CIDADE = 5


def _agora_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def criar_app() -> Flask:
    app = Flask(__name__)
    CORS(app)  # Requisito: CORS habilitado para testes via navegador.

    # ---- Tratamento centralizado de erros ---------------------------------

    @app.errorhandler(ApiError)
    def tratar_erro_api(erro: ApiError):
        return jsonify(erro.to_dict()), erro.status_code

    @app.errorhandler(404)
    def tratar_rota_nao_encontrada(_erro):
        return (
            jsonify(
                {
                    "erro": True,
                    "codigo": "ROTA_NAO_ENCONTRADA",
                    "mensagem": "A rota solicitada não existe nesta API.",
                }
            ),
            404,
        )

    # ---- Endpoint 3: Health Check ------------------------------------------

    @app.get("/api/v1/health")
    def health():
        status = "healthy"
        motivo = None
        try:
            ibge_service.verificar_disponibilidade()
        except Exception:  # noqa: BLE001 - qualquer falha externa só rebaixa o status
            status = "degraded"
            motivo = "Serviço externo indisponível"

        corpo = {
            "status": status,
            "versao": VERSAO_API,
            "timestamp": _agora_iso(),
        }
        if motivo:
            corpo["motivo"] = motivo

        return jsonify(corpo), 200

    # ---- Endpoint 1: Informações da cidade com clima -----------------------

    @app.get("/api/v1/clima/<nome_cidade>")
    def clima(nome_cidade: str):
        nome_cidade = validar_nome_cidade(nome_cidade)

        cidades_encontradas = cptec_service.buscar_cidade(nome_cidade)
        if not cidades_encontradas:
            raise ApiError(
                status_code=404,
                codigo="CIDADE_NAO_ENCONTRADA",
                mensagem="Nenhuma cidade encontrada com o nome informado",
                campos_extra={"nome_informado": nome_cidade},
            )

        # A busca por nome pode devolver mais de uma cidade (nomes repetidos
        # em estados diferentes, povoados pequenos sem previsão cadastrada
        # etc.). Em vez de depender só da primeira, tentamos algumas
        # candidatas em ordem até achar uma com previsão disponível — isso
        # deixa a busca confiável para qualquer nome de cidade digitado, não
        # só para os exemplos usados nos testes.
        ultimo_erro: ApiError | None = None
        for cidade in cidades_encontradas[:MAX_CANDIDATOS_CIDADE]:
            try:
                previsao = cptec_service.obter_previsao(cidade["id"])
            except ApiError as erro:
                ultimo_erro = erro
                continue

            clima_hoje = previsao["clima"][0]
            return (
                jsonify(
                    {
                        "nome": cidade["nome"],
                        "estado": cidade["estado"],
                        "clima": {
                            "temperatura_min": clima_hoje["min"],
                            "temperatura_max": clima_hoje["max"],
                            "condicao": clima_hoje.get("condicao_desc") or clima_hoje.get("condicao"),
                            "unidades": {"temperatura": "°C"},
                        },
                        "consultado_em": _agora_iso(),
                    }
                ),
                200,
            )

        # Nenhuma das cidades candidatas teve previsão disponível.
        raise ultimo_erro or ApiError(
            status_code=503,
            codigo="SERVICO_EXTERNO_INDISPONIVEL",
            mensagem="Não foi possível obter dados do serviço externo. Tente novamente em alguns instantes",
            campos_extra={"servico": "CPTEC"},
        )

    # ---- Endpoint 2: Listagem de cidades por estado -------------------------

    @app.get("/api/v1/cidades/<sigla_uf>")
    def cidades_por_estado(sigla_uf: str):
        sigla_uf = validar_sigla_uf(sigla_uf)

        limite = request.args.get("limite", default=LIMITE_PADRAO, type=int)
        if limite is None:
            limite = LIMITE_PADRAO
        limite = max(LIMITE_MINIMO, min(LIMITE_MAXIMO, limite))

        municipios = ibge_service.listar_municipios(sigla_uf)
        cidades = [{"nome": municipio["nome"]} for municipio in municipios[:limite]]

        return (
            jsonify(
                {
                    "uf": sigla_uf,
                    "quantidade_retornada": len(cidades),
                    "cidades": cidades,
                    "consultado_em": _agora_iso(),
                }
            ),
            200,
        )

    return app


app = criar_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=False)
