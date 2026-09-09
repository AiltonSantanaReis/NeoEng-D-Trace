# E13 — Fechamento técnico e portabilidade

**Estado:** `IN_PROGRESS`  
**Data de abertura:** 2026-09-09  
**Branch:** `Ailton/e08-renderer-20260908`  
**SHA de abertura:** `510cee7166eb90026c22e3b922d45d3624bb4c91`  
**Worktree oficial:** `build/e01-independent-scene-20260908`

## Autoridade e escopo

Este relatório é subordinado à governança em
`docs/GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md`, à
`docs/PLANO_MESTRE_ESTABILIZACAO.md`, ao plano de migração MSI R-016 e à fila
central `docs/evidence/PLANO_MESTRE_FILA_EXECUCAO_CENTRAL_2026-09-09.md`.

O lote fecha tecnicamente a portabilidade do produto já comprovado em E12:
pacote portátil final, instalador MSI per-user, instalação/desinstalação,
rollback/preservação de estado, auditoria de referências locais, manifestos e
limitações. Symlink e revisão humana não pertencem a este sublote e continuam
reservados para E13-D na auditoria final.

## Metas e critérios objetivos

| Meta | Estado inicial | Critério de saída |
|---|---|---|
| E13-A — pacote portátil final | `IN_PROGRESS` | build limpa r70 ou posterior, `source_commit`, manifesto, hash do binário e ZIP, smoke completo e execução fora do checkout |
| E13-B — MSI/instalador | `PLANNED` | WiX 4.0.6 pinado, MSI hashado, instalação per-user, execução CLI/GUI/exportação, desinstalação sem resíduos e estado do usuário preservado |
| E13-C — documentação/privacidade | `PLANNED` | referências locais removidas dos artefatos versionados, manifestos coerentes, limitações e rollback documentados |
| E13-D — auditoria final | `DEFERRED_UNTIL_FINAL_AUDIT` | somente no pacote final: symlink, revisão humana, findings e decisão formal |

Nenhuma meta muda para `PASS` antes de possuir teste executado, artefato,
hash, resultado observado, limitação e commit correspondente.

## Análise de impacto

- **Módulos afetados:** `scripts/build_windows.ps1`,
  `scripts/build_installer.ps1`, `tools/package_portable_release.py`,
  `tools/package_windows_msi.py`, `tools/validate_portable_release.py` e
  `tools/validate_windows_installer.py`.
- **Contratos preservados:** versão `0.3.0`, nomes dos executáveis, manifesto
  portátil, `source_commit`, estado por usuário e `UPGRADE_CODE` do MSI.
- **Riscos:** build fora da origem declarada, conteúdo instalado divergente,
  resíduos de desinstalação, vazamento de caminhos pessoais e não
  determinismo do pacote.
- **Proteções:** build exige checkout limpo; o MSI valida o manifesto portátil
  antes de empacotar; WiX é fixado em `4.0.6`; smoke e instalação são
  executados por scripts fail-closed; a auditoria final preserva symlink e
  revisão humana como gates distintos.

## Evidência executada até a abertura

| Evidência | Resultado | Referência |
|---|---|---|
| Registro canônico | `PASS` | `tools/validate_continuity_registry.py`, E13 ativo |
| E12 predecessor | `TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING` | build r69, smoke 11 checks, suíte `2104 passed, 2 skipped, 1 warning` |
| Binário predecessor | `PASS_LOCAL` | SHA-256 `07D3B3FBFAD22518628A8E8405FEA69E783750BBBD9593786A8E049781203152` |
| Captura predecessor | `PASS_AUTOMATED_CAPTURE_ONLY` | `artifacts/e12-binary-capture-r69-20260909/` |
| Symlink | `DEFERRED_UNTIL_FINAL_AUDIT` | não executar nesta fase |
| Revisão humana | `DEFERRED_UNTIL_FINAL_AUDIT` | não executar nesta fase |

## Comandos previstos e artefatos obrigatórios

Os comandos devem ser executados a partir do worktree oficial, com o Python
canônico do workspace (`<workspace-root>/.venv/Scripts/python.exe`). Caminhos
pessoais não devem ser gravados em manifestos, relatórios ou pacotes:

1. `tools/validate_continuity_registry.py`;
2. suíte oficial completa e gates estáticos;
3. `scripts/build_windows.ps1` para o pacote portátil r70 ou posterior;
4. `tools/validate_portable_release.py` no bundle e em uma cópia fora do
   checkout;
5. `scripts/build_installer.ps1` ou seus passos equivalentes, após validar a
   origem e o hash do pacote portátil;
6. `tools/validate_windows_installer.py` para instalação, execução,
   exportação, desinstalação e preservação do estado;
7. auditoria documental de referências locais, hashes e manifestos.

Os resultados brutos, relatórios JSON, hashes e capturas serão anexados a este
relatório somente após a execução corrente. Evidência histórica de E12 não é
reclassificada como evidência de E13.

## Decisão de abertura

`E13` está autorizado para execução técnica contínua no mesmo worktree. O
estado permanece `IN_PROGRESS` até que E13-A, E13-B e E13-C tenham critérios
comprovados por artefatos rastreados e commit. E13-D continua explicitamente
adiado para a auditoria final; não há aprovação de release, push, merge ou tag.
