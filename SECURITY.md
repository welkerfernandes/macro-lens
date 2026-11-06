# Segurança

Chaves local-alpha/local-beta são exclusivamente de demonstração. Configure API_KEYS com segredos
aleatórios por workspace e use TLS antes de exposição externa. Credenciais determinam a identidade.

O cliente HTTP acessa apenas hosts HTTPS permitidos, não segue redirects e tem timeout limitado.
URLs não são fornecidas livremente pelo usuário. SQL usa parâmetros e escopo de tenant.
A interface apresenta strings externas via textContent, sem interpretar HTML vindo das fontes.

Limites: não há OIDC, RBAC, rotação automática de credenciais, rate limiting distribuído,
criptografia de disco gerenciada ou auditoria independente. Cache de respostas públicas fica em memória.
Não publique .env, bancos SQLite, dados reais de clientes ou credenciais. Relate vulnerabilidades
de forma privada ao responsável pelo repositório.
