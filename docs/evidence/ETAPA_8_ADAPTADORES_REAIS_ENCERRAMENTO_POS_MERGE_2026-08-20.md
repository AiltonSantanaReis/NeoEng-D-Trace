# Etapa 8 — Encerramento pós-merge dos adaptadores reais

Decisão: APROVADA somente no escopo técnico dos adaptadores descrito no ADR de runtime. Isto não aprova a release, GPU/VRAM ou renderização nativa dos efeitos classificados como degraded.

## Proveniência

- PR: #127
- Merge: 91e62a30b534356a2f20dc15299157233c46ba8e
- HEAD candidato da PR: bf15df502c64a4547a133678640f801249cc25f6
- Branch de validação pós-merge: main
- CI: run 32440065240, jobs Linux 96648812376 e Windows 96648812011
- Worktree pós-merge: limpo; HEAD local e origin/main coincidentes
- Auditor: scripts/audit_runtime_adapters_stage8.py

O snapshot pré-merge em ETAPA_8_ADAPTADORES_REAIS_2026-08-20.md foi preservado e não foi reescrito retroativamente.

## Comandos executados

    .venv\Scripts\python.exe scripts\audit_runtime_adapters_stage8.py --output diretorio-temporario-novo
    .venv\Scripts\python.exe -m pytest -q --cov=src --cov-branch --cov-fail-under=90 --cov-report=xml
    .venv\Scripts\python.exe tools\check_coverage_policy.py coverage.xml
    .venv\Scripts\python.exe tools\baseline_integrity.py --verify --git-blob
    .venv\Scripts\python.exe tools\evidence_integrity.py

O auditor foi executado em diretório temporário fora da árvore versionada. Somente o relatório sanitizado, o índice e os JSONs de runtime foram preservados no pacote versionado; projetos temporários, Library do Unity, caches e logs brutos não foram incluídos.

## Resultados reais

| Gate | Resultado |
|---|---|
| Auditor Python | PASS |
| Importação headless Godot real | PASS; 2 camadas, 3 fixed ticks |
| Importação batchmode Unity real | PASS; 2 camadas, 6 sidecars, 3 fixed ticks |
| Privacidade do relatório | PASS; privacy_leaks=[] |
| Árvore limpa/proveniência | PASS |
| Suíte integral | 1570 passed, 2 skipped |
| Cobertura de linhas | 91,00% |
| Política de cobertura | PASS |
| Baseline por blobs Git | PASS |
| Integridade de evidências | PASS |
| CI Linux/Windows | PASS |

Os dois skips são os testes históricos de symlink condicionados à permissão do Windows. Não foram introduzidos, removidos ou alterados nesta etapa.

O Unity registrou avisos ambientais reais do LicensingClient, token ausente e tentativas de acesso à configuração pública com timeout. Eles permanecem no relatório sanitizado e não foram convertidos em sucesso silencioso; o retorno funcional e os marcadores do adaptador foram independentes desses avisos.

## Capacidades e limitações

Godot e Unity reproduziram nativamente, neste escopo, carregamento da cena, hierarquia de camadas, ciclo de vida e fixed update. Os sidecars de iluminação, shaders, partículas, pós-processamento, triggers e streaming foram carregados, validados por hash e expostos pela matriz como degraded/metadata. A execução não comprova renderização nativa desses efeitos dentro dos adaptadores e não declara suporte universal de backend, GPU ou VRAM.

## Artefatos hashados

Pacote: artifacts/runtime-adapters-stage8-postmerge-2026-08-20/.

| Arquivo | Bytes | SHA-256 |
|---|---:|---|
| artifact-index.json | 1232 | 8f5b13541343e6870f4af59dc9b807f284fecd2feb8f2ee71515074a4219b72c |
| stage8-report.json | 8168 | 58197e838a0871db497fd214a3b50016f9bf5bb13a150e476dab6b9af821 |
| runtime/adapters.json | 6573 | 4e367190f584a1bda14536ffbc1c4650a3234873e2391f6d533dbe5df37a0345 |
| runtime/lighting.json | 2104 | 06893ca3e9cbbc16faef29a21f177e41dacb8cd305045f3e0e2bfebd5dffef8f |
| runtime/particles.json | 862 | bf831cdbac7cc6a61782c9f888bae88e62b5a372b65541989216185bcd572fc5 |
| runtime/post_processing.json | 1031 | 091143799f7bbb25404f0974228b10b204be4087cabc58480ca4e39d6e166409 |
| runtime/scenario.ndtscenario.runtime.json | 1099 | 064100a3d2d3144d08f353a13fc3c140a04af7d2021e81655ad24b8a5e6ad74a |
| runtime/shaders.json | 1007 | 40f0f5494032ceae8d65a329ca846eb699b5c165f2888a476db75a07835e7117 |
| runtime/streaming.json | 732 | a8b103b688794594e18b65fbe7a7f3f60ff3f49e1e70009bee6c8d24c00686f5 |
| runtime/triggers.json | 2005 | c7ec71524fff7deada68e02ebd81f88f15c228d4efb113322e04c328afcc01bd |

## Rollback

O ponto de restauração da implementação é o merge 91e62a30b534356a2f20dc15299157233c46ba8e. A documentação e o pacote de evidências são aditivos; o snapshot pré-merge permanece disponível para comparação e rollback sem reescrita destrutiva.