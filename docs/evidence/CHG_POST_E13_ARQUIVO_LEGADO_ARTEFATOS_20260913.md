# Registro de limpeza reversível — arquivo legado de evidências pós-E13

**ID:** `CHG-POST-E13-ARQUIVO-LEGADO-ARTEFATOS-20260913`

**Estado:** `PASS`

**Data:** 2026-09-13

**Lote:** `POST-E13-SCENE-EDITOR-ASSET-PACKS`

**Branch:** `Ailton/audit-post-e13-scenario-editor-20260912`

**Produto/harness preservados:** produto `422483e2b25f541fe3f1b4fdcf850ecb0147a744`; harness `d7ddbefba24706f071c6d89cf539558adfe214c4`

**Governança:** [`GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md`](../GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md)

**Continuidade:** [`CONTROLE_CONTINUIDADE_ATUAL.md`](../CONTROLE_CONTINUIDADE_ATUAL.md)

## Objetivo e escopo

Reduzir o risco de uma nova conversa interpretar execuções históricas como a
base ativa, sem apagar evidências ou alterar o produto. Foram selecionados
somente diretórios sem referência em `src/`, `scripts/`, `tests/` ou `docs/`
rastreados, identificados como execuções anteriores, duplicadas ou
superseded. Evidências citadas por documentos ativos e o pacote corrente da
suíte oficial ficaram em `artifacts/`.

## Operação executada

| Campo | Resultado |
|---|---|
| Operação | `REVERSIBLE_MOVE_TO_LEGACY` |
| Origem | `artifacts/` |
| Destino | `archive/legacy/artifacts/post-e13-historical-20260913/` |
| Diretórios selecionados inicialmente | `23` |
| Diretórios movidos e mantidos no legado | `22` |
| Diretórios restaurados por serem rastreados | `1` |
| Arquivos preservados no conjunto total | `554` |
| Bytes preservados no conjunto total | `60.668.542` |
| Exclusões permanentes | `0` |
| Manifesto pré-movimento inicial | [`manifest-pre-move.json`](../../archive/legacy/artifacts/post-e13-historical-20260913/manifest-pre-move.json) — SHA-256 `DA457EB7FD600A8C851E0BA604000804B4092E7A0D2B15A3D319E1043BEEBCB3` |
| Manifesto inicial preservado | [`archive-manifest-initial-23-dirs.json`](../../archive/legacy/artifacts/post-e13-historical-20260913/archive-manifest-initial-23-dirs.json) — SHA-256 `D8938B4ED6E737313DC52F8B5573A63663237992D0F9B50FC60205180B2A4D03` |
| Manifesto final | [`archive-manifest.json`](../../archive/legacy/artifacts/post-e13-historical-20260913/archive-manifest.json) — SHA-256 `2E89672381BEF30BFAFD5E773D41FF0BDBDF742F99379B23A9A800CA5529F666` |
| Auditoria da restauração | [`restoration-audit-mask-viewer-r3.json`](../../archive/legacy/artifacts/post-e13-historical-20260913/restoration-audit-mask-viewer-r3.json) — SHA-256 `0C9E05251F4F973B04520A1D3A497BDBCBC64EDA12B2BF2CD4FEF17C4E72BE7B` |

Diretórios preservados na origem por terem referência ativa ou serem evidência
corrente incluem os lotes de material, máscara referenciada, vetor, localização
final, performance `r1/r2/r5`, runtime híbrido/Tilemap `r3` e a suíte oficial
`audit-post-e13-official-suite-20260913-r1`.

## Diretórios movidos

```text
audit-post-e13-binary-collider-20260912-r1
audit-post-e13-binary-entity-20260912-r1
audit-post-e13-binary-entity-20260912-r2
audit-post-e13-binary-hybrid-20260912-r1
audit-post-e13-binary-navmesh-20260912-r1
audit-post-e13-binary-renderer-20260912-r1
audit-post-e13-binary-tilemap-20260912-r1
audit-post-e13-binary-tileset-20260912-r1
audit-post-e13-binary-ux-20260912-r1
audit-post-e13-localization-native-20260912-r2
audit-post-e13-localization-native-20260912-r3
audit-post-e13-localization-native-20260912-r4
audit-post-e13-localization-native-20260912-r5
audit-post-e13-localization-native-20260912-r6
audit-post-e13-localization-native-20260912-r7
audit-post-e13-localization-native-20260912-r8
audit-post-e13-localization-native-20260912-r9
audit-post-e13-native-source-20260912-r2
audit-post-e13-native-source-20260912-r3
audit-post-e13-performance-20260913-r3
audit-post-e13-performance-20260913-r4
post-e13-tilemap-runtime-engines-postperf-20260913-r2
```

## Gates de segurança

| Gate | Observação | Estado |
|---|---|---|
| Referência cruzada | Nenhum dos 23 nomes apareceu textualmente na árvore rastreada fora de `artifacts/` e `archive/` antes da movimentação; a checagem Git adicional detectou o diretório rastreado e ele foi restaurado | `PASS` |
| Caminhos | Origem validada dentro de `artifacts/`; destino validado dentro de `archive/legacy/`; nenhum destino preexistente | `PASS` |
| Preservação | Os 541 pares arquivados conferem com o manifesto final; os 13 pares restaurados conferem com a auditoria de restauração; o conjunto inicial de 554 permanece íntegro | `PASS` |
| Produto rastreado | A checagem detectou 13 arquivos rastreados no lote de máscara; eles foram restaurados antes do commit e o estado rastreado final voltou a ficar limpo | `PASS` |
| Reversibilidade | Cada diretório pode ser restaurado com movimento explícito do destino para `artifacts/`; nenhuma remoção permanente foi feita | `PASS` |

O README no destino explica os critérios e o manifesto contém a lista completa
de arquivos. A limpeza não promove, rebaixa ou substitui qualquer gate
funcional; os itens de desempenho em escala, diagnósticos Unity, limites do
vertical slice, gizmo, modelos e revisão humana continuam com os estados
registrados nos documentos ativos.

## Correção durante a limpeza

O diretório `audit-post-e13-binary-mask-viewer-20260912-r3` não tinha
referência textual, mas continha arquivos rastreados pelo Git. A ausência de
referência não era critério suficiente para arquivamento. O lote foi movido
temporariamente, detectado pela verificação `git diff`, restaurado para
`artifacts/` e comparado arquivo a arquivo antes de qualquer commit. O
manifesto inicial foi mantido como histórico da tentativa; o manifesto final
exclui esse diretório e o relatório de restauração documenta a integridade dos
13 arquivos.
