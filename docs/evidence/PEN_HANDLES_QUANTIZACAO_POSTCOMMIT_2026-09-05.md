# Evidência pós-commit — alças e quantização da Caneta

ID: EVID-PEN-HANDLES-QUANTIZATION-POSTCOMMIT-20260905
Lote: PEN-HANDLES-20260905
Estado: IN_PROGRESS / BLOCKED
Data: 2026-09-05
Branch: Ailton/pen-handles-quantization-20260905
SHA auditado: 1068166f3c046e008928d98e68fdb187838c87bc
Base: 5b3e6b15cee93ef5c9d1d550745293fb8372b5b9

## Objetivo e escopo

Registrar a qualificação pós-commit do lote que remove tangentes implícitas
da criação por clique e cria alças somente por arraste explícito. A validação
determinística de polígonos inválidos, a quantização global, o histórico, os
snapshots legados e os contratos de persistência não foram relaxados nem
reescritos.

O commit foi criado somente após o aceite formal
`P2D-05 PRECOMMIT ACCEPT — PEN-HANDLES-20260905`. A evidência pré-commit
permanece preservada em
`docs/evidence/PEN_HANDLES_QUANTIZACAO_PRECOMMIT_2026-09-05.md` como snapshot
histórico e não é usada como prova do SHA atual.

## Ambiente

- Windows 11 convidado no VMware; `platform win32` e `platform_release 10`
  foram observados pelo Python/Windows API.
- Python 3.11.9, PySide6 6.10.1, pytest 9.1.1, Poetry 2.4.1 e PyInstaller
  6.22.0.
- O runner Qt utilizou `QT_QPA_PLATFORM=offscreen`; isto é teste de
  integração Qt, não clique nativo no sistema operacional.
- A árvore do worktree estava limpa antes do runner e do build:
  `build/pen-handles-worktree-20260905/`.
- Os recibos locais estão em diretórios `build/pen-handles-postcommit-*` e
  `build/pen-handles-base-shader-receipt-r2-20260905/`, fora do índice Git
  do produto; seus hashes e resultados estão registrados abaixo.

## Comandos executados

```text
python tools/run_windows_coverage_shards.py --output <receipt> --timeout-seconds 180
python tools/check_coverage_policy.py <receipt>/coverage.xml
python -B -m compileall -q src tests tools
flake8 src tests tools
black --check src tests tools
isort --check-only src tests tools
mypy src
python scripts/audit_stage4b5_quality.py --output <receipt>
pip-audit
bandit -q -r src -lll
python tools/baseline_integrity.py --verify --git-blob
python tools/evidence_integrity.py --require-tracked --git-blob
python tools/run_formal_legacy_gate.py --group all --output <receipt>
scripts/build_windows.ps1 -OutputRoot build/pen-handles-release-1068166-r3-20260905
```

O runner aprovado foi executado com o diretório `Scripts` do venv à frente
do `PATH`, para que `pyside6-qsb` resolvesse para o mesmo PySide6 do Python
3.11 usado pelos testes.

## Resultados observados

| Gate | Resultado observado |
|---|---|
| Runner Windows integral | PASS — `196/196` arquivos, `2019` testes, `0` falhas, `0` erros, `2` skips previstos |
| Cobertura integrada | PASS — linhas, branches e módulos mensuráveis acima dos limiares |
| Compileall | PASS |
| Flake8 | PASS |
| Black | PASS — `367` arquivos inalterados |
| isort | PASS |
| mypy | PASS — `148` arquivos sem erros |
| Stage 4B.5 | PASS — determinismo, benchmark e bytes dos artefatos |
| pip-audit | PASS — nenhuma vulnerabilidade conhecida; o pacote local não existe no PyPI e foi listado como não auditável |
| Bandit | PASS — nenhum achado em `-lll` |
| Baseline Git-blob | PASS — `3261` arquivos |
| Integridade de evidências Git-blob | PASS — `135` manifestos |
| Gate formal legado | ACCEPTED — `historical_returncode=1`, `exact=15`, `changed=11`, `missing=12`, `substitutes=42` |
| Build Windows portátil | PASS — PyInstaller, smoke e empacotamento concluídos |

O teste `tests/test_pen_creation_gestures.py` foi executado pelo runner
integral com `49` testes aprovados. A validação focada anterior, ainda no
mesmo conteúdo de código antes do commit, registrou `69 passed`; ela permanece
como evidência diagnóstica anterior, enquanto o runner acima é a qualificação
oficial do SHA commitado.

## Falha ambiental reproduzida e resolução controlada

A primeira execução pós-commit do runner falhou no shard
`test_stage3_runtime_shaders.py` com `14` testes, `2` falhas, porque o PATH
resolveu `C:\Users\atnco\AppData\Local\Programs\Python\Python313\Scripts\pyside6-qsb.exe`,
que não encontrou PySide6. O mesmo shard foi executado no worktree limpo da
base `5b3e6b1` e reproduziu exatamente `12 passed, 2 failed` com a mesma causa.
Essa falha foi preservada como diagnóstico ambiental herdado; não foi ocultada
nem atribuída ao patch. Com o qsb do venv explicitamente resolvido, o runner
integral passou e o shard de shaders registrou `14 passed`.

## Empacotamento

O script oficial `scripts/build_windows.ps1` foi executado em árvore limpa
com Poetry 2.4.1 usando o venv qualificado. O bundle portátil e o smoke foram
gerados com `SOURCE_COMMIT=1068166f3c046e008928d98e68fdb187838c87bc`. O ZIP
tem `314` arquivos, `124243242` bytes e SHA-256
`49108fc45c41ee8cbcd54beb7f487f5ed5d0000fe5b58b5364ce0255590f2ba2`.
O smoke retornou `SUCCESS` nos checks de CLI, projeto, JSON, GLB, perfis
Godot/Unity, GUI open/close e diretório de estado do usuário.

## Artefatos e hashes

| Artefato | Bytes | SHA-256 |
|---|---:|---|
| `build/pen-handles-postcommit-1068166-r2-20260905/coverage.xml` | 1202871 | f62cdf13c94fbcdab36b10209166384f549d64daa27106c6cccbff5bc4ce58f2 |
| `build/pen-handles-postcommit-1068166-r2-20260905/summary.json` | 169918 | 167b3194b446113f6cb127f48c2462daf99d074505f96c3a2b15249a3b442457 |
| `build/pen-handles-postcommit-1068166-static-20260905/static.log` | 2041 | 045bd94405058cd6693b6990ef9d9f2bba1ed82b4e69d19acbea9c067e965ddc |
| `build/pen-handles-postcommit-1068166-security-20260905/security.log` | 1824 | 88f5c565269c8a877fda7391ee2269588ce23b74a037079a8c99e55eed0a08d2 |
| `build/pen-handles-postcommit-1068166-stage4b5-r2-20260905/artifact-index.json` | 836 | d1014ff92ed3e601e8aca0c6cadba3b681f5a6fdc6b3dc02e1d621c221a14b7d |
| `build/pen-handles-postcommit-1068166-stage4b5-r2-20260905/benchmark-report.json` | 2935 | edd5f42a1b331b592b5d4aac51183cb4578652b1921b035e6ea450679ddd73a9 |
| `build/pen-handles-postcommit-1068166-legacy-20260905/formal-gate.json` | 11170 | 374bbfacfab8c609269a803a0800d40e896280443c23ccfffe8d5e9ae21cd773 |
| `build/pen-handles-postcommit-1068166-r2-20260905/junit/073-test_pen_creation_gestures.xml` | 7242 | b84eb46a95235c3756c6d1e092173ae5687869bc86a8034a089b973e0f3683aa |
| `build/pen-handles-postcommit-1068166-r2-20260905/junit/108-test_stage3_runtime_shaders.xml` | 2205 | b5c56ab3b60765758a0624104d0659c695072a4245bde8ab9b26606726529129 |
| `build/pen-handles-base-shader-receipt-r2-20260905/pytest.log` | 2606 | e30fa7847dda728874d07d01008d1025b2d42e28b3a2afdb8aa89e43b08e2e26 |
| `build/pen-handles-base-shader-receipt-r2-20260905/junit.xml` | 4792 | 37e76cdf125563808bae79a8611e9321c7310e6a8ef81012cbfa991c29dc0328 |
| `build/pen-handles-worktree-20260905/build/pen-handles-release-1068166-r3-20260905/portable/NeoEng-D-Trace/release-manifest.json` | 55754 | 0172c2a33b27c0be300e7157fd913dec31f3b910010970ccf8b73c2e6e2ef74d |
| `build/pen-handles-worktree-20260905/build/pen-handles-release-1068166-r3-20260905/NeoEng-D-Trace-0.3.0-win64-portable.zip` | 124243242 | 49108fc45c41ee8cbcd54beb7f487f5ed5d0000fe5b58b5364ce0255590f2ba2 |

## Limitações e decisão

- A auditoria nativa com cliques do sistema operacional no executável não foi
  executada nesta sessão; QTest/offscreen e o smoke de GUI não substituem essa
  prova. O helper nativo permanece bloqueado pelo ambiente de automação.
- CI remoto da branch ainda não foi executado; os gates locais não autorizam
  push, merge, tag ou release por si só.
- Os `2` skips do runner são os contratos históricos de symlink condicionados
  ao privilégio disponível nesta máquina; a prova VMware de symlink permanece
  separada e preservada.

Decisão formal: `IN_PROGRESS / BLOCKED`. A qualificação local do commit é
`PASS`; a publicação permanece bloqueada até revisão nativa e CI remoto
comprovados no SHA correspondente. Nenhum push, merge, tag ou release foi
realizado.
