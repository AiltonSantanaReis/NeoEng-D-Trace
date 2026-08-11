# Matriz funcional atual — NeoEng-D-Trace

**Snapshot local:** 2026-08-10

**Última âncora integrada:** `76dd6b7ca3e7da08fab653d66ae29a33a839baf3`

**Estado atual:** Etapa 9 integrada pela PR `#40`; Etapa 10 aprovada pré-merge na PR `#42`, ainda sem integração; os CIs `31450335289`, `31451363518` e `31452032479` foram rejeitados, e o run `31457937902` foi aceito por auditoria recursiva dos artefatos; release não aprovada.

**Estado integrado anterior:** Etapa 8 integrada pela PR `#38`; CI pós-merge `31441024001` aprovado em Linux e Windows, sem anotações.

**Fechamento integrado anterior:** Etapa 7 mesclada em `99326f2d7ccf7046e401d90830feb8a5d33e9f9a`; CI pós-merge `31437000772` aprovado.

**Riscos:** `R-006`, `R-007` e `R-008` encerrados nos escopos aprovados; `R-003` permanece aberto; release não aprovada.

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
| Exportação de colisões | INTEGRADO / APROVADO; PERFIS PRÉ-MERGE NÃO INTEGRADOS | Etapa 6 e `R-005` encerrados; schema v1, PR `#33`, merge `73a128ec44cde17867bbac6a7854ce86a43aba5a` e CI pós-merge `31431739320`; perfis Godot/Unity consumidos nas engines reais e CI pré-merge `31457937902` aceito | merge e CI pós-merge da Etapa 10 pendentes |
| Atlas | INTEGRADO / APROVADO; ROLLBACK LOCAL NÃO INTEGRADO | limites físico/JSON integrados; falha injetada no segundo commit restaura PNG/JSON | proteção contra interrupção física entre arquivos não é garantida pelo filesystem |
| JSON de cena/sprite | APROVADO PRÉ-MERGE NAS ENGINES / NÃO INTEGRADO | schemas v1, pivôs, colisão, Unicode, consumo real em Godot/Unity e CI `31457937902` aceito | merge e CI pós-merge pendentes |
| GLTF/GLB | APROVADO PRÉ-MERGE NAS ENGINES / NÃO INTEGRADO | estrutura externa e importação real no Godot `4.7` e Unity `6000.5.7f1` com glTFast `6.19.0`; CI `31457937902` aceito | UV, material, 2.5D, merge e CI pós-merge pendentes |
| Lasso magnético | APROVADO NO ESCOPO ATUAL | engine, preview assíncrono, QImage e ndarray reais | desempenho e UX ainda possuem limitações registradas |
| Colisão estática e APIs | INTEGRADO / APROVADO | API pública `src.collision`; 39 casos da etapa; PR `#40`, merge `76dd6b7ca3e7da08fab653d66ae29a33a839baf3`; CI pós-merge `31445518755` aprovado em Linux e Windows | nenhum no escopo da Etapa 9 |
| Bézier e triangulação | INTEGRADO / APROVADO | PR `#38`, merge `fc869250e5067fb7b06b70c7d2dd3c0e1e1ee94e`, CI pós-merge `31441024001`; núcleo com 95.59% de linhas e 93.29% de branches | nenhum no escopo da Etapa 8 |
| Segurança de dependências | INTEGRADO / APROVADO | Pillow 12.3.0; `pip-audit` sem vulnerabilidades conhecidas | nova auditoria obrigatória a cada lock/release |
| Tipagem | APROVADO LOCALMENTE | mypy com `check_untyped_defs`: zero erros em 70 arquivos | ampliar anotações explícitas gradualmente |
| Cobertura | PARCIAL | 729 testes; 73,77% de linhas, 57,91% de branches e 69,93% combinada | metas globais finais de 90% linhas/85% branches não atingidas; Etapa 11 prioriza UI |
| Build Windows/instalador | NÃO INICIADO | wheel Python validado | Etapa 14 obrigatória antes de release |

## Regra de leitura

`INTEGRADO / APROVADO` exige merge e CI pós-merge ligado ao SHA resultante.
`PARCIAL` e `NÃO INICIADO` não autorizam release.
