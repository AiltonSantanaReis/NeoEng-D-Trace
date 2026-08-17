# Etapa 8 — recursos avançados dos adaptadores nativos

## Decisão e escopo

- base da implementação: `86195af3203ba7092bae70161ededd064f2b718b`;
- escopo entregue: contrato v2 explícito, atlas real com bleed/extrusão,
  propriedades avançadas e conversão adicional de coordenadas;
- compatibilidade: manifesto v1 continua válido e segue o caminho anterior;
- plugins: continuam source-only, sem DLL, executável auxiliar, biblioteca
  nativa ou download;
- Etapas 9 e 10: não promovidas.

## Implementação verificada

O núcleo monta o v2 diretamente dos resultados reais do exportador de atlas.
Cada página é validada por caminho relativo, SHA-256 e dimensão. O Godot valida
e consome a página, região, filtro, repetição, `z_index`, escala de unidade e
hash da página. O Unity configura o `TextureImporter` como Sprite com `NPOT=None`,
aplica filtro/wrap, preserva as dimensões do atlas, usa extrusão, pixels por
unidade, sorting e profundidade, e valida os recursos gerados no prefab.

A normalização usada nos adaptadores é explícita: origem de imagem e polígono no
canto superior esquerdo; eixo Y da engine para cima; Unity converte pontos para
unidades usando o `pixels_per_unit` do contrato. A rotação de atlas transforma
pivô e polígono antes da criação do colisor.

## Testes locais do núcleo

- `tests/test_integration_manifest.py`: 28 passed;
- `tests/test_stage_10_engine_profiles.py`: 20 passed;
- compilação Python dos módulos alterados: passou;
- o teste v1 existente permaneceu aprovado e o v2 teve casos positivos,
  determinismo, bleed, hash e propriedades inválidas cobertos.

## Execução real dos engines

O harness `scripts/audit_native_advanced_stage8.py` gerou o atlas com o
exportador do projeto e executou os binários instalados, sem mocks:

- Godot `4.7.stable`: pre-import 0; inicial `UPDATED`; repetição `UNCHANGED`;
  alteração do atlas rejeitada por hash;
- Unity `6000.5.7f1`: inicial `UPDATED` com Sprite, colisor, prefab e
  propriedades avançadas validados; repetição `UNCHANGED`; alteração do atlas
  rejeitada por hash;
- marcadores finais: `NATIVE_ADVANCED_STAGE8=SUCCESS`,
  `GODOT_REAL_ATLAS_PROPERTIES=PASS`, `UNITY_REAL_ATLAS_PROPERTIES=PASS`,
  `REPEAT_IMPORT_DETERMINISTIC=PASS` e `HASH_DRIFT_REJECTED=PASS`.

Os artefatos reproduzíveis estão em
`docs/evidence/artifacts/native-advanced-stage8-2026-08-17/`. O arquivo
`stage8-index.json` foi verificado contra os bytes atuais: 11 arquivos, nenhum
hash divergente e sem auto-referência stale. Logs foram sanitizados para não
conter caminhos locais, identificadores de licença ou endereços de rede.

## Falhas encontradas e corrigidas durante a prova

As tentativas de desenvolvimento revelaram quatro problemas objetivos, todos
corrigidos e revalidados: o harness não executava o pre-import Godot; uma
asserção numérica do harness não respeitava a formatação canônica; a API Unity
exigia `uint` para extrusão; e o importer Unity redimensionava atlas NPOT. O
último caso foi corrigido com `TextureImporterType.Sprite` e `NPOT=None`, e a
validação final confirmou dimensões exatas. Nenhuma dessas tentativas falhas foi
contada como evidência positiva.

## Limitações declaradas

A CI atual executa a suíte Python e integridade, mas não inicializa Godot/Unity;
portanto os logs dos engines desta etapa são provas locais reproduzíveis, não
uma alegação de execução dinâmica no CI. Dry-run transacional, rollback de
múltiplas saídas e fechamento de fixtures/CI pertencem às etapas 9 e 10.

## Decisão formal

`STAGE8_STATUS=VALIDATED_PRE_MERGE`

`STAGE8_EVIDENCE=REAL_GODOT_AND_UNITY_ARTIFACTS`

`STAGE8_RELEASE_APPROVED=NO`

`STAGE9_STATUS=NOT_STARTED`

`STAGE10_STATUS=NOT_STARTED`