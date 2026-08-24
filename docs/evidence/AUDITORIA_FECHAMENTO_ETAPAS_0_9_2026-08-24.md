# Auditoria de fechamento — Etapas 0–9 — 2026-08-24

## Decisão executiva

**Resultado automatizado:** PASS técnico do código e da build dedicada, com dois bloqueios de governança dos auditores históricos e revisão humana ainda pendente.

**Decisão formal:** as Etapas 0–9 **não são declaradas concluídas sem ressalvas neste momento**. A build está pronta e identificada para revisão humana, mas a declaração formal exige: (1) revisão humana da própria build; (2) reconciliação dos auditores históricos Stage 1 e Stage 5; e (3) execução do empacotador oficial baseado em Poetry ou registro formal da equivalência aceita.

Não foi encontrado defeito funcional novo do produto nesta rodada. Os bloqueios abaixo não foram ocultados e não foram convertidos em PASS artificial.

## Escopo congelado e governança

- SHA auditado: `9b4a4fd49ee4dfe28c8997a9eb4621df373c1026`
- Branch: `Ailton/stage9-postmerge-documentation`
- O checkout de trabalho contém artefatos históricos não rastreados; ele não foi usado para gerar a build.
- A build foi gerada em clone limpo do SHA acima.
- Escopo exclusivo: Etapas 0–9 da interface e seus contratos de persistência/GUI necessários.
- Fora do escopo desta build: Etapas 10+, perfis Godot/Unity/Phaser, aprovação de release e qualquer teste de etapa posterior.

## Matriz de evidências

| Etapa | Resultado desta rodada | Evidência principal | Observação precisa |
|---|---|---|---|
| 0 | PASS automatizado | `source-ui-capture/visual-audit/visual-audit-report.json`; suíte completa; baseline integrity | Capturas atuais decodificadas, geometria e paleta sem achados. |
| 1 | CONDICIONAL — auditor histórico incompatível | `source-ui-capture/stage1-baseline-report.json`; testes Stage 1 | O comparador encontrou 192 deltas contra o baseline Stage 0, porque compara contra uma arquitetura anterior às Etapas 3–9. Isso é um bloqueio do contrato do auditor, não prova de defeito do produto. |
| 2 | PASS automatizado | `source-stage2-dpi/stage2-dpi-matrix-report.json` | Workers 100/125/150/200%; falhas vazias; auditor visual zero achados. |
| 3 | PASS automatizado | `source-ui-capture/visual-audit/visual-audit-report.json`; testes Stage 3 | Captura atual do shell e auditor visual fail-closed passaram. |
| 4 | PASS automatizado | `source-ui-capture/visual-audit/visual-audit-report.json`; testes Stage 4 | Top toolbar, menus e regiões do shell presentes na captura atual; zero achados visuais automatizados. |
| 5 | CONDICIONAL — auditor histórico incompatível | `artifacts/stage0-9-final-audit-20260824/source-stage5-legacy-auditor/stage5-viewport-hud-report.json`; `tests/test_stage5_viewport_hud.py` | Auditor antigo exige texto legado (`VIEW: LIT ...`) e largura 72–84; o contrato vigente testado exige HUD compacto (`VIEW:LIT | Z:...`) e largura <=84. O auditor precisa ser reconciliado. |
| 6 | PASS automatizado nativo Windows | `artifacts/stage0-9-final-audit-20260824/source-stage6-native-auditor/stage6-gizmo-report.json` | 24 capturas, 3 resoluções, 8 estados por resolução, zero falhas. |
| 7 | PASS automatizado nativo Windows | `source-stage7-panels/stage7-side-panels-complete-report.json` | Painéis Objects/Layers/Groups/Collision, toolbars e contratos verificados; zero achados. |
| 8 | PASS automatizado | `source-stage8-scenario-annotated/visual-audit-report.json`; `source-stage8-scenario/manifest.json` | Capturas do editor de cenários, geometria/overlap/clipping e auditor visual; zero achados. |
| 9 | PASS automatizado, revisão humana pendente | `source-stage9-functional/report.json`; `source-stage9-dpi/stage9-responsive-dpi-report.json` | Ações funcionais, geometria, menu, scroll, gizmo, camadas e modos X-Ray passaram; DPI 100/125/150/200% em 1280x720, 1366x768 e 1920x1080 passou. |

## Suíte completa

Arquivo: `artifacts/stage0-9-final-audit-20260824/source-full-suite.log`

Resultado comprovado no arquivo:

```text
1649 passed, 2 skipped in 39.71s
```

Os dois skips são os casos condicionais já existentes; não foram criados para obter aprovação.

## Build dedicada para revisão humana

Arquivo: `artifacts/stage0-9-final-audit-20260824/build/NeoEng-D-Trace-STAGE0-9-REVIEW-20260824-win64-portable.zip`

- Tipo: Windows x86_64, portable onedir.
- SHA-256: `a2f070d69873c6d6cc0ac5934786e5149ec6a6daf71ad0749274e13e78a0c45d`
- Tamanho: `1,551,829,839` bytes.
- Manifesto: `build/release-manifest.json`.
- Índice completo de hashes: `artifacts/stage0-9-final-audit-20260824/artifact-index.json`.
- Smoke report: `build/stage0-9-build-smoke.json`.

Smoke comprovado na própria build:

- CLI `--version`: saída 0, versão `0.3.0`.
- Round-trip genérico `--headless`: saída 0, projeto e JSON gerados.
- GUI `--smoke-test-gui`: saída 0; `application.opened`, `application.state.saved` e `application.closed` presentes com sucesso.

A build foi produzida diretamente com PyInstaller 6.22.0 a partir do spec oficial porque `poetry` não está instalado neste ambiente. O script oficial `scripts/build_windows.ps1` não foi declarado como executado. Essa diferença é uma limitação de reprodutibilidade do pipeline, não foi mascarada.

Avisos observados durante o empacotamento/execução:

- `tzdata` não localizado pelo hook do PyInstaller.
- DLLs opcionais `cuTENSOR`/`cuTENSORMg` não localizadas.
- A inicialização GUI registrou falha opcional de CuPy e fez fallback para CPU.

O smoke da GUI passou; esses avisos permanecem registrados para a revisão humana e não foram promovidos a falha das Etapas 0–9.

## Bloqueios reais para “sem ressalvas”

1. **Revisão humana ainda não executada.** Os PNGs e a build estão prontos, mas nenhuma aprovação visual/usabilidade humana pode ser inferida do PASS automatizado.
2. **Auditor Stage 1 histórico incompatível com a arquitetura final.** O relatório preserva as 192 diferenças; é necessário alinhar o baseline/comparador ao estado pós-Etapa 9 ou documentar formalmente a regra de comparação por fase.
3. **Auditor Stage 5 histórico incompatível com o contrato vigente.** É necessário atualizar o auditor para o HUD compacto e para a faixa de layout vigente, mantendo os testes atuais como referência.
4. **Wrapper oficial não executado.** A equivalência direta PyInstaller passou pelos smoke tests, mas não prova execução do fluxo Poetry do script oficial.
5. **CI do SHA desta auditoria não foi reexecutado nesta rodada.** O PASS de CI informado para a PR #160 permanece evidência histórica do merge, não evidência nova deste fechamento.

## Conclusão

A evidência atual sustenta: **código funcional aprovado automaticamente; build dedicada executável; nenhuma falha funcional nova comprovada; revisão humana pronta para começar**.

A evidência atual não sustenta honestamente: **“Etapas 0–9 concluídas formalmente sem ressalvas”**. Essa conclusão só deve ser emitida depois que os quatro bloqueios acima forem encerrados e reauditados.