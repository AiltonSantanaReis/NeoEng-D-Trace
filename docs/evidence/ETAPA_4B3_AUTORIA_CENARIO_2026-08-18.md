# Evidência — Etapa 4B.3: autoria lateral de cenários

## Identificação

- Escopo: painel lateral de camadas de cenário, inspetor de propriedades,
  autoria separada do `Scene`, Undo/Redo isolado e persistência lateral.
- Commit técnico publicado: `aa9de017474d1895da5296aa4779d1da60e5ca9a`.
- Estado: **APROVADO NO ESCOPO 4B.3 / ETAPA 4B GERAL AINDA ABERTA**.
- Manifesto: `docs/evidence/artifacts/stage4b3-authoring-2026-08-18/manifest.json`.

## Contrato implementado

A autoria usa `ScenarioAuthoringState` e `ScenarioCommandManager`, separados do
histórico do `Scene`. O documento lateral `.ndtscenario.json` é criado a partir
do projeto `.ndtproj`, vinculado ao hash do projeto, validado pelo schema lateral
v1 e salvo por substituição atômica. Falha de carregamento restaura o estado de
autoria anterior; falha de operação não altera o `Scene`.

A integração visual foi feita dentro de `LayersPanel`: a aba histórica de objetos
permanece disponível e uma aba `Scenario` expõe lista de camadas, visibilidade,
ordenação, adição/remoção, atribuição de objetos, profundidade/parallax, câmera e
salvar/recarregar/resetar. As ações de menu `scenario.save`, `scenario.load` e
`scenario.reset` têm IDs estáveis e habilitação dependente de projeto carregado.

O contrato `.ndtproj` v1, `SceneObject.position.z`, polígono, seleção e histórico
de comandos do editor normal não foram alterados. A preview 4B.2 continua sendo
apenas uma ponte de leitura; não foi declarado exportador de cenário nem consumo
Godot/Unity nesta etapa.

## Testes reais executados

Ambiente: Windows local, Python 3.11.9, Poetry e PySide6, com Qt offscreen para
as capturas automatizadas.

```text
poetry check --lock --strict
poetry run pytest -q tests/test_stage4b3_scenario_authoring.py --tb=short
poetry run pytest --cov=src --cov-branch --cov-fail-under=90 --cov-report=term-missing --cov-report=xml
poetry run python tools/check_coverage_policy.py coverage.xml
poetry run black --check src/core/scenario_authoring.py src/ui/scenario_authoring_actions.py src/ui/scenario_panel.py src/ui/layers_panel.py src/ui/main_window.py src/ui/responsive_layout.py src/ui/command_bindings.py tests/test_stage2_command_registry.py tests/test_stage4b3_scenario_authoring.py scripts/audit_scenario_authoring.py
poetry run isort --check-only --diff src/core/scenario_authoring.py src/ui/scenario_authoring_actions.py src/ui/scenario_panel.py src/ui/layers_panel.py src/ui/main_window.py src/ui/responsive_layout.py src/ui/command_bindings.py tests/test_stage2_command_registry.py tests/test_stage4b3_scenario_authoring.py scripts/audit_scenario_authoring.py
poetry run flake8 src/core/scenario_authoring.py src/ui/scenario_authoring_actions.py src/ui/scenario_panel.py src/ui/layers_panel.py src/ui/main_window.py src/ui/responsive_layout.py src/ui/command_bindings.py tests/test_stage2_command_registry.py tests/test_stage4b3_scenario_authoring.py scripts/audit_scenario_authoring.py
poetry run mypy src/core/scenario_authoring.py src/ui/scenario_authoring_actions.py src/ui/scenario_panel.py src/ui/layers_panel.py src/ui/main_window.py src/ui/responsive_layout.py
poetry run bandit -q -r src/core/scenario_authoring.py src/ui/scenario_authoring_actions.py src/ui/scenario_panel.py
poetry run pip-audit
poetry run python scripts/audit_scenario_authoring.py
```

Resultados observados:

- testes focais da 4B.3: **9 passed, 0 failed**;
- suíte completa final: **1.292 passed, 2 skipped, 10 warnings**;
- skips: os dois testes históricos condicionais de symlink; não foram criados,
  removidos ou usados para obter aprovação;
- cobertura XML: `14.861/16.021` linhas (`92,76%`) e `4.343/5.106`
  branches (`85,06%`); o relatório combinado do pytest registrou `90,90%`;
- `check_coverage_policy.py`: **PASS** com linhas >= 90%, branches >= 85% e
  módulos mensuráveis >= 30%; nenhum limiar foi modificado;
- `black`, `isort` e `flake8`: **PASS**;
- `mypy`: **Success: no issues found in 6 source files**;
- Bandit: nenhum achado no nível executado;
- pip-audit: `No known vulnerabilities found`; o pacote local `neoeng-d-trace`
  não está publicado no PyPI e foi explicitamente reportado como não auditável
  pela fonte externa;
- o auditor registrou `CuPy not found. Fallback to CPU processing`; isso é uma
  escolha de processamento local, não uma alegação de aceleração por GPU.

## Auditoria visual, geométrica e de hashes

O script leu os PNGs com Pillow/NumPy, verificou dimensões, modo RGB, alfa
`[255,255]`, pixels escuros, conteúdo não vazio, bordas e SHA-256. As áreas
foram obtidas de widgets Qt reais e a anotação marcou o canvas em verde e o
painel de cenário em amarelo.

| Estado | Janela | Canvas Qt | Painel Scenario Qt | Sobreposição | Clipping | PNG SHA-256 |
|---|---:|---|---|---|---|---|
| Compacto | 1280x720 | `[158,55,778,665]` | `[951,112,318,597]` | `false` | `false` | `07151c6fb5fc7c532fea8dccb7153103619ffc28cf9efaa1b8cec906fee0a1bb` |
| Desktop | 1920x1080 | `[158,55,1398,1025]` | `[1571,502,334,366]` | `false` | `false` | `c620b4dc6ff470ac8b2d63e16add4104da2737f1b2fa09a97fb6a7d68def00f0` |

PNG anotado compacto: `b1b9a96ccedf012c7d3c347b962262c15703f8e5a517ba81fa07c1a616e47156`.
PNG anotado desktop: `e83b061209008833e13d7466fe7e7bd323973a5c62d2836150087fd61be8d3b0`.

A transação real do auditor confirmou camada `layer_default`, Undo/Redo isolado
(`undo_count_after_redo=2`, `redo_count_after_redo=0`), lado `.ndtscenario.json`
de `733` bytes com SHA-256
`c4fb3456d8ca49baf4dc1c456b9413bef9945f56cbb53ef136ca9e572888d7fe`, projeto de
fixture de `30` bytes com SHA-256
`6b112cd645d9b382303cebd7c78a8408137ed6aba9e033db4e2ac273a05159db`, polígono
da cena preservado e `scene_undo_count=0`.

A inspeção visual realizada nas capturas anotadas confirmou tema escuro
consistente, canvas e painel dentro da janela e ausência de sobreposição. O
ambiente Qt offscreen exibiu fallback de glifos quadrados nos textos; isso é uma
limitação do renderizador de captura e não foi apresentado como prova de
legibilidade tipográfica no Windows interativo.

## Falhas reais encontradas e corrigidas antes da aprovação

1. A primeira captura compacta media a página interna invisível porque a aba
   externa `Objects` ainda estava selecionada. O auditor foi corrigido para
   selecionar as abas reais e a captura foi repetida.
2. A primeira captura desktop detectou clipping real do painel lateral por
   reserva de largura insuficiente. A reserva e as políticas de tamanho foram
   corrigidas; a captura final passou sem clipping.
3. Na transição compacto→desktop, widgets reparentados permaneciam invisíveis.
   O fluxo de reparenting passou a mostrar explicitamente os painéis e foi
   reauditado.
4. A primeira execução do fixture tinha sidecar pré-existente, tornando o
   resultado de Undo não determinístico. O auditor passou a resetar o estado
   depois do bind e a verificar a contagem real.
5. A primeira suíte completa encontrou duas regressões legítimas: o contrato
   histórico de IDs não conhecia as três ações novas e `main_window.py` ficou
   exatamente com 1.200 linhas. O teste histórico foi atualizado para os IDs
   efetivamente registrados e uma linha vazia sem efeito foi removida; os gates
   permaneceram intactos. A suíte completa foi então repetida.
6. A primeira medição após a implementação tinha branch coverage de `84,47%`,
   abaixo do gate. Foram adicionados testes negativos reais de estado, histórico
   obsoleto, rebind e adaptador; nenhum caminho foi excluído ou mascarado. A
   medição final passou com `85,06%` de branches.

Nenhuma regra, asserção, skip, xfail ou limiar foi alterado para fabricar PASS.
Não houve force push, force merge, alteração do schema de projeto v1 ou escrita
em projeto externo.

## Limitações e próximo gate

Esta etapa não implementa exportação de cenário, consumidor Godot/Unity,
benchmark Windows de runtime ou partículas/shaders/DoF. Também não declara
legibilidade visual interativa a partir da captura offscreen. Esses pontos ficam
para 4B.4/4B.5 conforme o plano; a Etapa 4B geral permanece aberta.

## Reconciliação documental encontrada

A validação de integridade também encontrou um manifesto histórico da 4B.2
referenciando `src/ui/main_window.py` por bytes de worktree que não coincidiam com o
blob Git do commit `638db729`. O blob exato do commit foi preservado em
`docs/evidence/artifacts/stage4b2-preview-2026-08-18/main_window.py`; somente o
manifesto histórico foi repontuado e seu registro foi corrigido para `45576` bytes e
SHA-256 `c7fc797fefd6d26d34fbda1a7a82195b13d22298349f7b1d0e6d6a17bee01339`. O
relatório histórico não foi reescrito. Depois da correção, o validador passou em
52 manifestos.

## Decisão

**APROVADO NO ESCOPO DA ETAPA 4B.3.** A autoria lateral, integração de interface,
histórico isolado, persistência hash-bound, rollback de carregamento, testes
negativos e auditoria visual reproduzível estão implementados e comprovados no
commit técnico publicado. A aprovação não é merge da Etapa 4B geral nem aprovação
de release.
