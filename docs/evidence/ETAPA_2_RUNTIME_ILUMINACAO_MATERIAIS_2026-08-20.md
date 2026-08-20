# Evidência — Etapa 2 — Iluminação e materiais do runtime

## Identificação

- Implementação auditada: `bd25b0e30b1896a8cc4192985428ea9267505f02`
- Branch auditada: `Ailton/runtime-phase2-lighting-materials`
- Data/hora do auditor: `2026-08-20T13:00:46+00:00`
- Auditor: `scripts/audit_runtime_lighting_phase2.py`
- Pacote: `docs/evidence/artifacts/runtime-lighting-phase2-2026-08-20/`

## Ambiente

- Sistema operacional: Windows 10 build `10.0.26200`
- Python: `3.11.9`
- Dependências: ambiente `.venv` do projeto, lockfile validado pelo CI
- Baseline contra blobs Git antes do pacote: `1677 files`
- Baseline final staged após incluir o pacote: `1689 files` — PASS.
- Manifests de evidência validados antes do pacote: `64`
- Manifests finais staged após incluir o pacote: `65` — PASS.

## Objetivo e escopo

Foi implementado o contrato versionado de iluminação e materiais como
sidecar do exportador de cenário runtime existente. O schema lateral
`neoeng-d-trace-scenario` v1 e o exportador runtime v1 não foram reinterpretados.

Incluído:

- `neoeng-d-trace-runtime-lighting` schema v1 e API v1;
- vínculo explícito ao hash SHA-256 do cenário runtime de origem;
- fontes `point`, `directional` e `spot` com limites finitos;
- materiais `lit` e `unlit`, albedo, emissão, opacidade e bindings por objeto;
- sockets de luz com posição 2.5D e referência de fonte;
- preview estrutural determinístico, sem relógio de parede ou aleatoriedade;
- fallback seguro `unlit` e decisão incompatível explícita;
- carregamento canônico, rejeição de BOM, duplicatas e números não finitos;
- preservação do estado anterior em substituição inválida;
- capacidade `runtime.lighting` registrada no host base.

## Comandos executados

O auditor executou os comandos abaixo no commit identificado:

- `pytest` focado e suíte integral;
- `black --check`;
- `flake8`;
- `mypy src/runtime`;
- `py_compile`;
- `tools/baseline_integrity.py --verify --git-blob`;
- `tools/evidence_integrity.py --require-tracked --git-blob`;
- `git diff --check`.

## Resultados

- Foco da etapa: `87 passed`.
- Suíte integral: `1440 passed, 2 skipped`.
- Black: PASS.
- flake8: PASS.
- mypy: PASS.
- py_compile: PASS.
- Baseline Git-blob: PASS, `1677 files`.
- Integridade de evidências: PASS, `64 manifests`.
- Diff: PASS.
- Auditor: `PASS`.

Os dois skips são os skips históricos condicionados à permissão de symlink no
Windows; não foram criados nem alterados nesta etapa.

## Artefatos e hashes

- `runtime-lighting-report.json`: 3698 bytes; SHA-256
  `8046cbf791eccd6792f15ec1f9d68f13d7c1a5b3d2fd6c5d422edf9fd5615a1f`.
- `artifact-index.json`: 1406 bytes; SHA-256 `48d84c41339b38eecca73f8ce83e33ee7bb157225aefb4ccc87e18d3d26abf60`.
- Os logs individuais de cada gate estão no mesmo diretório e são indexados
  pelo `artifact-index.json`.

## Falhas e causa raiz

Durante a preparação, o baseline inicialmente rejeitou o commit técnico
porque os novos arquivos ainda não estavam no manifesto. O manifesto foi
regenerado com `--git-blob`, verificado e registrado no commit separado de
reconciliação `bd25b0e` antes da auditoria final.

Uma primeira invocação do auditor também pré-criou o diretório de saída,
violando o contrato de não sobrescrita do próprio auditor. Nenhum relatório
foi aceito daquela execução; a execução válida foi feita em diretório novo e
produziu `PASS`.

## Limitações e riscos residuais

- O preview é avaliação estrutural determinística de cor, não rasterização
  GPU nem simulação de shader.
- Shaders, partículas, pós-processamento, triggers e streaming permanecem nas
  fases futuras do ADR.
- VRAM, FPS, driver e comportamento específico de hardware não são gates desta
  fase.
- Reprodução em Godot e Unity pertence à fase posterior de adaptadores reais.
- A integração da PR, CI remoto e validação pós-merge ainda são pendentes;
  este documento não declara encerramento formal antes desses gates.

## Decisão

**NÃO APROVADO — validação local PASS; PR, CI remoto, merge e validação
pós-merge pendentes.**
