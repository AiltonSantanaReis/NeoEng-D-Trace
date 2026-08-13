# Matriz funcional atual — NeoEng-D-Trace

**Snapshot local:** 2026-08-13

**Última âncora integrada:** `872bf079d228d13d0203d22b844052b1f920e99b`

**Estado atual:** Etapa 12 integrada pela PR `#49` em `872bf079d228d13d0203d22b844052b1f920e99b` e concluída após auditoria do CI pós-merge `31686321925`. Linux e Windows reproduziram `928` testes, 92,81% de linhas, 85,02% de branches e 90,91% combinada; o pacote documental de fechamento aprovou `929` testes localmente e baseline de `326` arquivos, sem alterar a cobertura do código-fonte. `R-012` está encerrado no escopo aprovado; `R-011`, Etapas 13–14 e release permanecem pendentes. O histórico completo das PRs `#42`/`#43` e dos CIs aceitos/rejeitados permanece preservado abaixo e na evidência da Etapa 10.

**Baseline integrada da Etapa 12:** PR `#49`, merge `872bf079d228d13d0203d22b844052b1f920e99b`, CI `31686321925`, `928` testes e cobertura combinada `90,91%`.

**Baseline integrada da Etapa 11:** PR `#45`, merge `2a38b89e542390b3b4396a88d9a416f3695caadc`, CI `31491221322`, `877` testes e cobertura combinada `90,91%`.

**Histórico integrado da Etapa 10:** PR `#42`; CIs `31450335289`, `31451363518` e `31452032479` rejeitados; `31457937902` aceito; merge `9b22bdc54b13992658172d4748bfab44f3127c8e`; pós-merge `31463873481` rejeitado; correção aceita em `31464786333`, integrada pela PR `#43` em `f8caec3e7156d308f03046f81d2c89996f959466` e reproduzida em `31469610508`.

**Estado integrado anterior:** Etapa 8 integrada pela PR `#38`; CI pós-merge `31441024001` aprovado em Linux e Windows, sem anotações.

**Fechamento integrado anterior:** Etapa 7 mesclada em `99326f2d7ccf7046e401d90830feb8a5d33e9f9a`; CI pós-merge `31437000772` aprovado.

**Riscos:** `R-003`, `R-006`, `R-007`, `R-008` e `R-012` encerrados nos escopos aprovados; `R-011` permanece aberto; release não aprovada.

Esta é a matriz viva. `MATRIZ_FUNCIONALIDADES.md` permanece apenas como
snapshot histórico.

| Área | Estado local | Prova vigente | Risco residual |
|---|---|---|---|
| Identidade e árvore única | APROVADO | testes de identidade e `test_single_source_tree.py` | nenhum no escopo |
| Ambiente e lock | APROVADO | `poetry check --lock --strict`, PEP 621 e instalação resolvida | nenhum aviso de metadados no Poetry 2.4.1 |
| Persistência `.ndtproj` schema v1 | APROVADO | round-trip, migração, escrita atômica, falhas negativas | autosave não implementado |
| Abrir/Salvar na UI | APROVADO | testes Qt Windows e evidência da Etapa 4 | wheel validado; executável e instalador standalone ainda ausentes |
| Undo/Redo da Etapa 5 | INTEGRADO / APROVADO | pacotes 1–5C, suíte oficial, reconciliação legada e CI pós-merge `31425585259` | nenhum no escopo da Etapa 5 |
| Camadas e grupos | INTEGRADO / APROVADO | comandos reversíveis e `LayersPanel` integrado à `MainWindow` | cobertura total da UI permanece meta |
| CLI/headless | INTEGRADO / APROVADO | matriz de argumentos, códigos `0`/`1`/`2`, subprocessos, saídas reais e CI pós-merge `31437000772` | múltiplas saídas não formam transação conjunta; build instalado permanece para a Etapa 14 |
| Exportação de colisões | INTEGRADO / APROVADO | Etapa 6 e `R-005`: PR `#33`, merge `73a128ec44cde17867bbac6a7854ce86a43aba5a` e CI `31431739320`; Etapa 10: PRs `#42`/`#43`, engines reais e pós-merge `31469610508` aceito | limites de GLB 2.5D permanecem fora do escopo |
| Atlas | INTEGRADO / APROVADO | limites físico/JSON, rollback e tetos de dimensão, pixels, itens e páginas; PR `#49` e CI pós-merge `31686321925` | interrupção física entre arquivos não é garantida pelo filesystem |
| JSON de cena/sprite | INTEGRADO / APROVADO | schemas v1, pivôs, colisão, Unicode, consumo real em Godot/Unity, PRs `#42`/`#43` e pós-merge `31469610508` | nenhum no escopo aprovado |
| GLTF/GLB | INTEGRADO / APROVADO NO LIMITE U16 | importação real anterior nas engines; PR `#49` e CI pós-merge `31686321925` rejeitam índice acima de `65.535` sem arquivo parcial | UV, material e 2.5D pendentes |
| Lasso magnético | APROVADO NO ESCOPO ATUAL | engine, preview assíncrono, QImage e ndarray reais | desempenho e UX ainda possuem limitações registradas |
| Colisão estática e APIs | INTEGRADO / APROVADO | API pública `src.collision`; 39 casos da etapa; PR `#40`, merge `76dd6b7ca3e7da08fab653d66ae29a33a839baf3`; CI pós-merge `31445518755` aprovado em Linux e Windows | nenhum no escopo da Etapa 9 |
| Bézier e triangulação | INTEGRADO / APROVADO | PR `#38`, merge `fc869250e5067fb7b06b70c7d2dd3c0e1e1ee94e`, CI pós-merge `31441024001`; núcleo com 95.59% de linhas e 93.29% de branches | nenhum no escopo da Etapa 8 |
| Segurança e limites | INTEGRADO / APROVADO | Pillow 12.3.0; pip-audit e Bandit limpos; schema estrito; corpus malformado; rotação e privacidade de logs; benchmarks Windows; CI pós-merge `31686321925` auditado | nenhuma ferramenta prova ausência total; tetos não constituem SLA |
| Tipagem | APROVADO LOCALMENTE | mypy com `check_untyped_defs`: zero erros em 73 arquivos | ampliar anotações explícitas gradualmente |
| Cobertura | INTEGRADO / APROVADO | `929` testes locais no fechamento e `928` no CI pós-merge funcional; `11.174/12.040` linhas (92,81%), `3.309/3.892` branches (85,02%) e 90,91% combinada | margem de branch de apenas 0,02 p.p.; qualquer mudança exige medição integral |
| Build Windows/instalador | NÃO INICIADO | wheel Python validado | Etapa 14 obrigatória antes de release |

## Regra de leitura

`INTEGRADO / APROVADO` exige merge e CI pós-merge ligado ao SHA resultante.
`PARCIAL` e `NÃO INICIADO` não autorizam release.
