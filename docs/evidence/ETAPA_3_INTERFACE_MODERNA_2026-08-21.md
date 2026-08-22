# Etapa 3 — Interface moderna profissional: barra esquerda

Estado desta evidência: **PASS LOCAL PRÉ-COMMIT — aguardando revisão de diff, CI e pós-merge**.

Este documento registra a validação da Etapa 3 do plano de interface moderna profissional. Ele não declara aprovação formal da etapa nem aprovação de release.

## Objetivo e escopo

Substituir a paleta vertical de ferramentas baseada em botões de texto por uma `QToolBar` vertical, orientada a ações e compatível com os contratos existentes:

- nove ferramentas existentes preservadas;
- seleção exclusiva por `QActionGroup` e `QButtonGroup`;
- ícones, tooltips, nomes acessíveis, foco de teclado e feedback de estado desabilitado;
- atalhos globais existentes preservados;
- separadores visuais entre grupos de ferramentas;
- largura de transição limitada para manter a geometria histórica enquanto a migração visual completa prossegue;
- implementação legada preservada em `docs/evidence/artifacts/ui-modernization-stage3-20260821/rollback/`, fora do pacote executável.

Ficam explicitamente fora desta etapa a realocação do Gizmo, a janela do Mask Viewer e a reforma dos painéis laterais. Esses itens permanecem nos gates posteriores do plano.

## Proveniência

- Branch de trabalho: `Ailton/interface-stage3-toolbar`.
- Commit observado na geração: `eaa6a559c729d1a394aab3d269e19adbde8a39b7`.
- Estado da árvore: `worktree_clean=false`, corretamente registrado porque a implementação ainda não havia sido commitada.
- Ambiente: Windows, Python 3.11.9, PySide6 6.10.1.
- Nenhum diretório histórico `release-stage9-*` foi incluído no escopo ou staged.

## Alterações verificadas

- `src/ui/tool_palette.py`: fachada pública compatível.
- `src/ui/tool_palette_impl.py`: implementação `QToolBar` orientada a ações.
- `tests/test_stage3_ui_toolbar.py`: testes reais do contrato Qt, interação, acessibilidade, feedback desabilitado, idioma e atalhos.
- `scripts/audit_stage3_ui_toolbar.py`: auditor reproduzível de contrato e captura.
- `docs/evidence/artifacts/ui-modernization-stage3-20260821/`: capturas, manifests, relatórios e índice SHA-256.
- `docs/evidence/artifacts/ui-modernization-stage3-20260821/rollback/tool_palette_legacy.py`: snapshot versionado para rollback, não importado pelo runtime.

## Comandos e resultados reais

Checks estáticos oficiais:

```text
python -m black --check --diff ...       PASS
python -m isort --check-only --diff ...  PASS
python -m flake8 ...                     PASS
python -m mypy src                        PASS
python -m py_compile ...                  PASS
```

Testes focados:

```text
28 passed in 6.79s
```

Suíte completa com o mesmo gate do CI:

```text
1591 collected
1589 passed, 2 skipped
Total coverage: 91.19%
```

Política integrada de cobertura:

```text
Coverage policy passed: total lines >= 90%, total branches >= 85%, measurable modules >= 30%.
```

Auditoria estrutural e visual offscreen:

```text
capture return code: 0
visual auditor: PASS
live Qt contract: PASS
finding_count: 0
```

Captura nativa no backend Windows:

```text
native capture return code: 0
native visual auditor: PASS
native finding_count: 0
```

Foram produzidos três estados em cada backend — FHD, 1366x768 e 1280x720 — com 15 PNGs por conjunto. A auditoria verificou dimensões observadas, transparência, hashes, clipping, geometria Qt, sobreposição e paleta contextual.

## Evidências e hashes

O índice `artifact-index.json` contém 77 entradas hashadas. SHA-256 dos principais manifests/relatórios:

```text
stage3-toolbar-report.json                         2e8a1da664d061ac173e12205bdc4fb6d90c5531a5bd8bf488c679c753cd6edf
stage3-toolbar-report.md                            ae08c042f6e2f68736b87995aa602e7edb347d7d8d0ae6eb664f4119f3b50327
artifact-index.json                                 8dbb1eb1e881da92c5d46740ebce5eb1ac8568d6753e1133b8af06c4f4d0fb3f
raw-captures/manifest.json                          0517b3bcedcfc0be385201b4123d1c383a602664adc1e687d4e16c62fd37809b
native-captures/manifest.json                       eac1640cc71572de025e7155187198aee0a5408139367cab9d77ae000a6339ce
visual-audit/visual-audit-report.json               f3e6cf2ef986344f5a11a8b2f9fa25b2d45f33c15703e9aa84b61eeee18e714f
native-visual-audit/visual-audit-report.json        4a839ef79c2699065d29a97fd4c834429c753e5fc170572fcc814fe8b175dbe0
```

O `git diff --check` também retornou código 0.

## Anomalias e limitações registradas

1. A primeira execução da política falhou legitimamente porque o snapshot legado estava em `src/ui`, produzindo um módulo de produção com 0% de cobertura e branches totais em 84,99%. O gate não foi alterado. O snapshot foi movido para o pacote de rollback fora de `src`; a política passou depois, com 91,19% de linhas e branches acima de 85%.
2. O backend Qt offscreen registrou ausência do diretório de fontes do PySide6 e avisos de `propagateSizeHints()`. Por isso, a legibilidade tipográfica não foi inferida das imagens offscreen.
3. A captura nativa Windows registrou avisos de geometria devido a DPI/escala do monitor: em FHD, a janela lógica solicitada de 1920x1080 resultou em janela observada de 1920x1060 e captura física de 3840x2120. Os manifests registram as dimensões reais; isso não foi ocultado nem convertido em correspondência exata.
4. A auditoria visual automática não substitui uma revisão estética humana completa. A inspeção nativa confirmou legibilidade e ausência visual evidente de clipping/sobreposição na captura analisada, mas não constitui aprovação pixel-a-pixel de todos os estados.

## Decisão do gate

**A implementação está aprovada apenas para revisão de diff e publicação da branch.** A Etapa 3 só poderá ser marcada como formalmente concluída após:

1. validação dos arquivos staged contra os blobs Git;
2. commit sem incluir artefatos fora do escopo;
3. push e PR;
4. CI Linux e Windows aprovados, incluindo baseline, evidências, cobertura e checks estáticos;
5. revisão dos artefatos da PR;
6. merge sem force;
7. validação pós-merge no `main`, com árvore limpa e nova evidência versionada.

Nenhum bypass, alteração de regra, supressão de asserção ou declaração baseada somente em CI foi utilizado.
