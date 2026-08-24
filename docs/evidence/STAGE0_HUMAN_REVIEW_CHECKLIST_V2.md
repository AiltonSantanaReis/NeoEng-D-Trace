# Revisão humana — Etapa 0

Status: aguardando aprovação humana  
Snapshot: `STAGE_0_SNAPSHOT:85eee11c9e91b9c4461aca1423d3ad7c99be10aa`  
Baseline final: `FINAL_TARGET v1`  
Artefatos: `artifacts/stage0-snapshot-20260824/`

## Regra de aprovação

A aprovação humana deve ser explícita e baseada nos artefatos deste snapshot. O revisor deve registrar `APROVADO` ou `REPROVADO`, além de apontar o arquivo e a resolução de cada achado. Uma aprovação não pode ser inferida por ausência de comentários.

## Matriz de revisão visual

Para cada resolução, revisar os oito estados:

- `no_project`;
- `project_open`;
- `panels`;
- `mask_viewer`;
- `xray`;
- `gizmo`;
- `validation`;
- `scenario_editor`.

Resoluções obrigatórias:

- 1280×720;
- 1366×768;
- 1920×1080.

Capturas: `artifacts/stage0-snapshot-20260824/visual-evidence/`

## Critérios obrigatórios

O revisor deve verificar, em cada captura aplicável:

- ausência de clipping de texto, ícones, botões, abas e painéis;
- ausência de sobreposição que impeça interação;
- hierarquia visual e leitura correta dos painéis;
- contraste, foco e estados visuais identificáveis;
- toolbar, rail, viewport, status e inspetor sem compressão impeditiva;
- Mask Viewer aberto e reconhecível;
- X-Ray e gizmo visualmente distinguíveis;
- painel de validação identificável;
- editor de cenários separado do editor principal;
- comportamento proporcional entre as três resoluções;
- ausência de evidência que dependa de uma etapa posterior.

## Resultado do revisor

```text
Revisor:
Data:
Snapshot analisado: STAGE_0_SNAPSHOT:85eee11c9e91b9c4461aca1423d3ad7c99be10aa

Decisão: APROVADO | REPROVADO

Achados:
- [ ] Nenhum
- [ ] Existem achados — listar estado, resolução, arquivo e descrição precisa

Observações:
Assinatura/identificação do revisor:
```

## Condição para o ciclo do commit

O ciclo completo só será executado após `APROVADO` explícito:

1. congelar o snapshot e o commit exato;
2. executar novamente a suíte completa;
3. validar manifesto, hashes e cadeia;
4. verificar que não há alteração rastreada inesperada;
5. registrar o resultado formal da revisão humana;
6. gerar ou validar os artefatos finais;
7. criar o commit formal da conclusão da etapa 0;
8. executar a validação pós-commit;
9. somente então preparar a etapa 1.

Qualquer achado reabre a etapa 0 e bloqueia o commit formal até ser corrigido e revisado novamente.
