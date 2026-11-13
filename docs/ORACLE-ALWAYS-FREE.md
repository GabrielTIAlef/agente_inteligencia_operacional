# Implantação Oracle Always Free

Registro em 12/11/2026, horário de São Paulo. URL pública: https://inteligencia-operacional.duckdns.org/. O endereço antigo https://137.131.236.116/ redireciona para o domínio.
Fonte: repositório público existente, base `23376d2`, com ajustes desta entrega versionados no GitHub após autorização do titular.

## Arquitetura e orçamento

- Mesma VM E2.1.Micro existente, Ubuntu 24.04.5, 952 MiB RAM, disco existente de 45 GiB.
- Nginx serve o React/Vite compilado no Windows. FastAPI roda com um worker em `127.0.0.1:8000`.
- PostgreSQL 16 nativo, em `127.0.0.1:5432`, com 32 MiB de shared_buffers e 15 conexões máximas. Banco persistido em `/var/lib/postgresql/16/main`.
- Sem Docker, n8n, Neon ou Cloudflare Pages nessa implantação. O workflow n8n original continua no repositório como referência e alternativa para ambiente maior.
- Monitor equivalente chama a mesma API autenticada às 09h de São Paulo, persiste os mesmos relatórios e regras no PostgreSQL, sem consumo de Gemini e sem envio externo de notificações.
- Swap de 1 GiB ocupa apenas o disco já existente. Não foi criado volume adicional.
- Não foram criados recursos OCI, planos pagos, contas externas ou assinaturas. Não houve alteração de shape, volume, IP, região ou plano.
- A API consumiu aproximadamente 57 MiB; houve aproximadamente 466 MiB disponíveis no sistema e zero swap em uma medição com o painel ativo. Isso não é um teste de carga nem garantia de capacidade.

O plano e a fatura global da conta Oracle não foram auditados no console. A exigência de R$ 0 depende de manter a VM/volume dentro das franquias e não ativar faturamento pago no Gemini. Limites de requisições não são teto financeiro.

Fontes consultadas em 12/11/2026:

- [Oracle Always Free](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm): E2.1.Micro elegível, armazenamento e possibilidade de retomada de VMs ociosas. Não simular utilização para evitar essa política.
- [Certificados IP gratuitos com Certbot](https://letsencrypt.org/2026/03/11/shorter-certs-certbot): certificado curto exige renovação automática.
- [Preços Gemini](https://aistudio.google.com/docs/pricing#gemini-3.1-flash-lite): texto de entrada/saída disponível no Free para o modelo selecionado; cotas e termos do projeto continuam aplicáveis.

## Segurança e acesso

- HTTPS real emitido pelo Let's Encrypt para o IP e para `inteligencia-operacional.duckdns.org`, com Certbot 5.10.0. HTTP e o endereço IP antigo redirecionam para o domínio HTTPS, exceto desafios ACME.
- Certificado do IP vence em 19/11/2026 e certificado inicial do domínio vence em 10/02/2027. `aio-cert-renew.timer` verifica todos os certificados duas vezes por dia; o hook recarrega Nginx.
- Firewall iptables mantém regras internas da Oracle e permite 80/443. SSH foi restrito ao IPv4 administrativo confirmado na sessão. O endereço não é publicado nesta documentação; consulte `sudo iptables -S INPUT` na VM.
- SSH somente por chave para `ubuntu`, sem senha nem login root. IPv6 SSH bloqueado. Se o IP da conexão administrativa mudar, será necessário atualizar a regra por uma sessão ainda aberta ou pelo console/console serial da Oracle. Não fechar a sessão administrativa durante recuperação.
- As regras da VCN/NSG não foram inspecionadas pelo console. Testes externos comprovaram 80/443 acessíveis e 5432/8000/5678 inacessíveis. O controle de origem do SSH é aplicado no sistema da VM.
- API aceita somente clientes loopback; Uvicorn não confia em cabeçalhos de proxy. Nginx fixa Host local e remove cabeçalhos de IP recebidos. CORS permite explicitamente o domínio HTTPS publicado e a origem HTTPS anterior do IP.
- Somente rotas necessárias do painel, relatório, histórico e saúde são publicadas. Execução do monitor, OpenAPI, documentação e métricas internas ficam bloqueadas no proxy.
- O painel contém somente dados fictícios públicos. Não carregar dados reais sem revisar autenticação e política de privacidade.
- Chat público sem senha, por solicitação explícita do titular em 12/11/2026. Mantém HTTPS, 2 requisições/minuto por IP, uma simultânea e orçamento global persistente de 30 requisições/dia em São Paulo. Cada pergunta pode gerar até 5 chamadas ao modelo; a cota é de perguntas, não de tokens ou dinheiro.
- O chat foi habilitado após configurar uma chave de projeto Free e testar uma resposta real. Não há fallback para serviços pagos. O monitor permanece determinístico mesmo após habilitar o chat.
- Credenciais ficam em `/etc/aio/app.env`, modo 0600. Conta de migração separada em `/etc/aio/migration.env`. Conta runtime somente lê pedidos e lê/insere histórico; não altera pedidos nem schema.
- Credenciais antigas do chat permanecem protegidas em `/etc/aio`, mas não são utilizadas pelo proxy público. Nunca copiar esses arquivos para Git ou chat.

## Operação

```bash
sudo systemctl status aio-api --no-pager
sudo journalctl -u aio-api -n 50 --no-pager
sudo systemctl list-timers --all | grep aio
sudo journalctl -u aio-monitor -u aio-health -u aio-backup -u aio-cert-renew -n 50 --no-pager
```

`aio-api.service` reinicia em falha e inicia no boot. Limite de memória da API: 300 MiB. Logs do journal têm limite de 100 MiB persistentes, 30 MiB em memória e retenção de 14 dias; Nginx usa a rotação do pacote Ubuntu.

- `aio-monitor.timer`: 09h São Paulo, idempotente por dia.
- `aio-health.timer`: a cada 5 minutos, verifica API, consulta ao banco e pelo menos 2 GiB livres. Falhas aparecem nos logs/systemd; não há alerta por e-mail ou mensageria configurado.
- `aio-backup.timer`: 03h São Paulo, `pg_dump -Fc`, últimos 7 arquivos em `/var/backups/aio`, modo 0600.
- `aio-cert-renew.timer`: duas vezes/dia, com atraso aleatório de até 30 minutos.

Os timers são persistentes: uma execução perdida pode ocorrer após ligar a VM. Um teste manual inicial concluiu o monitor; o horário agendado seguinte ainda não ocorreu no registro inicial.

## Backup e restauração

A restauração de um dump foi testada em banco separado, criado exclusivamente para validação e removido ao terminar. Foram recuperados os 1.000 pedidos. Além da cópia inicial, há cópia externa automática em `%LOCALAPPDATA%\InteligenciaOperacional\backups` no Windows, fora do repositório.

Backups diários na mesma VM não protegem contra perda da VM/disco. A tarefa Windows `InteligenciaOperacional-BackupExterno` copia e verifica o último dump a cada seis horas e ao entrar no Windows; mantém até 30 cópias e foi executada pelo próprio Agendador com retorno 0. Exige computador ligado, conectado e sessão aberta. O hash SHA-256 e o tamanho conferiram com o arquivo da VM. Não foi criado armazenamento cloud extra nem ativado serviço de backup cobrável. Credenciais e certificados não estão no dump; precisam ser recriados numa recuperação completa. Consulte [OFFSITE-BACKUP.md](OFFSITE-BACKUP.md) para condições, logs e recuperação.

Para testar novamente na VM, sem substituir o banco de produção:

```bash
sudo python3 /opt/aio/deploy/cloud-verify.py
```

Esse comando testa a base sintética atual e espera 1.000 pedidos. Ajustar a contagem esperada se a base mudar. Nunca executar restauração diretamente sobre produção sem backup e plano de recuperação específico.

## Gemini: configuração sem exposição da chave

Somente depois de confirmar que o projeto da chave mostra Free e não tem faturamento pago:

```bash
sudo python3 /opt/aio/deploy/cloud-configure-gemini.py
```

A chave é solicitada com digitação oculta, salva localmente com acesso restrito e a API reinicia. O procedimento não verifica automaticamente o plano do Google: a confirmação vem do titular. Não colar chave em comandos, chat ou repositório. Modelo inicial: `gemini-3.1-flash-lite`. Conferir sua disponibilidade Free novamente se alterar o modelo.

O build público usa `VITE_CHAT_ENABLED=true`. Manter `VITE_API_URL` vazio e `VITE_MONITOR_SCHEDULE` com a agenda real. O acesso ao chat não exige mais login; a chave Gemini continua somente no servidor.

## Validações já realizadas

- Build Vite e lint sem erros; instalação inicial do frontend auditada sem vulnerabilidades conhecidas naquele momento.
- 59 testes Python aprovados, incluindo integração PostgreSQL, orçamento persistente do chat e preservação de backups após transferência corrompida.
- Banco restaurado separadamente com 1.000 pedidos.
- API reiniciada manualmente; novo acesso SSH após restrição aprovado. Não foi realizado reboot completo da VM.
- HTTPS `/health` respondeu 200 com validação normal de certificado, e HTTP respondeu 301 para HTTPS.
- Painel e monitor abertos em navegador público: indicadores do PostgreSQL, exportação de relatório disponível e uma execução concluída no histórico.
- Renovação do certificado simulada com sucesso.

Não afirmar operação 24/7 garantida: não houve teste prolongado/carga, OCI pode retomar VMs ociosas, não há alerta externo contínuo e a cópia externa depende da disponibilidade do computador Windows.

Gemini validado em 12/11/2026 às 20h22 de São Paulo: após o titular inserir uma chave ativa diretamente na VM e autorizar o envio de pergunta/indicadores fictícios ao Google, o chat respondeu 200 pelo HTTPS público. A pergunta sobre a base completa acionou `get_general_metrics` e retornou “Existem 1.000 pedidos na base completa.” Depois, o titular solicitou remover a senha: novo teste externo sem cabeçalho de autenticação retornou a mesma resposta correta. O chat está habilitado na interface e mantém os limites de uso. Nenhum valor de credencial foi exibido. O plano Free foi confirmado pelo titular; não foi auditado por credenciais administrativas do Google.

## Atualizações

Domínio DuckDNS cadastrado pelo titular e validado em 12/11/2026: DNS A resolve para a VM existente. Certificado gratuito emitido para o nome, página HTTPS e saúde pública aprovadas. POST sem mensagem no chat retornou 422 de validação, confirmando o encaminhamento e a origem permitida sem chamada ao Gemini. Nenhuma chave ou token DuckDNS foi necessário. Sem atualizador DNS automático: caso o IP público da VM mude, atualizar o registro DuckDNS. O script `cloud-domain.py` registra a ativação do domínio; preservar ambos os certificados enquanto houver redirecionamento HTTPS do IP.

Os scripts `cloud-bootstrap.py` e `cloud-finalize.py` registram as ações desta VM e assumem PostgreSQL 16/Ubuntu 24.04; não são provisionamento genérico multiambiente. Revisar caminhos e IP antes de reutilizá-los. Compilar o frontend fora da VM. Enviar somente código, build e dependências declaradas, sem `.env`, `.git`, chaves, bancos, dumps ou `node_modules`.

Após trocar código: testar, atualizar `/opt/aio`, aplicar migrações com credenciais de migração e reiniciar `aio-api`. Preservar `/etc/aio`, `/var/lib/aio`, `/var/lib/postgresql` e `/etc/letsencrypt`. O titular autorizou o commit e envio desta entrega ao GitHub. Dumps, segredos e arquivos privados da tarefa Windows permanecem fora do repositório.
