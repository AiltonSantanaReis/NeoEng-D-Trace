# Política de Segurança

## Versão suportada

A linha `0.2.x` em desenvolvimento recebe correções de segurança. O projeto é
privado e ainda não possui release distribuível aprovada.

## Relato responsável

Use um GitHub Security Advisory privado no repositório. Não publique detalhes
exploráveis em issue, pull request ou discussão pública antes da triagem.

Inclua, quando disponível:

- versão, commit e sistema operacional;
- pré-condições e passos mínimos de reprodução;
- impacto observado e impacto potencial;
- arquivos de prova sanitizados, sem credenciais ou dados pessoais;
- sugestão de mitigação, sem exigir divulgação antecipada.

## Gates obrigatórios

O CI executa:

- `pip-audit` no ambiente resolvido pelo `poetry.lock`;
- Bandit para achados de alta severidade em `src`;
- testes Linux e Windows;
- cobertura de linhas e branches com piso incremental;
- mypy incluindo corpos de funções sem anotação.

Nenhuma execução limpa garante ausência futura de vulnerabilidades. O lock deve
ser auditado novamente antes de cada release e sempre que uma dependência mudar.
