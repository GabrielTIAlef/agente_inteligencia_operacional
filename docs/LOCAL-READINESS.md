> Registro histórico de validação anterior à atualização do GitHub. A interface e o contrato atuais estão no README e em [VALIDATION.md](VALIDATION.md). Referências a ausência de push descrevem a etapa original.

# Validação local e publicação futura

Verificação realizada em 11/11/2026, no Windows, sobre o commit base `3b3391c` da branch `main`. As mudanças desta tarefa permanecem locais; nenhum push, publicação, criação de recurso cloud ou ativação de agenda foi realizado.

## Resultado

O fluxo local PostgreSQL → FastAPI → React e n8n → FastAPI → PostgreSQL foi validado. O assistente consultou os dados via Gemini e respondeu 1.000 pedidos. Os 1.000 pedidos existentes foram preservados. O histórico real contém um sucesso diário, reutilizado nas chamadas repetidas e simultâneas.

| Verificação | Resultado |
| --- | --- |
| Schema executado duas vezes no banco `ai_operations` | Aprovado; `monitor_runs` e índices criados, pedidos preservados |
| Testes Python, incluindo integração com PostgreSQL | 45 aprovados, com `RUN_DB_TESTS=1` |
| Frontend: lint e build | Aprovados |
| Edge: 1440, 768 e 390 px | Painel, filtros, histórico e exportação aprovados |
| POST do monitor sem credencial | 403, conforme esperado |
| POST do monitor repetido e quatro chamadas simultâneas | 200; mesmo ID persistido |
| Workflow operacional no n8n | Duas execuções bem-sucedidas |
| Falha de processamento, recuperação e repetição | Testadas em tabela temporária PostgreSQL com rollback |
| n8n: resposta 503 temporária | Duas tentativas; recuperação e sucesso |
| n8n: resposta 503 persistente | Duas tentativas; execução com erro visível |
| Gemini por `/agent/chat` | 200; total de 1.000 confirmado por ferramenta |

## Correções

- Aplicado `etl/schema.sql` ao banco realmente usado pela API. A ausência de `monitor_runs` causava `UndefinedTable` e 503.
- Corrigida a linha malformada `GEMINI_MODEL` no `.env`, preservando a chave. O modelo validado é `gemini-3.1-flash-lite`; os exemplos e padrões do código foram alinhados.
- Atualizada a credencial Header Auth já selecionada pelo workflow instalado: cabeçalho `Authorization`, valor Bearer seguido do token local. Nenhuma credencial foi incluída no repositório.
- Preservada a chave de criptografia existente em `%USERPROFILE%\.n8n\config`. A ausência de `N8N_ENCRYPTION_KEY` no `.env` não é um defeito nesta instalação já inicializada. Não substituir essa chave por outra aleatória.
- Adicionados `etl/migrate.py`, `deploy/start-local.ps1`, `tests/test_monitor_database.py` e `n8n/validate_local.py`.
- A inicialização da API reutiliza o comando de migração e só carrega o CSV se a tabela estiver vazia.

## Iniciar sem Docker

Na raiz `<raiz-do-projeto>`, executar no PowerShell:

```powershell
.\deploy\start-local.ps1
```

O script usa Python do venv e Node instalado pelo NVM, abre os processos em segundo plano e mantém as portas no loopback. Não substitui processos que já ocupem as portas e não ativa workflows. O PostgreSQL deve estar iniciado como serviço do Windows. Logs locais ficam em `local-*.log` e são ignorados pelo Git. O n8n pode levar alguns minutos para iniciar neste PC.

- Painel: http://127.0.0.1:5173
- API: http://127.0.0.1:8000/health
- n8n: http://127.0.0.1:5678

Para migrar separadamente, sem carga de dados:

```powershell
.\.venv\Scripts\python.exe -m etl.migrate
```

Para repetir a suíte e a integração com PostgreSQL:

```powershell
$env:RUN_DB_TESTS='1'
.\.venv\Scripts\python.exe -m pytest -q
```

O teste de banco cria uma tabela temporária que oculta `monitor_runs` apenas na própria conexão e termina com rollback. Não apaga nem insere histórico na tabela real.

Para repetir os testes de falha do n8n:

```powershell
.\.venv\Scripts\python.exe -m n8n.validate_local
```

Esse comando usa um workflow de validação separado e inativo, `VALIDAÇÃO LOCAL — retry e falha (inativo)`. O servidor de falhas só existe durante o teste. Uma execução com erro nesse workflow é evidência esperada. Para repetir, usar o comando acima; a URL temporária não serve para execução manual posterior no editor. O workflow operacional original permanece inativo, com URL `http://127.0.0.1:8000/operations/monitor/run`.

O JSON distribuído em `n8n/operations-report.json` usa um ID de credencial de exemplo. Se houver nova importação, selecionar no nó HTTP a credencial local existente; não presumir que o ID do exemplo corresponde ao ID gerado pelo editor.

## Segurança local e limites

O `.env` está fora do versionamento. API, Vite e editor n8n são iniciados em `127.0.0.1`. O PostgreSQL escuta em todas as interfaces, mas as regras verificadas de `pg_hba.conf` aceitam somente localhost e exigem SCRAM. Não foram ampliadas regras de acesso nem abertas portas do firewall.

A conta PostgreSQL local configurada ainda é `postgres`, com privilégios administrativos. Antes de publicar, criar contas distintas para migração/carga e execução da API, com privilégios mínimos; não copiar essa configuração administrativa para a nuvem. O editor do n8n deve permanecer privado. O endpoint de disparo do monitor exige token e não deve ser exposto no proxy público.

Os dados são sintéticos de outubro de 2026. O monitor analisa 14 dias até o pedido mais recente, e não necessariamente os últimos 14 dias do calendário atual. O modo de notificação está desativado por padrão; não há envio externo implementado. O resumo Gemini do monitor é opcional e tem fallback; o chat usa Gemini real e depende da cota do provedor.

Com aproximadamente 6,7 GB livres, evitar Docker Desktop, reinstalações desnecessárias e acúmulo de logs/backups neste PC. Os processos locais não foram registrados para iniciar com o Windows: eles servem à validação e ao desenvolvimento. A operação contínua será configurada na hospedagem.

## Publicação 24/7 — executar somente após autorização

1. Confirmar conta, região, disponibilidade e limites no console Oracle. A documentação consultada em 11/11/2026 informa Ampere A1 Always Free equivalente a **2 OCPUs e 12 GB de RAM**, e até 200 GB de volumes compartilhados. Não assumir as cotas antigas de 4 OCPUs/24 GB. A oferta está sujeita a capacidade e retomada de instâncias ociosas, portanto não representa garantia de disponibilidade contínua.
2. Criar VM Linux elegível, preferencialmente Ubuntu na arquitetura disponível, com orçamento e alertas de custo. Dimensionar armazenamento dentro da cota exibida na conta. Docker Engine na VM é uma opção; Docker Desktop no Windows não é necessário. Alternativamente, usar serviços systemd para PostgreSQL, API e n8n e servir o build estático com Nginx.
3. Antes da migração, gerar backup do PostgreSQL com `pg_dump -Fc`; preservar o banco do n8n e sua chave de criptografia em armazenamento protegido. Usar backup consistente do SQLite, ou parar o n8n durante sua cópia. Fazer teste de restauração em ambiente separado. Não enviar `.env`, chave do n8n ou backups para GitHub.
4. Instalar e fixar as versões aprovadas de Python, Node e dependências. Revisar avisos de segurança e a versão do n8n antes de expô-lo a qualquer rede remota; atualizar com backup e repetir os testes se necessário. Validar compatibilidade ARM caso Ampere seja escolhido.
5. Restaurar dados, configurar credenciais novas da implantação e contas PostgreSQL com privilégios mínimos. Aplicar a migração sem sobrescrever pedidos. Manter banco, API e editor n8n privados. Preservar a chave antiga se as credenciais criptografadas forem restauradas.
6. Configurar domínio, HTTPS e proxy reverso. Servir `frontend/dist` e encaminhar apenas as rotas públicas necessárias à API. Adaptar a configuração local de Host/CORS/proxy para o domínio autorizado. O Nginx atual é de demonstração local e precisa dessa adaptação. Proteger o chat com autenticação e limitação de uso persistente antes da exposição pública, para controlar custos do Gemini.
7. Liberar somente 80/443 e SSH administrativo restrito. Acessar o editor n8n por túnel SSH ou solução privada autenticada. Manter `/operations/monitor/run` interno com Bearer token; alterar o endereço do workflow se os serviços estiverem em máquinas ou redes distintas.
8. Configurar reinício automático dos serviços, backup fora da VM com retenção e teste de restauração, rotação de logs, verificações externas de disponibilidade e alertas de disco/cota. Não depender deste PC ligado para manter o serviço online.
9. Repetir os testes integrados no servidor, verificar HTTPS, bloqueio das portas privadas, reinício da VM e preservação dos dados. Só então ativar o workflow diário às 09h de São Paulo e acompanhar a primeira execução agendada.

Os passos acima pertencem à implantação; nenhum recurso cloud foi criado ou modificado nesta tarefa. As credenciais/domínio/conta cloud e o ambiente remoto ainda precisam ser definidos pelo usuário na etapa autorizada de publicação.

Fontes oficiais consultadas:

- [Oracle: recursos Always Free, limites e retomada de instâncias ociosas](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm)
- [n8n: chave de criptografia existente e configuração](https://docs.n8n.io/hosting/configuration/configuration-examples/encryption-key/)
- [n8n: segurança e TLS](https://n8n.io/legal/security/)
