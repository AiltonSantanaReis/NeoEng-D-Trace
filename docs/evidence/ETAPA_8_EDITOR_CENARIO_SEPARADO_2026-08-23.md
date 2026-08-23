# Etapa 8 — Editor de cenário separado — evidência local

- Data da execução: 2026-08-23
- Plano: docs/PLANO_INTERFACE_MODERNA_PROFISSIONAL_2026-08-21.md
- Escopo: Etapa 8 do plano de interface moderna profissional.
- Commit de implementação validado: c11d56f7359db3d5a1b8646caa635e4b42bd820a
- Branch: Ailton/stage8-scenario-editor-completion-20260823
- Ambiente: Windows 10, Python 3.11.9, PySide6, backend Qt offscreen para a captura automatizada.
- Política: esta evidência não altera regras, thresholds, governança ou contratos para produzir PASS.

## Decisão atual

PASS_LOCAL_AUTOMATED e PASS_HUMAN_VISUAL_REVIEW.

A Etapa 8 ainda permanece NÃO CONCLUÍDA FORMALMENTE até que os gates remotos (push, PR, CI, revisão dos checks, merge autorizado e validação pós-merge) sejam executados e registrados. Não há declaração de release nesta evidência.

## Implementação verificada

A janela dedicada ScenarioEditorWindow mantém o editor principal separado e fornece:

- viewport próprio;
- layer stack selecionável com adicionar, remover, renomear, reordenar, visibilidade e bloqueio;
- inspector rolável;
- camera preview;
- parallax;
- sockets;
- overlays visuais sem mutação do documento;
- modos Authoring e Preview read-only;
- undo/redo próprio;
- salvamento/recarregamento do sidecar;
- exportação determinística do runtime;
- estado dirty preservado ao fechar/reabrir.

O contrato do auditor foi alinhado à hierarquia Qt real: o inspector profissional está dentro de professional_inspector_scroll; overflow vertical explícito é permitido somente quando o QScrollArea correspondente existe. Clipping horizontal, fora da área rolável ou sem evidência do scroll continua sendo FAIL.

## Matriz dos 16 critérios da Etapa 8

| Critério | Verificação real | Resultado |
|---|---|---|
| Janela dedicada aberta pela integração | tests/test_stage4b3_scenario_authoring.py e testes Stage 8 | PASS |
| Componentes obrigatórios acessíveis | test_dedicated_surface_has_required_components_and_isolated_close | PASS |
| Carga sem alterar documento principal | test_layer_stack_and_transform_use_the_same_professional_session | PASS |
| Seleção refletida em viewport, layer stack e inspector | test_selection_is_reflected_in_viewport_layer_stack_and_inspector | PASS |
| Movimento como uma transação de cenário | teste compara o histórico antes/depois | PASS |
| Transformação numérica persistente | test_numeric_save_reload_and_export_are_real_v2_artifacts | PASS |
| Operações de layer | test_layer_stack_covers_add_remove_rename_reorder_visibility_lock_and_selection | PASS |
| Câmera, parallax e sockets | test_camera_parallax_sockets_and_overlay_contracts_are_editable | PASS |
| Overlay somente visual | test_overlay_changes_rendered_pixels_without_mutating_document | PASS |
| Authoring/Preview e bloqueio de mutação | testes de preview read-only e bloqueio de drop | PASS |
| Undo/redo isolado do editor principal | test_scenario_undo_redo_and_close_preserve_state_without_main_history | PASS |
| Save/modify/reload byte-stable | test_numeric_save_reload_and_export_are_real_v2_artifacts | PASS |
| Export schema/bytes/hash | test_export_is_schema_valid_deterministic_and_hash_bound | PASS |
| Fechamento dirty sem perda | test_professional_dirty_state_survives_close_reopen_and_save | PASS |
| Matriz de resoluções e auditoria visual | capturas 1280x720, 1366x768, 1920x1080; relatório visual com zero findings | PASS |
| Regressão do editor principal | suíte completa e suites Stage 4B/Stage 3 | PASS |

## Execuções e resultados

1. Teste focado com JUnit:

    pytest -q tests/test_stage8_scenario_editor_separation.py --junitxml=...
    17 passed in 2.61s

2. Suíte completa com o comando equivalente ao CI:

    pytest -q --cov=src --cov-branch --cov-fail-under=90 --cov-report=term --cov-report=xml
    1644 passed, 2 skipped in 62.90s
    Total coverage: 91.11%

3. Métricas exatas do coverage.xml produzido pela execução:

    lines-valid=22343
    lines-covered=20772
    line-rate=0.9297
    branches-valid=6828
    branches-covered=5806
    branch-rate=0.8503

4. Gate de política:

    check_coverage_policy.py coverage.xml
    Coverage policy passed: total lines >= 90%, total branches >= 85%, measurable modules >= 30%.

5. Gates estáticos equivalentes ao CI:

    flake8 src tests tools app.py pack_for_ai.py: PASS
    black --check --diff src tests tools app.py pack_for_ai.py: PASS
    isort --check-only --diff src tests tools app.py pack_for_ai.py: PASS
    mypy src: Success: no issues found in 132 source files
    git diff --check: PASS

6. Captura e auditoria automatizada:

    audit_stage8_scenario_editor.py --output stage8-final-local-20260823-postcoverage
    finding_count=0
    status=PASS
    manifest_sha256=744faa9aaeef0083c07b4194cfc522ae72cba57a1cb7f6cc0dac5a9bf7639ccc

A auditoria executou Pillow/OpenCV, dimensões, transparência, SHA-256, clipping, geometria Qt, overlap, paleta QSS contextual/agregada e geração anotada.

## Revisão visual humana

As quatro PNGs foram abertas e revisadas:

- estado vazio 1280x720;
- autoria 1280x720;
- overlays 1366x768;
- preview read-only 1920x1080.

Resultado: PASS. Não foi observada sobreposição entre viewport, divisor, painel direito ou barra inferior; o inspector permanece rolável; overlays ficam no viewport; o modo preview é distinguível e desabilita edição. Uma suspeita inicial de texto truncado na captura vazia foi rechecada em recorte de pixels: Open Project e a mensagem de status estavam completos.

A revisão foi feita sobre imagens reais produzidas pelo projeto em execução Qt offscreen. Isso não substitui uma inspeção em GPU nativa nem a validação de DPI do Stage 9.

## Proveniência e limitações honestas

- O raw/manifest.json registra o commit, branch e worktree_clean=false. O estado falso não foi ocultado: existem diretórios de auditorias locais não rastreados anteriores ao checkpoint. Eles não foram incluídos no commit.
- O pacote contém os bytes exatos das capturas, JUnit, relatório bruto e imagens anotadas. artifact-index.json lista SHA-256 e tamanho de cada artefato, excluindo somente o próprio índice para evitar hash circular.
- As capturas usam fixture temporária real do fluxo Qt; não representam um projeto artístico externo nem comprovam funcionalidades nativas de Godot/Unity.
- Os dois skips da suíte são os testes condicionais históricos de symlink já existentes; não foram criados nem ampliados nesta etapa.
- Os checks remotos e a validação pós-merge ainda não foram executados neste registro.

## Gate

Até este documento ser atualizado com PR, checks remotos aprovados, merge autorizado e pós-merge reproduzível, a decisão correta é:

ETAPA 8 — NÃO CONCLUÍDA FORMALMENTE; validação local automatizada e revisão visual humana aprovadas.
