# Etapa 7 — Painéis laterais da interface moderna

**Estado atual:** `PASS_LOCAL / NÃO APROVADA`

Esta evidência registra a implementação e a validação local da Etapa 7 no
commit `9ee591615d30f98037e8506f513c4c2635fb207d`. A etapa ainda depende dos
gates remotos, revisão da PR, CI no SHA exato, merge autorizado e validação
pós-merge. Não é aprovação de release.

## Escopo e baseline

O escopo foi limitado à inconsistência comprovada entre os painéis `Layers`
e `Groups`. O `LayersPanel` já usava uma `QToolBar` compacta com ícones
vetoriais, enquanto o `GroupsPanel` ainda apresentava oito `QPushButton` em
quatro linhas de texto. O baseline local antes da alteração foi reproduzido
no `main` em `bd6ed662aee0d34a892bf7e60ca78f51d5318792`:

- 19 testes focados de UI passaram;
- o auditor visual geral passou com zero findings nas três resoluções;
- não foi encontrado clipping ou sobreposição atual que justificasse uma
  alteração genérica de `QScrollArea`, largura de dock, `SidePanel` ou
  `CollisionPanel`.

Essa distinção é importante: o trabalho corrigiu uma inconsistência visual e
de densidade de comandos demonstrada no código, sem alegar que havia um
defeito de clipping que o baseline não reproduziu.

## Implementação comprovada

Foram alterados somente:

- `src/ui/groups_panel.py` — toolbar compacta `groups_action_toolbar`, com os
  oito comandos existentes, ícones da biblioteca interna, tooltips, tamanho
  16×16 e handles `btn_*` legados preservados e ocultos;
- `scripts/audit_stage7_side_panels.py` — auditor nativo Windows para
  geometrias Qt, ações, tooltips, visibilidade e acessibilidade do painel;
- `tests/test_stage7_side_panels.py` — regressões para geometria, comandos,
  tradução, visibilidade do painel e acionamento real de ação.

Não foram removidos comandos, alterados contratos de persistência, modificados
os painéis `Objects`/`Collision`, alteradas regras de CI ou reduzidas
asserções.

## Execuções reais

Ambiente: Windows, Python 3.11.9, PySide6, backend Qt `windows`.

Comandos executados no commit acima:

```text
.\.venv\Scripts\python.exe -m pytest -q
1612 passed, 2 skipped

.\.venv\Scripts\python.exe -m pytest -q tests/test_stage7_side_panels.py tests/test_ui_responsive_layout.py tests/test_ui_defect_regressions.py tests/test_stage_11_ui_panel_branch_coverage.py --tb=short
22 passed

.\.venv\Scripts\python.exe -m py_compile src\ui\groups_panel.py scripts\audit_stage7_side_panels.py tests\test_stage7_side_panels.py
.\.venv\Scripts\python.exe -m black --check src\ui\groups_panel.py scripts\audit_stage7_side_panels.py tests\test_stage7_side_panels.py
.\.venv\Scripts\python.exe -m isort --check-only src\ui\groups_panel.py scripts\audit_stage7_side_panels.py tests\test_stage7_side_panels.py
.\.venv\Scripts\python.exe -m flake8 src\ui\groups_panel.py scripts\audit_stage7_side_panels.py tests\test_stage7_side_panels.py
PASS

.\.venv\Scripts\python.exe scripts\audit_stage7_side_panels.py --output <diretorio-local-de-saida>
PASS, 0 findings, 3 resoluções

.\.venv\Scripts\python.exe scripts\audit_ui_capture.py --output <diretorio-local-de-saida>
.\.venv\Scripts\python.exe scripts\audit_visual_artifacts.py --input <capturas> --output <auditoria>
PASS, 0 findings

.\.venv\Scripts\python.exe tools\evidence_integrity.py --git-blob
Evidence integrity passed: 104 manifests validated.

.\.venv\Scripts\python.exe -m pytest -q tests/test_evidence_privacy.py --tb=short
3 passed
```

Os marcadores `<diretorio-local-de-saida>` são deliberados: o relatório
versionado não expõe caminhos do computador. A reprodução deve usar uma pasta
local escolhida pelo executor.

## Evidências hashadas

Pacote: `artifacts/ui-modernization-stage7-20260822/`.

- `post-checkpoint-captures/manifest.json` — 130167 bytes — SHA-256
  `516de9f5dd17bcd5d6392eee00fc6840bb1189c23a06272988989026f2a2a0d4`;
- `post-checkpoint-visual-audit/visual-audit-report.json` — 15678 bytes —
  SHA-256 `74e4dcc41870f593cd3c209dee9788ec81a1620bed68924bb6d6d056277f12a0`;
- `groups-panel-audit-post-checkpoint/stage7-side-panels-report.json` — 3385
  bytes — SHA-256
  `6f5244669b6b48c2c00557f37d155314fb9c33e02b5b6e49cf953ec91a34b35f`;
- `stage7-execution-summary.json` — 1426 bytes — SHA-256
  `8ebc631fcfd3cb75d6426f564fa761dd273eb22d870849a3f61139413d3dbaa3`;
- `artifact-index.json` — 23873 bytes — SHA-256
  `425d8a91cc37dfcd4ce47a7009fbe6403af1b19bd76305540cb3bd7c4f287806`.

O auditor específico capturou `1920×1080`, `1366×768` e `1280×720`. Cada
captura registrou oito ações, ícones 16×16, toolbar dentro do painel, lista
renderizada e zero findings.

## Falha intermediária de evidência e tratamento

Uma tentativa de guardar o stdout bruto dos testes dentro do pacote falhou
legitimamente no teste de privacidade porque o `rootdir` absoluto do Windows
foi incluído no log; o próprio teste também reimprimiu o padrão detectado.
Os logs foram preservados fora do pacote versionado, não foram usados como
prova, e o pacote final não contém caminhos locais. Após a retirada desses
logs, a suíte completa e o teste de privacidade passaram novamente.

## Limitações e gates pendentes

- `worktree_clean=false` no relatório local porque existem diretórios locais
  de artefatos não rastreados preservados; isso não foi apresentado como
  árvore limpa;
- revisão visual humana das capturas não foi declarada nem substituída pelo
  auditor automatizado;
- PR, CI remoto, merge autorizado e validação pós-merge ainda não foram
  executados nesta etapa.

## Decisão

**PASS_LOCAL:** a melhoria comprovada foi implementada integralmente no
escopo limitado e validada com testes reais, auditoria Qt nativa, capturas,
hashes, integridade e privacidade. **A Etapa 7 permanece não aprovada** até
os gates remotos e pós-merge serem concluídos sem alterar as regras.
