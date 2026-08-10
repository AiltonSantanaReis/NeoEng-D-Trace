# Evidência — Encerramento pós-merge da Etapa 8

## Identificação

- data: 10 de agosto de 2026;
- commit técnico: `d11cd3dc0bd0063e325a53dd30fc439feda9dd24`;
- correção final de lint: `23d467f37b39e97251e589b544b84f29bcb18fee`;
- PR: `#38`;
- merge: `fc869250e5067fb7b06b70c7d2dd3c0e1e1ee94e`;
- branch validada: trabalho da Etapa 8, integrada à `main`;
- release: não aprovada.

## Objetivo

Fechar `R-007` somente depois de comprovar que a correção geométrica e seus
testes foram integrados, executados em Linux e Windows no HEAD da PR e repetidos
no merge commit da `main`.

## Histórico do gate remoto

A primeira execução da PR, workflow `31440385642`, falhou em ambos os sistemas
no Flake8 `E501`. A falha e sua causa estão preservadas no relatório pré-merge.
Não houve merge nesse estado.

Depois da correção `23d467f37b39e97251e589b544b84f29bcb18fee`, o workflow
da PR `31440755594` aprovou:

| Sistema | Job | Estado | Artefato | Digest SHA-256 |
|---|---:|---|---:|---|
| Linux | `93624768579` | `success` | `9082772395` | `22b636d22c6893c97a4f99fba4c65f6595999b5820746580a44461c104dfcdec` |
| Windows | `93624768624` | `success` | `9082802908` | `75cda9c0143251478abe50ee4eb9f00b1f60571800ae60f662b85de464a23259` |

Os dois jobs tiveram zero anotações. A PR foi então marcada pronta e mesclada
exigindo o SHA `23d467f37b39e97251e589b544b84f29bcb18fee`.

## Validação pós-merge

O workflow `31441024001` foi disparado por `push` no merge commit
`fc869250e5067fb7b06b70c7d2dd3c0e1e1ee94e` e aprovou:

| Sistema | Job | Estado | Artefato | Digest SHA-256 |
|---|---:|---|---:|---|
| Linux | `93625559051` | `success` | `9082863959` | `c64fc20e7a07f55b30473820103cf0a4dd3b662aa91ffb5f0c0606e6c3340eb9` |
| Windows | `93625559637` | `success` | `9082897744` | `49b6855dce17e088567965daf3f8bebc7b4a3c3741ea8753f006f9900e2ac4bb` |

Os dois jobs tiveram zero anotações. Compilação, baseline, Flake8, Black,
isort, mypy, auditoria de dependências, Bandit, suíte oficial e reconciliação
legada foram aprovados nos sistemas aplicáveis.

## Evidência funcional consolidada

- 125 testes focais aprovados localmente;
- 661 testes oficiais aprovados no pacote pré-merge e 662 no fechamento;
- 196 testes legados executados; 27/27 divergências exatas reconciliadas; zero
  inesperadas e zero ausentes;
- cobertura global: 72.95% de linhas, 56.48% de branches e 68.98% combinada;
- núcleo geométrico: 95.59% de linhas e 93.29% de branches;
- fallback de triangulação independente da orientação nos casos cobertos;
- degenerados, área divergente e índices inválidos falham de forma controlada;
- nenhuma alteração foi feita nos snapshots de testes históricos.

## Limitações e riscos residuais

- a cobertura global continua abaixo das metas finais de 90%/85%; `R-003`
  permanece aberto;
- a auditoria ampla de física, colisão e APIs duplicadas pertence à Etapa 9 e
  ainda não foi iniciada neste fechamento;
- limites operacionais, refatoração Qt, autosave, build e release permanecem
  pendentes em suas etapas próprias;
- nenhuma validação de release foi executada ou inferida deste CI.

## Decisão formal

- `PR_CI_EXECUTED=YES`
- `PR_CI_STATUS=SUCCESS`
- `PR_MERGED=YES`
- `POST_MERGE_CI_EXECUTED=YES`
- `POST_MERGE_CI_STATUS=SUCCESS`
- `R007_CLOSED=YES`
- `STAGE8_COMPLETED=YES`
- `STAGE9_STARTED=NO`
- `RELEASE_APPROVED=NO`

**Etapa 8 concluída e `R-007` encerrado no escopo aprovado.** Esta decisão não
aprova release e não antecipa a Etapa 9.
