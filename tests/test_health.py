from src.services import ibge_service


def test_health_retorna_200_e_status_healthy(client, monkeypatch):
    """Quando o serviço externo responde normalmente, o status deve ser 'healthy'."""
    monkeypatch.setattr(ibge_service, "verificar_disponibilidade", lambda: None)

    resposta = client.get("/api/v1/health")

    assert resposta.status_code == 200
    corpo = resposta.get_json()
    assert corpo["status"] == "healthy"
    assert corpo["versao"] == "1.0.0"
    assert "timestamp" in corpo


def test_health_retorna_degraded_quando_servico_externo_falha(client, monkeypatch):
    """Quando o serviço externo está fora do ar, o health check deve indicar 'degraded'."""

    def falha(*_args, **_kwargs):
        raise ConnectionError("serviço externo indisponível")

    monkeypatch.setattr(ibge_service, "verificar_disponibilidade", falha)

    resposta = client.get("/api/v1/health")

    assert resposta.status_code == 200
    corpo = resposta.get_json()
    assert corpo["status"] == "degraded"
    assert "motivo" in corpo
