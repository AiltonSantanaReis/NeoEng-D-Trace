# E02-A — evidência do contrato de primitivas independentes

**Data:** 2026-09-08  
**Estado:** `TECHNICAL_CHECKPOINT_PASS_PENDING_BUILD_AND_FINAL_AUDIT`  
**Branch:** `Ailton/e02-primitives-20260908`  
**Escopo:** schema V2, validação geométrica, modelo de autoria e histórico
Undo/Redo.

## Entregas verificadas

- `src/persistence/independent_scene_schema.py`: V2 explícito, migração V1→V2,
  retângulo, elipse, polígono e path, transformação, visibilidade e bloqueio;
- `src/persistence/independent_scene_io.py`: serialização, leitura e hash de
  V1/V2, mantendo rejeição de V2 incompleto;
- `src/core/independent_scene_authoring.py`: operações validadas, seleção,
  duplicação, remoção e transformação;
- `src/core/independent_scene_session.py`: integração da autoria com save/load
  e histórico Undo/Redo;
- `src/ui/independent_scene_window.py`: comandos PT-BR/EN para as três formas e
  Undo/Redo, além da lista de objetos;
- `tests/test_independent_scene_primitives.py` e
  `tests/test_independent_scene_ui.py`: cobertura do fluxo técnico.

## Resultado dos testes focados

Comando:

```text
.venv\Scripts\python.exe -m pytest -q tests/test_independent_scene_primitives.py tests/test_independent_scene_contract.py tests/test_independent_scene_ui.py tests/test_continuity_registry.py tests/test_repository_reference_hygiene.py
```

Resultado observado: `29 passed`.

Casos cobertos: round-trip V2, upgrade sem mutar V1, quatro tipos geométricos,
pontos repetidos, auto-interseção, path aberto preenchido, escala/pivô inválidos,
três formas persistidas, Undo/Redo, duplicação, remoção, transformação e
objeto bloqueado.

## Limites deste sub-lote

Ainda não fecha E02: faltam edição livre de pontos/gestos, fluxo visual final do
binário, comparação completa de reabertura após todas as operações e build
oficial deste SHA. Symlink e revisão humana continuam reservados à auditoria
final do Plano Mestre.
