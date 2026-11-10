# API de Agregação de Dados Climáticos e Geográficos

Atividade da disciplina **Técnicas de Integração de Sistemas (N703)**.

API REST que recebe apenas o **nome de uma cidade brasileira** (ou a **sigla
de um estado**) e devolve dados geográficos e climáticos combinados,
resolvendo toda a identificação da localidade e suas coordenadas de forma
**dinâmica**, consumindo APIs públicas — nenhuma coordenada é fixada no
código.

## Para quem vai avaliar (checklist rápido)

Pré-requisitos: Python 3.11+ e acesso à internet (a API consulta a Brasil API em tempo real, não há dados simulados em produção).

```bash
git clone <url-do-repositorio>
cd <pasta-do-repositorio>
python3 -m venv venv && source venv/bin/activate     # Windows: venv\Scripts\activate
pip install -r requirements.txt
python run.py          # deixa rodando em http://localhost:3000
```

Em outro terminal (ou colando os links no navegador, já que são todos `GET`):

| # | Critério da proposta | Requisição | Esperado |
|---|---|---|---|
| 1 | Health check | `curl http://localhost:3000/api/v1/health` | `200`, JSON com `status` |
| 2 | Clima — sucesso | `curl http://localhost:3000/api/v1/clima/Fortaleza` | `200`, JSON com dados geográficos + clima |
| 3 | Clima — cidade não encontrada | `curl -i http://localhost:3000/api/v1/clima/CidadeInexistenteXYZ` | `404`, `codigo: CIDADE_NAO_ENCONTRADA` |
| 4 | Clima — nome inválido | `curl -i http://localhost:3000/api/v1/clima/X` | `400`, `codigo: NOME_INVALIDO` |
| 5 | Cidades por estado — sucesso | `curl "http://localhost:3000/api/v1/cidades/CE?limite=5"` | `200`, lista com 5 cidades |
| 6 | Cidades por estado — UF não encontrada | `curl -i http://localhost:3000/api/v1/cidades/XX` | `404`, `codigo: UF_NAO_ENCONTRADA` |
| 7 | Cidades por estado — sigla inválida | `curl -i http://localhost:3000/api/v1/cidades/ceara` | `400`, `codigo: SIGLA_UF_INVALIDA` |
| 8 | `INTEGRANTES.md` | abrir o arquivo na raiz do repositório | tabela preenchida com nome e matrícula reais |
| 9 | Coleção Postman | abrir `docs/postman_collection.json` no Postman (Import) | 7 requisições, com testes automáticos embutidos |

Também é possível rodar `pytest -v` na raiz do projeto para ver a suíte de 9 testes automatizados passando (cobre os caminhos de sucesso e os erros 400/404 dos dois endpoints de dados, além do health check).

## Sumário

- [Arquitetura e decisões técnicas](#arquitetura-e-decisões-técnicas)
- [Estrutura do repositório](#estrutura-do-repositório)
- [Pré-requisitos](#pré-requisitos)
- [Como executar localmente](#como-executar-localmente)
- [Endpoints](#endpoints)
- [Testes automatizados](#testes-automatizados)
- [Coleção Postman](#coleção-postman)
- [Decisões e limitações conhecidas](#decisões-e-limitações-conhecidas)
- [Uso de IA generativa](#uso-de-ia-generativa)
- [Integrantes](#integrantes)
- [Referências](#referências)

## Arquitetura e decisões técnicas

| Camada | Tecnologia |
|---|---|
| Linguagem / Framework | Python 3.11+ / Flask |
| Cliente HTTP | `requests` |
| Testes | `pytest` (com mocks das APIs externas) |
| CORS | `flask-cors` |

**APIs públicas utilizadas:**

| API | Uso neste projeto |
|---|---|
| [Brasil API — CPTEC](https://brasilapi.com.br/docs#tag/CPTEC) | Busca da cidade pelo nome (`/cptec/v1/cidade/{nome}`) e previsão do tempo (`/cptec/v1/clima/previsao/{codigo}`) |
| [Brasil API — IBGE](https://brasilapi.com.br/docs#tag/IBGE) | Listagem de municípios de um estado (`/ibge/municipios/v1/{uf}`) e verificação de disponibilidade no health check (`/ibge/uf/v1`) |

**Fluxo do endpoint de clima** (`GET /api/v1/clima/{nome_cidade}`):

1. O nome da cidade informado é validado (mínimo 2 caracteres).
2. A aplicação consulta o CPTEC por esse nome e obtém o nome oficial, o
   estado (UF) e o **código interno do CPTEC** da cidade — nenhuma
   coordenada é digitada ou fixada no código; a resolução é sempre feita em
   tempo de execução.
3. Com esse código, a aplicação busca a previsão do tempo do dia atual
   (temperatura mínima, máxima e condição).
4. Os dois resultados são combinados em uma única resposta JSON padronizada.

> Optamos por resolver o fluxo inteiramente com Brasil API (CPTEC + IBGE) em
> vez de combinar IBGE + Open-Meteo. Isso evita uma etapa extra de geocoding
> para obter latitude/longitude, já que o próprio CPTEC aceita busca por
> nome de cidade e devolve estado e previsão do tempo a partir do mesmo
> código interno. A proposta permite essa escolha (ver seção 4 da atividade).

## Estrutura do repositório

```
.
├── README.md                     # este arquivo
├── INTEGRANTES.md                # dados da equipe
├── requirements.txt
├── pytest.ini
├── run.py                        # ponto de entrada (python run.py)
├── src/
│   ├── app.py                    # rotas Flask
│   ├── errors.py                 # exceção padronizada de erro da API
│   ├── services/
│   │   ├── cptec_service.py      # integração com Brasil API - CPTEC
│   │   └── ibge_service.py       # integração com Brasil API - IBGE
│   └── utils/
│       └── validators.py         # validação de entrada
├── tests/
│   ├── test_health.py
│   ├── test_clima.py
│   └── test_cidades.py
└── docs/
    └── postman_collection.json
```

## Pré-requisitos

- Python 3.11 ou superior
- `pip`

## Como executar localmente

```bash
# 1. Clonar o repositório
git clone <url-do-repositorio>
cd <pasta-do-repositorio>

# 2. Criar e ativar um ambiente virtual (recomendado)
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Instalar as dependências
pip install -r requirements.txt

# 4. Rodar a aplicação
python run.py
```

A API sobe em `http://localhost:3000`.

## Endpoints

Todas as respostas são em **JSON**, codificação **UTF-8**, e o CORS está
habilitado para testes via navegador.

### `GET /api/v1/health`

**Sucesso (200):**

```json
{
  "status": "healthy",
  "versao": "1.0.0",
  "timestamp": "2025-03-15T14:30:00Z"
}
```

**Degradado (200), quando a Brasil API está inacessível:**

```json
{
  "status": "degraded",
  "versao": "1.0.0",
  "timestamp": "2025-03-15T14:30:00Z",
  "motivo": "Serviço externo indisponível"
}
```

### `GET /api/v1/clima/{nome_cidade}`

| Parâmetro | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `nome_cidade` | string | Sim | Nome da cidade (pode ser parcial) |

Exemplo: `GET /api/v1/clima/Fortaleza`

**Sucesso (200):**

```json
{
  "nome": "Fortaleza",
  "estado": "CE",
  "clima": {
    "temperatura_min": 24,
    "temperatura_max": 32,
    "condicao": "Parcialmente Nublado",
    "unidades": { "temperatura": "°C" }
  },
  "consultado_em": "2025-03-15T14:30:00Z"
}
```

**Erros:**

| Cenário | HTTP | `codigo` |
|---|---|---|
| Cidade não encontrada | 404 | `CIDADE_NAO_ENCONTRADA` |
| Nome com menos de 2 caracteres | 400 | `NOME_INVALIDO` |
| Falha na API externa | 503 | `SERVICO_EXTERNO_INDISPONIVEL` |

### `GET /api/v1/cidades/{sigla_uf}`

| Parâmetro | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `sigla_uf` | string | Sim | Sigla do estado (2 caracteres) |

| Query param | Tipo | Default | Descrição |
|---|---|---|---|
| `limite` | integer | 10 | Quantidade máxima de cidades (1–100) |

Exemplo: `GET /api/v1/cidades/CE?limite=5`

**Sucesso (200):**

```json
{
  "uf": "CE",
  "quantidade_retornada": 5,
  "cidades": [
    { "nome": "Abaiara" },
    { "nome": "Acarape" },
    { "nome": "Acaraú" },
    { "nome": "Acopiara" },
    { "nome": "Aiuaba" }
  ],
  "consultado_em": "2025-03-15T14:30:00Z"
}
```

**Erros:**

| Cenário | HTTP | `codigo` |
|---|---|---|
| UF não encontrada (ex.: `XX`) | 404 | `UF_NAO_ENCONTRADA` |
| Sigla com formato inválido (ex.: `ceara`) | 400 | `SIGLA_UF_INVALIDA` |
| Falha na API externa | 503 | `SERVICO_EXTERNO_INDISPONIVEL` |

## Testes automatizados

```bash
pytest -v
```

A suíte cobre os três endpoints, incluindo os caminhos de sucesso e os
principais cenários de erro (cidade/UF não encontrada, entrada inválida). As
chamadas às APIs externas são simuladas (`monkeypatch`) para que os testes
sejam rápidos e não dependam de rede.

## Coleção Postman

Importe `docs/postman_collection.json` no Postman. A variável de coleção
`base_url` já aponta para `http://localhost:3000`; basta a API estar rodando
localmente (`python run.py`) para executar as requisições.

## Decisões e limitações conhecidas

- Quando a busca por nome de cidade no CPTEC retorna mais de um resultado
  (nomes de cidade duplicados em estados diferentes, ou povoados pequenos sem
  previsão cadastrada), a aplicação **não trava na primeira opção**: ela
  tenta, em ordem, até 5 das cidades retornadas pela busca e usa a primeira
  que tiver previsão do tempo disponível. Isso torna a busca confiável para
  nomes de cidade "do dia a dia" digitados por qualquer pessoa, não só para
  os exemplos de capitais usados nos testes.
- A busca de nome em si (aceitar nome parcial, sem acento, minúsculo etc.) é
  responsabilidade do próprio endpoint de busca do CPTEC na Brasil API; a
  aplicação não reimplementa correção ortográfica por cima disso.
- O endpoint `/api/v1/cidades/{sigla_uf}` trata respostas `400`, `404` e
  `200` com lista vazia da Brasil API — IBGE como "UF não encontrada", pois
  o comportamento da API externa para UFs inexistentes não é 100%
  consistente entre esses três casos.
- O `health check` faz uma checagem real (com timeout curto) contra a Brasil
  API — IBGE para decidir entre `healthy` e `degraded`.

## Uso de IA generativa

> **Equipe: revisem e ajustem esta seção para refletir com exatidão o que
> vocês efetivamente fizeram antes de enviar a atividade.** Declarar o uso
> de forma incompleta ou incorreta está sujeito às mesmas penalidades do
> uso não declarado.

Sim, a equipe utilizou uma ferramenta de IA generativa (**Claude, da
Anthropic**) durante o desenvolvimento desta atividade, da seguinte forma:

- **Leitura e interpretação da proposta:** o documento
  `N703_Proposta_de_Trabalho_2026_2.docx` foi fornecido à ferramenta para
  extrair os requisitos técnicos (estrutura de pastas, contratos dos três
  endpoints, formatos de erro, critérios de avaliação).
- **Implementação:** a ferramenta gerou a estrutura inicial do projeto, o
  código-fonte dos três endpoints (`src/`), os serviços de integração com a
  Brasil API (CPTEC e IBGE), as validações de entrada e o tratamento de
  erros.
- **Testes:** a ferramenta gerou a suíte de testes automatizados em
  `tests/` (casos de sucesso e de erro para os três endpoints).
- **Documentação:** este `README.md` e a coleção Postman
  (`docs/postman_collection.json`) também foram gerados com apoio da
  ferramenta, a partir da especificação da atividade.
- A pesquisa dos formatos reais de resposta das APIs da Brasil API
  (CPTEC e IBGE) foi feita pela ferramenta via busca na web, já que esses
  detalhes não estavam na proposta da atividade.
- Em uma segunda rodada, a ferramenta também adicionou uma lógica de
  retentativa no endpoint de clima (para cidades com nomes repetidos ou sem
  previsão cadastrada) e a seção "Para quem vai avaliar" deste README, a
  pedido da equipe.

**[A equipe deve completar aqui]:** quais partes do código foram revisadas,
testadas manualmente e compreendidas por cada integrante; se houve ajustes
manuais feitos pela equipe após a geração; e qualquer outra forma de uso de
IA (ex.: dúvidas pontuais, revisão de texto, etc.).

## Integrantes

Ver [`INTEGRANTES.md`](./INTEGRANTES.md).

## Referências

- [Brasil API — IBGE](https://brasilapi.com.br/docs#tag/IBGE)
- [Brasil API — CPTEC](https://brasilapi.com.br/docs#tag/CPTEC)
- [IBGE Localidades](https://servicodados.ibge.gov.br/api/docs/localidades)
- [Open-Meteo](https://open-meteo.com/en/docs)
- [Postman Learning Center](https://learning.postman.com/docs/)
