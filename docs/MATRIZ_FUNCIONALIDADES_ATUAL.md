# Matriz funcional atual — NeoEng-D-Trace

**Snapshot local:** 2026-08-10

**Última âncora integrada:** `fc869250e5067fb7b06b70c7d2dd3c0e1e1ee94e`

**Candidato técnico:** Etapa 9 no commit `28273dfb7cb0e0aeab1f8f9f3a99c07df3b08a76`, ainda sem merge ou CI da PR.

**Estado integrado:** Etapa 8 integrada pela PR `#38`; CI pós-merge `31441024001` aprovado em Linux e Windows, sem anotações.

**Fechamento integrado anterior:** Etapa 7 mesclada em `99326f2d7ccf7046e401d90830feb8a5d33e9f9a`; CI pós-merge `31437000772` aprovado.

**Riscos:** `R-006` e `R-007` encerrados; `R-008` aprovado localmente para encerramento condicionado; release não aprovada.

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
| Exportação de colisões | INTEGRADO / APROVADO | Etapa 6 e `R-005` encerrados; schema v1, PR `#33`, merge `73a128ec44cde17867bbac6a7854ce86a43aba5a` e CI pós-merge `31431739320` | perfis específicos das engines permanecem na Etapa 10 |
| Atlas | INTEGRADO / APROVADO | transparência de borda, rotação, limites físico/JSON e CI pós-merge | nenhum no escopo auditado |
| JSON de cena/sprite | INTEGRADO / APROVADO NO ESCOPO GENÉRICO | colisão canônica integrada aos metadados de cena e objeto; contratos e atomicidade testados | perfis específicos Godot e Unity permanecem na Etapa 10 |
| GLTF/GLB | APROVADO NO ESCOPO 2D | cena/objeto, bytes, metadados e subprocess headless | UV, material e contrato 2.5D permanecem |
| Lasso magnético | APROVADO NO ESCOPO ATUAL | engine, preview assíncrono, QImage e ndarray reais | desempenho e UX ainda possuem limitações registradas |
| Colisão estática e APIs | APROVADO LOCALMENTE / NÃO INTEGRADO | API pública `src.collision`; 39 casos da etapa; wrappers históricos por identidade; AST sem implementação concorrente | merge e CI pós-merge necessários para encerrar `R-008` |
| Bézier e triangulação | INTEGRADO / APROVADO | PR `#38`, merge `fc869250e5067fb7b06b70c7d2dd3c0e1e1ee94e`, CI pós-merge `31441024001`; núcleo com 95.59% de linhas e 93.29% de branches | nenhum no escopo da Etapa 8 |
| Segurança de dependências | INTEGRADO / APROVADO | Pillow 12.3.0; `pip-audit` sem vulnerabilidades conhecidas | nova auditoria obrigatória a cada lock/release |
| Tipagem | APROVADO LOCALMENTE | mypy com `check_untyped_defs`: zero erros em 69 arquivos | ampliar anotações explícitas gradualmente |
| Cobertura | PARCIAL | 701 testes; 73.65% de linhas, 57.65% de branches e 69.79% combinada; colisão canônica 89%–95% | metas globais finais de 90% linhas/85% branches não atingidas |
| Build Windows/instalador | NÃO INICIADO | wheel Python validado | Etapa 14 obrigatória antes de release |

## Regra de leitura

`INTEGRADO / APROVADO` exige merge e CI pós-merge ligado ao SHA resultante.
`PARCIAL` e `NÃO INICIADO` não autorizam release.
