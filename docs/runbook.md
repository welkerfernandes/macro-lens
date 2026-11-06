# Execução e operação

Inicie com o comando do README e valide `/health`, `/docs` e o modo demo.

## Configuração local

```powershell
$env:API_KEYS='{"uma-chave-local":"alpha","outra-chave-local":"beta"}'
$env:DATABASE_PATH='./local.db'
```

O diretório pai do banco deve existir. Configure TLS, segredos fortes e controles de acesso
antes de expor o serviço. A interface não guarda chaves em localStorage.

## Incidentes

- 401: chave não configurada ou inválida.
- 422: entrada não atende ao contrato.
- 404: fonte sem registro ou snapshot inexistente no workspace.
- 502: payload inválido ou falha HTTP da fonte.
- 503: timeout, indisponibilidade de rede ou limite do provedor.

Confirme o status da fonte antes de repetir consultas. Não há repetição automática de 429.
O servidor usa logs de acesso Uvicorn; não há métricas distribuídas ou alarmes configurados.
Para backup consistente, pare o processo e copie o banco. Nunca publique o arquivo SQLite.
Exclusões removem apenas snapshots locais; não apagam backups nem dados do provedor.

## Capacidade

Cache em memória reinicia com o processo e não é compartilhado entre workers. HTTP é síncrono
no threadpool. Faça medições com a carga pretendida antes de aumentar workers ou definir SLOs.
Não há scheduler, fila, política automática de retenção ou alta disponibilidade implementada.
