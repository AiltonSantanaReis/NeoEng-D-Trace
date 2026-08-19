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

- testes focais da Etapa 2: **19 passed**;
- suíte completa: **1350 passed, 2 skipped**;
- cobertura integrada: **92,88% linhas** e **85,20% branches**;
- policy checker de cobertura: **PASS**;
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
- relatório: `92e95109532a473448f36ffa0c868a50cf5432cd1c8a97695e3aa7178abc1b51` (1355 bytes).

## Hashes das entradas de código/documentação

- `src/core/scene_authoring_model.py` — `fdd54e11a9e068c551deb90b136f90c14b12081eb8919ec58cca84a5b8152526` (7931 bytes);
- `src/persistence/scene_authoring_schema.py` — `fb14520064ed5ee34099fadeac37057e4c5023976b3694c57065a11b6a52896e` (7838 bytes);
- `tests/test_stage2_scene_authoring_model.py` — `6777c888c86b38ea33eb6a6dbbc6c5ad3942df296f3abd4255ba93ebbee12949` (10757 bytes);
- `docs/PLANO_CENARIOS_PROFISSIONAL_2026-08-19.md` — `efb2aefe64099e10f90369bdeb20d224155d68bf1db96e93f59ea8b46dd98a79` (4197 bytes).

## Correção após CI

A primeira execução da PR encontrou branch coverage global de 84,93%, abaixo
do gate imutável de 85%. Foram adicionados somente testes de ramos negativos e
operações de edição que estavam sem exercício; o gate não foi alterado, nenhum
código foi excluído e não houve bypass. A nova medição local atingiu 85,20%.

## Rollback e limites

O rollback desta etapa é a reversão do commit da PR, sem migração automática de
projetos existentes. Não há alegação de drag-and-drop visual, viewport Qt,
efeitos, sockets, runtime ou import/export de engines nesta evidência.
