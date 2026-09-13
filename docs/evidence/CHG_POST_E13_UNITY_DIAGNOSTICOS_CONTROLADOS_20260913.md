# Registro de mudança — Diagnósticos Unity controlados pós-E13

**ID:** `CHG-POST-E13-UNITY-DIAGNOSTICS-CONTROLLED-20260913`
**Status:** `PASS`
**Tipo:** ferramenta de auditoria somente leitura + testes de contrato
**Data:** 2026-09-13
**Checkout:** `72e60784d90030219a5300a4d6677726f5d0815e`
**Fonte de produto preservada:** `7f5c0477b3f4594928751aec6b97a4b1e9c0178b`

## Autoridade e motivo

- Governança: `docs/GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md`.
- Evidência: `docs/evidence/EVD_POST_E13_UNITY_DIAGNOSTICOS_CONTROLADOS_20260913.md`.
- Índice ativo: `docs/INDICE_DOCUMENTAL_ATIVO_CANONICO_2026-08-24.md`.

Os logs anteriores continham sinais de licensing e encerramento que não podiam
ser tratados como limpos. Faltava uma classificação reproduzível que não
exigisse repetir o Unity no host. O objetivo desta mudança é tornar a distinção
observável, preservar os sinais e impedir que um classificador seja interpretado
como prova de runtime nativo limpo.

## Escopo e impacto

Arquivos adicionados:

- `tools/qualify_post_e13_unity_diagnostics.py` — lê logs, conta marcadores e
  publica estados controlados; não importa subprocessos e não executa comandos
  de engine, `-quit`, shutdown ou terminação de processos.
- `tests/test_post_e13_unity_diagnostics.py` — três testes com fixtures
  determinísticas cobrindo positivo, negativo, sinais de licensing/shutdown e
  falha por marcador funcional ausente.
- `docs/evidence/EVD_POST_E13_UNITY_DIAGNOSTICOS_CONTROLADOS_20260913.md` —
  resultado e limites.

Nenhum arquivo de produto, adapter, schema, persistência, engine, build ou
dependência foi alterado. Nenhum log histórico foi apagado ou normalizado.

## Verificação

- Teste focado: `3 passed`.
- Execução Docker Desktop: rede desativada, checkout somente leitura e saída
  isolada gravável.
- Artefato corrente: `artifacts/post-e13-unity-diagnostics-controlled-20260913-r2/report.json`; o r1 permanece preservado.
- Resultado: `status=PASS`, `native_unity_reexecuted=false`,
  `native_shutdown_or_process_termination_requested=false`.
- O resultado funcional dos logs permanece `PASS` para o positivo e o negativo;
  licensing limpo e shutdown/soak limpo permanecem `PENDING_EVIDENCE`.

## Não regressão e reexecução

O fluxo do produto não foi alterado. A suíte oficial deve ser executada depois
da inclusão desta ferramenta/teste para registrar a regressão completa. A
classificação só precisa ser repetida se o parser, seus padrões, o contrato de
licensing/shutdown, os logs de origem ou o schema do relatório mudar. Não se
deve repetir Unity nativamente neste computador.
