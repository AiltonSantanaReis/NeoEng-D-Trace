# Auditoria e correção dos defeitos de UI — 2026-08-18

## Escopo

Esta evidência registra a correção dos defeitos reproduzidos nas capturas anexadas: autoria de cenário misturada ao editor principal, painel comprimido, controles sem estado explicativo, gizmo sobrepondo HUD, feedback textual sem reserva geométrica e modos X-Ray pouco acessíveis no Mask Viewer.

A evidência foi gerada localmente no Windows, em branch isolada, contra o commit-base `b73fa027e0f5144fb132f49051099123f6e8330a`. O manifest com hashes está em `docs/evidence/artifacts/ui-defect-fix-2026-08-18/manifest.json`.

## Correções implementadas

- A autoria de cenário saiu da aba Layers da MainWindow. O editor principal mantém o preview somente leitura; a autoria abre em `ScenarioEditorWindow`, com canvas próprio, inspetor rolável e ações de salvar, recarregar, redefinir, exportar e overlays.
- A ação `scenario.open` foi registrada no CommandRegistry e ficou disponível nos menus Scenario e View.
- O painel de autoria passou a ter estado vazio explícito, controles traduzíveis, exportação runtime funcional e layout vertical sem dependência de largura excessiva.
- A largura responsiva dos painéis principais foi corrigida para comportar os `minimumSizeHint` reais dos painéis em 1280x720, 1366x768 e 1920x1080.
- O botão do gizmo deixou de usar geometria absoluta dentro do canvas e passou a ser um controle da toolbar de navegação.
- O feedback do gizmo calcula posições candidatas e rejeita retângulos que intersectem a geometria do gizmo.
- O Mask Viewer recebeu um painel de controles verticalmente rolável e quatro botões explícitos: Original, X-Ray Sobel, X-Ray Canny e X-Ray Laplaciano. O combo histórico foi preservado.
- Os scripts de auditoria foram atualizados para o contrato de janela separada sem sobrescrever os artefatos históricos anteriores.

## Gates executados

Comando dos testes direcionados:

```text
.\.venv\Scripts\python.exe -m pytest -q tests/test_ui_responsive_layout.py tests/test_ui_defect_regressions.py tests/test_stage2_command_registry.py tests/test_stage4b3_scenario_authoring.py --tb=short
```

Resultado: `23 passed`.

Comando da suíte completa:

```text
.\.venv\Scripts\python.exe -m pytest -q --tb=short
```

Resultado: `1330 passed, 2 skipped`.

Os 2 skips são os skips históricos já existentes em `tests/test_integration_sync.py`; não foram criados, removidos ou convertidos em Pass nesta alteração.

Gate estrutural: `src/ui/main_window.py` ficou com `1199` linhas, mantendo o contrato existente de ficar abaixo de `1200`.

## Auditoria de capturas

Comando:

```text
.\.venv\Scripts\python.exe scripts/audit_ui_defect_capture.py
```

O script executa captura real em 1280x720, 1366x768 e 1920x1080 para a MainWindow e o editor de cenário separado; também captura o Mask Viewer. Para cada PNG ele verifica dimensões Qt/PNG, alpha, borda não vazia e SHA-256. A auditoria verifica geometrias Qt, clipping por `minimumSizeHint`, sobreposição canvas/painel, parentagem do gizmo e ativação dos quatro modos X-Ray.

Resultado no manifest:

- `layers_scenario_separation: true`;
- `gizmo_toolbar_parent: true`;
- `mask_xray_modes: true`;
- `no_unexpected_clipping: true`;
- `main_clipping: []` e `scenario_clipping: []` nas três resoluções;
- `overlap: false` para canvas/inspector e para feedback/gizmo.

Principais hashes das capturas finais:

| Artefato | SHA-256 |
| --- | --- |
| `compact_1280x720_main.png` | `79708e5a0b405cc9e3728857d915c440039b18404262a985754c6b64d569d8de` |
| `compact_1280x720_gizmo_feedback.png` | `34e2d449866d4f20731a16027e4c0219c87dc97135ccc196774212b380882622` |
| `compact_1280x720_scenario_editor.png` | `be97e3d2512fa312777134905a35445afcd45e568e6cb31be49d44c413215c67` |
| `compact_1366x768_main.png` | `6f09fd2250978896c042077e4871dc8fd4a92b951d3c8fc6738282d8e902ccdb` |
| `desktop_1920x1080_main.png` | `19d9f9041e353145e586ebaf49938a16d21757534d0db52253481d254840f0` |
| `mask_viewer_xray_controls.png` | `89d24792887bebb3c7888f2641e1e907a8da4625efe78ab1e44712d1c0a583ff` |

As imagens anotadas registram as áreas de canvas, inspetor, feedback e gizmo; elas não são usadas para alterar o resultado do teste.

## Falhas encontradas durante a validação

A primeira execução da auditoria falhou porque a largura fixa de 340 px era menor que os `minimumSizeHint` reais. A segunda execução mostrou que o inspetor de cenário ainda exigia 508 px por causa de layouts horizontais. Ambos os problemas foram corrigidos e a auditoria foi repetida com sucesso.

A primeira execução da suíte completa encontrou a regressão do gate de tamanho (`1211` linhas). A duplicação de configuração das toolbars foi condensada e quatro comentários redundantes foram removidos; o gate voltou a `1199` linhas. Nenhuma asserção foi enfraquecida.

Também foi corrigida uma inconsistência do próprio anotador: suas primeiras caixas de gizmo usavam coordenadas locais como se fossem coordenadas da janela. O manifest final diferencia coordenadas locais do canvas e coordenadas convertidas para a janela.

## Limitações declaradas

A auditoria usa `QT_QPA_PLATFORM=offscreen` para tornar a captura reprodutível e não depende de inspeção humana para decidir Pass/Fail. Ela comprova layout, geometria e renderização Qt do conteúdo da janela; não comprova decoração nativa do Windows, escala DPI específica do monitor ou comportamento de driver gráfico.

O auditor histórico `scripts/audit_scenario_authoring.py`, adaptado para a janela separada, também foi executado com sucesso. Seus artefatos estão em `docs/evidence/artifacts/stage4b3-authoring-window-2026-08-18/manifest.json`; ele comprovou `main_layers_tabs: 1`, `scenario_editor_separate: true`, ausência de sobreposição/clipping do viewport e transação Undo/Redo do sidecar.

A saída informou que CuPy não está instalado e usou o fallback CPU. Isso não é falha da UI nem foi tratado como Pass artificial; a auditoria solicitada não depende de aceleração CuPy.

Esta alteração ainda não foi commitada, enviada ou mergeada. O próximo gate é revisar o diff e decidir explicitamente sobre commit/PR.
