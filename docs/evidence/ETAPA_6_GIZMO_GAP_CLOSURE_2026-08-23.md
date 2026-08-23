# Etapa 6 — Fechamento das lacunas do Gizmo — 2026-08-23

## Classificação atual

PASS_LOCAL / PR, CI e pós-merge pendentes. Esta evidência não aprova a etapa formalmente nem autoriza release. O escopo local foi implementado e reproduzido; a promoção remota só poderá ocorrer após revisão do diff, CI aprovado e validação pós-merge.

## Governança aplicada

Antes da implementação foram relidos docs/POLITICA_QUALIDADE_E_EVIDENCIAS.md, docs/POLITICA_NAO_REGRESSAO.md, docs/PLANO_MESTRE_ESTABILIZACAO.md, docs/MATRIZ_RISCOS_ESTABILIZACAO.md, .github/pull_request_template.md, o plano vivo e a reconciliação das Etapas 0–7. Nenhuma regra, threshold de CI ou contrato de evidência foi alterado para obter PASS. Os snapshots históricos não foram reescritos.

## Escopo implementado

- Modo de gizmo contextual para vértice selecionado: somente X, Y e XY; rotação e escala não são oferecidas para um ponto individual.
- Preview, commit, cancelamento/Escape e undo/redo delegados à PolygonGestureTransaction já existente.
- Inspector numérico no SidePanel principal para Position, Rotation e Scale, aplicado atomicamente via TransformObjectsCommand e com limites explícitos.
- QScrollArea no painel lateral para impedir compressão abaixo do minimumSizeHint dos campos em resoluções compactas.
- Auditoria Windows ampliada para inspector e vértice, mantendo captura Pillow/OpenCV, hashes, paleta, geometria Qt, contenção e anotação.

## Checkpoint de origem

- Branch: Ailton/stage6-gizmo-gap-closure
- Commit do código/testes/auditor: fec2ee1b068b46d2cfe096519a0526ea576059ec
- Os diretórios históricos locais não rastreados foram preservados e não foram adicionados.

## Testes reproduzidos

Comando focal:
.\.venv\Scripts\python.exe -m pytest -q tests/test_stage6_gizmo_gap_closure.py tests/test_stage6_professional_gizmo.py tests/test_transform_gesture.py tests/test_stage_5_package_3b_vertex_editing.py --tb=short

Resultado: 31 passed in 1.49s.

Suíte integral Windows:
.\.venv\Scripts\python.exe -m pytest -q --tb=short

Resultado: 1621 passed, 2 skipped in 40.39s. Os dois skips são os existentes no teste de integração de symlink; não foram criados, ampliados ou reclassificados nesta etapa.

Gates estáticos nos seis arquivos alterados: black --check, isort --check-only e flake8 — PASS.

## Auditoria visual automatizada real

Comando:
.\.venv\Scripts\python.exe scripts/audit_stage6_professional_gizmo.py

Resultado no backend Qt nativo Windows:
- decisão: PASS;
- capturas: 24 — oito estados por resolução;
- falhas: 0;
- resoluções lógicas: 1920x1080, 1366x768, 1280x720;
- estados: selected, hover, feedback, undo, numeric, numeric_undo, vertex, vertex_undo;
- cada PNG foi validado por Pillow e OpenCV, com dimensões concordantes, alfa opaco, hash SHA-256, paleta escura, geometria real e anotações;
- os campos do inspector permaneceram dentro do painel e acima do limite de clipping efetivo após a introdução da rolagem.

Relatório: docs/evidence/artifacts/ui-modernization-stage6-20260822/stage6-gizmo-report.json
SHA-256 do relatório: 988eef79593f170c12999bf1045007ac062c7d802e6d87d040f9db2460f75358

Amostras SHA-256:
- windows-captures/1080p_FHD_05_numeric.png: df2e7566e9f2ec037dc35acfbf5471fd57d3a087d47d6f444c68e46105d7aa1f
- windows-captures/720p_Compacta_07_vertex.png: 78dbba77d09a73b2fe6ef0b1c9e37c6125505a59a43fceb3a9e823f55b2c9f25
- windows-visual-audit/768p_Minima_08_vertex_undo_annotated.png: bb57e834d0c77d0c4615579a1693fab651f0251969b62075599deb66b6216803

O relatório registra source_state.commit=fec2ee1 e source_state.worktree_clean=false porque foi gerado antes do commit dos próprios artefatos. Isso é declarado, não mascarado; a validação de árvore limpa será executada após o commit dos artefatos e novamente após o merge.

## Regressões e limitações

Não foi encontrada regressão nos 1621 testes. A primeira execução da auditoria falhou por causa real: os campos do inspector eram comprimidos para aproximadamente 11–12px lógicos, abaixo do QDoubleSpinBox.minimumSizeHint real de 23px. A correção foi estrutural (QScrollArea), e a auditoria seguinte passou sem alteração do threshold.

Ainda não há CI, PR, merge ou validação pós-merge deste checkpoint. A revisão visual humana das capturas anotadas ainda não foi declarada como aprovada. O suporte continua sendo 2D: o modo de vértice não oferece operações 3D fictícias.

## Próximo gate

1. revisar o diff e os artefatos;
2. versionar este relatório, PNGs e documentação reconciliada;
3. executar baseline/evidence integrity e a suíte local pós-commit;
4. abrir PR sem force;
5. aguardar CI Linux/Windows;
6. somente com checks aprovados, realizar merge e executar a validação pós-merge.
## Integridade do pacote staged

Após preparar os bytes versionados, a validação por blobs Git retornou Evidence integrity passed: 109 manifests validated. O baseline foi regenerado e verificado contra os mesmos bytes, retornando Baseline verified: 2597 files. Esses números são do pacote staged desta etapa e não incluem os diretórios locais históricos preservados.
### Reconciliação do CI da PR #152 — 2026-08-23

O run `32627926745` falhou legitimamente nos jobs Linux e Windows no gate `poetry run mypy src`, antes da execução dos testes funcionais posteriores. Ambos reportaram `src/tools/polygon_edit_tool.py:202`: retorno inferido como `tuple[int, ...]` incompatível com `tuple[int, int] | None`. A falha foi reproduzida localmente com o mesmo comando, sem alterar o gate.

A correção foi limitada ao retorno explícito dos dois componentes inteiros do vértice. Após a correção: `mypy src` PASS em 131 arquivos; Black/isort/Flake8 PASS; testes focados `31 passed`; suíte completa `1621 passed, 2 skipped`. A PR requer novo run de CI; nenhum PASS remoto é presumido a partir desses resultados locais.
### Encerramento pós-merge — 2026-08-23

A PR #152 foi merged em `ebdb889bc415eca4ea263a98e59551645130fbd5`. O CI remoto `32628620905` passou nos jobs Linux e Windows. A validação local executada sobre o `main` pós-merge passou com `1621 passed, 2 skipped`; `evidence_integrity.py --require-tracked --git-blob` validou `109 manifests`; `baseline_integrity.py --verify --git-blob` validou `2597 files`; e `main` local/remoto apontaram para o mesmo commit. A implementação permanece sem aprovação de release nesta evidência.