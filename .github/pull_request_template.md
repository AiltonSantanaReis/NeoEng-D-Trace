## Problema

Descreva o defeito ou requisito com evidência reproduzível.

## Escopo

- [ ] O diff contém somente alterações relacionadas.
- [ ] Não foram adicionadas funcionalidades fora da etapa.

## Causa raiz

Explique a causa confirmada. Não use hipótese como conclusão.

## Solução

Descreva a implementação e os contratos alterados.

## Testes e evidências

- Commit testado:
- Sistema operacional:
- Python:
- Comandos executados:
- Resultado unitário:
- Resultado de integração:
- Resultado de UI/E2E:
- Cobertura antes/depois:
- Relatório em `docs/evidence/`:

## Cenários negativos

Liste falhas, cancelamentos, entradas inválidas e limites testados.

## Riscos residuais

Declare tudo que permaneceu PARCIAL, BLOQUEADO ou NÃO TESTADO.

## Checklist obrigatório

- [ ] A falha foi reproduzida antes da correção.
- [ ] Foi adicionado teste de regressão.
- [ ] Todos os checks obrigatórios passaram.
- [ ] Nenhum teste foi removido ou enfraquecido para obter sucesso.
- [ ] Nenhum placeholder ou fallback silencioso foi introduzido.
- [ ] Documentação e manifesto foram atualizados.
- [ ] O rollback está descrito.

## Identidade e estado exatos

- Base branch:
- Base SHA:
- Head branch:
- Head SHA testado:
- PR draft: SIM | NÃO
- CI ligado ao HEAD exato:
- Linux:
- Windows:
- Baseline:

## Governança documental

- [ ] `README.md` foi revisado contra o estado real.
- [ ] Plano Mestre, Matriz de Riscos e índice de evidências foram revisados.
- [ ] Documentos históricos não foram reescritos como estado atual.
- [ ] Toda afirmação de CI identifica o SHA correspondente.
- [ ] Estados `PENDING`, `BLOCKED`, `PARTIAL` e `NOT TESTED` não foram convertidos em aprovação.
- [ ] Arquivos novos/untracked estão presentes integralmente no pacote de evidências; `git diff` isolado não foi tratado como escopo completo.
- [ ] Métricas do relatório permanente foram preenchidas pela execução atual, sem reutilizar contagens ou horários de gate anterior.
- [ ] Gestos contínuos foram testados para Undo, Redo, Escape, cancelamento, conflito externo e consolidação em uma única entrada de histórico.
- [ ] O polígono Bézier amostrado foi normalizado para orientação anti-horária e entradas degeneradas ou auto-intersectantes foram rejeitadas sem mutar o modelo ou o histórico.
- [ ] A validade geométrica foi comprovada exclusivamente pelo validador determinístico do ambiente bloqueado, sem decisão condicionada a Shapely opcional, incluindo contato de extremidade, sobreposição colinear e curva fechada com terminal duplicado.
- [ ] Coordenadas Bézier não representáveis e aritmética geométrica não finita foram rejeitadas por conversão central, sem `OverflowError` exposto na criação, edição, amostragem direta da cena ou exportação de sprite, sem mutação parcial ou entrada no histórico.
- [ ] A avaliação cúbica preservou o resultado e o arredondamento histórico no domínio ordinário, manteve finitude para controles extremos, e a amostragem pública, exportação e sincronização da Caneta aplicaram o mesmo invariante canônico.
- [ ] O reparo de polígonos foi estritamente opt-in: desativado, nenhuma heurística foi chamada; ativado, entradas não representáveis foram rejeitadas de forma controlada.
- [ ] O índice de handle exigiu inteiro estrito e não booleano; booleanos, floats equivalentes e valores não hashable foram rejeitados sem exceção bruta, mutação ou histórico.
- [ ] Ready for review, merge, exclusão de branch, fechamento de risco e transição de etapa foram tratados como gates independentes.
