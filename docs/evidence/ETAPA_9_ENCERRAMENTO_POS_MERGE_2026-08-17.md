# Evidência — Etapa 9 — encerramento pós-merge

## Identificação

- escopo: dry-run, segurança e rollback dos adaptadores nativos Godot/Unity;
- PR funcional: #81;
- merge integrado no main: e1620571ab2f638ba671baa33ac508858e229313;
- commit-fonte validado antes do merge: 5d17fa6227b088c75ed9fb72b70016aa7c7b3ee8;
- CI pré-merge: 32011747754;
- CI pós-merge do main: 32012110722;
- data do fechamento: 2026-08-17.

## Escopo efetivamente integrado

A Etapa 9 integrou planejamento sem escrita, validação de schema e hashes,
rejeição fail-closed de destinos inseguros, aplicação determinística,
proteção contra drift e rollback do conjunto de saídas nos adaptadores nativos.
O código não declara proteção contra queda de energia ou corrupção externa do
filesystem; o rollback comprovado é o da falha durante a transação no mesmo
processo.

## Evidências e gates

- CI pré-merge 32011747754: Linux e Windows em success;
- CI pós-merge 32012110722: Linux e Windows em success;
- validação local: 1167 passed, 2 skipped; os skips correspondem aos testes de
  symlink quando a permissão não está disponível no Windows local;
- cobertura total: 90,72%; política de linhas/branches aprovada;
- mypy src: sem erros;
- baseline e integridade das evidências: aprovados;
- git diff --check: aprovado;
- pip-audit: limitação declarada porque o pacote local não está publicado no
  PyPI; não foi reportado como PASS;
- Bandit: dez ocorrências B110 históricas fora dos arquivos alterados pela
  Etapa 9; nenhum arquivo alterado nesta etapa foi promovido como vulnerável.

## Execução real das engines

O harness scripts/audit_native_stage9.py executou os binários instalados,
sem mocks para os importadores:

- Godot 4.7.stable: dry-run, aplicação inicial, repetição determinística,
  rejeição de caminho inseguro e rejeição de drift de hash;
- Unity 6000.5.7f1: dry-run sem mutação do projeto, aplicação inicial,
  repetição determinística e falha forçada com restauração sem saídas parciais;
- os marcadores agregados registrados foram:
  NATIVE_STAGE9=SUCCESS, GODOT_REAL_DRY_RUN=PASS,
  UNITY_REAL_DRY_RUN=PASS, HASH_DRIFT_REJECTED=PASS e
  REPEAT_IMPORT_DETERMINISTIC=PASS;
- a execução dinâmica de Godot/Unity não faz parte da CI atual. Os resultados
  das engines são evidências locais reais e reproduzíveis, não uma alegação de
  cobertura dinâmica no CI.

## Artefatos

O diretório docs/evidence/artifacts/native-stage9-2026-08-17/ contém 13
arquivos versionados. O stage9-index.json lista 12 payloads com tamanho e
SHA-256; o próprio índice completa o conjunto. O stage9-report.json registra
os resultados estruturados, e os logs separados preservam dry-run, aplicação,
repetição, rejeições, drift e rollback. A varredura final de privacidade não
encontrou nome de usuário, caminho local, processo, identidade ou dado de
licença.

## Falhas intermediárias e correções auditáveis

As falhas intermediárias foram preservadas no histórico de desenvolvimento e
não foram contadas como sucesso: houve correção da ordem de validação de
symlink, remoção de referência indevida à branch no documento, e correção do
teste de destinos duplicados normalizados para ser portátil entre Linux e
Windows. O CI corretivo passou nos dois sistemas antes do merge; o CI
pós-merge também passou nos dois sistemas.

## Limitações e decisão

A Etapa 9 está integrada no escopo aprovado. Isso não aprova release e não
promove a Etapa 10. Permanecem explícitos: execução real das engines somente
como evidência local, limitação do pip-audit para o pacote local não publicado,
ocorrências históricas B110 fora do escopo e ausência de garantia contra queda
de energia/corrupção externa do filesystem.

STAGE9_STATUS=INTEGRATED
STAGE9_MERGE=e1620571ab2f638ba671baa33ac508858e229313
STAGE9_POST_MERGE_CI=32012110722
STAGE9_EVIDENCE=REAL_GODOT_AND_UNITY_ARTIFACTS
STAGE9_RELEASE_APPROVED=NO
STAGE10_STATUS=NOT_STARTED