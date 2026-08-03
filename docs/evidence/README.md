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

- `ETAPA_2_INVENTARIO_FUNCIONAL_CARACTERIZACAO.md` — inventário, caracterização e riscos da Etapa 2 antes do merge.
- `ETAPA_2_ENCERRAMENTO_POS_MERGE.md` — validação da `main` e registro de encerramento da Etapa 2 depois do merge.


- `ETAPA_3_PACOTE_1_PERSISTENCIA_VERSIONADA.md` — implementação, auditoria e
  validação do formato de projeto v1.
- `ETAPA_3_PACOTE_1_ENCERRAMENTO_POS_MERGE.md` — validação da `main` e registro
  de encerramento do Pacote 1 da Etapa 3 depois do merge funcional.

- `ETAPA_4_ENCERRAMENTO_POS_MERGE.md` — validação da `main` e encerramento
  formal da Etapa 4 depois do merge.
- `ETAPA_4_EVIDENCE_MANIFEST.json` — manifesto estruturado da Etapa 4.

- `ETAPA_5_PACOTE_1_COMMAND_MANAGER_CONTRACT.md` — implementação e validação
  funcional do contrato, pilhas, transação e estado da UI.
- `ETAPA_5_PACOTE_1_ENCERRAMENTO_POS_MERGE.md` — validação da `main` e
  encerramento formal do Pacote 1 da Etapa 5.
- `ETAPA_5_PACOTE_1_EVIDENCE_MANIFEST.json` — manifesto estruturado do
  encerramento do Pacote 1 da Etapa 5.

- `ETAPA_5_PACOTE_2A_OBJECT_RELATIONS.md` — integridade transacional de
  identidade, relações, colisão, forma e limpeza no núcleo da cena.
- `ETAPA_5_PACOTE_2B_UI_COMMAND_PATHS.md` — remoção dos fallbacks manuais nos
  caminhos de interface cobertos pelos comandos do Pacote 2A.
- `ETAPA_5_PACOTE_3A_GIZMO_GESTURE.md` — prévia contínua e consolidação do
  movimento pelo gizmo em uma única operação reversível.
- `ETAPA_5_PACOTE_3B_VERTEX_EDITING.md` — movimento, inclusão e
  exclusão de vértices por transações reversíveis.
- `ETAPA_5_PACOTE_4A_OBJECT_DELETION.md` — exclusão simples e múltipla por comandos reversíveis.
