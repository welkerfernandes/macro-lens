# Native analysis engine — Rust

Este componente participa do caminho real de análise quando NATIVE_ENGINE está configurado.
O modo Python é a referência local e permite executar o projeto sem instalar outro compilador.
Quando configurado, erro no motor nativo retorna 502 e não é ocultado por fallback.

```bash
cd engines/trend
cargo test
cargo build --release
```

NATIVE_ENGINE recebe um array JSON de argumentos, executado sem shell e com timeout de cinco segundos.
Configure caminhos a partir da raiz do projeto. Exemplos por plataforma:

- Go: `["engines/weather/weather-engine"]` (Windows: weather-engine.exe).
- Java: `["java","-cp","engines/registry/build","RegistryPolicy"]`.
- Rust: `["engines/trend/target/release/macro-trend"]` (Windows: macro-trend.exe).

Go recebe JSON e devolve análise meteorológica completa. Java recebe CNPJ, código de situação
e quatro flags booleanos em linhas separadas, valida identidade e devolve a avaliação cadastral.
Rust recebe pares `ano TAB valor`, calcula inclinação e R² em precisão f64 e devolve JSON.
O envelope HTTP, persistência, recuperação de fonte e identidade continuam sob responsabilidade Python.

É uma fronteira de processo local, não um microsserviço remoto. Não há alegação de ganho de desempenho
sem benchmark. A seleção explícita permite comparar implementações e testar falhas da fronteira.
