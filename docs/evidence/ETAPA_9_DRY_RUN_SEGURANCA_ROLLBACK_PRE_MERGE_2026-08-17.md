# Etapa 9 — dry-run, segurança e rollback dos adaptadores nativos

## Baseline e escopo

- baseline verificado: 531ca525327b4e5bc5346f7bdc5ad900416259c;
- branch de trabalho: branch de validação da Etapa 9;
- escopo: planejamento sem escrita, validação de schema e hashes, rejeição
  fail-closed de caminhos inseguros e rollback de conjuntos de saídas;
- Etapa 10: não promovida;
- o plano vivo continua declarando as etapas 9 e 10 como não iniciadas até
  merge e CI pós-merge.

## Implementação verificada

- src/exporters/integration_sync.py: contrato Python de plano imutável,
  diff determinístico CREATE/UPDATE/UNCHANGED, validação de caminhos
  relativos, contenção na raiz, symlinks, hashes de imagem/atlas e aplicação
  multi-saída sobre AtomicOutputTransaction;
- integrations/godot/addons/neoeng_d_trace/import_generator.gd: dry-run
  completo antes de criar a raiz, plano de todas as saídas, commit agrupado e
  restauração de backups em falha;
- integrations/unity/package/com.neoeng.dtrace/Editor/UnityImportGenerator.cs:
  dry-run sem criação de Generated, validação de fontes/atlas, snapshot da
  raiz gerada e restauração em exceção;
- scripts/audit_native_stage9.py: fixture real, execução dos binários
  instalados, coleta de marcadores, hashes e sanitização de logs;
- tests/test_integration_sync.py: casos positivos e negativos para raiz
  inválida, destinos inseguros/duplicados, contenção externa, symlink,
  alteração do conjunto, drift de payload, rollback, hashes e metadata.

## Gates locais do projeto

Comandos executados no workspace antes desta evidência:

- pytest --cov=src --cov-branch --cov-fail-under=90 --cov-report=xml:
  1167 passed, 2 skipped, 10 warnings; cobertura total 90,72%;
- tools/check_coverage_policy.py coverage.xml: passou com linhas >= 90% e
  branches >= 85%;
- py_compile, black --check, isort --check-only e flake8 nos três arquivos
  Python da etapa: passaram;
- mypy src: Success: no issues found in 91 source files;
- git diff --check: passou;
- pip_audit --strict: não pode auditar o pacote local
  neoeng-d-trace (0.2.0) porque ele não está publicado no PyPI; isso é uma
  limitação real do gate, não foi convertido em PASS;
- Bandit reportou dez ocorrências B110 históricas em arquivos fora do escopo
  desta etapa; nenhum arquivo alterado pela Etapa 9 foi apontado.

## Execução real do Godot e Unity

O comando python scripts/audit_native_stage9.py foi executado com os
binários instalados, sem mocks para o importador:

- Godot 4.7.stable: dry-run sem artefatos, aplicação inicial,
  repetição determinística, rejeição de caminho inseguro e rejeição de drift
  de hash. Marcadores:
  GODOT_STAGE9_DRY_RUN=PASS,
  GODOT_STAGE9_APPLY=PASS,
  GODOT_STAGE9_REPEAT=PASS,
  GODOT_STAGE9_UNSAFE_PATH=REJECTED e
  GODOT_STAGE9_HASH_DRIFT=REJECTED;
- Unity 6000.5.7f1: dry-run real com Success=true,
  PlannedAssets=1, project_unchanged=true; aplicação inicial e repetição
  reais bem-sucedidas; cenário de falha retornou código 1, Success=false
  e partial_outputs_after_failure=[], comprovando restauração do conjunto;
- marcador Unity do dry-run:
  UNITY_NATIVE_STAGE9_DRY_RUN=SUCCESS;
- marcador agregado do harness:
  NATIVE_STAGE9=SUCCESS,
  GODOT_REAL_DRY_RUN=PASS,
  UNITY_REAL_DRY_RUN=PASS,
  HASH_DRIFT_REJECTED=PASS e
  REPEAT_IMPORT_DETERMINISTIC=PASS.

Os artefatos reproduzíveis estão em
docs/evidence/artifacts/native-stage9-2026-08-17/. O índice contém 11
arquivos, tamanho e SHA-256 de cada arquivo. A varredura final de privacidade
não encontrou nome de usuário, caminho local, endereço, processo, identidade
ou dado de licença nos artefatos.

## Falhas intermediárias observadas

As execuções intermediárias que não passaram não foram contadas como
evidência positiva:

- a primeira execução Godot revelou que o fixture precisava de pre-import
  antes da validação; o harness foi corrigido e o cenário foi repetido;
- duas versões iniciais do coletor Unity procuravam marcadores em escopo
  incorreto durante o bootstrap do projeto; foram corrigidas sem alterar o
  código avaliado;
- a primeira sanitização deixou metadados de sessão no log; a evidência foi
  invalidada, o sanitizador foi reforçado e todos os artefatos foram
  regenerados;
- a política de branches falhou inicialmente em 84,94%; foram adicionados
  testes reais de contenção e destinos normalizados duplicados, sem reduzir
  o limiar. A política final passou.

## Limitações e decisão

A CI atual executa os gates Python, tipagem, cobertura e integridade, mas não
inicializa dinamicamente Godot/Unity. Portanto, os resultados dos engines são
evidências locais reais e reproduzíveis, e não uma alegação de execução
dinâmica no CI. A implementação não afirma tolerância a queda de energia ou
corrupção de filesystem; o contrato comprovado cobre falha durante a
transação no mesmo processo.

STAGE9_STATUS=VALIDATED_PRE_MERGE

STAGE9_EVIDENCE=REAL_GODOT_AND_UNITY_ARTIFACTS

STAGE9_RELEASE_APPROVED=NO

STAGE10_STATUS=NOT_STARTED
