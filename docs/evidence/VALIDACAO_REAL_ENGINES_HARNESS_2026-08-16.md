# Evidência — validação real do harness de exportadores nas engines

## Identificação

- Commit do código testado: `67d6df6`
- Branch: desenvolvimento local (nome omitido por higiene do repositório)
- Data: 2026-08-16
- Escopo: harness oficial existente para validar exports JSON/PNG/GLB em Godot e Unity

## Limite de escopo

Esta execução valida o fluxo de exportação já existente no projeto. Ela não
valida plugins nativos source-only, importação de manifesto
`neoeng-d-trace-engine-integration`, sincronização automática, overrides,
Sprite2D/CollisionPolygon2D gerados pelo novo plano ou recursos Unity gerados
pelo novo plano. Esses componentes ainda não foram implementados; R-017 e as
etapas 3 a 10 continuam abertos.

## Ambiente

- Sistema operacional: Windows
- Godot: `4.7.stable.official.5b4e0cb0f`
- Unity: `6000.5.7f1`
- Pacote Unity: `com.unity.cloud.gltfast` `6.19.0`
- Harness: `tools/validate_engine_exports.py`
- Validadores: `tools/godot_engine_validator.gd` e `tools/unity_engine_validator.cs`
- Caminhos absolutos dos executáveis foram usados localmente, mas não são
  reproduzidos neste relatório para não expor endereços da máquina.

## Comandos executados

O comando inicial do Godot usando apenas o alias do shell foi executado e
falhou na resolução interna do harness:

```text
poetry run python tools/validate_engine_exports.py --engine godot --executable godot.exe --work-dir <workspace-godot-resolution> --report <artifact-dir>/godot-report.json
```

O mesmo teste foi repetido com o executável local explicitamente resolvido:

```text
poetry run python tools/validate_engine_exports.py --engine godot --executable <godot-executable-resolved-locally> --work-dir <workspace-godot-real> --report <artifact-dir>/godot-report-real.json
```

Validação Unity:

```text
poetry run python tools/validate_engine_exports.py --engine unity --executable <unity-executable-resolved-locally> --work-dir <workspace-unity> --report <artifact-dir>/unity-report.json
```

As substituições entre `<...>` representam somente os diretórios/executáveis
locais omitidos no relatório; não são caminhos fictícios usados no teste.

## Resultados observados

### Godot

- Primeira execução: reprovada antes de iniciar a engine porque o harness não
  aceitou `godot.exe` como arquivo resolvido. Relatório preservado em
  `godot-report.json`.
- Segunda execução: aprovada.
- Importação real do projeto headless: código `0`.
- Script real de validação: código `0`.
- Marcador: `ENGINE_VALIDATION=SUCCESS`.
- Versão observada no stdout: `4.7-stable (official)`.
- Checks aprovados: metadados, textura, colisão, GLB externo e GLB importado
  pelo Godot.
- Verificações do script: JSON/schema v1, nome Unicode `sprite_ação`, região
  de atlas 40×20, offset/pivô, colisão poligonal e instanciação do GLB.

### Unity

- Criação do projeto batch: código `0`.
- Validação do projeto: código `0`.
- Marcador persistido em `unity-engine-validation-result.txt`:
  `ENGINE_VALIDATION=SUCCESS`.
- Versão persistida: `6000.5.7f1`.
- `packages-lock.json` resolveu GLTFast `6.19.0`.
- Checks aprovados: metadados, textura, colisão, GLB externo e GLB importado
  pelo Unity.
- Verificações do script: JSON/schema v1, nome Unicode `sprite_ação`, textura,
  retângulo convertido para o sistema de coordenadas do Unity, pivô 20×10 e
  carregamento do GLB como `GameObject`.

## Artefatos e hashes

O índice completo está em
`docs/evidence/artifacts/engine-validation-2026-08-16/engine-validation-index.json`.
Ele inclui relatórios, probes JSON, PNGs, GLBs, lock de pacotes e o resultado
persistido do Unity, sem incluir a pasta `Library` gerada pelo editor.

Principais hashes SHA-256:

- `godot-report-real.json`: `8e90823e...79701e6ba`
- `unity-report.json`: `9c71fa2...4b1481d`
- `godot-scene.glb` e `unity-scene.glb`: `de8ece4...5125fde`
- `godot-source.png` e `unity-source.png`: `06285ff...f9554cc`
- `unity-packages-lock.json`: `48ed050...c3d930f`
- `unity-engine-validation-result.txt`: `77919ab...a3f5d`

Os valores completos e os tamanhos estão no índice hashado; os prefixos acima
são apenas uma leitura resumida.

## Anomalias e riscos residuais

- O alias do Godot não é aceito pelo `_resolve_executable` quando passado como
  argumento explícito; o teste real passou após informar o executável resolvido.
  Isso é uma fragilidade do harness e deve ser corrigida em uma etapa futura,
  com teste de resolução por PATH.
- Os logs do Unity registraram timeout de uma requisição opcional de configuração
  de produção. O pacote necessário foi resolvido, o processo retornou código `0`
  e o marcador de validação foi persistido. O timeout não afetou os checks, mas
  permanece uma condição operacional a monitorar em ambientes sem rede.
- Não houve evidência de importação dos novos manifestos nem de plugin nativo,
  pois esses componentes ainda não existem no código.

## Decisão

**APROVADO NO ESCOPO DO HARNESS EXISTENTE.** Godot e Unity validaram os exports
atuais com evidências reais. **NÃO APROVADO COMO VALIDAÇÃO DOS PLUGINS NATIVOS**;
essa conclusão seria falsa enquanto as etapas 3 a 10 não forem implementadas.