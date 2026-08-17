# Evidência — reprodução das falhas históricas da Etapa 6 Unity

## Identificação
- Commit/base do pacote: `94299183ba3386c590020a8a0c48073058a3ed25`
- Branch/base: `main`
- Data: 2026-08-16
- Tipo: reprodução real nova; não substitui logs históricos ausentes.

## Objetivo e escopo

Executar novamente no Unity Editor instalado os dois estados documentados na
Etapa 6: erro de compilação C# `CS1012` e binding inválido do marker com
`m_Script: {fileID: 0}`. As falhas foram produzidas em cópias temporárias do
pacote; o pacote versionado não foi alterado durante a execução.

## Ambiente e comando

- Windows local; Unity `6000.5.7f1`.
- Harness: `scripts/reproduce_unity_stage6_missing_logs.py`.
- Comando: `python scripts/reproduce_unity_stage6_missing_logs.py`.
- O harness sanitiza caminhos locais, endereços de rede, IDs de processo e
  identificadores de sessão antes de gravar os logs.

## Resultados

- `CS1012`: reproduzido com retorno Unity `1` e diagnóstico real “Too many
  characters in character literal”.
- Binding do marker: prefab gerado inicialmente pelo Unity, depois alterado
  somente no YAML para `m_Script: {fileID: 0}`; Unity retornou `1`, emitiu
  `UNITY_NATIVE_IMPORT_STAGE6=FAILURE` e rejeitou a ausência de estado de
  sincronização.
- Os dois casos foram confirmados pelo próprio harness com gates específicos.

## Artefatos e hashes

- `artifacts/unity-import-stage6-reproductions-2026-08-16/reproduction-report.json`
- `artifacts/unity-import-stage6-reproductions-2026-08-16/reproduction-index.json`
- `reproduction-csharp-compile.log` e `reproduction-marker-script-binding.log`.
- O índice registra bytes e SHA-256 dos três artefatos principais.

## Limitações e decisão

Os logs históricos `initial-failure-csharp-compile.log` e
`initial-failure-marker-script-binding.log` continuam indisponíveis e não foram
