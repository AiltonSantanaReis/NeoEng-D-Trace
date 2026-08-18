# Evidência — Etapas 4A–4B.5: encerramento pós-merge

## Identificação

- Plano: `PLANO_CENARIOS_PARALLAX_E_PALETA_2026-08-18.md`;
- PR: `#99`;
- commit da PR validado: `36aaef402c2a8c550e209ad8f4f1ade460510bb2`;
- merge commit no `main`: `a129cd251345456c39254b39682d1ef083fd28d0`;
- CI pós-merge: run `32184900502`;
- data do merge: 18 de agosto de 2026;
- estado: integrado e aprovado no escopo das etapas 4A–4B.5.

## Escopo encerrado

O merge integra câmera/parallax, schema lateral versionado, preview somente leitura,
overlays, autoria lateral, exportação e validação real dos consumidores Godot/Unity,
além dos gates de determinismo, limites, evidências e qualidade.

## Gate pós-merge

- evento: `push` no `main`;
- conclusão do run: `success`;
- job Linux: `test`, concluído com `success`;
- job Windows: `test-windows`, concluído com `success`;
- baseline e integridade de evidências passaram nos dois jobs;
- cobertura, auditoria de qualidade, higiene da árvore e demais gates do workflow passaram nos jobs aplicáveis.

## Limites declarados

Este encerramento não amplia o escopo para partículas, shaders, pós-processamento,
triggers, streaming de texturas ou runtime completo de engine. A release `v0.2.0`
permanece um snapshot anterior; este merge não é uma nova release.

## Decisão

As etapas 4A–4B.5 estão encerradas no escopo aprovado e podem ser tratadas como
integradas no `main`. Qualquer expansão do módulo deve iniciar novo plano, contrato,
testes e evidências sem reclassificar este encerramento.
