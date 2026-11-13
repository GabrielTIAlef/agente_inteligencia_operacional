# Backup externo automático, sem serviços pagos

O PostgreSQL já gera um backup diário na VM às 03h de São Paulo. A tarefa Windows `InteligenciaOperacional-BackupExterno` copia o último dump concluído às **03h30, 09h30, 15h30 e 21h30**, e também ao entrar no Windows. A agenda usa o fuso do computador; a instalação atual foi conferida em São Paulo.

## Destino e condições

Pasta instalada: `%LOCALAPPDATA%\InteligenciaOperacional\backups`.

- O computador deve estar ligado, conectado à internet e com a sessão do titular aberta. Não é necessário deixar o navegador, o chat ou um terminal aberto. A execução fica oculta e não pede senha.
- A tarefa tenta executar novamente após uma falha e processa horários perdidos quando o computador volta a estar disponível. Se continuar desligado, a VM mantém sua própria agenda; não existe cópia externa instantânea nessas condições.
- Retém até 30 dumps locais válidos; a VM mantém até 7. Quando o computador fica desligado por vários dias, somente o último backup disponível é copiado ao voltar, não todo o histórico perdido.
- A pasta local permite acesso somente ao titular e à conta SYSTEM. Os dumps não são criptografados separadamente; herdam a proteção do computador/disco. Não compartilhar essa pasta.
- Usa a chave SSH já existente em Downloads, somente pelo caminho local. A chave não é copiada ao repositório nem enviada ao chat.
- Usa o IP da VM e valida a identidade SSH com `StrictHostKeyChecking=yes`. Não aceita automaticamente uma identidade alterada.
- A regra SSH da VM permite apenas o IPv4 administrativo configurado. Ao trocar de conexão/IP, atualizar essa regra por acesso administrativo antes de esperar a próxima cópia.
- Não usa Oracle Object Storage, serviços pagos, credenciais Google nem o Gemini. Custo adicional de nuvem: nenhum recurso criado.

## Verificação de cada cópia

`cloud-export-backup.py`, executado como root pelo SSH administrativo existente, exporta somente arquivos `.dump` concluídos da pasta fixa `/var/backups/aio`. Não exporta `.env`, credenciais, chaves ou outros arquivos do servidor.

O cliente consulta nome, tamanho e SHA-256; exige nome/tamanho válidos e backup com até 30 horas. Faz a transferência binária para um arquivo temporário, confere SHA-256, tamanho e cabeçalho PostgreSQL e só então publica a cópia local. Uma transferência incompleta ou corrompida não substitui backups anteriores. Se o mesmo arquivo já estiver íntegro, não baixa de novo. O servidor não recebe acesso ao computador Windows.

O tamanho máximo por dump é 256 MiB, apropriado à base sintética atual. Se os dados crescerem, revisar armazenamento, limite e retenção antes de aumentar esse valor.

## Consultar resultado ou executar manualmente

No PowerShell do próprio titular:

```powershell
Get-Content "$env:LOCALAPPDATA\InteligenciaOperacional\status.json"
Get-ScheduledTaskInfo -TaskName 'InteligenciaOperacional-BackupExterno'
Start-ScheduledTask -TaskName 'InteligenciaOperacional-BackupExterno'
```

`LastTaskResult=0` e `ok=true` no arquivo indicam sucesso. `status.json` registra horário da última tentativa e do último sucesso, arquivo e checksum; `backup.log` registra resultados, com rotação. Uma falha preserva o último sucesso registrado e as cópias já verificadas. Não há notificações externas configuradas: conferir esse estado periodicamente.

Se a chave mudar de pasta, atualizar `identity_file` no `config.json` dessa pasta privada ou reinstalar com o caminho correto. Nunca inserir o conteúdo da chave no arquivo JSON.

## Instalação em outro computador autorizado

Requer Windows, OpenSSH, Python 3.11+ com `pythonw.exe`, acesso SSH já autorizado e a identidade da VM já validada no `known_hosts` desse usuário. O exportador deve estar instalado em `/opt/aio/deploy/cloud-export-backup.py` na VM. A tarefa usa o usuário conectado e privilégio limitado; não armazena senha do Windows.

```powershell
.\deploy\install-offsite-backup.ps1 -IdentityFile 'C:\caminho\chave.key' -PythonExecutable 'C:\caminho\python.exe'
```

O instalador mantém a pasta estável em `%LOCALAPPDATA%`, independente da pasta do repositório. Não altera políticas globais do Windows. Não é necessário ativar planos nem cadastrar meios de pagamento.

## Recuperação

Guardar os dumps fora da VM permite recuperar o banco mesmo se a instância original for perdida. Antes de restaurar em produção, criar um banco separado, usar `pg_restore --exit-on-error --no-owner --no-privileges` com versão compatível, conferir os pedidos e o histórico e somente então planejar a troca. Senhas, chave Gemini, certificados e configurações do servidor precisam ser recriados: não estão no dump.

A restauração de 1.000 pedidos foi testada separadamente na VM. O cliente externo também foi executado pelo próprio Agendador, e o arquivo copiado foi conferido com o mesmo SHA-256 do servidor. O teste automatizado de transferência corrompida garante a preservação de cópias anteriores.
