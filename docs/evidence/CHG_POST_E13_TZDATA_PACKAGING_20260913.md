# Registro de mudança — tzdata no runtime portátil pós-E13

**ID:** `CHG-POST-E13-TZDATA-PACKAGING-20260913`
**Status:** `IN_PROGRESS`
**Tipo:** correção de dependência e empacotamento
**Data:** 2026-09-13
**Checkout:** `72e60784d90030219a5300a4d6677726f5d0815e` antes do commit desta etapa
**Fonte de produto:** `7f5c0477b3f4594928751aec6b97a4b1e9c0178b`

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

`poetry check --lock` retornou `All set!`. A suíte focada e a suíte oficial,
além da nova build portátil e do smoke, ainda precisam ser executados para
promover este registro a `PASS`.

## Não regressão e reexecução

A mudança é aditiva e limitada à disponibilidade de dados IANA no runtime. O
fallback de `datetime.timezone.utc` permanece intacto. O pacote não deve ser
removido para silenciar o warning; se uma versão futura alterar o lock, será
necessário repetir o teste `ZoneInfo`, a suíte oficial, a análise PyInstaller,
o smoke e a verificação do executável.
