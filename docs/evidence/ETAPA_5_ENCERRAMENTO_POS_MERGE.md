# Evidência — Etapa 5: encerramento pós-merge e remediação auditada

## Identificação

- etapa: `5 — Undo/Redo completo`;
- risco principal: `R-004 — Undo/Redo incompleto`;
- PR funcional: `#27`;
- merge funcional em `main`: `6c4bcb3d945405a4615a4d6551247d1b01ce79f1`;
- HEAD documental final da PR: `8ce44c238aaea79dafa64b8e1bba3ba5a8a7157e`;
- CI pós-merge histórico: `#84`, run `31136893143`, Linux e Windows aprovados;
- artefatos históricos: Linux `8978309717` e Windows `8978326062`;
- branch remota de fechamento: `docs/etapa-5-encerramento-pos-merge`;
- commit auditado: `236eefd41ee51c7085e21d52fc80074eede0a793`;
- PR de fechamento: `#28`, draft, base `main`;
- CI da PR: run `31422290050`, conclusão `success`;
- jobs: Linux `test` (`93565684359`) e Windows `test-windows` (`93565684441`), ambos `success`;
- artefatos: Linux `9075840830` (`sha256:0ee90984bd1d907fdccfbb32df6a75c473e3a3d40eb6ce18e32809e1f175440b`) e Windows `9075871031` (`sha256:ca28dcf439bcd60ffd79406e8c1b7e01405ab9d7d79d761c7690835c7a6f032e`);
- auditoria corretiva: 2026-08-10, Windows/Python 3.11.9.

## Cadeia funcional comprovada

Todos os pacotes 1, 2A, 2B, 3A, 3B, 3B.1, 4A, 4B, 4C, 5A, 5B e 5C estão
integrados no merge funcional. A auditoria posterior não encontrou falha nova
no contrato Undo/Redo da Etapa 5, mas encontrou bloqueios de governança,
segurança e fluxos adjacentes que invalidavam a recomendação documental
anterior até sua remediação.

## Bloqueios encontrados e tratados

- Pillow atualizado de 12.0.0 para 12.3.0; lock regenerado e `pip-audit` limpo;
- suíte legada preservada executada integralmente: 196 testes, 26 falhas brutas;
- as 26 divergências foram classificadas em
  `quality/legacy_tests/reconciliation.json`, com assinatura exata e testes
  substitutos; gate final: 26/26 correspondentes, zero inesperadas e zero
  ausentes;
- CLI rejeita exportação de objeto sem `--object-id`;
- atlas preserva limites de frames transparentes e dimensões físicas rotacionadas;
- painel de colisões grava JSON atômico real e não declara sucesso no cancelamento;
- `LayersPanel` está integrado à `MainWindow`;
- `src.tools.lasso` reexporta a classe canônica em vez de manter implementação concorrente;
- PIL é convertido com segurança por `ViewProcessor`;
- mypy verifica corpos sem anotação e passa sem erros;
- CI mede branches, bloqueia queda abaixo de 62%, audita dependências, executa
  Bandit de alta severidade e roda a reconciliação legada no Windows;
- retenção dos artefatos do CI foi elevada de 7 para 30 dias.

## Gate local de remediação

- testes documentais: `19 passed`;
- suíte completa: `532 passed`;
- cobertura combinada: `62.18%`;
- baseline: `272` arquivos;
- mypy estrito: aprovado em 65 arquivos;
- segurança: `pip-audit` e Bandit alta severidade aprovados;
- flake8 integral bloqueante: zero achados;
- suíte legada: reconciliação aprovada;
- build e smoke instalado: aprovados;
- wheel: `neoeng_d_trace-0.2.0-py3-none-any.whl`; SHA-256
  `4A0F5CEB0094912EA3595052A38C60A200125C01888B7D228A5F0BE2C2547996`;
- smoke isolado fora do checkout: entry point em `site-packages` e `pip check` aprovados;
- fluxo headless pelo wheel: projeto válido gerou JSON (1092 bytes), GLB (996 bytes, magic `glTF`) e round-trip `.ndtproj` (974 bytes); entrada sem polígonos foi rejeitada;
- diff: sem whitespace inválido.

## Limitações e riscos residuais

- `R-003` permanece aberto até as metas finais de 90% de linhas e 85% de branches;
- `R-005` permanece parcial para unificação do schema de colisões na Etapa 6;
- `R-006` permanece parcial para a matriz completa de CLI da Etapa 7;
- `R-007`, `R-008`, `R-011` e `R-012` mantêm escopos futuros explícitos;
- build Windows standalone, instalador e release pertencem à Etapa 14;
- PR `#28` permanece draft; merge e CI pós-merge da `main` ainda não foram executados.

## Estado controlado

    LOCAL_REMEDIATION_COMPLETE=YES
    DOCUMENTATION_PACKAGE_PREPARED=YES
    COMMIT_CREATED=YES
    PUSH_EXECUTED=YES
    PR_CREATED=YES
    PR_NUMBER=28
    PR_DRAFT=YES
    PR_CI_EXECUTED=YES
    PR_CI_STATUS=SUCCESS
    POST_MERGE_CI_EXECUTED=NO
    R004_CLOSED=NO
    STAGE5_COMPLETED=NO
    STAGE6_STARTED=NO
    RELEASE_APPROVED=NO

## Decisão

**APROVADO REMOTAMENTE PARA REVISÃO E MERGE.**

O commit auditado, o push e o CI Linux/Windows da PR foram concluídos. `R-004`
e a Etapa 5 permanecem abertos até merge da PR `#28`, CI pós-merge da `main` e
evidência desse estado integrado. O projeto não está aprovado para release.
