# Instalação e configuração local

O caminho principal de instalação está no [README](../README.md). Ambiente de referência: Windows, Python 3.12, Node 24 e PostgreSQL 17. A validação usa dependências já instaladas; não representa uma instalação limpa em outro computador.

## Configuração

Copie `.env.example` somente em uma instalação nova. Crie um banco dedicado e preencha `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER` e `DB_PASSWORD`. Use um token aleatório próprio em `MONITOR_TOKEN`. A conta administrativa local não é configuração recomendada para hospedagem.

| Variável | Uso |
| --- | --- |
| `GEMINI_API_KEY` | Necessária para o chat; nunca deve ir ao frontend ou Git |
| `GEMINI_MODEL` | Modelo do chat; padrão do projeto `gemini-3.1-flash-lite`, sujeito à disponibilidade da conta |
| `APP_CORS_ORIGINS` | Origens explícitas permitidas; não usar `*` |
| `MONITOR_TOKEN` | Bearer token exigido no disparo do monitor |
| `MONITOR_GEMINI_ENABLED` / `MONITOR_GEMINI_MODEL` | Resumo opcional apenas com alerta; padrão desativado |
| `MONITOR_NOTIFICATION_MODE` | `off` por padrão; `preview` apenas sinaliza a prévia, sem envio externo |
| `N8N_ENCRYPTION_KEY` | Nova instalação/Compose: definir antes do primeiro início; instalação existente: preservar a chave original |

Não copie credenciais de CI para uso local. O `.env.example` usa campos vazios intencionalmente.

## Início pelo script

```powershell
.\deploy\start-local.ps1
```

O script exige `.venv`, dependências do frontend instaladas, Node em `%LOCALAPPDATA%\Author Software\nvm\installs` e n8n global nessa instalação do Node. Não instala dependências. Logs `local-*.log` ficam ignorados no Git. Verifica portas antes de iniciar; um processo existente precisa ser conferido pelo usuário. O PostgreSQL deve estar iniciado e o banco deve existir.

## Alternativa manual sem NVM

Com Python, Node/npm e n8n disponíveis no PATH, execute cada serviço em um terminal separado na raiz do projeto:

```powershell
# API: aplica schema e carrega o CSV somente se pedidos estiver vazia
.\.venv\Scripts\python.exe -m deploy.start-api
```

```powershell
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

```powershell
$env:N8N_LISTEN_ADDRESS='127.0.0.1'
$env:N8N_DIAGNOSTICS_ENABLED='false'
$env:N8N_PERSONALIZATION_ENABLED='false'
$env:GENERIC_TIMEZONE='America/Sao_Paulo'
n8n start
```

O n8n iniciado manualmente não lê automaticamente o `.env` do projeto. Em instalação nova, configure sua chave no ambiente antes do primeiro início; na existente mantenha a configuração original. Use Ctrl+C nos terminais manuais para parar os serviços.

Migração separada, sem carga: `.\.venv\Scripts\python.exe -m etl.migrate`.

## Workflow n8n

Importe [operations-report.json](../n8n/operations-report.json). Mantenha-o inativo. No nó **Gerar e registrar relatório**, selecione uma credencial **Header Auth**: nome `Authorization`, valor `Bearer ` seguido do token configurado na API. O ID distribuído é um exemplo, não uma credencial real.

Uma execução manual grava histórico operacional. Repetir no mesmo dia reutiliza o sucesso diário. A consulta da aba Monitoramento não executa esse fluxo. Não ative a agenda durante a preparação do GitHub.

## Compose opcional

Em ambiente com Docker Engine/Compose disponível, preencha as variáveis obrigatórias, incluindo `N8N_ENCRYPTION_KEY` própria, e execute:

```powershell
docker compose up -d --build --wait
```

Interface: http://127.0.0.1:8080; editor: http://127.0.0.1:5678. São volumes próprios do Compose: não reutilizam automaticamente o PostgreSQL e o n8n nativos. API e banco não publicam portas; o editor fica no loopback do host. O proxy não expõe o disparo do monitor. Não use `docker compose down -v` para parar um ambiente com dados a preservar.

Compose não foi reexecutado nesta revisão local; seu teste integrado pertence ao [CI](../.github/workflows/ci.yml).

## Diagnóstico

- Banco indisponível: confira serviço, nome do banco e conexão sem expor senha em relatórios.
- Node não selecionado: selecione a instalação existente com seu gerenciador; não é necessário reinstalar tudo.
- Porta ocupada: confira o processo; o script não o encerra nem substitui.
- Gemini 429/503: confira cota/disponibilidade; não há retry automático no chat. A pausa visual de 30 segundos não garante renovação de cota.
- Histórico vazio: importar o workflow não executa o monitor. Não invente registros para preencher a tela.
