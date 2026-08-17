# Evidência — Auditor visual reproduzível

## Identificação

- Commit testado: `3a31525c9d34df3fdee30b2020b2ba6887754d0b`
- Branch: feature branch (identifier omitted by repository hygiene policy).
- Data: 2026-08-16
- Escopo: captura real da `MainWindow` e auditoria automática dos PNGs produzidos.

## Ambiente

- Sistema: Windows, Python 3.11.9 64-bit
- Pillow: 12.3.0
- OpenCV: 4.12.0
- Qt: PySide6 do ambiente virtual do projeto
- Dependências: ambiente `.venv` já existente; nenhuma dependência nova foi instalada.

## Objetivo e contrato

O auditor lê cada PNG com Pillow e OpenCV, confere dimensões e bytes por SHA-256,
analisa alfa/transparência, mede atividade nas bordas, valida geometrias reais
capturadas pelo Qt, detecta clipping de widgets e sobreposição entre irmãos,
confere as cores obrigatórias do QSS escuro e gera uma imagem anotada por PNG.

O resultado é fail-closed: qualquer PNG ausente, não catalogado, ilegível,
alterado, transparente em captura, com geometria inválida, clipping,
sobreposição ou paleta ausente produz `FAIL`. O relatório não depende de
inspeção humana para decidir `PASS` ou `FAIL`.

## Comandos executados

```text
.\.venv\Scripts\python.exe -m pytest tests/test_visual_artifact_auditor.py -q
.\.venv\Scripts\python.exe scripts\audit_ui_capture.py --output docs/evidence/artifacts/remediation-pr63-73-2026-08-16/visual-audit-final/input
.\.venv\Scripts\python.exe scripts\audit_visual_artifacts.py --input docs/evidence/artifacts/remediation-pr63-73-2026-08-16/visual-audit-final/input --output docs/evidence/artifacts/remediation-pr63-73-2026-08-16/visual-audit-final/output
.\.venv\Scripts\python.exe -m pytest -q
python tools/evidence_integrity.py --require-tracked
```

## Resultados

- Testes do auditor: `4 passed`.
- Suíte completa: `1126 passed`, `0 failed`, `0 skipped`; `10` warnings Qt de depreciação já existentes.
- Capturas: três resoluções, cinco estados por resolução, mais o fixture de imagem.
- PNGs auditados: `16`; PNGs anotados: `16`.
- Auditor real: `PASS`, `0` findings.
- Reprodutibilidade: duas execuções independentes tiveram SHA-256 idêntico em todos os PNGs e fixtures.
- Integridade do pacote: `36` arquivos indexados no `visual-audit-index.json`.

## Artefatos

- Entrada e manifesto Qt: `docs/evidence/artifacts/remediation-pr63-73-2026-08-16/visual-audit-final/input/`
- PNGs anotados e relatório: `docs/evidence/artifacts/remediation-pr63-73-2026-08-16/visual-audit-final/output/`
- Índice de bytes/SHA-256: `docs/evidence/artifacts/remediation-pr63-73-2026-08-16/visual-audit-final/visual-audit-index.json`
- Relatório automático: `visual-audit-report.json` e `visual-audit-report.md` no diretório `output`.

## Cenários negativos cobertos

Os testes alteram intencionalmente uma imagem para provocar mismatch de hash,
produzem alfa parcial para provocar falha de transparência e deslocam um widget
para provocar sobreposição. Todos foram rejeitados pelo auditor. Nenhum teste
altera regra, usa `skip`, `xfail`, mock do comportamento auditado ou recalcula
hash para transformar falha em aprovação.

## Limitações declaradas

- A validação de clipping é geométrica e determinística: compara os widgets Qt
  visíveis com os limites da captura e com seus pais/irmãos. Ela não afirma
  reconhecimento semântico de glifos individuais nem substitui uma referência
  tipográfica por fonte diferente.
- O modo Qt usado é `offscreen`, conforme o gerador existente; isso comprova o
  layout renderizado nesse ambiente, não todos os drivers de composição de uma
  sessão interativa.
- `CuPy not found. Fallback to CPU processing.` foi emitido durante a captura;
  não bloqueou a captura nem alterou o contrato visual, mas permanece registrado
  como condição do ambiente.

## Decisão

**APROVADO no escopo do auditor automatizado e dos artefatos reproduzíveis acima.**
Isso não transforma a validação em aprovação geral da aplicação nem substitui
os gates de push, merge, CI e eventual inspeção interativa do Windows.
