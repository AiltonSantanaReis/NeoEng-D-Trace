# Evidência de pré-commit — alças e quantização da Caneta

ID: EVID-PEN-HANDLES-QUANTIZATION-20260905
Lote: PEN-HANDLES-20260905
Estado: IN_PROGRESS / PRECOMMIT_PENDING
Data: 2026-09-05
Branch: Ailton/pen-handles-quantization-20260905
Base: 5b3e6b15cee93ef5c9d1d550745293fb8372b5b9
SHA candidato: inexistente; os arquivos ainda não estão commitados

## Objetivo e escopo

Corrigir a criação implícita de tangentes que fazia cliques simples introduzir
alças e, após a quantização da amostra, podia produzir um auto-retorno
inválido. O lote cria cantos por clique e alças somente por arraste explícito.
O validador determinístico, a preparação canônica, a quantização global e os
snapshots legados não foram alterados.

## Ambiente

- Windows 11 no VMware, host observado como win32.
- Python 3.11.9 no ambiente bloqueado já sincronizado.
- PySide6 6.10.1 e pytest 9.1.1.
- QT_QPA_PLATFORM=offscreen nas execuções Qt.
- Worktree isolado: build/pen-handles-worktree-20260905.
- Recibos de execução: build/pen-handles-qualification-20260905/.

Os testes usam eventos Qt QTest no CanvasView real. Eles não são cliques
nativos do sistema operacional no executável empacotado; essa auditoria nativa
continua pendente e não é substituída por esta evidência.

## Comandos executados

python -B -m pytest tests/test_pen_creation_gestures.py tests/test_functional_user_flows.py tests/test_stage_11_pen_tool_branch_coverage.py -q --tb=short --junitxml=green-r4/junit.xml
python -B -m compileall -q -f src tests
python -m flake8 src tests tools app.py pack_for_ai.py
python -m black --check --diff src tests tools app.py pack_for_ai.py
python -m isort --check-only --diff src tests tools app.py pack_for_ai.py
python -m mypy src
python -B -m pytest -q --tb=short --junitxml=full-pytest-r2/junit.xml

## Resultados brutos

| Execução | Resultado |
|---|---|
| Red baseline do novo contrato | 33 failed, 3 passed; os 3 inválidos passaram |
| Rodada focada candidata | 69 passed |
| Compilação | PASS |
| Flake8 | PASS |
| Black | PASS |
| isort | PASS |
| mypy | PASS |
| Baseline Git-blob staged | PASS — 3261 arquivos |
| Integridade de evidências Git-blob staged | PASS — 135 manifestos |
| Suíte agregada no worktree candidato | 2016 passed, 2 skipped, 1 failed |

A falha agregada é
test_p2d05_status_notice.py::test_new_pen_inherits_active_language_and_preserves_rejected_path[pt],
por QMessageBox modal residual. O mesmo prefixo de 590 testes, até esse
arquivo, foi executado em um worktree limpo da base e reproduziu a mesma
falha. Portanto ela é preservada como FAIL diagnóstico herdado e não é
atribuída ao lote da Caneta. Os 2 skips são os contratos históricos de
symlink condicionados ao privilégio disponível.

## Cobertura comportamental

Os 69 testes aprovados cobrem:

- cliques simples como cantos em 20, 40, 60, 80 e 100 px;
- sentidos direto e reverso e zoom 0.75, 1.0 e 2.0;
- arraste de novo vértice com alças opostas explícitas;
- preservação de alças ao acrescentar vizinhos;
- fechamento pelo primeiro vértice e duplo clique;
- limiar de arraste em pixels de tela;
- soltura, movimento posterior sem botão, Escape e troca de ferramenta;
- prioridade de Undo/Redo sobre a prévia não consolidada;
- rejeição de área zero, auto-interseção e sobreposição colinear;
- reprodução explícita do padrão de controles que causava a rejeição antiga;
- histórico, salvar/reabrir, reanexar imagem e exportar PNG real.

## Hashes e tamanhos dos arquivos do escopo

Os valores abaixo são do worktree candidato não commitado e não representam
um SHA final:

| Arquivo | Bytes | SHA-256 |
|---|---:|---|
| src/tools/pen_tool.py | 34370 | db707f4bf9ac7337e3c27162dcc6aa5a628367e7b5c5e6e4975eedf3e0ef3c4f |
| src/ui/tool_palette_impl.py | 15181 | e4a468d48aea83d2854a832ca9f81545fa225abeb69b5cbcf2e21c4a2639f1d7 |
| tests/test_functional_user_flows.py | 16195 | e4ebb51a9add61738c667f3df32b8a2f993a65849d771b68368def3eca423f3f |
| tests/test_pen_creation_gestures.py | 13045 | 6dd1fe7cf55f0a47fe60c2a3a311df815ac355830f4634f365f5466b060d0885 |
| docs/LOTE_CANETA_ALCAS_QUANTIZACAO_2026-09-05.md | 6930 | 4908b7c63c05bceae917006cf60aede2efebd47570c4dc5543d146da2d50b811 |
| README.md | 16181 | ec8a290e0b1ed63e8ce71c7b1389c2d6b4f89791c973f2e6bf79f0fee38a9ffd |
| CHANGELOG.md | 64355 | 39b364eb1db433ea3cc6159a9c7a0304d759dbe45b9725faacf04287a150ef45 |
| docs/PLANO_MESTRE_ESTABILIZACAO.md | 30263 | 0b757038587980d1d3150af0ee391ffda25cbc0847befc4c88a7c12302fc4d8f |
| docs/MATRIZ_RISCOS_ESTABILIZACAO.md | 31727 | e4a6831ef9c89bf9f0f4ee5e11a6faa6f6b43ee545c8d057358960c656d414e9 |
| docs/P2D05_REQUALIFICACAO_ATUAL.md | 8629 | 53d073aff3b3ed9d42d5a17025dd30aea4de1149387bed456312b18d35354765 |
| docs/evidence/README.md | 54703 | b2ce0579d7a4827e2857a38dd7dc3be692aeeb50969aac65d1bbe473089f679a |
| docs/INDICE_DOCUMENTAL_ATIVO_CANONICO_2026-08-24.md | 10819 | 01b0683850244ed4c8be45c328e10b6c688850a04655a1484465aa93a0027415 |
| docs/INDICE_DOCUMENTAL_ATIVO_2026-08-24.md | 5681 | 46f1da0eefcb7baabe17a002eb735cadee2673a4b9e996d94906562aa1e5f76f |

| Recibo | Bytes | SHA-256 |
|---|---:|---|
| green-r4/pytest.log | 824 | 4caa34f0222159a3e607b05bafac4b2c04bb3097cb4dc54e469859eb33cb4239 |
| green-r4/junit.xml | 10129 | 5961fdf3607ea21053a8f8a88e2e9f2201a45f56ce82773b3fafa9d7effff116 |
| full-pytest-r2/pytest.log | 19279 | 07821f1c4efaeb593c459883fc24dfc0e67474bbd63c8d5adeff27fc47a6930d |
| full-pytest-r2/junit.xml | 292625 | 13a1fad747eff54fab0f97652312e98122e92bc8d7a5cac43ca173f35e875ccb |

## Limitações e decisão

Runner oficial com cobertura, Stage 4B.5, pip-audit, Bandit, gate legado,
empacotamento, CI remoto e revisão nativa não foram executados para este lote
porque ainda não existe um SHA limpo commitado. Baseline e integridade Git-blob
foram verificados no índice staged como gates de pré-commit. A falha agregada
herdada permanece visível.

Decisão: PENDING_EVIDENCE. O patch está pronto somente para revisão humana
do diff exato e eventual aceite P2D-05 PRECOMMIT ACCEPT. Sem esse aceite,
não realizar commit, push, merge, tag ou release.
