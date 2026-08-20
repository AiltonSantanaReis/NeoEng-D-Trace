# EvidÃªncia â€” RUNTIME-ETAPA-4 â€” PartÃ­culas

## Estado

**APROVADO LOCALMENTE NO ESCOPO DA ETAPA / PR, CI, MERGE E PÃ“S-MERGE PENDENTES.**

Esta evidÃªncia registra a execuÃ§Ã£o real no commit local `7fb09a2e7d11a3c8a994dc1ad6136ee852883982`, no branch `Ailton/runtime-stage4-particles`. Ela nÃ£o declara integraÃ§Ã£o em `main`, aprovaÃ§Ã£o de PR ou release.

## GovernanÃ§a e escopo

A fase foi executada sob as polÃ­ticas globais do projeto, nÃ£o apenas sob o ADR especÃ­fico:

- `docs/POLITICA_QUALIDADE_E_EVIDENCIAS.md`;
- `docs/POLITICA_NAO_REGRESSAO.md`;
- `docs/PLANO_MESTRE_ESTABILIZACAO.md`;
- `docs/MATRIZ_RISCOS_ESTABILIZACAO.md`;
- `docs/evidence/README.md`;
- `.github/workflows/ci.yml` e regras de revisÃ£o.

O ADR `docs/ADR_RUNTIME_CENARIOS_EFEITOS_2026-08-20.md` Ã© o plano especÃ­fico do runtime e foi reconciliado para registrar que a Etapa 4 estÃ¡ em execuÃ§Ã£o, sem substituir as polÃ­ticas globais.

## Objetivo e implementaÃ§Ã£o

Foi implementado o contrato lateral versionado `neoeng-d-trace-runtime-particles` v1, vinculado por SHA-256 ao export de cenÃ¡rio `neoeng-d-trace-scenario-runtime` v1. O escopo comprovado contÃ©m:

- emissores estritos com limites de quantidade, vida, velocidade, taxa e capacidade total;
- fixed update com acumulador e limite de catch-up;
- sementes determinÃ­sticas, inclusive preservaÃ§Ã£o explÃ­cita de `seed=0`;
- ciclo de vida `ready`, `running`, `paused` e `stopped`;
- pausa sem mutar estado simulado;
- replay transitÃ³rio hash-bound, com versÃ£o de formato, algoritmo, `fixed_dt` e limite de ticks;
- persistÃªncia canÃ´nica UTF-8 JSON apenas do estado autoral;
- rejeiÃ§Ã£o de BOM, chaves duplicadas, nÃºmeros nÃ£o finitos, campos desconhecidos, limites invÃ¡lidos e bytes nÃ£o canÃ´nicos;
- gravaÃ§Ã£o atÃ´mica, preservando os bytes anteriores quando a nova exportaÃ§Ã£o Ã© rejeitada;
- capacidade `runtime.particles` anunciada no host somente apÃ³s a implementaÃ§Ã£o da etapa;
- auditor fail-closed com checks funcionais, privacidade, hashes e Ã¡rvore limpa.

A alteraÃ§Ã£o nos testes de capacidade das Etapas 1 e 3 registra a transiÃ§Ã£o contratual prevista de `runtime.particles` para `native` e mantÃ©m o caminho negativo com `runtime.unknown`. Isso nÃ£o removeu asserÃ§Ã£o nem comprovou regressÃ£o: a suÃ­te integral nÃ£o reproduziu regressÃ£o.

## Ambiente real

- Windows `10.0.26200`;
- Python `3.11.9`;
- ambiente virtual do projeto;
- branch e commit registrados no relatÃ³rio do auditor;
- sem caminhos locais ou identidade de mÃ¡quina nos artefatos versionados.

## Comandos e resultados

- `python -m pytest --cov=src --cov-branch --cov-fail-under=90 --cov-report=term-missing --cov-report=xml` â€” **1483 passed, 2 skipped**, cobertura total `91,08%`.
- `python tools/check_coverage_policy.py coverage.xml` â€” **PASS**; linhas >= 90%, branches >= 85% e mÃ³dulos mensurÃ¡veis >= 30%.
- `python -m pytest -q tests/test_stage1_runtime_base.py tests/test_stage2_runtime_lighting.py tests/test_stage3_runtime_shaders.py tests/test_stage4_runtime_particles.py` â€” **68 passed**.
- `black --check --diff src tests tools app.py pack_for_ai.py` â€” **PASS**.
- `isort --check-only --diff src tests tools app.py pack_for_ai.py` â€” **PASS**.
- `flake8 src tests tools app.py pack_for_ai.py` â€” **PASS**.
- `mypy src` â€” **PASS**, sem problemas em 120 arquivos.
- `python -m compileall -q src tests tools app.py pack_for_ai.py` â€” **PASS**.
- `python -m pip_audit` â€” **PASS**, nenhum CVE conhecido; o pacote local `neoeng-d-trace` nÃ£o existe no PyPI e foi reportado pelo prÃ³prio auditor como nÃ£o auditÃ¡vel nessa fonte.
- `python -m pytest -q -rs` â€” **1483 passed, 2 skipped**. Os dois skips sÃ£o preexistentes em criaÃ§Ã£o de symlink no Windows (`WinError 1314`), nÃ£o foram criados pela Etapa 4 e permanecem visÃ­veis. A cobertura de symlink Ã© executada no ambiente compatÃ­vel do CI; nÃ£o foi mascarada nem convertida em PASS local.

## Auditoria reproduzÃ­vel

Auditor: `scripts/audit_runtime_particles_phase4.py`.

A execuÃ§Ã£o preliminar, antes do checkpoint, retornou `FAIL` exclusivamente porque `source_tree_clean=false`; todos os checks funcionais eram verdadeiros. Essa execuÃ§Ã£o nÃ£o foi usada como aprovaÃ§Ã£o.

A execuÃ§Ã£o final foi realizada em diretÃ³rio de saÃ­da novo, apÃ³s o commit `7fb09a2`, com Ã¡rvore limpa, e retornou `PASS`:

- `source_tree_clean`: `true`;
- `canonical_sidecar_roundtrip`: `true`;
- `authorial_state_excludes_transient_state`: `true`;
- `fixed_update_is_deterministic`: `true`;
- `seed_zero_is_preserved`: `true`;
- `pause_preserves_state`: `true`;
- `limits_are_enforced`: `true`;
- `replay_is_hash_bound_and_reproducible`: `true`;
- `atomic_persistence_preserves_previous_bytes`: `true`;
- `privacy`: `true`.

Dados do contrato auditado: `format_id=neoeng-d-trace-runtime-particles`, schema `1`, algoritmo `1`, sidecar canÃ´nico de `862` bytes, SHA-256 `6b14443676c3ca8bbc612c1c470951f357bfb43b9de00601ad1226fbd4aa7408`, `fixed_dt=0.1`, um emissor e capacidade de quatro partÃ­culas no cenÃ¡rio de auditoria.

## Artefatos hashados

Pacote: `docs/evidence/artifacts/runtime-particles-phase4-2026-08-20/`.

- `stage4-runtime-particles-report.json` â€” `1993` bytes â€” SHA-256 `1df49e476e8711b0b291f43962b3f4d440311d336dfb4dcf86ddf592b144f8f2`;
- `particle-sidecar.json` â€” `862` bytes â€” SHA-256 `6b14443676c3ca8bbc612c1c470951f357bfb43b9de00601ad1226fbd4aa7408`;
- `particles.json` â€” `862` bytes â€” SHA-256 `6b14443676c3ca8bbc612c1c470951f357bfb43b9de00601ad1226fbd4aa7408`;
- `artifact-index.json` â€” `514` bytes â€” SHA-256 `ff1e77bf10e5fda4980d2c9b0d627c388449c892a7beb82b2c4d37134b4a7221`.

O Ã­ndice registra bytes e SHA-256 dos arquivos do pacote, excluindo apenas o prÃ³prio Ã­ndice, conforme o contrato do auditor.

## Falhas observadas e correÃ§Ãµes

- O primeiro teste focado revelou duas falhas reais de implementaÃ§Ã£o/teste: o loader expunha erro de validaÃ§Ã£o interna em vez de `ParticleFormatError`, e o teste de lifetime emitia partÃ­culas novas durante a verificaÃ§Ã£o de expiraÃ§Ã£o. Ambos foram corrigidos na origem; nÃ£o houve supressÃ£o de exceÃ§Ã£o nem relaxamento de asserÃ§Ã£o.
- A primeira execuÃ§Ã£o do auditor falhou corretamente em Ã¡rvore modificada. O checkpoint foi criado, a Ã¡rvore foi limpa e o auditor foi reexecutado com `PASS`.
- A cobertura de branches inicialmente ficou em `84,90%`, abaixo do gate de `85%`. Foram adicionados testes negativos de limites e estados invÃ¡lidos; o limiar permaneceu inalterado e o resultado final passou.
- Nenhuma regressÃ£o foi reproduzida na suÃ­te integral ou na validaÃ§Ã£o focada. A menÃ§Ã£o anterior a regressÃ£o foi reclassificada no ADR como hipÃ³tese nÃ£o confirmada, nÃ£o como evidÃªncia.

## Rollback e limitaÃ§Ãµes

O ponto anterior verificÃ¡vel Ã© o merge `342f55f` em `main`; o checkpoint da etapa Ã© `7fb09a2`. O rollback Ã© praticÃ¡vel por revert normal do checkpoint, sem force push ou reescrita de histÃ³rico, preservando os commits anteriores.

NÃ£o fazem parte desta fase e permanecem **nÃ£o testados/nÃ£o concluÃ­dos**:

- rasterizaÃ§Ã£o GPU, shaders de partÃ­culas, iluminaÃ§Ã£o e pÃ³s-processamento;
- VRAM, FPS e comportamento especÃ­fico de driver/backend;
- execuÃ§Ã£o real em Godot/Unity;
- partÃ­culas persistidas como estado transitÃ³rio ou replay salvo em arquivo; somente o estado autoral Ã© persistido por contrato;
- triggers, streaming e runtime completo da engine.

## Falha do primeiro CI e correção

A execução remota `32404980740` falhou nos jobs Linux `96541819933` e Windows `96541820201` antes dos testes, no gate `Verify clean baseline manifest`. A causa confirmada foi a alteração posterior de `docs/evidence/README.md` sem regenerar o `baseline_manifest.json` correspondente. A falha não foi mascarada nem tratada como PASS; o baseline foi regenerado contra os blobs staged, a integridade de evidências foi revalidada e o fix será submetido em novo SHA para nova execução integral do CI.
## DecisÃ£o

**APROVADO LOCALMENTE NO ESCOPO DA RUNTIME-ETAPA-4, NÃƒO INTEGRADO.** A implementaÃ§Ã£o, os testes locais, a auditoria fail-closed e os artefatos reproduzÃ­veis estÃ£o concluÃ­dos neste checkpoint. A etapa sÃ³ poderÃ¡ ser considerada formalmente concluÃ­da apÃ³s validaÃ§Ã£o dos bytes rastreados, atualizaÃ§Ã£o do baseline/manifesto, revisÃ£o do diff, PR, CI obrigatÃ³rio Linux/Windows, merge normal e validaÃ§Ã£o pÃ³s-merge. AtÃ© lÃ¡, nÃ£o declarar a capacidade como integrada em `main` nem promover release.
