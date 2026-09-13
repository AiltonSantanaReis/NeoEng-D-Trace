# Registro de mudança — reconciliação da continuidade pós-E13

**ID:** `CHG-POST-E13-CONTINUIDADE-RECONCILIACAO-20260913`

**Estado:** `PASS`

**Data:** 2026-09-13

**Lote:** `POST-E13-SCENE-EDITOR-ASSET-PACKS`

**Branch atual:** `Ailton/audit-post-e13-scenario-editor-20260912`

**HEAD após a mudança:** `9e2d2a20cdf49d82172e46bc959d9ef271cce4f4`

**Governança:** [`GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md`](../GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md)

**Evidência relacionada:** [`EVD_POST_E13_RUNTIME_REQUALIFICACAO_20260913.md`](EVD_POST_E13_RUNTIME_REQUALIFICACAO_20260913.md)

## Motivo

Os arquivos ativos `docs/CONTROLE_CONTINUIDADE_ATUAL.md` e
`docs/CONTROLE_CONTINUIDADE_ATUAL.json` ainda apontavam para a branch
`Ailton/e08-renderer-20260908`, para o produto `dd344f47` e para a próxima ação
de revisão humana. Esses valores eram válidos como histórico de um checkpoint
anterior, mas não descreviam o checkout usado nesta auditoria nem respeitavam a
decisão de manter a revisão humana adiada até o fechamento dos itens funcionais
abertos.

Isso criava risco operacional de uma nova conversa iniciar em uma base errada,
repetir etapas antigas ou promover a revisão humana antes da autorização.

## Escopo controlado

Foram atualizados somente os ponteiros de estado atual, sem reabrir E13 e sem
alterar código de produto:

- branch e HEAD do checkout sob auditoria;
- commit de produto atual (`422483e`) e commit do harness (`d7ddbef`);
- resultado da suíte oficial corrente (`2625 passed, 2 skipped, 5 warnings`);
- próxima ação autorizada, mantendo revisão humana em `PENDING_EVIDENCE`;
- referências atuais para a requalificação de Tilemap/híbrido e para a baseline
  de desempenho;
- escopo do lote, deixando a produção de novos modelos/asset packs e o gizmo
  para etapas explicitamente adiadas.

Os hashes, builds, commits antigos, skips, warnings e falhas históricas não
foram removidos. O valor antigo de `dd344f47` continua apenas como
proveniência do build/checkpoint em que foi produzido.

## Antes e depois

| Campo | Antes | Depois |
|---|---|---|
| Branch ativa | `Ailton/e08-renderer-20260908` | `Ailton/audit-post-e13-scenario-editor-20260912` |
| Produto sob auditoria | `dd344f47` | `422483e` |
| Harness de auditoria | não identificado no registro ativo | `d7ddbef` |
| HEAD documental | `dd344f47` | `9e2d2a2` |
| Suíte corrente | `2226/2/1` | `2625/2/5` |
| Próxima ação | solicitar revisão humana | fechar evidências funcionais/residuais; revisão humana somente após os gates exigidos |
| Modelos/gizmo | não explicitado no ponteiro corrente | adiado, sem alteração nesta mudança |

## Verificação

| Gate | Resultado | Estado |
|---|---|---|
| Validador estruturado `tools/validate_continuity_registry.py` | registry válido, E13 preservado como `TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING` | `PASS` |
| Contratos documentais | `55 passed` incluindo índice, estados, evidência, integridade e privacidade | `PASS` |
| Suíte oficial | `2625 passed, 2 skipped, 5 warnings`, sem filtros | `PASS` |
| Runtime Tilemap/híbrido | r3 pós-commit, engines reais, capturas e casos negativos | `PASS` técnico |
| Revisão humana final | ainda condicionada pela decisão formal | `PENDING_EVIDENCE` |

Esta mudança é documental e de continuidade. Não promove o lote, não executa
push/merge/tag/release, não altera thresholds e não transforma skips ou warnings
em aprovação.

## Critério de continuidade

O estado corrente deve ser obtido com `git rev-parse HEAD` no checkout atual;
os valores históricos devem ser lidos somente como proveniência. A próxima
execução deve usar a branch atual, ler a governança antes da etapa e apontar
para a requalificação pós-E13 de 20260913 antes de considerar qualquer revisão
humana.
