# NeoEng-D-Trace

NeoEng-D-Trace é uma ferramenta desktop proprietária e principalmente offline para preparar assets de jogos a partir de imagens 2D: detectar objetos, corrigir contornos, editar polígonos e curvas Bézier, configurar colisões e exportar sprites, atlas, metadados e GLTF/GLB.

## Autoridade e estado operacional

O estado real do repositório local e remoto prevalece sobre qualquer snapshot documental. Antes de alterar código, consulte `docs/PLANO_MESTRE_ESTABILIZACAO.md`, `docs/MATRIZ_RISCOS_ESTABILIZACAO.md`, o índice `docs/evidence/README.md`, a PR atual e o CI ligado ao HEAD exato.

Snapshot de referência desta reconciliação documental, em 6 de agosto de 2026:

- `main` integrada até o Pacote 5B da Etapa 5, em `ee38a2f1dc85093e34140ddd087312629b4ecb43`;
- Etapa 5 ativa, com o risco `R-004` ainda aberto;
- Pacote 5C na PR `#27`, draft e não integrado; o HEAD funcional validado é `9bf83af0d58b5984ccfefc59a543428379b02632`, com 20 arquivos no escopo, gate local Windows/Python 3.11.9 de 95 testes focais, 16 documentais e 517 totais, cobertura global de 66%, validação manual aprovada e integração visual automática com 17/17 estados aprovados;
- o workflow `Private validation` `#82` (`31115744015`) foi concluído com Linux e Windows em `success` para o HEAD funcional `9bf83af0d58b5984ccfefc59a543428379b02632`;
- artefato Linux: `8973550294`, SHA-256 `d6cee9f94f04d706cccb106d6456dcbc3e482e4ed84aec2fa15b6bfa396be435`; artefato Windows: `8973729078`, SHA-256 `a433a229cdbc1bfe58d03804baa2edb223c5bc2f6c37d17431b90e86f3777aa6`;
- não havia comentários, reviews ou threads pendentes na PR no momento da verificação pré-merge;
- esta reconciliação cria um novo HEAD exclusivamente documental e exige novo CI Linux/Windows ligado ao commit que a contém antes de qualquer decisão sobre Ready for review;
- Etapa 6 não iniciada;
- nenhum texto deste README autoriza Ready for review, merge, fechamento de risco ou transição de etapa.

## Capacidades comprovadas no estado integrado

- identidade NeoEng-D-Trace em UI, logger e metadados;
- interface em inglês e português;
- ambiente reproduzível em Python 3.11 com Poetry e CI Linux/Windows;
- formato de projeto `.ndtproj`, identificador `neoeng-d-trace-project` e schema v1 estrito;
- round-trip de camadas, grupos, polígonos, colisões personalizadas e segmentos Bézier;
- ciclo Abrir/Salvar validado na interface do Windows;
- histórico transacional integrado para os Pacotes 1, 2A, 2B, 3A, 3B, 3B.1, 4A, 4B, 4C, 5A e 5B da Etapa 5;
- exportação de sprite, atlas e metadados Generic/Godot/Unity/Phaser;
- exportação GLTF/GLB de cena e objeto com generator, geometria, metadados e padding validados;
- entrada gráfica e headless por `app.py`.

A PR `#27` contém trabalho ainda não integrado. O HEAD `9bf83af0d58b5984ccfefc59a543428379b02632` é a âncora funcional já validada localmente, visualmente e pelo CI. O commit exclusivamente documental que contém esta reconciliação deve passar por novo CI Linux/Windows antes de Ready for review.

Ready for review, merge, fechamento de `R-004`, conclusão da Etapa 5 e início da Etapa 6 permanecem decisões independentes. O relatório funcional v4.1 continua preservado como snapshot histórico e não é reescrito retroativamente.

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
& ".\.venv\Scripts\python.exe" -m poetry check --lock
& ".\.venv\Scripts\python.exe" -m poetry sync --no-interaction --no-ansi
& ".\.venv\Scripts\python.exe" -m poetry run python .\app.py
```

O caminho acima usa a instalação padrão do Python 3.11 no perfil do Windows sem depender do `py` launcher. Em outro computador, ajuste apenas `$Python311` depois de confirmar a versão exata.

Quando `poetry` já estiver disponível no terminal:

```powershell
poetry check --lock
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
poetry check --lock
poetry run python -m compileall -q -f app.py src tests pack_for_ai.py tools
poetry run flake8 src tests tools app.py pack_for_ai.py --count --select=E9,F63,F7,F82 --show-source --statistics
poetry run black --check --diff src tests tools app.py pack_for_ai.py
poetry run isort --check-only --diff src tests tools app.py pack_for_ai.py
poetry run mypy src --ignore-missing-imports
poetry run pytest --cov=src --cov-report=term-missing --cov-report=xml
poetry run python tools/baseline_integrity.py --verify
git diff --check
```

A validação oficial de interface e dos correctors deve ocorrer no Windows 11 do mantenedor. CI Linux não substitui o gate Windows, e teste local não substitui o CI do HEAD publicado.

## Configuração

Por compatibilidade, a configuração continua em `config.json` na raiz do projeto. Uma mudança futura para AppData exige etapa própria, importação explícita e rollback.

## Limitações e riscos abertos

- `R-003`: cobertura integral de UI e ferramentas ainda pendente;
- `R-004`: Undo/Redo ainda não pode ser encerrado antes da integração e do encerramento formal do Pacote 5C;
- `R-005`: exportação de colisões pertence à Etapa 6, ainda não iniciada;
- `R-006`: confiabilidade integral da CLI pertence à Etapa 7;
- `R-007`: persistência Bézier está implementada, mas validações geométricas adicionais pertencem à Etapa 8;
- `R-008`: APIs duplicadas ou parciais pertencem à Etapa 9;
- `R-011`, `R-012` e `R-013` permanecem nas etapas definidas pela matriz de riscos;
- `LayersPanel` existe e foi validado isoladamente, mas sua integração à `MainWindow` não foi comprovada no Pacote 4C;
- autosave, 2.5D, build Windows, instalador e validação completa nas engines ainda não estão concluídos;
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
