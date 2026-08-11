# Evidência — Encerramento pós-merge da Etapa 9

## Identificação

- data: 10 de agosto de 2026;
- commit técnico: `28273dfb7cb0e0aeab1f8f9f3a99c07df3b08a76`;
- HEAD final da PR: `86cfb6b0cf43613417b12b3366f423216bd1e036`;
- PR: `#40`;
- merge: `76dd6b7ca3e7da08fab653d66ae29a33a839baf3`;
- branch validada: trabalho da Etapa 9, integrada à `main`;
- release: não aprovada.

## Objetivo

Fechar `R-008` somente depois de comprovar que a API pública única de colisão
estática, os adaptadores históricos e os testes de regressão foram integrados,
executados em Linux e Windows no HEAD final da PR e repetidos no merge commit
da `main`.

## Histórico do gate remoto

O workflow `31444322950` falhou em Linux e Windows antes dos testes porque o
manifesto de baseline não havia sido regenerado. O workflow `31444483410`
também falhou antes dos testes ao expor que `baseline_date` era comparada com a
data corrente do runner. Nenhum desses runs foi tratado como aprovação.

A causa raiz foi corrigida: a data permanece um campo ISO válido, mas não
participa da comparação de integridade temporal. O workflow corretivo
`31444774539` aprovou os dois sistemas no HEAD
`eed101ee03e74298e36c15cf271e378fd51be5dc`. Depois do registro documental, o
workflow final da PR `31445205968` aprovou o HEAD exato
`86cfb6b0cf43613417b12b3366f423216bd1e036`:

| Sistema | Job | Estado | Artefato | Digest SHA-256 |
|---|---:|---|---:|---|
| Linux | `93637806013` | `success` | `9084271305` | `48655366b6ce064a0cf53430f39076f789076ff42a87e00ec8620332b6a8d0bd` |
| Windows | `93637806062` | `success` | `9084293627` | `d65ea2f044ac085821f11240a988b1d4f7a22f54872e6a2542419d1a8b4bb49b` |

Os dois jobs finais da PR tiveram zero anotações. A PR foi marcada pronta e
mesclada somente após essa verificação.

## Validação pós-merge

O workflow `31445518755` foi disparado por `push` no merge commit
`76dd6b7ca3e7da08fab653d66ae29a33a839baf3` e aprovou:

| Sistema | Job | Estado | Artefato | Digest SHA-256 |
|---|---:|---|---:|---|
| Linux | `93638764726` | `success` | `9084385461` | `53ca01b259805188f07490c9648980c1c9efb7412f56c7d84b537bcb9705ff72` |
| Windows | `93638764754` | `success` | `9084401751` | `b22b0636d594dc4fce8a0e9e2d8200533a19b7dd1c8f4a033dd49a0867586e5f` |

Os dois jobs tiveram zero anotações. Baseline, compilação, Flake8, Black,
isort, mypy, auditoria de dependências, Bandit, suíte oficial e reconciliação
legada foram aprovados nos sistemas aplicáveis.

## Evidência funcional consolidada

- 39 testes focais da etapa e 702 testes oficiais aprovados localmente;
- 196 testes históricos executados; 27/27 divergências exatas reconciliadas;
  zero inesperadas e zero ausentes;
- cobertura global: 73.65% de linhas, 57.65% de branches e 69.79% combinada;
- módulos canônicos de colisão entre 89% e 95%; adaptadores históricos em 100%;
- IDs heterogêneos, polígonos côncavos, entradas inválidas e direção do MTV
  possuem regressões executáveis;
- `src.collision` é a API pública canônica e `src.physics` não mantém
  implementações concorrentes;
- nenhuma promessa de simulação dinâmica foi declarada como concluída.

## Limitações e riscos residuais

- a cobertura global permanece abaixo das metas finais; `R-003` continua aberto;
- validações reais dos perfis Godot e Unity pertencem à Etapa 10;
- limites operacionais, refatoração Qt, autosave, build e instalador permanecem
  pendentes nas Etapas 12–14;
- esta evidência não aprova release nem valida executável ou instalador.

## Decisão formal

- `PR_CI_EXECUTED=YES`
- `PR_CI_STATUS=SUCCESS`
- `PR_MERGED=YES`
- `POST_MERGE_CI_EXECUTED=YES`
- `POST_MERGE_CI_STATUS=SUCCESS`
- `R008_CLOSED=YES`
- `STAGE9_COMPLETED=YES`
- `STAGE10_STARTED=NO`
- `RELEASE_APPROVED=NO`

**Etapa 9 concluída e `R-008` encerrado no escopo aprovado.** Esta decisão não
aprova release e não antecipa validações das engines declaradas.
