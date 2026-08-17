# Etapa 8 — encerramento pós-merge

## Identificação

- escopo: recursos avançados dos adaptadores nativos;
- PR de implementação: #79;
- merge de implementação: `8b40be3c72705cdd99c2e28849f030b7b3182bf0`;
- CI pré-merge: `31995537696`, jobs Linux `95286399340` e Windows `95286399351`, ambos `success`;
- CI pós-merge: `31995768720`, jobs Linux `95287026235` e Windows `95287026149`, ambos `success`;
- release: não aprovada;
- etapas 9 e 10: não iniciadas.

## Implementação integrada

A Etapa 8 integrou o contrato v2 dos adaptadores, preservando o contrato v1,
com atlas real contendo bleed/extrusão, hashes e dimensões por página,
propriedades avançadas por engine e normalização explícita de coordenadas.
Os importadores Godot e Unity consomem esses campos e rejeitam drift de hash,
sem substituir recursos manuais silenciosamente.

A evidência histórica pré-merge permanece em
`docs/evidence/ETAPA_8_RECURSOS_AVANCADOS_PRE_MERGE_2026-08-17.md`. Os artefatos
produzidos pelo harness estão em
`docs/evidence/artifacts/native-advanced-stage8-2026-08-17/`, com PNGs, manifestos,
logs sanitizados e índice verificável.

## Gates comprovados

- execução local posterior à correção: `1147 passed`, com 10 warnings de
  depreciação já conhecidos; nenhum teste foi removido ou marcado como ignorado;
- cobertura local: `90,68%` total; o limiar pytest de 90% foi aprovado e a
  política integrada de branches foi aprovada sem alteração de limiar;
- compilação, lint, formatação, imports, mypy, pip-audit, bandit, baseline e
  integridade de evidências passaram localmente;
- a suíte legada reconciliada terminou com código zero, `27/27` referências
  reconciliadas e `17` referências de substituição coletadas; falhas históricas
  registradas pelos testes legados continuam sendo tratadas como histórico, não
  foram convertidas artificialmente em sucesso;
- o CI pré-merge e o CI pós-merge passaram todos os passos Linux/Windows;
- o harness local executou Godot 4.7 e Unity 6000.5.7f1 reais, com marcadores
  `NATIVE_ADVANCED_STAGE8=SUCCESS`, propriedades das duas engines aprovadas,
  repetição determinística e rejeição de alteração de hash.

## Limitações e riscos residuais

O workflow atual valida Python, integridade, cobertura e reconciliação, mas não
inicializa os executáveis Godot/Unity. Portanto, a prova dinâmica das engines é
local e reproduzível pelos artefatos versionados; não é alegada como execução do
CI. Dry-run transacional, rollback de múltiplas saídas e fechamento de fixtures
permanecem no escopo das etapas 9 e 10. A release continua não aprovada.

## Decisão formal

`STAGE8_STATUS=INTEGRATED`

`STAGE8_MERGE=8b40be3c72705cdd99c2e28849f030b7b3182bf0`

`STAGE8_PRE_MERGE_CI=31995537696`

`STAGE8_POST_MERGE_CI=31995768720`

`STAGE8_EVIDENCE=REAL_GODOT_AND_UNITY_LOCAL_ARTIFACTS`

`STAGE8_RELEASE_APPROVED=NO`

`STAGE9_STATUS=NOT_STARTED`

`STAGE10_STATUS=NOT_STARTED`