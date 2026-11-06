# ADR 001 — Adaptadores explícitos e persistência de evidências

Status: implementado.

## Contexto

Comparações econômicas precisam explicitar unidade, período, dados ausentes e limites da tendência calculada.

## Decisão

Monólito modular com contratos HTTP em main.py, casos de uso em service.py,
regras analíticas em domain.py e transporte/persistência em infrastructure.py.
SQLite torna a demonstração independente de serviços gerenciados. Consultas SQL são parametrizadas
e operações de histórico incluem tenant na chave de leitura/exclusão.

Resultados de negócio são gravados somente após análise completa. O snapshot inclui versão do método,
origem, horário UTC e hash SHA-256 do JSON decodificado da resposta da fonte, não dos bytes do transporte.
O hash permite comparar conteúdo observado; não é assinatura digital do provedor nem prova de autenticidade.
No modo demo, o hash se refere à fixture sintética, e o modo fica registrado explicitamente.

## Resiliência

GETs externos têm timeout, tentativas limitadas e cache TTL. Não há fallback automático para demo.
404 da fonte mapeia para 404, 429/timeout para 503 e respostas inválidas para 502.
Cache é compartilhado apenas entre dados públicos e não contém identidade do workspace.
O lock protege a estrutura do cache; consultas simultâneas frias podem gerar chamadas duplicadas.
Não há circuit breaker, single-flight ou cache distribuído.

## Tradeoffs

Um escritor SQLite por vez limita capacidade. Não há transação distribuída entre requisição externa
e banco. Uma repetição pode criar snapshots distintos e isso é intencional: análises são observações,
não movimentações de dinheiro. Health é liveness, não readiness ou teste de conectividade externa.

## Próximos passos

Adicionar metadados e última atualização da fonte, testes de revisão de séries, exportação versionada e avaliação de robustez das tendências a outliers e mudanças estruturais.
