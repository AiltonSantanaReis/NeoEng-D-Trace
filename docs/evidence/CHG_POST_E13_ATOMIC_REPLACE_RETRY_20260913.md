# Registro de mudança — retry controlado de replace atômico do atlas

**ID:** `CHG-POST-E13-ATOMIC-REPLACE-RETRY-20260913`
**Status:** `IN_PROGRESS`
**Data:** 2026-09-13
**Escopo:** robustez do commit atômico de atlas PNG/JSON no Windows

## Autoridade e causa

- Governança: `docs/GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md`.
- Finding preservado: `docs/evidence/EVD_POST_E13_OFFICIAL_SUITE_PRIVACY_FAILURE_20260913.md`.
- Código afetado: `src/exporters/atlas_exporter.py`.

Uma execução oficial r6 observou `PermissionError: WinError 5` em
`os.replace` ao trocar o PNG do atlas. A execução focada subsequente passou
12/12, portanto o finding foi classificado como bloqueio transitório não
determinístico do Windows, sem evidência para remover o contrato atômico.

## Alteração controlada

`_atomic_replace` mantém `os.replace` como única operação de commit e tenta
novamente somente `PermissionError` em três intervalos curtos (`50`, `100` e
`200 ms`). Outros erros continuam imediatos; depois da última tentativa a
exceção original é relançada. Nenhum destino é pré-apagado e o rollback
continua protegido.

O teste `test_atlas_retries_transient_windows_replace_denial` simula duas
recusas transitórias, exige quatro chamadas no total e verifica PNG, JSON e
limpeza dos temporários.

## Gates obrigatórios

1. teste focado de exportação atômica e regressões do exporter;
2. suíte oficial completa sem filtros, warnings ou falhas;
3. build limpa e smoke portátil real;
4. requalificação das evidências de privacidade e continuidade.

## Limites e segurança

Esta mudança não altera symlink, shutdown, Unity, CuPy ou o schema de cena.
Nenhum teste de symlink/shutdown será executado nativamente no host.

## Regra de reexecução

Reexecutar se o helper de replace, o exporter de atlas, a política de
rollback, o runtime Windows/Python ou os critérios de atomicidade mudarem.
