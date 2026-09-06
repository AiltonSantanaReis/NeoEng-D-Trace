# Evidência — Caneta: saída da edição por clique vazio

ID: `PEN-EMPTY-CLICK-EDIT-EXIT-20260905`
Data: `2026-09-05`
Status: `PASS_LOCAL / BLOCKED_NATIVE_REMOTE`
Branch: `Ailton/pen-handles-quantization-20260905`
Commit auditado: `a554e4dc9e63890ac2436e7aa4f19fe1fbd99b6f`
Commit pai funcional: `cab473a40d13927a90e025a5b37c97efc1e96ec3`
Base histórica do lote: `5b3e6b15cee93ef5c9d1d550745293fb8372b5b9`

## Objetivo e decisão de interação

Investigar o estado que mantinha a Caneta presa ao último Bézier fechado e
definir o comportamento de clique fora com referência às ferramentas locais.

- Um Bézier fechado continua carregado para edição de âncoras e alças.
- Clique fora de todas as âncoras/alças encerra a edição local e deseleciona;
  não cria ponto nem entrada de histórico.
- O clique seguinte, com a Caneta limpa, é o início explícito de outro
  caminho.
- Clique em âncora/alça mantém a edição existente; fechamento no primeiro
  vértice continua usando o comando transacional.
- Rejeições geométricas continuam controladas e sem mutação parcial.

Essa decisão foi comparada ao `SelectionTool`, que deseleciona em clique vazio,
e às ferramentas de laço/forma, que tratam a criação como gesto separado e
limpam a prévia após commit. Não foi feita alegação de equivalência integral
com um produto externo.

## Causa raiz e alteração

Após `commit_selection(closed=True)`, o objeto criado permanecia carregado
para edição, mas `_clear_loaded_bezier_object()` não redefinia `_closed`. O
próximo caminho podia receber nós sem nunca satisfazer a condição de
fechamento. A correção redefine `_closed` e o cursor transitório ao limpar o
objeto; o handler de clique vazio agora limpa/deseleciona e retorna sem
consumir o clique como novo ponto. O tooltip em inglês e português documenta
os dois passos.

Arquivos alterados no candidato:

- `src/tools/pen_tool.py`
- `src/ui/tool_palette_impl.py`
- `tests/test_pen_creation_gestures.py`

Snapshots históricos não foram reescritos.

## Ambiente e comandos

Ambiente Windows do worktree candidato: Python `3.11.9`, PySide6 via Poetry,
pytest `9.1.1`, PyInstaller `6.22.0`, plataforma reportada pelo build como
`Windows-10-10.0.26200-SP0`, arquitetura portátil `windows-x86_64`.

Comandos executados no worktree, todos com saída de sucesso:

```text
.\.venv\Scripts\python.exe -m pytest tests\test_pen_creation_gestures.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_pen_creation_gestures.py tests\test_functional_user_flows.py tests\test_stage3_professional_scene_editor.py tests\test_stage9_functional_ui_audit.py -q
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m flake8 src tests tools app.py pack_for_ai.py
.\.venv\Scripts\python.exe -m black --check --diff src tests tools app.py pack_for_ai.py
.\.venv\Scripts\python.exe -m isort --check-only --diff src tests tools app.py pack_for_ai.py
.\.venv\Scripts\python.exe -m mypy src
.\scripts\build_windows.ps1 -OutputRoot build\pen-handles-release-a554e4d-20260905
build\pen-handles-release-a554e4d-20260905\portable\NeoEng-D-Trace\NeoEng-D-Trace-CLI.exe --version
```

Resultados observados:

- Caneta: `51 passed`.
- Fluxos Caneta/paleta/UI: `75 passed`.
- Suíte oficial sem filtros: `2019 passed, 2 skipped, 1 warning`.
- Flake8: retorno `0`.
- Black: `369 files would be left unchanged`.
- isort: retorno `0`.
- mypy: `Success: no issues found in 148 source files`.
- CLI da build: `NeoEng-D-Trace-CLI.exe 0.3.0`, exit code `0`.

## Build e hashes

O manifesto versionado pela própria build registra `source_commit` igual ao
SHA auditado. O pacote local foi gerado em
`build/pen-handles-release-a554e4d-20260905/`.

| Artefato | Bytes | SHA-256 |
| --- | ---: | --- |
| `portable/NeoEng-D-Trace/NeoEng-D-Trace.exe` | 10281027 | `0de8a177416a491289a4f1f39b03e1dca40a885da1309fd091f38a7c80f39093` |
| `portable/NeoEng-D-Trace/NeoEng-D-Trace-CLI.exe` | 10169411 | `5f89481694b68560a412808fb19c165e98c2f6f5ccfb43bf696dc20951d76dda` |
| `NeoEng-D-Trace-0.3.0-win64-portable.zip` | 124243731 | `4cc95383463f0aaf581d5f6fe80f7afface8ae9263a6ba98b292b68345dadc07` |

Smoke checks da build: `cli-version`, `versioned-project-input`,
`headless-project`, `headless-json`, `headless-glb`, `godot-profile-json`,
`godot-release-glb`, `unity-profile-json`, `unity-release-glb`,
`gui-open-close`, `user-state-directory` — todos `SUCCESS`.

O PyInstaller registrou o warning não fatal `Hidden import "tzdata" not
found!`. Ele foi preservado nesta evidência e requer acompanhamento próprio;
não foi convertido silenciosamente em sucesso adicional.

## Limitações e decisão formal

O executável portátil foi gerado e teve apenas o smoke automatizado de
abertura/fechamento. A auditoria nativa de cliques — iniciar o `.exe`, clicar
em pontos reais, fechar, clicar fora, clicar novamente e observar a UI — não
foi executada: o helper de automação visual permaneceu indisponível antes do
primeiro clique, com falhas de processo/sandbox (`trusted Node process exited
unexpectedly` e `helper_unknown_error: apply deny-read ACLs`). Não há PNG
temporária ou captura antiga apresentada como prova deste SHA.

Portanto, o comportamento está `PASS` no harness Qt real e a build está
`PASS` no smoke local; o requisito de auditoria nativa permanece
`PENDING_EVIDENCE/BLOCKED`. CI remoto, push, merge, tag e release não foram
executados.
