# Evidência — Etapa 5: persistência, exportação e adaptadores nativos

## Estado da etapa

Esta evidência registra a implementação e a validação local da Etapa 5 do
plano profissional. O commit/CI/PR desta etapa ainda não está aprovado neste
registro; a promoção depende dos gates finais e da revisão remota.

## Escopo implementado

- I/O determinístico para `SceneAuthoringDocumentV1` e `V2`, preservando a
  versão explícita no carregamento;
- upgrade V1→V2 somente por chamada explícita, sem migração silenciosa;
- leitura UTF-8 estrita, rejeição de BOM, números não finitos e chaves JSON
  duplicadas;
- referências de assets relativas, verificação SHA-256 e rejeição de escape;
- escrita atômica com rollback da substituição;
- exportação genérica, Godot e Unity com hash do documento, mapeamento de
  coordenadas e capacidades declaradas;
- importador Godot separado, integrado ao menu do plugin, com criação de
  layers, `Sprite2D`, transforms, profundidade, sockets e metadados;
- importador Unity separado, com menu/headless, criação de layers,
  `SpriteRenderer`, transforms, profundidade, sockets e metadata preservado;
- casos negativos nativos para divergência de hash nos dois engines.

O contrato lateral `neoeng-d-trace-scenario` schema v1 não foi alterado.

## Testes Python

Execução local focada:

```text
29 passed
```

Os testes cobrem round-trip V1/V2, determinismo, assets reais, deriva de hash,
JSON inválido, rollback, exportação nos três targets, deriva de capacidades e
contratos dos adaptadores, incluindo caminhos ausentes, escape de asset, UTF-8
inválido, números não finitos e destinos de exportação inválidos.

A suíte completa local coletou 1406 testes e terminou com `1404 passed, 2
skipped`; os dois skips são os cenários históricos de symlink já declarados no
contrato de integração. A política de cobertura passou com linhas acima de 90%
e branches acima de 85%.

Gates locais dos arquivos novos: Black, isort, flake8 e mypy aprovados.

## Godot real

- engine: `4.7.stable.official.5b4e0cb0f`;
- positivo: `returncode=0`, marcador
  `GODOT_NATIVE_PROFESSIONAL_SCENE_STAGE5=SUCCESS`, 1 layer e 1 `Sprite2D`;
- negativo: `returncode=1`, marcador de falha e rejeição explícita
  `professional scene asset hash does not match`;
- asset fixture: 78 bytes, SHA-256
  `010217fefacff21fec538b7e961cc4e00fe0e2b3a64b919211603d9d43647a5f`;
- export Godot: 2900 bytes, SHA-256
  `600075344b2bc1a7f062a171d8a7cc5e6523059bb5002104080f5d1b1c75a80e`;
- log positivo SHA-256:
  `fadc373f13284e53f63e2db95f2136bda9895ab134d9ba25c11f5da67bfdf4ba`;
- log negativo SHA-256:
  `a6c538ab5ad44429fb300f058fda5536069433685eb352f138e3357672405b54`.

## Unity real

- engine: `6000.5.7f1`;
- positivo: `returncode=0`, marcador
  `UNITY_NATIVE_PROFESSIONAL_SCENE_STAGE5=SUCCESS`, 1 layer e 1 objeto;
- negativo: `returncode=1`, marcador de falha e rejeição explícita por hash;
- asset fixture: 78 bytes, SHA-256
  `010217fefacff21fec538b7e961cc4e00fe0e2b3a64b919211603d9d43647a5f`;
- export Unity: 2900 bytes, SHA-256
  `880ed07ca79cf75c28f61c16556c241a4fd577658f623e43f2748590eac7901f`;
- log positivo SHA-256:
  `56bff0612c94116b5f0db4cfbe9a8c4e87e288af4609eaea3815c588e5e0e9cd`;
- log negativo SHA-256:
  `8bf359f4475a8d95a5db854ca1761944f138c080a76ab62f2f69a56823a11e26`.

O Unity registrou dois avisos ambientais nos casos positivo e negativo:
`Access token is unavailable; failed to update` e `Curl error 42: Callback
aborted`. Eles não foram ocultados; não impediram a compilação/importação
local nem alteraram o resultado do adaptador. O caso negativo também contém a
exceção esperada de hash e o marcador de falha.

## Artefatos

Os logs, exports, assets e relatórios estão em
`docs/evidence/artifacts/stage5-professional-scene-2026-08-19/`. Os logs foram
sanitizados para remover caminhos locais e identificadores de processo antes
do registro; seus hashes acima são dos bytes sanitizados versionados.

## Rollback

O rollback da etapa é a reversão do commit da Etapa 5 por PR, mantendo o merge
da Etapa 4 como referência funcional anterior. Os arquivos de usuário não são
migrados automaticamente.
