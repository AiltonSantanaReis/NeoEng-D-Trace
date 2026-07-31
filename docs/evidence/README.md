# Evidências de validação

Cada etapa deve criar um arquivo `ETAPA_<numero>_<nome>.md` baseado no modelo abaixo.

## Modelo obrigatório

```markdown
# Evidência — Etapa N

## Identificação
- Commit:
- Branch:
- Data/hora:
- Responsável:

## Ambiente
- Sistema operacional:
- Python:
- Dependências/lockfile:

## Objetivo e escopo

## Entradas
- Arquivo:
- SHA-256:

## Comandos executados

## Resultados
- Aprovados:
- Reprovados:
- Ignorados:
- Bloqueados:
- Cobertura:

## Artefatos

## Falhas e causa raiz

## Limitações e riscos residuais

## Decisão
APROVADO | REPROVADO | BLOQUEADO | PARCIAL | NÃO TESTADO
```

Uma captura isolada, relato verbal ou resultado sem commit identificado não é evidência suficiente.

## Evidências registradas

- `ETAPA_1_AMBIENTE_REPRODUZIVEL_CI_WINDOWS_LINUX.md` — validações da Etapa 1
  anteriores ao merge.
- `ETAPA_1_ENCERRAMENTO_POS_MERGE.md` — validação da `main` e encerramento
  formal da Etapa 1 depois do merge.
