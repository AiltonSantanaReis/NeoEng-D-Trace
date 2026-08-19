# Evidência — Etapa 2 da extensão profissional de cenários

## Estado do gate

- Escopo: modelo editável independente do cenário lateral v1.
- Estado: **APROVADO PARA REVISÃO DA PR**; encerramento depende de CI verde,
  merge normal e verificação pós-merge.
- Base integrada: `7b697f88e07d653767111b775391c50678fa6f8e`.
- Manifesto: `docs/evidence/artifacts/stage2-professional-scene-model-2026-08-19/manifest.json`.

## O que foi implementado

- contrato versionado separado: `neoeng-d-trace-scene-authoring` v1;
- referências de assets somente relativas, com SHA-256 obrigatório;
- transformações completas com posição XYZ, rotação XYZ, escala positiva,
  pivô normalizado e flip X/Y;
- seleção múltipla determinística com objeto primário;
- translação relativa preservando offsets entre objetos selecionados;
- grupos sem referências pendentes, remoção segura e bloqueios de objeto/camada;
- snapping de pixel/grade com espaçamento positivo e validação estrita.

O documento lateral `neoeng-d-trace-scenario` v1 e o projeto `.ndtproj` v1 não
foram alterados nem reinterpretados. UI, renderização, sockets, persistência do
novo documento e adaptadores de engines permanecem nas etapas posteriores.

## Resultados reais

- testes focais da Etapa 2: **13 passed**;
- suíte completa: **1344 passed, 2 skipped**;
- Flake8: **PASS**;
- Black: **PASS**, 241 arquivos sem alterações;
- isort: **PASS**;
- mypy: **PASS**, 108 módulos analisados;
- nenhum novo skip foi introduzido; os dois skips são condicionais já existentes.

O relatório completo e reproduzível está em
`validation-output.txt`; os caminhos locais foram substituídos por
`<repo-root>` para evitar dados de identidade do computador.

## Hashes do artefato

- fixture: `3d820a0a95edb6bbce51642b583a56ee43022ead704653acd2ce28ad61a2ea9c` (1394 bytes);
- relatório: `61630aa64772a1f8ce394b42bccef493fa96088a53ffc9ac3c77f3041f922012` (11527 bytes).

## Hashes das entradas de código/documentação

- `../../../../src/core/scene_authoring_model.py` — `fdd54e11a9e068c551deb90b136f90c14b12081eb8919ec58cca84a5b8152526` (7931 bytes)
- `../../../../src/persistence/scene_authoring_schema.py` — `fb14520064ed5ee34099fadeac37057e4c5023976b3694c57065a11b6a52896e` (7838 bytes)
- `../../../../tests/test_stage2_scene_authoring_model.py` — `98d2723e448a762efe700020863463e4e519f34776cb5d72fc02a4f928fc0cf0` (6554 bytes)
- `../../../../docs/PLANO_CENARIOS_PROFISSIONAL_2026-08-19.md` — `efb2aefe64099e10f90369bdeb20d224155d68bf1db96e93f59ea8b46dd98a79` (4197 bytes)

## Rollback e limites

O rollback desta etapa é a reversão do commit da PR, sem migração automática de
projetos existentes. Não há alegação de drag-and-drop visual, viewport Qt,
efeitos, sockets, runtime ou import/export de engines nesta evidência.
