"""
Ponto de entrada para executar a API localmente.

Uso:
    python run.py

A API ficará disponível em http://localhost:3000
"""
from src.app import app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=False)
