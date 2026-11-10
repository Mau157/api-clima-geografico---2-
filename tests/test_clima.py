from src.errors import ApiError
from src.services import cptec_service


def _fake_busca_fortaleza(_nome_cidade):
    return [{"nome": "Fortaleza", "estado": "CE", "id": 64}]


def _fake_previsao_fortaleza(_codigo_cidade):
    return {
        "cidade": "Fortaleza",
        "estado": "CE",
        "atualizado_em": "2026-11-10",
        "clima": [
            {
                "data": "2026-11-10",
                "condicao": "pn",
                "min": 24,
                "max": 32,
                "indice_uv": 10,
                "condicao_desc": "Parcialmente Nublado",
            }
        ],
    }


def test_clima_cidade_valida_retorna_dados_combinados(client, monkeypatch):
    """Caso de sucesso: nome de cidade válido deve combinar dados geográficos e climáticos."""
    monkeypatch.setattr(cptec_service, "buscar_cidade", _fake_busca_fortaleza)
    monkeypatch.setattr(cptec_service, "obter_previsao", _fake_previsao_fortaleza)

    resposta = client.get("/api/v1/clima/Fortaleza")

    assert resposta.status_code == 200
    corpo = resposta.get_json()
    assert corpo["nome"] == "Fortaleza"
    assert corpo["estado"] == "CE"
    assert corpo["clima"]["temperatura_min"] == 24
    assert corpo["clima"]["temperatura_max"] == 32
    assert corpo["clima"]["condicao"] == "Parcialmente Nublado"
    assert corpo["clima"]["unidades"]["temperatura"] == "°C"
    assert "consultado_em" in corpo


def test_clima_cidade_nao_encontrada_retorna_404(client, monkeypatch):
    """Tratamento de erro: nome de cidade inexistente deve retornar 404 com código correto."""
    monkeypatch.setattr(cptec_service, "buscar_cidade", lambda _nome: [])

    resposta = client.get("/api/v1/clima/CidadeInexistente")

    assert resposta.status_code == 404
    corpo = resposta.get_json()
    assert corpo["erro"] is True
    assert corpo["codigo"] == "CIDADE_NAO_ENCONTRADA"
    assert corpo["nome_informado"] == "CidadeInexistente"


def test_clima_usa_proxima_candidata_quando_primeira_nao_tem_previsao(client, monkeypatch):
    """
    Robustez: se a busca por nome devolver mais de uma cidade e a primeira não
    tiver previsão disponível no CPTEC, a API deve tentar a próxima candidata
    em vez de falhar direto - importante para nomes de cidade comuns a mais
    de um município.
    """
    candidatas = [
        {"nome": "Santo André (povoado)", "estado": "PI", "id": 1},
        {"nome": "Santo André", "estado": "SP", "id": 2},
    ]
    monkeypatch.setattr(cptec_service, "buscar_cidade", lambda _nome: candidatas)

    def previsao_falha_ou_sucesso(codigo_cidade):
        if codigo_cidade == 1:
            raise ApiError(
                status_code=503,
                codigo="SERVICO_EXTERNO_INDISPONIVEL",
                mensagem="sem previsão cadastrada",
                campos_extra={"servico": "CPTEC"},
            )
        return {
            "cidade": "Santo André",
            "estado": "SP",
            "atualizado_em": "2026-11-10",
            "clima": [
                {
                    "data": "2026-11-10",
                    "condicao": "pn",
                    "min": 18,
                    "max": 26,
                    "indice_uv": 7,
                    "condicao_desc": "Parcialmente Nublado",
                }
            ],
        }

    monkeypatch.setattr(cptec_service, "obter_previsao", previsao_falha_ou_sucesso)

    resposta = client.get("/api/v1/clima/Santo%20Andre")

    assert resposta.status_code == 200
    corpo = resposta.get_json()
    assert corpo["nome"] == "Santo André"
    assert corpo["estado"] == "SP"


def test_clima_nome_muito_curto_retorna_400(client):
    """Tratamento de erro: nome com menos de 2 caracteres deve retornar 400."""
    resposta = client.get("/api/v1/clima/X")

    assert resposta.status_code == 400
    corpo = resposta.get_json()
    assert corpo["erro"] is True
    assert corpo["codigo"] == "NOME_INVALIDO"
