# Evidência — Encerramento pós-merge da Etapa 10

## Identificação

- data: 11 de agosto de 2026;
- PR funcional: `#42`;
- merge funcional: `9b22bdc54b13992658172d4748bfab44f3127c8e`;
- PR corretiva: `#43`;
- HEAD corretivo: `2c7777586f8841f7b43ff182860a1d9f1c984ab1`;
- merge corretivo: `f8caec3e7156d308f03046f81d2c89996f959466`;
- release: não aprovada.

## Objetivo

Fechar a Etapa 10 somente depois de comprovar a integração dos exportadores,
dos perfis Godot e Unity, do rollback do atlas e da correção que tornou a
cobertura do gerenciador de colisões determinística entre Linux e Windows.

## Resultado pós-merge funcional rejeitado

O workflow `31463873481`, executado no merge funcional, terminou verde nos
dois sistemas. Ele foi rejeitado após a inspeção dos XMLs mostrar `8.581`
linhas e `2.145` branches cobertos no Linux, contra `8.582` e `2.146` no
Windows. A diferença dependia da ordem não contratual de um conjunto e foi
isolada pelo teste `test_manager_normalizes_reverse_broadphase_pair_order`.

## CI pré-merge corretivo aceito

O workflow `31464786333` validou o merge sintético
`a4360b2b5a12783fb923201f1bffef1b9557d5b3`, cujos pais eram a base
`9b22bdc54b13992658172d4748bfab44f3127c8e` e o HEAD fonte
`2c7777586f8841f7b43ff182860a1d9f1c984ab1`.

| Sistema | Job | Estado | Artefato | Digest SHA-256 |
|---|---:|---|---:|---|
| Linux | `93695329283` | `success` | `9091131139` | `b796130d54658f1e5d126ac81f7c72eb11beb2f29021df513f677ab095836eff` |
| Windows | `93695329206` | `success` | `9091140223` | `e3b7978dc86ff396be1bf4bcf04865331f93e7bc632a40e88a36e0720c43ca02` |

Os dois sistemas executaram `730` testes e produziram exatamente `8.582` de
`11.634` linhas e `2.146` de `3.706` branches cobertos, com `69,93%` de
cobertura combinada. A comparação detalhada dos `11.634` registros dos XMLs
não encontrou divergência de hits ou branches.

## Validação pós-merge corretiva

O workflow `31469610508` foi disparado por `push` no merge corretivo
`f8caec3e7156d308f03046f81d2c89996f959466`.

| Sistema | Job | Estado | Artefato | Digest SHA-256 |
|---|---:|---|---:|---|
| Linux | `93709824327` | `success` | `9092862008` | `61bcfda5048427e932d683cbb94dd361abb09b0b55ac539ff6d35927c4a5a04c` |
| Windows | `93709824406` | `success` | `9092878881` | `edb3cc8edb1d9d7f179b0f969b1f469c951ad0c0b24274cc9427569c69c033c2` |

A auditoria independente confirmou:

- `730 passed` em Linux e Windows;
- `8.582/11.634` linhas, `2.146/3.706` branches e `69,93%` combinada nos dois sistemas;
- XMLs equivalentes em todos os `11.634` registros de linha;
- baseline de `301` arquivos aprovado antes e depois dos testes;
- resumo legado schema v4 íntegro, com commit testado e HEAD fonte iguais ao merge;
- `196` testes históricos, `27/27` divergências previstas, zero inesperadas e zero ausentes;
- `45` evidências sem diferença de conteúdo: `41` idênticas byte a byte e `4` idênticas após normalização `LF`/`CRLF`;
- `51` arquivos externos e `1.410` payloads examinados, incluindo ZIPs aninhados;
- zero referências proibidas, zero caminhos pessoais e zero checksums divergentes.

## Evidência funcional consolidada

- perfis Godot e Unity versionados e unificados entre cena e objeto;
- pivôs, offsets e colisões validados em dados reabertos;
- rollback de PNG/JSON comprovado por falha injetada no segundo commit;
- Godot `4.7` e Unity `6000.5.7f1` executados em caminhos Unicode;
- PNG, JSON e GLB consumidos nas duas engines reais;
- suíte local canônica com `730` testes e cobertura igual à obtida remotamente.

## Limitações e riscos residuais

- `R-003` permanece aberto; as metas finais de cobertura não foram atingidas;
- `R-011` permanece aberto para refatoração Qt protegida;
- `R-012` permanece parcial até a auditoria de limites operacionais;
- autosave, build Windows, instalador e validação real de release permanecem pendentes;
- UV, materiais, 2.5D e limites de índice do GLB continuam fora do escopo aprovado;
- esta evidência não aprova release, executável ou instalador.

## Decisão formal

- `CORRECTIVE_PR_CI_EXECUTED=YES`
- `CORRECTIVE_PR_CI_STATUS=SUCCESS`
- `CORRECTIVE_PR_MERGED=YES`
- `POST_MERGE_CI_EXECUTED=YES`
- `POST_MERGE_CI_STATUS=SUCCESS`
- `STAGE10_COMPLETED=YES`
- `STAGE11_STARTED=NO`
- `RELEASE_APPROVED=NO`

**Etapa 10 concluída no escopo aprovado.** A cobertura dependente da ordem de
conjunto foi eliminada e o resultado foi reproduzido em Linux e Windows. A
release permanece não aprovada.
