# Preparação para hospedagem 24/7

Estado em 12/11/2026: aplicação validada localmente; nenhuma implantação cloud ou ativação de agenda faz parte desta atualização do GitHub. Este documento é um plano, não uma comprovação de operação contínua.

## Decisões e requisitos antes de provisionar

1. Escolher provedor, região, arquitetura, domínio e orçamento. Conferir cotas e condições no console e documentação oficial na data da contratação; plano gratuito não garante capacidade nem disponibilidade.
2. Revisar versões e avisos de segurança, especialmente n8n e imagens Compose. Fixar versões aprovadas e testar atualizações em ambiente separado.
3. Definir autenticação para a aplicação e o chat, limites persistentes por usuário e orçamento/cotas Gemini. O limitador por processo e a pausa da interface não bastam para exposição pública.
4. Adaptar Host, CORS, proxy e acesso local em `app/access.py` para o domínio e topologia aprovados. Não liberar origens ou hosts indiscriminadamente.

## Dados, credenciais e rede

- Criar contas PostgreSQL separadas para migração e execução, com privilégios mínimos. Não copiar a conta administrativa local.
- Gerar backup PostgreSQL consistente com `pg_dump -Fc` e testar restauração separada. Preservar o banco do n8n e sua chave de criptografia original; fazer cópia consistente, com o serviço parado quando necessário.
- Manter segredos fora do Git, em armazenamento protegido do ambiente. Definir credenciais da implantação, sem substituir a chave que protege credenciais n8n restauradas.
- Manter PostgreSQL, FastAPI e editor n8n privados. Expor somente HTTPS para rotas necessárias, com HTTP apenas para redirecionamento. Restringir acesso administrativo.
- Manter `/operations/monitor/run` interno e autenticado por Bearer token; não expor a rota no proxy público.
- Adaptar a URL do workflow quando API e n8n não compartilharem localhost. O Compose local usa namespace de rede compartilhado; n8n Cloud exige outra topologia privada/autenticada.

## Operação e aceite

- Servir o build estático atrás de proxy com HTTPS; configurar reinício automático e limites de recursos.
- Configurar rotação de logs, retenção, backup fora do servidor, alertas de disco/cota e verificação externa de disponibilidade. `/health` responde sobre a API, não comprova sozinho acesso ao banco ou Gemini.
- Repetir testes integrados, conferir regras de firewall, bloqueio de portas privadas, comportamento de falhas, reinício e persistência dos dados.
- Validar novamente Gemini real e os custos; registrar indisponibilidade honestamente.
- Somente depois do aceite e autorização específica, ativar a agenda n8n e acompanhar a primeira execução às 09h de São Paulo.

## Critério para apresentar como disponível 24/7

URL HTTPS publicada e verificada, acesso protegido, reinício e restauração testados, observabilidade em funcionamento e limitações do provedor documentadas. Até lá, apresentar o projeto como demonstração local.

Detalhes históricos do ambiente estão em [LOCAL-READINESS.md](LOCAL-READINESS.md); suas referências de cota são datadas e não substituem nova consulta na implantação.
