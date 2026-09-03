# Evidência — Etapa 7 — CI remoto verde da PR #166 — 03/09/2026

**Status do gate remoto:** `PASS`

**Estado do plano:** `IN_PROGRESS`

**Integração:** `BLOCKED` — revisão humana e autorização de merge ainda não
foram registradas.

## Objetivo e escopo

Este snapshot registra a análise do CI remoto disparado pelo commit publicado
da candidata `fix/legacy-27-functional-regressions`. Ele fecha a pendência
remota do ajuste de timeout Windows sem reescrever a falha anterior registrada
em `ETAPA_7_CI_TIMEOUT_WINDOWS_2026-09-03.md`.

A validação cobre os gates Linux e Windows do workflow oficial, o runner Windows
por shards, a reconciliação formal do legado, a integridade da baseline e das
evidências e os dois contratos focais de symlink. Não declara encerramento global
do plano nem autoriza merge, tag ou release.

## Regras e fontes consultadas

Antes deste registro foram relidas:

- `docs/GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md`;
- `docs/POLITICA_QUALIDADE_E_EVIDENCIAS.md`;
- `docs/POLITICA_NAO_REGRESSAO.md`;
- `docs/evidence/README.md`;
- `docs/PLANO_CORRECAO_26_FALHAS_LEGADAS_2026-09-01.md`;
- `docs/ADR_WINDOWS_COVERAGE_SHARD_RUNNER_2026-09-03.md`;
- `.github/workflows/ci.yml`;
- `tools/run_windows_coverage_shards.py`;
- `tools/run_legacy_tests.py`;
- os snapshots protegidos em `quality/legacy_tests/`.

A regra aplicada foi preservar falhas e snapshots históricos, separar o
`tested_commit` da cabeça-fonte da PR e aceitar somente resultados observados
nos jobs oficiais e nos artefatos correspondentes.

## Identificação e proveniência

- PR: `#166`;
- branch: `fix/legacy-27-functional-regressions`;
- cabeça-fonte publicada: `f61ba6108f1c13ffe2c3d9b6b03aca132f3e4fe9`;
- base `main`: `7f3799c1b29835f6db5ab6d35c0cab5deda5765b`;
- workflow: `Private validation`;
- run: `33785352331`;
- evento: `pull_request`;
- resultado do run: `completed / success`;
- criado em `2026-09-03T17:34:21Z) e concluído em
  `2026-09-03T17:45:18Z`.

O checkout do CI buscou explicitamente
`refs/remotes/pull/166/merge`, no commit testado
`1eb297dec2faea82b06779778b6463b94a625897`. A API do GitHub confirmou que
esse objeto é `Merge f61ba6108f1c13ffe2c3d9b6b03aca132f3e4fe9 into
7f3799c1b29835f6db5ab6d35c0cab5deda5765b`, com a cabeça da PR como segundo
pai. O gate formal registrou separadamente
`source_head_commit=f61ba6108f1c13ffe2c3d9b6b03aca132f3e4fe9) e validou a
ancestralidade. Portanto, a diferença entre os SHAs é o merge sintético normal
do evento `pull_request`, não uma divergência não explicada.

## Resultado dos jobs

| Job | ID | Resultado | Resultado observado |
|---|---:|---|---|
| Linux `test` | `100748662139` | `SUCCESS` | `1919 passed`, 1 warning; baseline/evidence integrity e Stage 4B.5 passaram |
| Windows `test-windows` | `100748662510` | `SUCCESS` | runner `ACCEPTED`, `189/189` arquivos, `1919` testes, `0` falhas, `0` erros, `0` skips |

Ambos os jobs passaram a política de cobertura e verificaram
`Baseline verified: 3210 files`. A integridade de evidências reportou
`129 manifests validated` nos dois jobs. O Stage 4B.5 reportou
`STAGE4B5=PASS`.

### Cobertura extraída dos XMLs remotos

| Sistema | XML | Linhas | Branches |
|---|---|---:|---:|
| Linux | 1.157.539 bytes; SHA-256 `02d1de472493690f69eea9fbf8458928737c1672b85257183a45242ce1c91783` | `23890/25799` — 92,60% | `6665/7838` — 85,03% |
| Windows | 1.184.094 bytes; SHA-256 `5a87a7ac05bb214e97d2ec41c5bf2e4dc1488e7a390a62d2f72274246b431acc` | `23890/25799` — 92,60% | `6666/7838` — 85,05% |

Os thresholds e a seleção oficial não foram alterados. O runner Windows
registrou `selection_filters=[]`, timeout de shard de 300 segundos e aceitação
dos 189 arquivos.

## Symlink

No job Windows remoto, o JUnit
`windows-coverage/junit/039-test_integration_sync.xml` registrou
`31` testes, `0` skips e `0` falhas. Os dois contratos específicos foram
executados e passaram:

- `test_plan_rejects_symlink_escape`;
- `test_plan_rejects_symlink_destination`.

Isso comprova os dois contratos no checkout sintético do CI da PR. A evidência
VMware continua preservada em
`docs/evidence/ETAPA_7_SYMLINK_VMWARE_2026-09-02.md`, com a reconstrução
identificada pelo ZIP e patch, e permanece `PASS_SCOPED`; ela não é
reclassificada como evidência do SHA Git.

## Runner legado e snapshots

O artefato formal Windows
`legacy-tests/formal-gate.json` registrou:

- `accepted=true`;
- `tested_commit=1eb297dec2faea82b06779778b6463b94a625897`;
- `source_head_commit=f61ba6108f1c13ffe2c3d9b6b03aca132f3e4fe9`;
- runner histórico bruto: `196` testes, `26` falhas, `0` erros, `0`
  skips, retorno `1`;
- `15` assinaturas exatas, `11` assinaturas divergentes,
  `12` ausências e `42` substitutos aprovados.

O resultado formal aceitou a reconciliação atual sem transformar o runner
histórico em aprovação. Os snapshots
`quality/legacy_tests/manifest.json` e
`quality/legacy_tests/reconciliation.json` não foram editados, regenerados ou
removidos.

## Artefatos externos e hashes

Os artefatos do run permanecem retidos pelo GitHub por 30 dias e foram
identificados pela API:

| Artefato | ID | Bytes | Digest publicado |
|---|---:|---:|---|
| `validation-linux-python-3.11` | `9905289811` | `75862` | `sha256:3b6074db0895d1a28d2803f7ccb6944d5ebd1def93b97e6ed2edab27c00f8233` |
| `validation-windows-python-3.11` | `9905574609` | `63220911` | `sha256:1ae8d5e744727bce0d4f6aaa2e8318a53055f2452586aba5079954a0e2bd9522` |

Os hashes dos arquivos relevantes extraídos, o resumo do runner e o gate
formal estão no índice
`artifacts/etapa7-ci-rerun-pr166-2026-09-03/artifact-index.json`.

## Decisão formal e limites

O gate remoto da PR `#166`, no commit-fonte
`f61ba6108f1c13ffe2c3d9b6b03aca132f3e4fe9`, está `PASS`. A correção do
timeout Windows foi comprovada nos dois jobs oficiais, sem alterar os snapshots,
a seleção, os thresholds ou os critérios.

O plano permanece `IN_PROGRESS` e a integração `BLOCKED`: a aprovação dos
jobs não substitui revisão humana nem autorização explícita de merge. Não foram
executados merge, tag ou release. Qualquer novo commit, inclusive documental,
deve ser validado pelo CI correspondente antes de ser tratado como revisão
corrente.

Rollback: reverter o commit técnico
`febc85471e5ced519f47626665f5d995e7cf60a9` e, separadamente, o commit
documental que registra este snapshot; os snapshots anteriores permanecem
preservados.
