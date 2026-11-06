# Registro de validação

Validação em 6 de novembro de 2026.

- 20 testes Python aprovados localmente.
- [Workflow remoto aprovado](https://github.com/welkerfernandes/macro-lens/actions/runs/42280368063).
- Fluxo em Chromium desktop e viewport mobile de 390 px aprovado, sem erros JavaScript detectados.
- Capturas reais produzidas pelo job browser: [desktop](dashboard.png) e [mobile](mobile.png).
- 5 testes Rust e suíte Python com motor Rust ativo; build React/TypeScript e imagem Docker aprovados na CI. Consulta real ao Banco Mundial aprovada localmente.

As verificações demonstram os cenários exercitados, não ausência de defeitos, capacidade de produção
ou acurácia de modelos em dados reais. A suíte automatizada usa dados sintéticos e transportes simulados;
consultas live, quando mencionadas, foram verificações pontuais adicionais, sem garantia de disponibilidade futura.
