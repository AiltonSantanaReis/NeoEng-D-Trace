# Evidência — Etapa 4B.4: correção de validadores e integridade por blobs

## Identificação

- Commit técnico validado: `0891230e1adcd159d206176a8cd18eebf6b33539`
- Branch de trabalho: `stage4-parallax-camera`
- Data: 18 de agosto de 2026
- Estado: candidato pré-merge da PR `#99`; não representa integração em `main` nem aprovação de release.

## Problema reproduzido e causa-raiz

A execução CI anterior (`32168346925`) rejeitou a integridade dos manifests porque o worktree Windows continha CRLF enquanto os blobs Git continham LF. O validador local lia o worktree e podia declarar PASS para bytes diferentes dos revisados pelo CI. A divergência foi reproduzida comparando os bytes do worktree com `git show :<arquivo>`; não foi tratada como falso positivo.

## Correções aplicadas

- `.gitattributes` fixa LF para `*.py`, `*.gd`, `*.cs`, `*.meta` e mantém o contrato de evidências.
- `tools/evidence_integrity.py` ganhou `--git-blob`; validação e `--rewrite` podem usar os bytes staged.
- `tools/baseline_integrity.py` e os quatro gates correspondentes do CI também usam `--git-blob`.
- Manifests de evidência e `baseline_manifest.json` foram regenerados contra os bytes versionados.
- Validadores Godot e Unity agora rejeitam identidade, chaves extras/ausentes, hashes não canônicos, limites, referências duplicadas e valores de câmera/parallax inválidos.
- O harness real passou a executar cinco casos negativos independentes por engine.

## Testes locais

- Foco de integridade/contrato: `40 passed`.
- Suíte completa: `1325 passed, 2 skipped, 10 warnings`.
- Cobertura exibida pelo pytest: `90,88%`; `coverage.xml`: `92,72%` linhas e `85,10%` ramos; política de cobertura aprovada.
- `mypy`, `flake8`, `black --check`, `isort --check-only`, compilação Python e Bandit: aprovados.
- `pip-audit`: nenhuma vulnerabilidade conhecida; o pacote local `neoeng-d-trace` não é publicado no PyPI e foi reportado como não auditável, sem ser convertido artificialmente em PASS.
- Suíte legada: `196` testes brutos, `27` falhas históricas exatamente reconciliadas (`27/27`), zero falhas inesperadas; o resultado bruto não é apresentado como `196 passed`.

## Execução real Godot/Unity

Comando executado:

```text
python scripts/audit_stage4b4_engines.py
```

- Godot: `4.7.stable`; positivo/plugin: exit `0`; cada caso negativo: exit `1`.
- Unity: `6000.5.7f1`; positivo: exit `0`; cada caso negativo: exit `1`.
- Casos negativos: `wrong_format`, `generator_identity`, `lowercase_binding_hash`, `camera_zoom`, `parallax_range`.
- `payload_sha256`: `75ba287e57a77e86b5383030da2ae9a5cf62e753e29f7e833b371f2b8e24bfdc`.
- `artifact-index.json` SHA-256: `7e590775f84f7d9ebd294f8004eae1b2e357607dec43a9010ad387173697eb13`.
- `engine-report.json` SHA-256: `71f47d69e48ac6a9bd675755dab74ff6f3934aa59084bf2fc865a7c1c4d6f77d`.
- O relatório final foi `PASS`.

A primeira execução após o fortalecimento falhou porque o adaptador Godot usava, por engano, o identificador runtime para validar o binding do sidecar. A falha foi corrigida para o identificador do schema lateral e a execução real foi repetida; os resultados acima são da repetição aprovada. Essa falha intermediária permanece registrada nesta evidência.

## Artefatos

- `docs/evidence/artifacts/stage4b4-engine-validation-2026-08-18/engine-report.json`
- `docs/evidence/artifacts/stage4b4-engine-validation-2026-08-18/artifact-index.json`
- logs positivos, negativos e de plugin no mesmo diretório.
- Os logs foram sanitizados pelo harness; nenhum caminho local ou identificador de host é requisito da evidência publicada.

## Limitações e riscos residuais

- O CI atual valida os contratos Python e a integridade dos artefatos; ele não inicializa dinamicamente Godot/Unity. A execução real das engines permanece evidência local reproduzível, conforme a governança vigente.
- Os 27 resultados legados continuam sendo falhas brutas históricas reconciliadas, não foram removidos nem reclassificados como testes aprovados.
- A PR ainda depende dos jobs Linux e Windows remotos; não é permitido retirar o draft, fazer merge ou declarar release aprovada antes desses jobs.

## Decisão

APROVADO PARA SUBMISSÃO À CI REMOTA — NÃO APROVA MERGE OU RELEASE.
