# Etapa 7 — falha remota de timeout Windows e correção da medição

**Data:** 03/09/2026 (America/Sao_Paulo)
**PR:** `#166` — `fix/legacy-27-functional-regressions` → `main`
**Status:** `BLOCKED` — correção local comprovada; rerun remoto ainda não autorizado até o push desta revisão
**Pacote:** `docs/evidence/artifacts/etapa7-windows-timeout-2026-09-03/`

## 1. Objetivo e escopo

Investigar a falha observada no job Windows do CI após a correção
cross-platform do gate legado, preservar a falha como snapshot histórico,
corrigir somente a medição de tempo do request assíncrono e reexecutar os gates
no mesmo commit em uma árvore limpa. Nenhum merge, tag ou release é autorizado
por este relatório.

Foram consultados antes da alteração: a governança de integridade e
antialucinação, a política de qualidade e evidências, a política de não
regressão, a ADR do runner Windows, o plano vivo da reconciliação legada, os
snapshots protegidos de `quality/legacy_tests/` e os validadores de baseline e
evidência.

## 2. Falha remota preservada

O rerun remoto `33767197026` foi executado sobre o SHA anterior publicado
`59e82cf`. O job Linux `100687993442` passou. O job Windows `100687993643`
falhou no shard `44/189`, sem crash dump nativo:

```text
tests/test_legacy_phase4_contracts.py::test_phase4_real_segment_timeout_cancels_and_discards_late_result
assert float(payloads[0]["elapsed_ms"]) >= settings.segment_timeout_ms
observed: elapsed_ms=47.0; segment_timeout_ms=50
```

Os outros dez testes do arquivo passaram. O log completo e o JUnit foram
baixados do artefato `validation-windows-python-3.11` e a referência do job
está no artefato `remote-ci-windows-timeout.json`; o snapshot não será
reescrito depois da correção.

## 3. Causa raiz e decisão de engenharia

`_MagneticPathWorker.run()` iniciava seu relógio quando o worker começava a
executar. Entretanto, `_start_async_path()` enfileira o worker no
`QThreadPool` e inicia o `QTimer` do timeout no nível da solicitação. Sob carga,
o worker podia aguardar alguns milissegundos na fila depois do início do
request; nesse intervalo o timeout já podia estar válido enquanto o campo
`elapsed_ms` ainda media somente o tempo de execução do worker. Isso explica a
observação `47.0 < 50` sem indicar falha do solver, do cancelamento ou do
runner.

A decisão foi preservar a asserção do contrato e mover o instante inicial para
a construção/enfileiramento do worker. Assim, `elapsed_ms` mede a vida completa
da solicitação, incluindo a latência de fila, e continua sendo comparável ao
deadline usado pelo timer. Os snapshots legados e suas assinaturas não foram
alterados.

Alteração no commit local `febc85471e5ced519f47626665f5d995e7cf60a9`:

```text
src/tools/magnetic_lasso.py
  _MagneticPathWorker.__init__: self._started_at = time.monotonic()
  _MagneticPathWorker.run: usa self._started_at
```

Rollback documentado: `git revert febc85471e5ced519f47626665f5d995e7cf60a9`.

## 4. Validação local no commit corrigido

Ambiente observado no worktree limpo: Windows `10.0.26200`, Python `3.11.9`,
PySide6/Qt e dependências instaladas por Poetry a partir do lock. O runner
versionado foi executado sem filtros:

```text
poetry run python tools/run_windows_coverage_shards.py --output <temp>/neoeng-windows-coverage-febc854-r1
Windows coverage shards: ACCEPTED; files=189/189; tests=1919;
failures=0; errors=0; skipped=2
```

O teste que falhou remotamente foi repetido `20/20` vezes após a correção, com
`FAILURES=0/20`. No runner integral, a cobertura foi `23888/25799` linhas
(`92,59%`) e `6664/7838` branches (`85,02%`), acima dos thresholds de `90%`
e `85%`. O resumo do runner tem `152988` bytes e SHA-256
`56700ec4a6268d2d509086a4e1f5a3b8fe94dd5c5c85c36eb13852e643bd8fff`; o
`coverage.xml` tem `1184138` bytes e SHA-256
`51e64e97278ffc54e90941eba560aa6b8386092c11d644684f21d2b640590aa6`.

Também passaram no mesmo worktree e SHA:

- `poetry check --lock --strict`, compileall, Flake8, Black, isort e mypy
  (`145` arquivos-fonte);
- `pip-audit` sem vulnerabilidades conhecidas nas dependências auditáveis;
  o pacote local não está publicado no PyPI;
- Bandit (`-lll`), política de cobertura e auditoria Stage 4B.5;
- gate formal: histórico preservado em `196/26/0/0`, retorno `1`, `15`
  correspondências exatas, `11` assinaturas divergentes, `12` ausências e
  `42` substitutos;
- baseline Git-blob (`3206` arquivos) e evidência Git-blob (`128` manifests);
- empacotamento Windows com PyInstaller `6.22.0`, `11` smoke checks e `314`
  arquivos no manifesto.

O ZIP portátil gerado possui `124181911` bytes e SHA-256
`89cfb73482ed6b44f616fdd642c21a748c49512a23d142e99e76f6c06ac56b4f`; o
manifesto do pacote possui `55754` bytes e SHA-256
`3d9d7284c54c679a9422da2c8c85be1c23ca455dbaeddf448d4c6dffb993e157`.

## 5. Symlink e limitações

A prova de symlink no VMware Windows 11 com Developer Mode permanece válida
somente como `PASS_SCOPED` para a reconstrução identificada de ZIP/patch,
conforme `ETAPA_7_SYMLINK_VMWARE_2026-09-02.md`. Ela não é promovida a prova
do SHA `febc854`, pois a candidata do VMware não foi reconstruída a partir
deste commit. No host do worktree, os testes equivalentes continuam limitados
por `WinError 1314`; isso não foi ocultado nem convertido em sucesso.

## 6. Decisão e próximo passo

O defeito remoto foi reproduzido no artefato do CI, teve causa técnica
identificada, foi corrigido preservando o contrato e passou na validação local
integral. O estado desta revisão é `PASS_LOCAL / BLOCKED_REMOTE_RERUN`.

O próximo passo permitido é registrar este pacote, fazer o push controlado do
commit e aguardar novamente os dois jobs remotos. Qualquer falha deve ser
analisada antes de nova alteração. Merge, tag, release e aprovação permanecem
bloqueados até Linux e Windows passarem no SHA publicado e a revisão humana
autorizar explicitamente o avanço.
