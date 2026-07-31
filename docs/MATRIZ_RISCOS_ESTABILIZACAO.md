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

## Validações candidatas a encerramento

| ID | Estado | Evidência técnica | Condição restante |
|---|---|---|---|
| R-009 | PARCIAL | PR `#7`; commit `837aa6ac170e34868a87036ac2d33032eac99188`; execução `#29` (`30556955141`); jobs `test-windows` (`90919758232`) e `test` (`90919758259`) concluídos com `success` | Integrar o relatório e esta matriz e obter uma nova execução completa do CI sobre o commit de integração |
| R-010 | PARCIAL | `poetry.lock` formato `2.1`; SHA-256 canônico `43aaa1fd290d83f69c55ecf6bdc4abb7f55c170aa3172444f8828af01abeca86`; `poetry sync` aprovado em Windows e Linux; artefatos `8765255412` e `8765217747` | Integrar o relatório e esta matriz e obter uma nova execução completa do CI sobre o commit de integração |

## Severidades

- **P0:** risco de perda de dados, corrupção, segurança grave ou impossibilidade de confiar no produto. Bloqueia qualquer release e novas funcionalidades.
- **P1:** falha funcional importante, automação falsa ou regressão relevante. Bloqueia avanço da área afetada.
- **P2:** dívida técnica ou risco moderado com mitigação conhecida. Deve ser planejado e medido.
- **P3:** melhoria sem impacto material imediato. Não pode substituir correções P0/P1.

A matriz deve ser atualizada quando um risco for descoberto, reclassificado ou encerrado. Encerramento exige referência ao commit, testes e relatório de evidência.
