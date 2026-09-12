# E08-E — Determinismo temporal e matriz de capacidades

Status: `TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING`.

Contrato: timestep/seed reproduzíveis, comparação temporal com tolerância
registrada e matriz explícita por backend/destino. A implementação está em
`src/runtime/temporal_qualification.py`, com auditoria em
`scripts/audit_e08_temporal_capabilities_phase8.py`.

## Resultado técnico

- Commit: `18257a316708039228f8117d27fb521d92e096c6`.
- Tolerância registrada antes da medição: fixed timestep `1/60`, erro temporal
  absoluto `1e-9`, erro visual por componente `1/255`, fração máxima divergente
  `0`, estado lógico exato.
- Quatro checkpoints de partículas foram executados duas vezes com a mesma
  seed e fixed-step; todos os hashes de estado coincidiram e o erro temporal
  máximo foi `0.0`.
- Duas saídas de frame do pós-processamento foram comparadas; erro máximo e
  fração divergente foram `0.0`.
- Matriz com 12 entradas: local-raster/CPU-preview é `native`; fixed-update
  dos adapters Godot/Unity é `native` como contrato; partículas, shaders e
  pós-processamento nos destinos são `degraded`, com motivo explícito de que o
  runtime nativo do destino ainda não está implementado.
- Auditoria: `PASS`, relatório em
  `artifacts/e08-renderer-20260908/runtime-temporal-audit-e8-18257/stage8-e-temporal-capabilities-report.json`.
- Suíte oficial: `2079 passed, 2 skipped, 1 warning`.

## Build e fluxo do usuário

A build r48 foi gerada do SHA acima, com binário
`4EF02616209C4F9AD3F1ADFC277C0C9F9EF8B4179075338D01C7584AEA8BEF52`, pacote
portátil `544b4042493b252bc39cddc51f941c5334ac932e7f465ebe34bd9599c44668a0`
e smoke aprovado em 11 checks. O fluxo real carregou a fixture V2 de FX no
executável e percorreu Preview, Autoria, controles inferiores e PageUp de
Parallax. As capturas r48 coincidem byte a byte com r47:
`docs/evidence/E08_E_R48_TEMPORAL_CAPABILITIES_MANIFESTO.json`.

## Limitações e próximo passo

Determinismo lógico não é declarado como equivalência visual GPU. Os destinos
Godot/Unity permanecem `degraded` para FX até execução real dos adapters.
Symlink e revisão humana continuam exclusivamente na auditoria final. Com E08
completo em checkpoint técnico, a próxima etapa autorizada é E09 — fluxo
imagem → vetor/colisão → objeto de cenário.
