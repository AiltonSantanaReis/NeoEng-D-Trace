# Registro de mudança — reconciliação do manifesto de baseline

**ID:** `CHG-POST-E13-BASELINE-RECONCILIACAO-20260914`
**Status:** `IN_PROGRESS`
**Data:** 2026-09-14
**Escopo:** baseline de integridade do checkout pós-E13
**Requisitos afetados:** `REQ-F12-QUALITY-GATES`
**Feature/componente:** `FEAT-QA-EVIDENCE-PACKAGE`, `MOD-TOOLS-EVIDENCE`
**Testes afetados:** `TEST-QA-EVIDENCE-MANIFEST`, `TEST-QA-EVIDENCE-HASH`, `TEST-QA-EVIDENCE-COMMIT`

## Causa

O PR #174 falhou no passo remoto `Verify clean baseline manifest`, antes da
instalação de dependências ou da execução de testes. A investigação do log
oficial mostrou que o branch continha arquivos versionados pós-E13 que ainda
não estavam representados no `baseline_manifest.json`.

## Comparação auditada

| Estado | Data do manifesto | Arquivos elegíveis | SHA-256 do manifesto |
| --- | --- | ---: | --- |
| anterior no commit `cac6cd4` | 2026-09-12 | 3.496 | `784fb8e2c85506aa85b194b0b13b33e92ce23d81bb01c1abc759be5162d86b7f` |
| regenerado pelo gerador oficial | 2026-09-14 | 3.901 | calculado no artefato final; não duplicado neste documento para evitar auto-referência |

O aumento representa arquivos já versionados no branch, incluindo evidências,
testes e a integração Unity. Nenhum arquivo foi removido, ignorado para obter
`PASS` ou alterado semanticamente pelo gerador.

## Correção

`tools/baseline_integrity.py --write --git-blob` regenerou o manifesto a partir
dos blobs staged do Git. A verificação integral subsequente executou
`tools/baseline_integrity.py --verify --git-blob` e retornou:

```text
Baseline verified: 3901 files
```

## Impacto e proteção

- Nenhum código de produto, teste ou artefato foi apagado.
- O manifesto continua excluindo somente diretórios/arquivos locais definidos
  pelo contrato (`build`, caches e ambientes virtuais).
- Nenhum caminho proibido está rastreado.
- Os dois `skipped` controlados de symlink permanecem intactos e separados do
  resultado de baseline; não foram criados skips novos.
- A falha do PR #174 permanece preservada como evidência de diagnóstico e não
  será reclassificada como sucesso.

## Validação e vínculo

O checkout local passou a verificação oficial do manifesto, os gates de
continuidade/governança e a suíte completa `2651 passed, 2 skipped`. O commit
corretivo e o resultado do novo PR deverão ser registrados aqui antes da
promoção do status para `PASS`.

## Dependências documentais

- [Governança de Integridade, Execução e Antialucinação](../GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md)
- [Índice Documental Ativo Canônico](../INDICE_DOCUMENTAL_ATIVO_CANONICO_2026-08-24.md)
- [Registro Canônico de IDs](../REGISTRO_IDS_PRODUTO_PROFISSIONAL_CANONICO_2026-08-24.yaml)
- `baseline_manifest.json`
