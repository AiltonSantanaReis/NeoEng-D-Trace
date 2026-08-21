# Etapa 8 — Adaptadores reais Godot/Unity

Estado: PASS funcional e auditoria limpa local concluída. A aprovação de
integração no repositório ainda depende de revisão, CI, merge e validação
pós-merge.

## Proveniência

- Commit auditado: 09df5da54f29507bdc61e829bc77ee44859a9a47
- Branch auditada: Ailton/runtime-stage8-adapters
- Worktree no auditor: limpo
- Auditor: scripts/audit_runtime_adapters_stage8.py
- Bundle: neoeng-d-trace-runtime-adapters v1
- Engines reais: Godot 4.7.stable.official.5b4e0cb0f e Unity 6000.5.7f1
- Privacidade: nenhum vazamento detectado nos artefatos versionados.

## Comandos reproduzíveis

- .\.venv\Scripts\python.exe scripts\audit_runtime_adapters_stage8.py --output <diretorio-novo>
- .\.venv\Scripts\python.exe -m pytest --cov=src --cov-branch --cov-fail-under=90 --cov-report=xml
- .\.venv\Scripts\python.exe tools\check_coverage_policy.py coverage.xml
- .\.venv\Scripts\python.exe tools\baseline_integrity.py --verify --git-blob

O auditor cria projetos temporários e invoca os executáveis reais em modo
headless. O diretório de saída deve ser novo; o auditor recusa sobrescrever
uma saída existente.

## Resultado funcional

| Validação | Resultado |
|---|---|
| Bundle Python para Godot | PASS |
| Bundle Python para Unity | PASS |
| Importação headless Godot | PASS |
| Importação headless Unity | PASS |
| Hierarquia de camadas observada | 2 |
| Fixed ticks observados | 3 |
| Sidecars observados no Unity | 6 |
| Índice de artefatos | PASS |
| Privacidade | PASS |
| Status formal fail-closed | PASS |

A matriz distingue native, degraded e incompatible. Nesta etapa, o adaptador
reproduz nativamente a importação da hierarquia, o ciclo de vida e o fixed
tick. Iluminação, shaders, partículas, pós-processamento, triggers e
streaming são carregados, hashados e expostos como sidecars/metadata com
compatibilidade degraded; a evidência não declara renderização nativa desses
efeitos dentro dos adaptadores.

## Avisos reais do Unity

A execução funcional retornou código 0 e emitiu todos os marcadores do
adaptador. O log também registrou falhas ambientais do LicensingClient,
token indisponível e tentativas de acesso à configuração pública da Unity
com timeout. Esses avisos foram preservados no relatório sanitizado,
classificados como não bloqueantes para este teste funcional e não foram
apagados nem convertidos artificialmente em PASS.

## Suíte e gates

- Suíte completa: 1.570 passed, 2 skipped já existentes.
- Cobertura de linhas: 91,00%.
- Gate de branches: >=85%.
- Gate de módulos mensuráveis: >=30%.
- Black, isort, Flake8, mypy, Bandit, py_compile e diff check: PASS.
- Baseline Git-blob: PASS.

## Artefatos hashados

| Artefato | Bytes | SHA-256 |
|---|---:|---|
| artifact-index.json | 1232 | ea911dde996227d6c52cbddc3fcc6bb553eda5f017d8fdc133401585bcb86285 |
| stage8-report.json | 8216 | 8358635ed394cd66db7bf6575d0313d46a810ceaf504af06147f2da28618428 |
| runtime/adapters.json | 6573 | 4e367190f584a1bda14536ffbc1c4650a3234873e2391f6d533dbe5df37a0345 |
| runtime/scenario.ndtscenario.runtime.json | 1099 | 064100a3d2d3144d08f353a13fc3c140a04af7d2021e81655ad24b8a5e6ad74a |
| runtime/lighting.json | 2104 | 06893ca3e9cbbc25404af29a21f177e41dacb8cd305045f3e0e2bfebd5dffef8f |
| runtime/shaders.json | 1007 | 40f0f5494032ceae8d65a329ca846eb699b5c165f2888a476db75a07835e7117 |
| runtime/particles.json | 862 | bf831cdbac7cc6a61782c9f888bae88e62b5a372b65541989216185bcd572fc5 |
| runtime/post_processing.json | 1031 | 091143799f7bbb25404f0974228b10b204be4087cabc58480ca4e39d6e166409 |
| runtime/triggers.json | 2005 | c7ec71524fff7deada68e02ebd81f88f15c228d4efb113322e04c328afcc01bd |
| runtime/streaming.json | 732 | a8b103b688794594e18b65fbe7a7f3f60ff3f49e1e70009bee6c8d24c00686f5 |

A pasta de evidências contém somente o relatório sanitizado, o índice e os
oito JSON necessários; caches, Library do Unity, logs brutos e projetos
temporários não fazem parte da evidência versionada.