# NeoEng-D-Trace

NeoEng-D-Trace é uma ferramenta desktop proprietária e principalmente offline para preparar assets de jogos a partir de imagens 2D: detectar objetos, corrigir contornos, editar polígonos e curvas Bézier, configurar colisões e exportar sprites, atlas, metadados e GLTF/GLB.

## Autoridade e estado operacional

O estado real do repositório local e remoto prevalece sobre qualquer snapshot documental. Antes de alterar código, consulte `docs/PLANO_MESTRE_ESTABILIZACAO.md`, `docs/MATRIZ_RISCOS_ESTABILIZACAO.md`, o índice `docs/evidence/README.md`, a PR atual e o CI ligado ao HEAD exato.

Encerramento formal da Etapa 10 em 11 de agosto de 2026:

- PR `#42` integrada em `9b22bdc54b13992658172d4748bfab44f3127c8e`; os CIs `31450335289`, `31451363518` e `31452032479` foram rejeitados, e o pré-merge `31457937902` foi aceito após inspeção recursiva;
- CI pós-merge `31463873481` rejeitado apesar dos jobs verdes por divergência de cobertura entre sistemas;
- correção validada no CI pré-merge `31464786333`, integrada pela PR `#43` em `f8caec3e7156d308f03046f81d2c89996f959466` e reproduzida no pós-merge `31469610508`;
- schemas Godot/Unity unificados entre cena e objeto, pivôs corrigidos e atlas protegido por rollback multi-arquivo;
- harness reproduzível com Godot `4.7` e Unity `6000.5.7f1`; GLB importado no Unity pelo pacote oficial glTFast `6.19.0`;
- caminhos e nomes Unicode aprovados nas duas engines reais;
- `17` testes da etapa, `730` oficiais e `196` históricos com reconciliação `27/27`;
- cobertura local e remota de `73,77%` de linhas, `57,91%` de branches e `69,93%` combinada; mypy sem erros em `70` arquivos;
- Etapa 10: **CONCLUÍDA**; Etapa 11: **NÃO INICIADA**; release: **NÃO APROVADA**.

Encerramento formal da Etapa 9, comprovado em 10 de agosto de 2026:

- commit técnico: `28273dfb7cb0e0aeab1f8f9f3a99c07df3b08a76`;
- API pública única em `src.collision`; `src.physics` preservado somente como compatibilidade sem implementações próprias;
- falhas corrigidas: IDs heterogêneos, falso positivo côncavo, entradas inválidas, MTV invertido e promessas inertes de física dinâmica;
- suíte local: 39 casos da etapa, 702 testes oficiais e 196 históricos com 27/27 divergências exatas;
- cobertura: 73.65% de linhas, 57.65% de branches e 69.79% combinada; colisão canônica entre 89% e 95%;
- CI final da PR `31445205968` e CI pós-merge `31445518755`: Linux e Windows em `success`, zero anotações;
- PR `#40` mesclada em `76dd6b7ca3e7da08fab653d66ae29a33a839baf3`; artefatos e digests registrados na evidência permanente;
- `R-008`: **ENCERRADO NO ESCOPO APROVADO**;
- Etapa 9: **CONCLUÍDA**; Etapa 10: **NÃO INICIADA**; release: **NÃO APROVADA**.

Snapshot histórico de encerramento formal da Etapa 8, em 10 de agosto de 2026:

- commits técnico e corretivo: `d11cd3dc0bd0063e325a53dd30fc439feda9dd24` e `23d467f37b39e97251e589b544b84f29bcb18fee`;
- PR `#38` mesclada em `fc869250e5067fb7b06b70c7d2dd3c0e1e1ee94e`;
- CI da PR `31440755594` e CI pós-merge `31441024001`: Linux e Windows em `success`, zero anotações;
- artefatos pós-merge: Linux `9082863959` e Windows `9082897744`, com digests registrados na evidência permanente;
- suíte local: 125 testes focais, 661 totais no pacote pré-merge e 662 no fechamento; núcleo geométrico com 95.59% de linhas e 93.29% de branches;
- legado: 196 executados, 27/27 divergências exatas reconciliadas, zero inesperadas e zero ausentes;
- `R-007`: **ENCERRADO NO ESCOPO APROVADO**; Etapa 8: **CONCLUÍDA**;
- `R-003` permanece aberto; Etapa 9: não iniciada; release: **NÃO APROVADA**.

Snapshot histórico do encerramento formal da Etapa 7, em 10 de agosto de 2026:

- implementação e evidência pré-merge: `a940ef13018aabc430126db3fd705b521fc1be06` e `51e55a37021c506471111ef1f4e7bc9abe67c65d`;
- PR `#36` mesclada em `99326f2d7ccf7046e401d90830feb8a5d33e9f9a`;
- CI da PR `31436763095` e CI pós-merge `31437000772`: Linux e Windows em `success`, zero anotações;
- artefatos pós-merge: Linux `9081388807` e Windows `9081419753`, com digests registrados na evidência permanente;
- suíte local: 620 testes no commit técnico, 621 no pacote pré-merge e 622 no fechamento; cobertura combinada 68.53%; launcher 85%; mypy sem erros em 66 arquivos;
- `R-006`: **ENCERRADO NO ESCOPO APROVADO**; Etapa 7: **CONCLUÍDA**;
- `R-003` e metas finais de cobertura permanecem abertos;
- Etapa 8: não iniciada; release: **NÃO APROVADA**.

Snapshot histórico do encerramento formal da Etapa 6, em 10 de agosto de 2026:

- implementação e evidência pré-merge: `3c80bb7f0f72a26f5f4972c5aeb483b8d16e2e98` e `321ccf3a692c7c1916eeeb61e7a041ee8bcef035`;
- PR `#33` mesclada em `73a128ec44cde17867bbac6a7854ce86a43aba5a`;
- CI da PR `31431473940` e CI pós-merge `31431739320`: Linux e Windows em `success`, zero anotações;
- artefatos pós-merge: Linux `9079413130` e Windows `9079450269`, com digests registrados na evidência permanente;
- suíte local de fechamento: 543 testes aprovados; cobertura combinada: 62.45%; mypy: zero erros em 66 arquivos;
- `R-005`: **ENCERRADO NO ESCOPO APROVADO**; Etapa 6: **CONCLUÍDA**;
- Etapa 7: não iniciada; release: **NÃO APROVADA**.

Snapshot de referência do encerramento formal da Etapa 5, em 10 de agosto de 2026:

- âncora técnica integrada e auditada da Etapa 5: `574be9bd0268e70c384903f93f16cf6e73aa57a2`;
- PR `#27` fechada e mesclada a partir do HEAD documental `8ce44c238aaea79dafa64b8e1bba3ba5a8a7157e`;
- Pacotes 1, 2A, 2B, 3A, 3B, 3B.1, 4A, 4B, 4C, 5A e 5B da Etapa 5: integrados; Pacote 5C: integrado;
- gate funcional v4.1 no Windows/Python 3.11.9: 95 testes focais, 16 documentais, 517 totais e cobertura global de 66%;
- validação manual aprovada e integração visual automática aprovada em 17/17 estados;
- CI final pré-merge `Private validation` `#83` (`31135700216`): Linux e Windows em `success`;
- CI pós-merge `Private validation` `#84` (`31136893143`) no merge commit: Linux e Windows em `success`;
- artefato Linux pós-merge: `8978309717`, SHA-256 `25ee252a77fb43796a6c5b1cbbf10c5987791187a6e860a11c17e9980d45b091`;
- artefato Windows pós-merge: `8978326062`, SHA-256 `0432e2e7ccc11d21d8769f160268f820ccf62af7edb5fd6f5a2070bcca4c912f`;
- branch funcional preservada no remoto;
- PR de fechamento `#28` mesclada a partir do HEAD `ab71e148c0b7441bd36f489472856d0b4adfaa1e`;
- pacote técnico final PR `#29`, HEAD `956db473a88641bfdcfbd49ed122479f3fa2c51d`, mesclado em `574be9bd0268e70c384903f93f16cf6e73aa57a2`;
- CI pós-merge técnico `31425585259`: Linux `93576381868` e Windows `93576382048` em `success`, zero anotações;
- artefatos técnicos finais: Linux `9077091136` (`sha256:0ce0ad1f77b348f1d4061c7783a3467633a3089f19b18327627979f51befce51`) e Windows `9077113199` (`sha256:ab18e3e260f3f2b1e64b41e834363460f721112131411f350ac83e779fa9dae8`);
- `R-004`: **ENCERRADO NO ESCOPO APROVADO**; Etapa 5: **CONCLUÍDA**;
- Etapa 6: não iniciada.

As Etapas 5, 6, 7, 8, 9 e 10 possuem fechamento pós-merge comprovado. Na Etapa 10, o CI `31463873481` foi rejeitado, a correção foi integrada pela PR `#43` e o pós-merge `31469610508` foi aceito após auditoria dos artefatos. A Etapa 11 ainda não foi iniciada e a release permanece não aprovada.

## Auditoria corretiva publicada — 10 de agosto de 2026

A auditoria rigorosa inicialmente bloqueou o encerramento. O commit
`236eefd41ee51c7085e21d52fc80074eede0a793` foi publicado na PR `#28`; o HEAD
final `ab71e148c0b7441bd36f489472856d0b4adfaa1e` e o CI `31422901244`
aprovaram Linux e Windows. A PR foi integrada e o CI pós-merge `31423386971`
também foi aprovado, sem declarar release:

- Pillow 12.3.0 e lock auditados sem vulnerabilidades conhecidas;
- 196 testes legados executados, com 26 divergências brutas estritamente
  reconciliadas e zero falhas inesperadas;
- falso sucesso da CLI, limites do atlas e exportação real do painel de colisões
  corrigidos;
- `LayersPanel`, alias canônico do lasso, SAT compatível e PIL cobertos;
- mypy incluindo corpos não anotados: zero erros em 65 arquivos;
- suíte oficial completa: 532 testes aprovados;
- cobertura combinada de linhas e branches: 62.18%, com piso incremental de 62% no CI;
- matriz funcional viva: `docs/MATRIZ_FUNCIONALIDADES_ATUAL.md`;
- evidência: `docs/evidence/AUDITORIA_RIGOROSA_2026-08-10.md`;
- aviso de runtime resolvido: a PR `#29` atualizou as três Actions para
  `v7`/Node.js 24; o CI técnico final e as execuções subsequentes tiveram zero
  anotações.

## Capacidades comprovadas no estado integrado

- identidade NeoEng-D-Trace em UI, logger e metadados;
- interface em inglês e português;
- ambiente reproduzível em Python 3.11 com Poetry e CI Linux/Windows;
- formato de projeto `.ndtproj`, identificador `neoeng-d-trace-project` e schema v1 estrito;
- round-trip de camadas, grupos, polígonos, colisões personalizadas e segmentos Bézier;
- ciclo Abrir/Salvar validado na interface do Windows;
- histórico transacional integrado para os Pacotes 1, 2A, 2B, 3A, 3B, 3B.1, 4A, 4B, 4C, 5A, 5B e 5C da Etapa 5;
- exportação de sprite, atlas e metadados Generic/Godot/Unity/Phaser;
- exportação GLTF/GLB de cena e objeto com generator, geometria, metadados e padding validados;
- entrada gráfica e headless por `app.py`.

A PR `#27` foi mesclada por merge commit. O HEAD funcional
`8ce44c238aaea79dafa64b8e1bba3ba5a8a7157e` e o merge commit
`6c4bcb3d945405a4615a4d6551247d1b01ce79f1` são as âncoras funcionais da
Etapa 5. O relatório funcional v4.1 e a validação pré-merge continuam
preservados como snapshots históricos e não são reescritos retroativamente.

O pacote documental pós-merge da Etapa 5 registra `R-004` como **ENCERRADO
NO ESCOPO APROVADO**. A Etapa 6 foi concluída posteriormente pela PR `#33` e
pelo CI pós-merge `31431739320`. A Etapa 7 foi concluída posteriormente pela PR `#36` e pelo CI pós-merge `31437000772`. A Etapa 8 não foi iniciada e a release permanece não aprovada.

## Estrutura aprovada

Existe uma única árvore de implementação:

```text
app.py
src/
├── collision/
├── core/
├── exporters/
├── models/
├── physics/
├── tools/
├── ui/
└── utils/
```

Não existe uma segunda árvore `neoeng_d_trace/`, nem aliases entre pacotes. O nome de distribuição é `neoeng-d-trace`; internamente, o código continua em `src/`.

## Ambiente reproduzível no Windows

Faixa oficial: Python `>=3.11,<3.12`. A referência operacional é Python 3.11.9, Poetry 2.4.1 e ambiente virtual local `.venv`.

```powershell
Set-Location "C:\caminho\do\NeoEng-D-Trace"
$Python311 = "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe"
& $Python311 --version
& $Python311 -m venv .venv
& ".\.venv\Scripts\python.exe" -m pip install --upgrade pip
& ".\.venv\Scripts\python.exe" -m pip install "poetry==2.4.1"
$env:POETRY_VIRTUALENVS_IN_PROJECT = "true"
& ".\.venv\Scripts\python.exe" -m poetry check --lock --strict
& ".\.venv\Scripts\python.exe" -m poetry sync --no-interaction --no-ansi
& ".\.venv\Scripts\python.exe" -m poetry run python .\app.py
```

O caminho acima usa a instalação padrão do Python 3.11 no perfil do Windows sem depender do `py` launcher. Em outro computador, ajuste apenas `$Python311` depois de confirmar a versão exata.

Quando `poetry` já estiver disponível no terminal:

```powershell
poetry check --lock --strict
poetry sync --no-interaction --no-ansi
poetry run python .\app.py
```

Ajuda da CLI:

```powershell
poetry run python .\app.py --help
```

Entrada instalada:

```powershell
neoeng-d-trace
```

## Gate local mínimo

```powershell
poetry run python tools/baseline_integrity.py --verify
poetry check --lock --strict
poetry run python -m compileall -q -f app.py src tests pack_for_ai.py tools
poetry run flake8 src tests tools app.py pack_for_ai.py
poetry run black --check --diff src tests tools app.py pack_for_ai.py
poetry run isort --check-only --diff src tests tools app.py pack_for_ai.py
poetry run mypy src
poetry run pip-audit
poetry run bandit -q -r src -lll
poetry run pytest --cov=src --cov-branch --cov-fail-under=62 --cov-report=term-missing --cov-report=xml
poetry run python tools/run_legacy_tests.py --group all
poetry run python tools/baseline_integrity.py --verify
git diff --check
```

A validação oficial de interface e dos correctors deve ocorrer no Windows 11 do mantenedor. CI Linux não substitui o gate Windows, e teste local não substitui o CI do HEAD publicado.

## Configuração

Por compatibilidade, a configuração continua em `config.json` na raiz do projeto. Uma mudança futura para AppData exige etapa própria, importação explícita e rollback.

## Limitações e riscos abertos

- `R-003`: cobertura integral de UI e ferramentas ainda pendente;
- `R-004`: encerrado no escopo aprovado; Etapa 5 concluída após integração do registro e CI final da `main`;
- `R-005`: encerrado no escopo aprovado após schema v1 unificado, PR `#33` e CI pós-merge `31431739320`;
- `R-006`: encerrado no escopo aprovado após matriz integral da CLI, PR `#36` e CI pós-merge `31437000772`;
- `R-007`: persistência Bézier está implementada, mas validações geométricas adicionais pertencem à Etapa 8;
- `R-008`: encerrado no escopo aprovado após API estática unificada, PR `#40`, merge `76dd6b7ca3e7da08fab653d66ae29a33a839baf3` e CI pós-merge `31445518755`;
- `R-011` permanece para refatoração protegida;
- `R-012` está mitigado por auditoria automatizada, mas limites operacionais permanecem na Etapa 12;
- `R-013`: encerrado no escopo auditado após integração e CI pós-merge aprovado;
- `LayersPanel` está integrado à `MainWindow` e coberto por teste Qt;
- validação Godot/Unity da Etapa 10 foi integrada pela PR `#42`; o CI pós-merge `31463873481` foi rejeitado, a correção foi integrada pela PR `#43` e o pós-merge `31469610508` foi aceito; autosave, 2.5D, build Windows, instalador e release continuam pendentes;
- `PERF-MAGNETIC-001`, `UI-RESIZE-PT-001`, `POLY-VALIDATION-UX-001`, `GLTF-2D-001`, `GLTF-UV-001`, `GLTF-MATERIAL-001`, `GLTF-U16-001` e `GLTF-CLEANUP-001` permanecem limitações registradas.

## Regras de continuidade

- nenhuma funcionalidade será removida silenciosamente;
- correções e melhorias exigem testes, rollback e evidência vinculada ao SHA;
- documentos históricos não devem ser reescritos como se fossem estado atual;
- documentos vivos devem indicar data, commit ou condição de verificação;
- não usar `git reset`, `git clean`, force-push ou rebase destrutivo para limpar estado parcial;
- não executar Ready for review, merge, exclusão de branch, fechamento de risco ou transição de etapa sem autorização específica;
- não atribuir licença open source sem decisão jurídica formal.

## Baseline privada

A origem e as limitações do primeiro baseline limpo estão registradas em `docs/BASELINE_2026-07-29.md`. A integridade do estado rastreado atual é verificável por `python tools/baseline_integrity.py --verify`.
