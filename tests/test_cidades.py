from src.errors import ApiError
from src.services import ibge_service


def _fake_municipios_ce(_sigla_uf):
    return [
        {"nome": "Abaiara", "codigo_ibge": "2300101"},
        {"nome": "Acarape", "codigo_ibge": "2300150"},
        {"nome": "Acaraú", "codigo_ibge": "2300200"},
    ]


def test_cidades_uf_valida_retorna_lista(client, monkeypatch):
    """Caso de sucesso: sigla de UF válida deve retornar a lista de cidades do estado."""
    monkeypatch.setattr(ibge_service, "listar_municipios", _fake_municipios_ce)

    resposta = client.get("/api/v1/cidades/CE?limite=2")

    assert resposta.status_code == 200
    corpo = resposta.get_json()
    assert corpo["uf"] == "CE"
    assert corpo["quantidade_retornada"] == 2
    assert corpo["cidades"] == [{"nome": "Abaiara"}, {"nome": "Acarape"}]
    assert "consultado_em" in corpo


def test_cidades_sigla_invalida_retorna_400(client):
    """Tratamento de erro: sigla que não tem exatamente 2 letras deve retornar 400."""
    resposta = client.get("/api/v1/cidades/ceara")

    assert resposta.status_code == 400
    corpo = resposta.get_json()
    assert corpo["erro"] is True
    assert corpo["codigo"] == "SIGLA_UF_INVALIDA"


def test_cidades_uf_nao_encontrada_retorna_404(client, monkeypatch):
    """Tratamento de erro: sigla bem formada mas de estado inexistente deve retornar 404."""

    def fake_levanta_nao_encontrada(sigla_uf):
        raise ApiError(
            status_code=404,
            codigo="UF_NAO_ENCONTRADA",
            mensagem="Estado com a sigla informada não foi encontrado",
            campos_extra={"sigla_uf_informada": sigla_uf},
        )

    monkeypatch.setattr(ibge_service, "listar_municipios", fake_levanta_nao_encontrada)

    resposta = client.get("/api/v1/cidades/XX")

    assert resposta.status_code == 404
    corpo = resposta.get_json()
    assert corpo["erro"] is True
    assert corpo["codigo"] == "UF_NAO_ENCONTRADA"
