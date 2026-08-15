# Matriz de Riscos de Estabilização

| ID | Severidade | Risco confirmado | Impacto | Evidência exigida para encerramento |
|---|---|---|---|---|
| R-001 | P0 | Persistência incompleta do projeto | Perda silenciosa de dados | Testes de round-trip completos, migração e falha de gravação |
| R-002 | P0 | Ausência do ciclo Abrir/Salvar completo na UI | Trabalho não persistido | Testes UI e ponta a ponta no Windows |
| R-003 | P0 | Cobertura insuficiente de UI e ferramentas | Regressões não detectadas | Inventário de controles e testes positivos/negativos |
| R-004 | P1 | Undo/Redo incompleto | Edição irreversível ou estado incorreto | Invariante executar/undo/redo por operação |
| R-005 | P1 | Exportação de colisão inconsistente | Falso sucesso e arquivo ausente | Arquivo criado, reaberto e validado |
| R-006 | P1 | CLI pode retornar sucesso sem concluir operação | Automação não confiável | Matriz de argumentos, códigos de saída e outputs |
| R-007 | P1 | Bézier provisório e geometrias inválidas | Forma exportada incorretamente | Testes matemáticos, degenerados e propriedades |
| R-008 | P1 | APIs duplicadas ou parcialmente implementadas | Comportamento contraditório | Contrato único e testes de compatibilidade |
| R-009 | P1 | CI apenas Linux/offscreen | Falhas Windows não detectadas | Job `windows-latest` e testes PySide6 reais |
| R-010 | P1 | Dependências transitivas sem lockfile | Builds não reproduzíveis | Instalação limpa a partir de lockfile |
| R-011 | P2 | Módulos grandes e acoplados ao Qt | Retrabalho e dificuldade de teste | Refatoração posterior protegida por caracterização |
| R-012 | P2 | Limites operacionais e segurança incompletos | Travamento, uso excessivo ou exposição | Testes de limites, caminhos e entradas malformadas |
| R-013 | P1 | Metadados do atlas podem exceder os limites da textura | Recorte incorreto ou falha em engines consumidoras | PNG e JSON reabertos; retângulos contidos; testes unitários e de integração |
| R-014 | P1 | Artefatos Windows não possuem assinatura de código | Alerta de confiança e cadeia de distribuição não autenticada | Assinar GUI, CLI e MSI; validar assinatura e timestamp |
| R-015 | P1 | Texto jurídico, política de publicação e identidade visual final pendentes | Publicação sem base legal ou apresentação oficial | Aprovação jurídica, política de dados e ícone final versionado |
| R-016 | P2 | Governança da toolchain MSI migrada | Termos da ferramenta precisam ser revisados antes da release pública | Manter WiX 4.0.6 fixado e preservar provas de reprodutibilidade, instalação, upgrade e reparo |

## Estado operacional atual dos riscos

Snapshot vivo de 15 de agosto de 2026. A PR `#60` foi integrada no merge `5b9a435e3910c4192dcf1db36c721e5d6d9069f6`; o CI pós-merge `31907063633` aprovou os testes em Linux e Windows, com baseline íntegra e evidências auditadas. A primeira release oficial foi autorizada pelo proprietário. `R-014` e a formalização futura de `R-015` são riscos aceitos/deferidos e não bloqueiam essa primeira release por decisão do proprietário. `R-016` está validado tecnicamente após a migração para WiX 4.0.6, com governança da toolchain ainda pendente. Os artefatos atuais continuam sem assinatura; isso é declarado, não mascarado.

Âncoras integradas anteriores permanecem preservadas: Etapa 11 com `877` testes, `90,91%` combinada e `R-003` encerrado; Etapa 12 com merge final `fc81c2ea10e751c15a39627d462ddfff390eeb04`, CI `31688307089` e `R-012` encerrado.

| ID | Estado atual | Evidência/encaminhamento vigente |
|---|---|---|
| R-001 | ENCERRADO NO ESCOPO APROVADO | Persistência v1 integrada; colisões personalizadas e Béziers preservados no round-trip; evidências da Etapa 3 |
| R-002 | ENCERRADO NO ESCOPO APROVADO | Ciclo Abrir/Salvar integrado e validado no Windows; evidências da Etapa 4 |
| R-003 | ENCERRADO NO ESCOPO APROVADO | PR `#45` integrada em `2a38b89e542390b3b4396a88d9a416f3695caadc`; CI pós-merge `31491221322` aceito após auditoria de 877 testes, cobertura 92,77%/85,05%, legado 27/27 e artefatos recursivos sem violações |
| R-004 | ENCERRADO NO ESCOPO APROVADO | PR `#28` fechou o registro; PR técnica `#29`, HEAD `956db473a88641bfdcfbd49ed122479f3fa2c51d`, integrada em `574be9bd0268e70c384903f93f16cf6e73aa57a2`; CI pós-merge `31425585259` aprovou Linux e Windows |
| R-005 | ENCERRADO NO ESCOPO APROVADO | Schema `neoeng-d-trace-collisions` v1 unifica toolbar, painel, metadados genéricos e TXT atômico; PR `#33`, merge `73a128ec44cde17867bbac6a7854ce86a43aba5a`; CI pós-merge `31431739320` aprovou Linux e Windows |
| R-006 | ENCERRADO NO ESCOPO APROVADO | Matriz integral, subprocessos, códigos `0`/`1`/`2` e saídas reais; PR `#36`, merge `99326f2d7ccf7046e401d90830feb8a5d33e9f9a`; CI pós-merge `31437000772` aprovou Linux e Windows |
| R-007 | ENCERRADO NO ESCOPO APROVADO | PR `#38`, merge `fc869250e5067fb7b06b70c7d2dd3c0e1e1ee94e`; CI da PR `31440755594` e pós-merge `31441024001` aprovaram Linux e Windows sem anotações; núcleo geométrico com 95.59% de linhas e 93.29% de branches |
| R-008 | ENCERRADO NO ESCOPO APROVADO | API pública única, wrappers históricos sem implementação própria e regressões; PR `#40`, merge `76dd6b7ca3e7da08fab653d66ae29a33a839baf3`; CI final da PR `31445205968` e pós-merge `31445518755` aprovados em Linux e Windows |
| R-009 | ENCERRADO | CI Linux e Windows estabelecida |
| R-010 | ENCERRADO | Lockfile e instalação reproduzível estabelecidos |
| R-011 | ENCERRADO NO ESCOPO APROVADO | PR `#51`, merge `e7eb4a4c81fa2b46e8b9d5db40562e4ce7021108` e CI pós-merge `31698961646`; refatoração Qt e autosave auditados em Linux/Windows |
| R-012 | ENCERRADO NO ESCOPO APROVADO | PR `#49`, merge `872bf079d228d13d0203d22b844052b1f920e99b` e CI pós-merge `31686321925`; limites de configuração, imagem, projeto, geometria, detecção, broadphase, atlas, GLTF e logs; `928` testes em Linux/Windows; artefatos e legado auditados |
| R-013 | ENCERRADO NO ESCOPO AUDITADO | Limites físico/JSON, transparência de borda e rotação corrigidos; CI pós-merge técnico `31425585259` aprovado |
| R-014 | ACEITO / DEFERIDO PARA FUTURAS BUILDS/RELEASES | GUI, CLI e MSI retornam `NotSigned`; a primeira release oficial pode ser distribuída sem assinatura por decisão do proprietário, com hashes e transparência |
| R-015 | DECISÃO DE ROADMAP REGISTRADA / FORMALIZAÇÃO FUTURA | ícone gerado por IA e autorizado pelo proprietário; NOTICE, política e roteiro atualizados; licenciamento, atribuições e trâmites formais ficam para futuras versões |
| R-016 | VALIDADO TECNICAMENTE / GOVERNANÇA PENDENTE | WiX 4.0.6 fixado; dois builds independentes, build oficial, instalação, upgrade, reparo e desinstalação validados. Revisão de termos permanece no gate de release |

## Auditoria corretiva publicada — 10 de agosto de 2026

A recomendação de encerramento foi reavaliada após o CI pós-merge `#84`,
execução da suíte legada, auditoria de dependências e provas reais de CLI, atlas
e colisões. Os achados e
suas remediações estão em
`docs/evidence/AUDITORIA_RIGOROSA_2026-08-10.md`.

As PRs `#28`/`#29` e o CI pós-merge `31425585259` confirmam a integração da
âncora técnica auditada. `R-004` e `R-013` estão encerrados nos escopos comprovados; os
demais riscos mantêm os estados explícitos da tabela.

## Progresso da Etapa 5

| Pacote | PR | Integração | Evidência principal |
|---|---:|---|---|
| 1 | `#15`/`#16` | integrado | `ETAPA_5_PACOTE_1_COMMAND_MANAGER_CONTRACT.md` e encerramento pós-merge |
| 2A | `#17` | integrado em `5109ba0b03a4d075c73e5183c473b29d94bc7f5c` | relações de objetos e atomicidade |
| 2B | `#18` | integrado em `46f73d47081bcc6e997f494eb0c092c615a8f108` | caminhos de UI sem fallback direto |
| 3A | `#19` | integrado em `830075b354b2fc4f96a8c1516757c1f10cac9833` | gesto do gizmo transacional |
| 3B | `#20` | integrado em `4c9b8a4ad00834b956aedee0871454b9d40439f9` | edição de vértices transacional |
| 3B.1 | `#21` | integrado em `e2e95b332f2647e7e1debd0ff0ed4759676bb992` | remoção do caminho duplicado |
| 4A | `#22` | integrado em `8b59e4fa4dfbe14ad44e85e155073a0843634fd1` | exclusão de objetos transacional |
| 4B | `#23` | integrado em `f8a7e3dce61acd6e9312d70575cdf9eb89297a9a` | movimento e escala de colisão |
| 4C | `#24` | integrado em `0fc089bfc58ff9589f50bb394acd579bc2f71dd3` | camadas e grupos; integração de `LayersPanel` à `MainWindow` comprovada na remediação local de 2026-08-10 |
| 5A | `#25` | integrado em `9235ddc1ceaeddaec2074050eaebdeacaf588e53` | caminhos ativos de criação |
| 5B | `#26` | integrado em `ee38a2f1dc85093e34140ddd087312629b4ecb43` | lotes e geração de colisões reversíveis |
| 5C | `#27` | integrado em `6c4bcb3d945405a4615a4d6551247d1b01ce79f1` | HEAD final `8ce44c238aaea79dafa64b8e1bba3ba5a8a7157e`; 517 testes; CI `#83` e `#84`; validação visual 17/17 |

## Achados registrados na Etapa 2

> **SNAPSHOT HISTÓRICO:** a tabela abaixo registra o que foi observado na Etapa 2. Ela não representa o estado operacional atual e não deve substituir a seção anterior.

| ID | Estado | Evidência consolidada | Encaminhamento |
|---|---|---|---|
| R-001 | CONFIRMADO / ABERTO | Colisão personalizada e Bézier são perdidos; formato sem versão | Etapa 3 |
| R-002 | ABERTO | Persistência interna existe, mas o ciclo Abrir/Salvar não está completo na UI | Etapa 4 |
| R-003 | ABERTO | Caracterização ampliada; cobertura integral de UI permanece pendente | Etapa 11 |
| R-004 | CONFIRMADO / ABERTO | Pacote 1 integrou contrato observável, rollback transacional, pilhas consistentes e estado da UI; comandos por operação, relações completas e mutações diretas permanecem incompletos | Etapa 5 — Pacote 2+ |
| R-005 | ABERTO | Exportação de resultados do painel de colisão permanece parcialmente desconectada | Etapa 6 |
| R-006 | CONFIRMADO / ABERTO | Dois cenários negativos retornam código 0 sem arquivo | Etapa 7 |
| R-007 | CONFIRMADO / ABERTO | Bézier não persiste; métricas geométricas ainda são insuficientes | Etapa 8 |
| R-008 | CONFIRMADO / ABERTO | Duas implementações de LassoTool foram identificadas | Etapa 9 |
| R-011 | ABERTO | Acoplamento ao Qt permanece dívida para refatoração protegida | Etapa 13 |
| R-012 | CONFIRMADO / ABERTO | Schema desconhecido é aceito; tipos incorretos falham sem validação controlada | Etapa 12 |
| R-013 | CONFIRMADO / ABERTO | Retângulo JSON do atlas excede o PNG controlado em 1 pixel | Etapa 10 |

Relatório permanente:
`docs/evidence/ETAPA_2_INVENTARIO_FUNCIONAL_CARACTERIZACAO.md`.

Manifesto estruturado:
`docs/evidence/ETAPA_2_EVIDENCE_MANIFEST.json`.

Pacote bruto preparado para publicação no artefato Windows do CI:
`docs/evidence/raw/NeoEng-D-Trace_Etapa2_Raw_Evidence_Bundle.zip`.

Nenhum risco acima está encerrado por esta etapa.

## Encerramentos registrados

| ID | Estado | Evidência de encerramento |
|---|---|---|
| R-009 | ENCERRADO | Commit `f8f534edd74490f7264ebb153110ae65fce7066c`; workflow `Private validation` `#30` (`30596616841`); jobs Linux `test` (`91050247336`) e Windows `test-windows` (`91050247386`) concluídos com `success`; manifesto íntegro com 207 arquivos antes e depois |
| R-010 | ENCERRADO | Instalação por `poetry sync` no Linux e Windows; lockfile canônico `43aaa1fd290d83f69c55ecf6bdc4abb7f55c170aa3172444f8828af01abeca86`; artefatos Linux `8780354978` e Windows `8780366021` vinculados ao commit validado |
| ETAPA-2 | APROVADA PARA ENCERRAMENTO | PR `#9`; merge `d41093e706d3c8c555f64ef0c15c9ad40219a208`; workflow pós-merge `#36` (`30646258120`); jobs Linux `test` (`91208257924`) e Windows `test-windows` (`91208257772`) com `success`; artefatos `8799557767` e `8799571608`; pacote pós-merge `5356fcfc5bbbe0597f1103e4f063ae7aa5d9474911dba9fc7ae7aac090374069`; riscos R-001 a R-008 e R-011 a R-013 permanecem abertos |
| R-001 | APROVADO PARA ENCERRAMENTO | PR `#11`; HEAD `891fbc9550b5bba9bce041272da1db1f3bc3a7b3`; merge `4a45e9c396da6cd63f44f1cf9792526c305478ec`; workflow da PR `#40` (`30672383923`) e workflow da `main` `#41` (`30672598358`) com Linux e Windows em `success`; `212` testes por sistema; round-trip completo preservando colisões e Béziers; migração legada; escrita atômica; pacote bruto `e082e552c015dd7fd742e8a05a27e454c2db6b63feea052ba162c9e31e2dfe28`; pacote pós-merge `a057fa82620cd0f7a5d8644a615adc65f923a0db36d71caacbf2a6dd41e54396`; encerramento condicionado à integração desta evidência e ao CI final da `main` |
| ETAPA-3-PACOTE-1 | APROVADO PARA ENCERRAMENTO | Persistência v1 integrada por merge commit; correção de path traversal validada; `R-002` e `R-012` permanecem abertos; `R-007` permanece aberto para qualidade geométrica fora deste pacote |

| R-002 | APROVADO PARA ENCERRAMENTO | PR `#13`; HEAD `3469a4a9bfab20fa8cd687e2925a64928e7903d3`; merge `4d663f028c5d501a2da44e3a34077023087df58c`; workflow da PR `#44` (`30741145009`) e workflow da `main` `#45` (`30746901415`) com Linux e Windows em `success`; validação manual GUI v4 com `15/15` checks aprovados, `0` erros automáticos, ciclo Abrir/Salvar, cancelamento, descarte, avisos de imagem, rejeição atômica de JSON corrompido e salvamento no fechamento; encerramento condicionado à integração desta evidência e ao CI final da `main` |
| ETAPA-4 | APROVADA PARA ENCERRAMENTO | Ciclo Abrir/Salvar integrado e validado na UI Windows; `R-004` permanece aberto e é o próximo risco da ordem obrigatória; nenhuma implementação da Etapa 5 iniciada nesta PR documental |

| ETAPA-5-PACOTE-1 | INTEGRADO / APROVADO NO ESCOPO | PR `#15`; HEAD funcional `587a0cc93c3efe6c4e668cb86d624cf79a2479b4`; HEAD mesclado `fb5c72b001e4d8085ec902e383190e04a17dae8c`; merge `46cc0664cd8cfe04a6bd3b89bb6dc56e9681f62a`; workflow pós-merge `#55` (`30769951023`) com Linux `test` (`91555266247`) e Windows `test-windows` (`91555266229`) em `success`; `235` testes locais; cobertura global `53%`; `src/core/commands.py` `60%`; validação manual Windows `9/9`; pacote pós-merge `7e0fc5d64cf0edcdef6ab96cc43d23b7d0d3ce7bfd515ad31db50a4ac9dabe41`; `R-004` permanece aberto para os pacotes seguintes |


| R-004 | ENCERRADO NO ESCOPO APROVADO | PR funcional `#27`; fechamento `#28`; pacote técnico `#29`; âncora `574be9bd0268e70c384903f93f16cf6e73aa57a2`; CI pós-merge `31425585259` com Linux e Windows em `success` |
| R-013 | ENCERRADO NO ESCOPO AUDITADO | Correção de limites físico/JSON, transparência e rotação integrada; CI pós-merge técnico `31425585259` aprovado |
| ETAPA-5 | CONCLUÍDA | Pacotes 1 a 5C, auditoria corretiva e pacote técnico final integrados; CI pós-merge `31425585259` aprovado sem anotações; naquele encerramento, Etapa 6 não iniciada e release não aprovada |
| ETAPA-6 | CONCLUÍDA | Contrato de colisões v1 integrado pela PR `#33`; merge `73a128ec44cde17867bbac6a7854ce86a43aba5a` e CI pós-merge `31431739320` aprovados; `R-005` encerrado; Etapa 7 e release não iniciadas |
| ETAPA-7 | CONCLUÍDA | Contrato integral da CLI integrado pela PR `#36`; merge `99326f2d7ccf7046e401d90830feb8a5d33e9f9a` e CI pós-merge `31437000772` aprovados sem anotações; `R-006` encerrado; Etapa 8 e release não iniciadas |
| ETAPA-8 | CONCLUÍDA | Bézier e geometria integrados pela PR `#38`; merge `fc869250e5067fb7b06b70c7d2dd3c0e1e1ee94e` e CI pós-merge `31441024001` aprovados; `R-007` encerrado |
| ETAPA-9 | CONCLUÍDA | PR `#40`, merge `76dd6b7ca3e7da08fab653d66ae29a33a839baf3`; CI final `31445205968` e pós-merge `31445518755` aprovados; `R-008` encerrado |
| ETAPA-10 | CONCLUÍDA | PR `#42`; CIs `31450335289`, `31451363518` e `31452032479` rejeitados; pré-merge `31457937902` aceito; merge `9b22bdc54b13992658172d4748bfab44f3127c8e`; pós-merge `31463873481` rejeitado; CI corretivo `31464786333`, PR `#43`, merge `f8caec3e7156d308f03046f81d2c89996f959466` e pós-merge `31469610508` aceitos após auditoria |
| ETAPA-13 | CONCLUÍDA | PR funcional `#51`; fechamento `#52`, merge `b4d9390dbd1274c283a3e3985d6d79be47de45d6` e CI pós-merge final `31705652046` auditado; `R-011` encerrado; naquele encerramento, Etapa 14 não iniciada e release não aprovada |
| ETAPA-14 | CONCLUÍDA NO ESCOPO TÉCNICO | PR `#58`, merge `f15193a55d1a5de0c7031f5bab656107302eee1b`; fechamento documental PR `#60`, merge `5b9a435e3910c4192dcf1db36c721e5d6d9069f6`; CI pós-merge `31907063633` auditado; testes, cobertura, legado e evidências reproduzidos; primeira release oficial autorizada pelo proprietário; `R-014` e formalização futura de `R-015` deferidos; `R-016` validado tecnicamente |

## Severidades

- **P0:** risco de perda de dados, corrupção, segurança grave ou impossibilidade de confiar no produto. Bloqueia qualquer release e novas funcionalidades.
- **P1:** falha funcional importante, automação falsa ou regressão relevante. Bloqueia avanço da área afetada.
- **P2:** dívida técnica ou risco moderado com mitigação conhecida. Deve ser planejado e medido.
- **P3:** melhoria sem impacto material imediato. Não pode substituir correções P0/P1.

A matriz deve ser atualizada quando um risco for descoberto, reclassificado ou encerrado. Encerramento exige referência ao commit, testes e relatório de evidência.
