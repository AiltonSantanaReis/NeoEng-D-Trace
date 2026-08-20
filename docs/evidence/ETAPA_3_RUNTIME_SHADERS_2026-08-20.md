# Evidência — Etapa 3 — Runtime de shaders

## Identificação

- Commit auditado: `1c75c8591897e925d5398358ea6be31756581b48`.
- Branch auditada: `Ailton/runtime-phase3-shaders`.
- Auditor: `scripts/audit_runtime_shaders_phase3.py`.
- Pacote: `docs/evidence/artifacts/runtime-shaders-phase3-2026-08-20/`.
- Estado: validação local pré-merge; CI, PR, merge e pós-merge pendentes.

## Ambiente

- Sistema operacional: Windows 10 build `10.0.26200`.
- Python: `3.11.9`.
- Backend real: Qt Shader Tools `qsb.exe` fornecido pelo PySide6.
- Dependências: ambiente `.venv` do projeto e lockfile existente.

## Objetivo e escopo

Foi implementado o contrato versionado de shaders/materials do runtime, sem
reinterpretar o schema `.ndtproj` v1, o schema lateral de cenário ou o
contrato de iluminação existente.

Incluído:

- sidecar `neoeng-d-trace-runtime-shader` v1/API v1;
- vínculo explícito ao SHA-256 do sidecar de iluminação;
- programas vertex/fragment com backend declarado `qt-qsb`;
- uniforms finitos e limitados, referências únicas e validação estrita;
- JSON canônico, rejeição de BOM, chaves duplicadas, NUL e limites;
- compilação real de ambos os estágios pelo `qsb`;
- publicação atômica somente após todos os estágios compilarem;
- preservação dos binários anteriores em compilação inválida ou timeout;
- capacidade `runtime.shaders` no host, sem anunciar partículas ou efeitos não
  implementados.

Fora do escopo: partículas, pós-processamento, triggers, streaming e
adaptadores completos de runtime Godot/Unity.

## Comandos e resultados

- `python -m pytest --cov=src --cov-branch --cov-fail-under=90 --cov-report=term-missing --cov-report=xml` — **1456 passed, 2 skipped**, cobertura de linhas `91,02%`.
- `python tools/check_coverage_policy.py coverage.xml` — **PASS**; linhas >= 90%, branches >= 85% e módulos mensuráveis >= 30%.
- `black --check --diff src tests tools app.py pack_for_ai.py` — **PASS**.
- `isort --check-only --diff src tests tools app.py pack_for_ai.py` — **PASS**.
- `flake8 src tests tools app.py pack_for_ai.py` — **PASS**.
- `mypy src` — **PASS**, sem problemas em 119 arquivos.
- `compileall -q src tools app.py pack_for_ai.py` — **PASS**.
- testes focados de shaders, documentação e evidências — **60 passed**.
- `python scripts/audit_runtime_shaders_phase3.py --output <output>` —
  **PASS**, árvore limpa no commit auditado.

## Auditoria real e checks

Relatório: `stage3-runtime-shaders-report.json`.

- `source_tree_clean`: `true`;
- `canonical_sidecar_roundtrip`: `true`;
- `real_qt_qsb_resolved`: `true`;
- `both_stages_compiled`: `true`;
- `invalid_stage_rejected_without_replacement`: `true`;
- `privacy`: `true`.

A compilação produziu dois binários reais e a tentativa posterior com fragment
inválido foi rejeitada pelo `qsb`, preservando os hashes dos binários anteriores.
A execução preliminar em worktree modificado foi preservada apenas como evento
não aprovado; ela falhou corretamente em `source_tree_clean` e não foi usada
para obter PASS.

## Artefatos e hashes SHA-256

- `stage3-runtime-shaders-report.json`: 2077 bytes — `4ed53b0789f81ef2e50d42e18b05cc9ba80c8884725f780dc9f963356892a7b1`.
- `artifact-index.json`: 791 bytes — `1e023e4c04d7ea1d56dfc004c2376ee39d3e9ada6e66ef930b516e9c8fde5304`.
- `compiled/basic.vertex.qsb`: 401 bytes — `a423babf7303038a9a609ba30f460ca981e2f6782f3e7c09f2cebda216a74e1a`.
- `compiled/basic.fragment.qsb`: 216 bytes — `f922f9d64a646c1a38ad40fee0dafc20dd04bbfae4165cbfa09c9db7fb133272`.
- `shader-sidecar.json`: 1007 bytes — `e230c8fbc2c6aaf722fca1a564a814051fcfbb15a64cd725df47b514e237d607`.
- `shader-sidecar-copy.json`: 1007 bytes — `e230c8fbc2c6aaf722fca1a564a814051fcfbb15a64cd725df47b514e237d607`.

O `artifact-index.json` contém os hashes e tamanhos de todos os arquivos do
pacote, excluindo apenas o próprio índice.

## Falhas e causa raiz

A primeira execução do auditor foi feita antes do checkpoint, com a árvore
modificada. Ela falhou exclusivamente no requisito de árvore limpa, enquanto
compilação, rejeição negativa, canonicalização e privacidade passaram. Nenhum
limiar, scanner, asserção ou regra foi alterado. A execução posterior no commit
`1c75c85` foi feita em diretório novo e passou integralmente.

## Limitações e riscos residuais

- O backend real comprovado nesta etapa é Qt Shader Tools (`qsb`); backends
  não declarados são rejeitados explicitamente, sem fallback silencioso.
- Não há ainda validação de rasterização GPU, VRAM, FPS ou driver específico.
- A reprodução em Godot/Unity pertence à fase posterior de adaptadores reais.
- CI remoto, promoção de PR, merge e validação pós-merge ainda estão pendentes.

## Validação pós-commit local

Após o commit da evidência `355cb6dadca5e4b1b0ebcbde933f665e22ee34cd`, a
árvore permaneceu limpa e os bytes rastreados foram revalidados:

- baseline por blobs Git: **PASS**, `1743 files`;
- integridade de evidências por blobs Git: **PASS**, `70 manifests`;
- auditor temporário: **PASS**, commit-fonte `355cb6d`;
- `source_tree_clean`, compilação dos dois estágios, rejeição negativa e
  privacidade: todos `true`.

Essa execução confirma a proveniência pós-commit; os artefatos hashados
versionados continuam sendo os do auditor final executado no commit de
implementação `1c75c85`.

## Decisão

**NÃO APROVADO PARA MERGE — implementação e validação local PASS; falta CI
remoto obrigatório, revisão da PR, merge normal e validação pós-merge.**
