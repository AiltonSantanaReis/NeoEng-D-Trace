# E02-A — evidência do contrato de primitivas independentes

**Data:** 2026-09-08  
**Estado:** `TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING`
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
  Undo/Redo, lista de objetos e preview determinístico renderizado no canvas,
  usando tokens semânticos do tema;
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
objeto bloqueado. A suíte oficial completa no mesmo worktree resultou em
`1985 passed, 2 skipped, 1 warning`.

## Build oficial e captura real

- build: `release/e02-primitives-20260908-r4/`;
- source commit: `d709f24f07b3576ae220d9c77e16ae7fe4279975`;
- binário: `portable/NeoEng-D-Trace/NeoEng-D-Trace.exe`;
- SHA-256 do binário: `2C445EC4A9C21DFBF96E423D1079D00D112F3A3ECE27996540342C87EEE6A970`;
- SHA-256 do ZIP portátil: `3C8C66F26F445017DD794A5110A09CEBFA213393627D8D8FDBEFEE0848CADF0D`;
- smoke portátil: `SUCCESS`, 11 checks;
- captura principal: `artifacts/e02-primitives-20260908/captures-r4/03-independent-scene-primitives.png`;
- SHA-256 da captura principal: `C60B12A45CD3FA60C4479CBE6D8B8368C79C57478230A951CA9EC329297DA62B`;
- janela observada: `1986x1431`;
- entrada real: `Ctrl+Shift+R`, `Ctrl+Shift+E`, `Ctrl+Shift+P`;
- resultado observado: retângulo, elipse e polígono desenhados no canvas, lista
  de objetos em PT-BR e metadados `3 objetos` visíveis.

## Finding corrigido no mesmo lote

A captura r3 (`253D029CDCC8439772FEE38F52FB4C629A6287DBF7F671AB84FDEFA1198C2F64`)
mostrou que a lista e os contadores eram atualizados, mas o canvas permanecia
vazio. A causa era a ausência de um renderer visual no widget de preview. A
correção foi aplicada em `d709f24`, com teste de contagem/renderização no widget,
revalidação da suíte completa e nova captura r4 acima. As cores do preview usam
`THEME_TOKENS`; nenhuma exceção foi adicionada ao contrato visual.

## Limites deste sub-lote

Ainda não fecha E02: faltam edição livre de pontos/gestos e comparação completa
de reabertura após todas as operações. Symlink e revisão humana continuam
reservados à auditoria final do Plano Mestre.
