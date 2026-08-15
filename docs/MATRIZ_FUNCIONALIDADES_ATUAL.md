# Matriz funcional atual — NeoEng-D-Trace

**Snapshot local:** 2026-08-13

**Âncora integrada de encerramento da Etapa 13:** `b4d9390dbd1274c283a3e3985d6d79be47de45d6`

**Âncora técnica da Etapa 14:** `828cf626b7ce382c360723b1be10c4ce718c4187`

**Âncora integrada pós-merge da Etapa 14:** `f15193a55d1a5de0c7031f5bab656107302eee1b` (PR `#58`, CI pós-merge `31905237922`)

**Estado atual:** Etapas 11 a 13 permanecem encerradas nos escopos aprovados. A Etapa 14 foi integrada pela PR `#58` e o CI pós-merge `31905237922` foi aceito após auditoria de logs e artefatos: `982` testes por sistema, cobertura `92,80%`/`85,02%`, legado `27/27` reconciliado e árvore limpa. `R-014` e `R-015` permanecem abertos; `R-016` está validado tecnicamente; release não aprovada.

**Baseline integrada da Etapa 12:** PR funcional `#49`, merge `872bf079d228d13d0203d22b844052b1f920e99b` e CI `31686321925` com `928` testes; fechamento `#50`, merge final `fc81c2ea10e751c15a39627d462ddfff390eeb04`, CI `31688307089`, `929` testes e cobertura combinada `90,91%`.

**Baseline integrada da Etapa 11:** PR `#45`, merge `2a38b89e542390b3b4396a88d9a416f3695caadc`, CI `31491221322`, `877` testes e cobertura combinada `90,91%`.

**Histórico integrado da Etapa 10:** PR `#42`; CIs `31450335289`, `31451363518` e `31452032479` rejeitados; `31457937902` aceito; merge `9b22bdc54b13992658172d4748bfab44f3127c8e`; pós-merge `31463873481` rejeitado; correção aceita em `31464786333`, integrada pela PR `#43` em `f8caec3e7156d308f03046f81d2c89996f959466` e reproduzida em `31469610508`.

**Estado integrado anterior:** Etapa 8 integrada pela PR `#38`; CI pós-merge `31441024001` aprovado em Linux e Windows, sem anotações.

**Fechamento integrado anterior:** Etapa 7 mesclada em `99326f2d7ccf7046e401d90830feb8a5d33e9f9a`; CI pós-merge `31437000772` aprovado.

**Riscos:** `R-003`, `R-006`, `R-007`, `R-008`, `R-011`, `R-012` e `R-016` validados/encerrados nos escopos aprovados; `R-014` e `R-015` permanecem abertos e bloqueiam release pública.

Esta é a matriz viva. `MATRIZ_FUNCIONALIDADES.md` permanece apenas como
snapshot histórico.

| Área | Estado local | Prova vigente | Risco residual |
|---|---|---|---|
| Identidade e árvore única | APROVADO | testes de identidade e `test_single_source_tree.py` | nenhum no escopo |
| Ambiente e lock | APROVADO | `poetry check --lock --strict`, PEP 621 e instalação resolvida | nenhum aviso de metadados no Poetry 2.4.1 |
| Persistência `.ndtproj` schema v1 e autosave | INTEGRADO / APROVADO | round-trip, migração, escrita atômica, falhas negativas, timer real, recuperação entre processos, PR `#51` e CI `31698961646` | autosave não substitui backup |
| Abrir/Salvar na UI | APROVADO | testes Qt Windows, executável standalone e MSI exercitados com projeto real | validação de release ainda limitada a um host Windows |
| Undo/Redo da Etapa 5 | INTEGRADO / APROVADO | pacotes 1–5C, suíte oficial, reconciliação legada e CI pós-merge `31425585259` | nenhum no escopo da Etapa 5 |
| Camadas e grupos | INTEGRADO / APROVADO | comandos reversíveis e `LayersPanel` integrado à `MainWindow` | cobertura total da UI permanece meta |
| CLI/headless | INTEGRADO / APROVADO | matriz de argumentos, códigos `0`/`1`/`2`, subprocessos, saídas reais, perfis de engine e binário instalado exercitado | múltiplas saídas não formam transação conjunta |
| Exportação de colisões | INTEGRADO / APROVADO | Etapa 6 e `R-005`: PR `#33`, merge `73a128ec44cde17867bbac6a7854ce86a43aba5a` e CI `31431739320`; Etapa 10: PRs `#42`/`#43`, engines reais e pós-merge `31469610508` aceito | limites de GLB 2.5D permanecem fora do escopo |
| Atlas | INTEGRADO / APROVADO | limites físico/JSON, rollback e tetos de dimensão, pixels, itens e páginas; PR `#49` e CI pós-merge `31686321925` | interrupção física entre arquivos não é garantida pelo filesystem |
| JSON de cena/sprite | INTEGRADO / APROVADO | schemas v1, pivôs, colisão, Unicode, consumo real em Godot/Unity, PRs `#42`/`#43` e pós-merge `31469610508` | nenhum no escopo aprovado |
| GLTF/GLB | INTEGRADO / APROVADO NO LIMITE U16 | importação real anterior nas engines; PR `#49` e CI pós-merge `31686321925` rejeitam índice acima de `65.535` sem arquivo parcial | UV, material e 2.5D pendentes |
| Lasso magnético | APROVADO NO ESCOPO ATUAL | engine, preview assíncrono, QImage e ndarray reais | desempenho e UX ainda possuem limitações registradas |
| Colisão estática e APIs | INTEGRADO / APROVADO | API pública `src.collision`; 39 casos da etapa; PR `#40`, merge `76dd6b7ca3e7da08fab653d66ae29a33a839baf3`; CI pós-merge `31445518755` aprovado em Linux e Windows | nenhum no escopo da Etapa 9 |
| Bézier e triangulação | INTEGRADO / APROVADO | PR `#38`, merge `fc869250e5067fb7b06b70c7d2dd3c0e1e1ee94e`, CI pós-merge `31441024001`; núcleo com 95.59% de linhas e 93.29% de branches | nenhum no escopo da Etapa 8 |
| Segurança e limites | INTEGRADO / APROVADO | Pillow 12.3.0; pip-audit e Bandit limpos; schema estrito; corpus malformado; rotação e privacidade de logs; benchmarks Windows; CI pós-merge `31686321925` auditado | nenhuma ferramenta prova ausência total; tetos não constituem SLA |
| Tipagem | INTEGRADO / APROVADO | mypy com `check_untyped_defs`: zero erros em `80` arquivos no CI pós-merge da Etapa 13 | ampliar anotações explícitas gradualmente |
| Cobertura | INTEGRADO / APROVADO | `955` testes por sistema; `11.581/12.478` linhas (92,81%), `3.370/3.964` branches (85,02%), 90,93% combinada e zero módulos abaixo de 30%; CI pós-merge final `31705652046` | margem de branch de 0,02 p.p. |
| Build Windows/instalador | INTEGRADO / APROVADO NO ESCOPO TÉCNICO | WiX 4.0.6 fixado; builds MSI reproduzíveis; instalação, smoke, upgrade, reparo, desinstalação, Godot/Unity, manifestos e CI pós-merge auditados | sem assinatura; pendências jurídica/visual |

## Regra de leitura

`INTEGRADO / APROVADO` exige merge e CI pós-merge ligado ao SHA resultante.
`PARCIAL` e `NÃO INICIADO` não autorizam release.
