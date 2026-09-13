# Registro de mudança — tzdata no runtime portátil pós-E13

**ID:** `CHG-POST-E13-TZDATA-PACKAGING-20260913`
**Status:** `PASS`
**Tipo:** correção de dependência e empacotamento
**Data:** 2026-09-13
**Checkout de diagnóstico:** `72e60784d90030219a5300a4d6677726f5d0815e` antes do commit desta etapa
**Fonte qualificada:** `98ee5b4ea437d35b89f8767a03e26769636f5f99`

## Autoridade e motivo

- Governança: `docs/GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md`.
- Índice ativo: `docs/INDICE_DOCUMENTAL_ATIVO_CANONICO_2026-08-24.md`.
- Evidência relacionada: `docs/evidence/EVD_POST_E13_OFFICIAL_SUITE_SAFE_20260913.md`.
- Build portátil: `packaging/NeoEng-D-Trace.spec` e `scripts/build_windows.ps1`.

O PyInstaller registrava `Hidden import "tzdata" not found`. A verificação
controlada no Python 3.11 reproduziu a consequência: sem o pacote,
`ZoneInfo("UTC")` falhou com `ZoneInfoNotFoundError`. Embora os timestamps
principais usem `datetime.timezone.utc`, a distribuição Windows não deve
depender de dados de fuso presentes no sistema.

## Alteração exata

- `pyproject.toml`: adicionada dependência runtime pinada `tzdata = "2026.4"`.
- `poetry.lock`: regenerado pelo Poetry 2.4.1; o pacote entrou no grupo `main`
  com hashes oficiais do wheel e do source distribution.
- Nenhum código de produto, schema, persistência, engine, asset ou threshold foi
  alterado.

## Verificação já realizada

Antes da alteração, o probe registrou `tzdata_spec=False` e falha de
`ZoneInfo("UTC")`. Após instalar a versão pinada no ambiente de validação, o
mesmo probe retornou:

```text
tzdata=2026.4
utc=UTC
```

`poetry check --lock` retornou `All set!`. O teste de contrato
`tests/test_post_e13_tzdata_packaging.py` foi incluído na suíte oficial r8,
que terminou com `2633 passed, 2 skipped, 0 warnings`. A build portátil limpa
r5 observou o hook `tzdata` carregado, sem `Hidden import tzdata not found`, e
o smoke real terminou `SUCCESS` com 11 checks. A evidência hashada está em
`EVD_POST_E13_BUILD_CUPY_ATOMIC_20260913.md`.

O warning histórico da build anterior permanece preservado nos artefatos de
comparação; não foi apagado nem reclassificado.

## Não regressão e reexecução

A mudança é aditiva e limitada à disponibilidade de dados IANA no runtime. O
fallback de `datetime.timezone.utc` permanece intacto. O pacote não deve ser
removido para silenciar o warning; se uma versão futura alterar o lock, será
necessário repetir o teste `ZoneInfo`, a suíte oficial, a análise PyInstaller,
o smoke e a verificação do executável.
