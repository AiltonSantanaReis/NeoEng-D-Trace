# Matriz funcional atual — NeoEng-D-Trace

**Snapshot integrado:** 2026-08-10

**Base remota:** `56533b65f81d21fd9c762aa10c0d3e6747d742ca`

**Estado:** PR `#28` mesclada; CI pós-merge Linux/Windows `31423386971` aprovado.

Esta é a matriz viva. `MATRIZ_FUNCIONALIDADES.md` permanece apenas como
snapshot histórico.

| Área | Estado local | Prova vigente | Risco residual |
|---|---|---|---|
| Identidade e árvore única | APROVADO | testes de identidade e `test_single_source_tree.py` | nenhum no escopo |
| Ambiente e lock | APROVADO | `poetry check --lock --strict`, PEP 621 e instalação resolvida | nenhum aviso de metadados no Poetry 2.4.1 |
| Persistência `.ndtproj` schema v1 | APROVADO | round-trip, migração, escrita atômica, falhas negativas | autosave não implementado |
| Abrir/Salvar na UI | APROVADO | testes Qt Windows e evidência da Etapa 4 | wheel validado; executável e instalador standalone ainda ausentes |
| Undo/Redo da Etapa 5 | INTEGRADO / APROVADO | pacotes 1–5C, suíte oficial, reconciliação legada e CI pós-merge `31423386971` | nenhum no escopo da Etapa 5 |
| Camadas e grupos | INTEGRADO / APROVADO | comandos reversíveis e `LayersPanel` integrado à `MainWindow` | cobertura total da UI permanece meta |
| CLI/headless | PARCIAL | cenário real positivo; falta de `--object-id` agora retorna erro | matriz completa da Etapa 7 pendente |
| Exportação de colisões | PARCIAL | toolbar e painel gravam JSON real; cancelamento sem sucesso | schema unificado da Etapa 6 pendente |
| Atlas | INTEGRADO / APROVADO | transparência de borda, rotação, limites físico/JSON e CI pós-merge | nenhum no escopo auditado |
| JSON de cena/sprite | PARCIAL | perfis e atomicidade testados | colisão não integra o schema genérico, risco `R-005` |
| GLTF/GLB | APROVADO NO ESCOPO 2D | cena/objeto, bytes, metadados e subprocess headless | UV, material e contrato 2.5D permanecem |
| Lasso magnético | APROVADO NO ESCOPO ATUAL | engine, preview assíncrono, QImage e ndarray reais | desempenho e UX ainda possuem limitações registradas |
| APIs de lasso/SAT | INTEGRADO / APROVADO | alias único de `LassoTool`; SAT compatível coberto | revisão arquitetural ampla da Etapa 9 permanece |
| Segurança de dependências | INTEGRADO / APROVADO | Pillow 12.3.0; `pip-audit` sem vulnerabilidades conhecidas | nova auditoria obrigatória a cada lock/release |
| Tipagem | INTEGRADO / APROVADO | mypy com `check_untyped_defs`: zero erros em 65 arquivos | ampliar anotações explícitas gradualmente |
| Cobertura | PARCIAL | linhas+branches medidas; piso CI incremental de 62% | metas finais de 90% linhas/85% branches não atingidas |
| Build Windows/instalador | NÃO INICIADO | wheel Python validado | Etapa 14 obrigatória antes de release |

## Regra de leitura

`INTEGRADO / APROVADO` exige merge e CI pós-merge ligado ao SHA resultante.
`PARCIAL` e `NÃO INICIADO` não autorizam release.
