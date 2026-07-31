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

## Achados registrados na Etapa 2

| ID | Estado | Evidência consolidada | Encaminhamento |
|---|---|---|---|
| R-001 | CONFIRMADO / ABERTO | Colisão personalizada e Bézier são perdidos; formato sem versão | Etapa 3 |
| R-002 | ABERTO | Persistência interna existe, mas o ciclo Abrir/Salvar não está completo na UI | Etapa 4 |
| R-003 | ABERTO | Caracterização ampliada; cobertura integral de UI permanece pendente | Etapa 11 |
| R-004 | CONFIRMADO / ABERTO | Fluxos selecionados funcionam, mas falhas de comando são ocultadas do chamador | Etapa 5 |
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
| ETAPA-2 | APROVADA PARA ENCERRAMENTO | PR `#9`; merge `d41093e706d3c8c555f64ef0c15c9ad40219a208`; workflow pós-merge `#36` (`30646258120`); jobs Linux `test` (`91208257924`) e Windows `test-windows` (`91208257772`) com `success`; artefatos `8799557767` e `8799571608`; pacote pós-merge `809c7b92da3a403e3a75f1f97a7f887c98c6174c798e32326b0cba93a8800e9c`; riscos R-001 a R-008 e R-011 a R-013 permanecem abertos |


## Severidades

- **P0:** risco de perda de dados, corrupção, segurança grave ou impossibilidade de confiar no produto. Bloqueia qualquer release e novas funcionalidades.
- **P1:** falha funcional importante, automação falsa ou regressão relevante. Bloqueia avanço da área afetada.
- **P2:** dívida técnica ou risco moderado com mitigação conhecida. Deve ser planejado e medido.
- **P3:** melhoria sem impacto material imediato. Não pode substituir correções P0/P1.

A matriz deve ser atualizada quando um risco for descoberto, reclassificado ou encerrado. Encerramento exige referência ao commit, testes e relatório de evidência.
