# AI Operations Agent

API de indicadores de um marketplace fictício, com FastAPI, PostgreSQL e um agente Gemini. Os dados de pedidos são sintéticos. O frontend React/Vite contém a tela inicial do projeto.

## Backend

Com Python 3.12, execute na raiz do repositório no PowerShell.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m uvicorn app.main:app
```

A documentação interativa está em http://127.0.0.1:8000/docs. As rotas de saúde e de métricas do CSV funcionam com os arquivos do repositório.

## PostgreSQL e Gemini

Para uma instalação nova, crie um banco PostgreSQL e execute o arquivo `etl/schema.sql` nele. Copie `.env.example` para `.env` se ainda não existir e preencha as configurações do banco e a chave do Gemini localmente.

Para carregar a base sintética em um banco destinado a esses dados, rode `.\.venv\Scripts\python.exe -m etl.load_orders`. A carga insere ou atualiza pedidos pelo ID. As rotas `/metrics/database` consultam o PostgreSQL. A rota `POST /agent/chat` recebe um objeto JSON com o campo `message`.

## Frontend

Na pasta `frontend`, use uma versão do Node compatível com o Vite registrado no arquivo de dependências.

```powershell
npm ci
npm run lint
npm run build
npm run dev
```
