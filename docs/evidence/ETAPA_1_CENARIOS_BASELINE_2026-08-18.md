# Evidência — Etapa 1: baseline e caracterização

**Estado:** CONCLUÍDA no escopo desta evidência
**Escopo:** baseline, ADR, inventário e caracterização; nenhuma funcionalidade
de paleta ou parallax implementada.

## Identidade

- Baseline funcional de código: `b6549ffc1f0e92fb8eeb0f7846414356172191a8`
- HEAD documental verificado: `45b99f058601092a6121a7db4153ba27795325c0`
- PR documental integrada: `#93`
- Sistema de teste: Windows, Python 3.11.9, PySide6 em modo Qt offscreen
- ADR: `docs/ADR_CENARIOS_PARALLAX_PALETA_ETAPA1_2026-08-18.md`
- Teste: `tests/test_stage1_scenario_characterization.py`

## Contratos caracterizados

- schema de projeto `neoeng-d-trace-project`, versão `1`;
- transformação persistida com `position.z` preservado;
- ações atuais de projeto, edição, visualização e raio-X presentes;
- nenhuma `QAction` atual usa `Ctrl+K`;
- menus e ações existentes permanecem a fonte de comportamento a ser
  reutilizada pela etapa de paleta.

## Comandos e resultados

```text
.\.venv\Scripts\python.exe -m pytest -q tests/test_stage1_scenario_characterization.py
RESULTADO: 2 passed em 0.70s

.\.venv\Scripts\python.exe tools\baseline_integrity.py --verify
RESULTADO: Baseline verified: 1387 files

.\.venv\Scripts\python.exe tools\evidence_integrity.py
RESULTADO: execução concluída sem erro observável; os testes oficiais de
integridade de evidências também passaram na suíte completa.

.\.venv\Scripts\python.exe -m pytest -q
RESULTADO: 1204 passed, 2 skipped, 10 warnings em 20.91s

Verificação SHA-256 dos artefatos listados neste relatório
RESULTADO: Stage 1 artifact hashes verified
```

Formatação Black, ordenação de imports, Flake8 e `git diff --check` passaram.
Os dois skips são testes condicionais preexistentes e não foram criados,
removidos ou alterados nesta etapa.

## Riscos e limites

- Não há teste de paleta, câmera ou parallax nesta etapa; esses itens estão
  corretamente NÃO INICIADOS.
- A existência atual de `position.z` não autoriza reutilizá-lo como profundidade
  de parallax.
- A auditoria visual do documento de referência não faz parte desta execução.

## Decisão

A Etapa 1 está concluída integralmente no escopo aprovado: baseline, ADR,
inventário e caracterização foram entregues; não há implementação parcial de
produto. A etapa seguinte somente poderá começar após o commit, push, PR e
merge deste conjunto com os checks obrigatórios aprovados.
