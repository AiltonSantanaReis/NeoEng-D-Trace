# Matriz funcional atual — NeoEng-D-Trace

**Snapshot integrado:** 2026-08-10

**Âncora técnica integrada e auditada:** `73a128ec44cde17867bbac6a7854ce86a43aba5a`

**Estado:** Etapa 6 integrada pela PR `#33`; CI pós-merge Linux/Windows `31431739320` aprovado sem anotações.

**Risco encerrado:** `R-005` encerrado no escopo aprovado; Etapa 7 e release não iniciadas.

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
| CLI/headless | PARCIAL | cenário real positivo; falta de `--object-id` agora retorna erro | matriz completa da Etapa 7 pendente |
| Exportação de colisões | INTEGRADO / APROVADO | schema `neoeng-d-trace-collisions` v1, round-trip, rejeições e escrita atômica; CI pós-merge `31431739320` | perfis específicos das engines permanecem na Etapa 10 |
| Atlas | INTEGRADO / APROVADO | transparência de borda, rotação, limites físico/JSON e CI pós-merge | nenhum no escopo auditado |
| JSON de cena/sprite | INTEGRADO / APROVADO NO ESCOPO GENÉRICO | colisão canônica integrada aos metadados de cena e objeto; contratos e atomicidade testados | perfis específicos Godot e Unity permanecem na Etapa 10 |
| GLTF/GLB | APROVADO NO ESCOPO 2D | cena/objeto, bytes, metadados e subprocess headless | UV, material e contrato 2.5D permanecem |
| Lasso magnético | APROVADO NO ESCOPO ATUAL | engine, preview assíncrono, QImage e ndarray reais | desempenho e UX ainda possuem limitações registradas |
| APIs de lasso/SAT | INTEGRADO / APROVADO | alias único de `LassoTool`; SAT compatível coberto | revisão arquitetural ampla da Etapa 9 permanece |
| Segurança de dependências | INTEGRADO / APROVADO | Pillow 12.3.0; `pip-audit` sem vulnerabilidades conhecidas | nova auditoria obrigatória a cada lock/release |
| Tipagem | INTEGRADO / APROVADO | mypy com `check_untyped_defs`: zero erros em 66 arquivos | ampliar anotações explícitas gradualmente |
| Cobertura | PARCIAL | 543 testes; linhas+branches em 62.45%; piso CI incremental de 62% | metas finais de 90% linhas/85% branches não atingidas |
| Build Windows/instalador | NÃO INICIADO | wheel Python validado | Etapa 14 obrigatória antes de release |

## Regra de leitura

`INTEGRADO / APROVADO` exige merge e CI pós-merge ligado ao SHA resultante.
`PARCIAL` e `NÃO INICIADO` não autorizam release.
