# Evidência — Etapa 5: encerramento pós-merge e remediação auditada

## Identificação

- etapa: `5 — Undo/Redo completo`;
- risco principal: `R-004 — Undo/Redo incompleto`;
- PR funcional: `#27`;
- merge funcional em `main`: `6c4bcb3d945405a4615a4d6551247d1b01ce79f1`;
- HEAD documental final da PR funcional: `8ce44c238aaea79dafa64b8e1bba3ba5a8a7157e`;
- CI pós-merge histórico: `#84`, run `31136893143`, Linux e Windows aprovados;
- artefatos históricos: Linux `8978309717` e Windows `8978326062`;
- branch remota de fechamento: `docs/etapa-5-encerramento-pos-merge`;
- commit auditado: `236eefd41ee51c7085e21d52fc80074eede0a793`;
- HEAD final da PR de fechamento: `ab71e148c0b7441bd36f489472856d0b4adfaa1e`;
- PR de fechamento: `#28`, mesclada em `main` em 2026-08-10;
- merge do fechamento: `56533b65f81d21fd9c762aa10c0d3e6747d742ca`;
- CI final da PR: run `31422901244`, conclusão `success`;
- jobs da PR: Linux `test` (`93567667841`) e Windows `test-windows` (`93567667795`), ambos `success`;
- artefatos da PR: Linux `9076065640` (`sha256:998110fa36fcde9f7fb63a5637355318c5cd78a646869ad3610e342f2efd2d22`) e Windows `9076102334` (`sha256:ecbd075f639a05b710a8b8bfc1da84da3da6cf71a7443d3fb8f3398eed8b4b20`);
- CI pós-merge do fechamento: run `31423386971`, conclusão `success`;
- jobs pós-merge: Linux `test` (`93569241989`) e Windows `test-windows` (`93569242024`), ambos `success`;
- artefatos pós-merge: Linux `9076253153` (`sha256:b62f58240eb2f015d3f1906668e3402847668cab7ee6daa083f6a44fa1fd3443`) e Windows `9076283257` (`sha256:8ea7e557aa1eedf7a442962a49cee8a0cf778c02c678e72e75f05adc61438ef7`);
- pacote técnico final: PR `#29`, HEAD `956db473a88641bfdcfbd49ed122479f3fa2c51d`, merge `574be9bd0268e70c384903f93f16cf6e73aa57a2`;
- CI pós-merge técnico final: run `31425585259`, conclusão `success`, zero anotações;
- jobs técnicos finais: Linux `93576381868` e Windows `93576382048`;
- artefatos técnicos finais: Linux `9077091136` (`sha256:0ce0ad1f77b348f1d4061c7783a3467633a3089f19b18327627979f51befce51`) e Windows `9077113199` (`sha256:ab18e3e260f3f2b1e64b41e834363460f721112131411f350ac83e779fa9dae8`);
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
- as Actions emitiram aviso de depreciação do Node.js 20 para
  `actions/checkout@v4`, `actions/setup-python@v5` e
  `actions/upload-artifact@v4`; os jobs foram executados com Node.js 24 e
  concluíram com sucesso. A PR `#29` atualizou as três actions para
  `v7`/Node.js 24 e o CI técnico final teve zero anotações;
- a Etapa 6 não foi iniciada e nenhum estado deste relatório aprova release.

## Estado controlado

    LOCAL_REMEDIATION_COMPLETE=YES
    DOCUMENTATION_PACKAGE_PREPARED=YES
    COMMIT_CREATED=YES
    PUSH_EXECUTED=YES
    PR_CREATED=YES
    PR_NUMBER=28
    PR_DRAFT=NO
    PR_MERGED=YES
    PR_CI_EXECUTED=YES
    PR_CI_STATUS=SUCCESS
    POST_MERGE_CI_EXECUTED=YES
    POST_MERGE_CI_STATUS=SUCCESS
    R004_CLOSED=YES
    STAGE5_COMPLETED=YES
    STAGE6_STARTED=NO
    RELEASE_APPROVED=NO

## Decisão

**ETAPA 5 FORMALMENTE ENCERRADA.**

O commit auditado, o push, o CI Linux/Windows da PR, o merge da PR `#28` e o CI
pós-merge da `main` foram concluídos. `R-004` está encerrado no escopo aprovado
e a Etapa 5 está concluída. A Etapa 6 não foi iniciada e o projeto não está
aprovado para release.
