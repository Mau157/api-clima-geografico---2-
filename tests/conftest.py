import pytest

from src.app import criar_app


@pytest.fixture
def client():
    """Cliente de teste do Flask. Cada teste recebe uma instância nova da app."""
    app = criar_app()
    app.config.update(TESTING=True)
    with app.test_client() as test_client:
        yield test_client
