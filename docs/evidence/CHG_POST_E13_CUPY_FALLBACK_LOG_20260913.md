# Registro de mudança — fallback opcional CuPy sem warning esperado

**ID:** `CHG-POST-E13-CUPY-FALLBACK-LOG-20260913`
**Status:** `PASS`
**Data:** 2026-09-13
**Escopo:** observabilidade do fallback CPU na build portátil

## Autoridade e motivo

- Governança: `docs/GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md`.
- Decisão de dependência: `docs/evidence/ADR_POST_E13_CUPY_AVALIACAO_20260913.md`.
- A build portátil exclui `cupy`/`cupyx` deliberadamente e permanece CPU-first.

O log `CuPy not found. Fallback to CPU processing.` era emitido como
`WARNING` mesmo quando a ausência do acelerador era o caminho esperado e
funcional da distribuição portátil. Isso poluía o diagnóstico de uma
execução saudável. A mudança separa os estados:

- ausência esperada de CuPy: `INFO`, com fallback CPU explícito;
- erro inesperado ao inicializar CuPy/driver: `WARNING`, preservado;
- falha durante processamento GPU: `ERROR` e fallback CPU, preservado.

## Alteração controlada

Foi extraída a inicialização opcional para
`src/core/view_processor.py::_initialize_optional_cupy`, sem alterar a rota
CPU, a seleção de `HAS_GPU`, a cadeia X-Ray ou o contrato de empacotamento.
Foram adicionados testes de severidade e de erro anormal em
`tests/test_post_e13_cupy_logging.py`.

## Verificação concluída

Os gates desta mudança foram concluídos:

1. os testes focados de logging passaram (`48 passed` no pacote diagnóstico);
2. a suíte oficial r8 passou sem filtros com `2633 passed, 2 skipped,
   0 warnings`;
3. a build limpa r5 passou com smoke real de 11 checks, janela visível em PT,
   salvamento de estado e fechamento com `exit_code=0`;
4. o relatório PyInstaller r5 não contém `cupy`, `cupyx` ou `tzdata` como
   hidden import ausente, e os manifestos/smoke estão hashados em
   `EVD_POST_E13_BUILD_CUPY_ATOMIC_20260913.md`.

Como a ausência de CuPy passou a `INFO`, a validação GUI não emitiu evento
`python.log` de warning. Isso é compatível com a mudança e não significa que
o fallback foi removido: a política CPU-first continua ativa e os testes de
severidade preservam `WARNING` para inicialização anormal e `ERROR` para falha
de processamento.

Nenhum CuPy será adicionado ao `pyproject.toml` por esta mudança, nenhum
driver será instalado/alterado e nenhum teste de symlink/shutdown será feito
no host.

## Regra de reexecução

Reexecutar os testes de logging e o smoke de build se o inicializador CuPy,
as mensagens/severidades, o fallback CPU, a especificação PyInstaller ou a
política de empacotamento mudarem. Alterações apenas documentais, de assets ou
de UI não exigem essa reexecução.
