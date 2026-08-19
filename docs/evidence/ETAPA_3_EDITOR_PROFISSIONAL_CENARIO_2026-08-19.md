# Evidência — Etapa 3: Editor profissional de cenário

## Identificação

- Commit-fonte da captura: `3396878ebc32361affeb37621699009c67e9fed4`
- Branch: `stage3`
- Data/hora: 2026-08-19 15:03:37 -03:00
- Proveniência: `worktree_clean_at_capture_start: true`

## Ambiente e escopo

Windows 10, Python 3.11.9, PySide6 do ambiente virtual, captura real em
`QT_QPA_PLATFORM=offscreen`. A Etapa 3 entrega a janela profissional
separada, viewport, drag-and-drop seguro, gizmo, inspector, snapping e
Undo/Redo transacional. Persistência do documento profissional, parallax,
sockets, exportadores e runtime permanecem nas etapas posteriores.

## Comandos e resultados

- `pytest -q tests/test_stage3_professional_scene_editor.py`: **12 passed**.
- Suíte completa com cobertura: **1362 passed, 2 skipped**, cobertura total
  **90.98%**.
- `tools/check_coverage_policy.py coverage.xml`: **PASS**.
- Captura e auditor visual: **PASS**, 0 findings.
- Pillow e OpenCV decodificaram os três PNGs; dimensões 1280x720;
  transparência, clipping, geometria Qt, sobreposição, paleta e hashes
  passaram.
- Flake8, Black, isort, py_compile e mypy passaram nos arquivos novos/testes
  e módulos src da Etapa 3.
- Os únicos skips são os 2 testes históricos de symlink já existentes;
  nenhum skip foi criado nesta etapa.

## Artefatos e integridade

A fonte de autoridade dos hashes é o conjunto versionado abaixo, e não cópias
redigitadas neste documento:

- `docs/evidence/artifacts/stage3-professional-scene-editor-2026-08-19/captures/manifest.json`
- `docs/evidence/artifacts/stage3-professional-scene-editor-2026-08-19/captures/stage3_01_sem_projeto.png`
- `docs/evidence/artifacts/stage3-professional-scene-editor-2026-08-19/captures/stage3_02_projeto_paineis.png`
- `docs/evidence/artifacts/stage3-professional-scene-editor-2026-08-19/captures/stage3_04_gizmo_feedback.png`
- `docs/evidence/artifacts/stage3-professional-scene-editor-2026-08-19/audited/visual-audit-report.json`
- `docs/evidence/artifacts/stage3-professional-scene-editor-2026-08-19/audited/visual-audit-report.md`
- PNGs anotados correspondentes na pasta `audited/`.

O manifest contém SHA-256 por arquivo, dimensões, perfis de estado, geometria
Qt, ausência de caminhos absolutos e referência ao commit-fonte. O relatório
registra o mesmo SHA-256 do manifest e `status: PASS`, `finding_count: 0`.

## Falhas intermediárias corrigidas

- Saída do auditor inicialmente dentro da entrada: separado em
  `captures/` e `audited/`.
- Perfil de geometria antigo não representava a janela profissional:
  perfis explícitos para estado vazio/carregado, mantendo os checks antigos.
- Paleta do estado vazio: conjunto mínimo explícito; paleta completa exigida
  no estado carregado.
- Runtime Windows rejeitou `b"PNG"`: Qt passou a inferir PNG pela extensão.
- Proveniência consultada depois da criação da saída: coleta movida para antes
  da criação; execução final registrou worktree limpo.

Nenhum PASS foi obtido por bypass, exclusão, alteração de regra ou mascaramento.

## Revalidação da PR #106

A primeira execução remota `32299592245` reprovou nos jobs Linux e Windows
pelo mesmo motivo: `E501` nas linhas 61 e 93 de
`tests/test_ui_defect_regressions.py` (89 caracteres, limite 88). A falha
não foi funcional nem de ambiente; as duas linhas foram quebradas sem alterar
asserções ou comportamento. A correção foi validada localmente com o lint
estrito do arquivo e 16 testes de regressão/Etapa 3 aprovados. O baseline foi
regenerado contra os bytes staged e verificado com 1.532 arquivos.

A execução remota `32300986840` confirmou no Windows uma reprovação de `black --check`: o segundo ajuste do `assert` ainda não estava normalizado. No Linux, o job não alcançou o código do projeto: o passo `Refresh apt package indexes for Qt` excedeu o timeout de 10 minutos do runner. A normalização Black foi aplicada e passou localmente; o Linux exige nova execução para validação remota.

Na execução `32303557990`, o job Windows foi aprovado. O job Linux falhou novamente no passo `Refresh apt package indexes for Qt` após 10 minutos; o rerun do mesmo job (`96234478458`) repetiu o timeout. Assim, há duas tentativas Linux independentes com a mesma falha de infraestrutura, sem execução dos testes do projeto nesse job.

Execução final `32305826961`: os jobs Linux e Windows concluíram com sucesso, incluindo os gates de integridade, lint, formatação, testes, cobertura e árvore de fontes. O timeout Linux foi transitório e não se repetiu nesta execução.

A PR está pronta para revisão; o merge permanece pendente de autorização explícita.

## Limitações e decisão

A captura offscreen não substitui teste interativo de GPU. Persistência/reabertura
do documento profissional, parallax, sockets e exportação de engines não fazem
parte da Etapa 3. A CI remota ainda precisa aprovar a PR.

**Decisão: APROVADO LOCALMENTE E NO CI; PR PRONTA PARA REVISÃO; MERGE PENDENTE DE AUTORIZAÇÃO.**
