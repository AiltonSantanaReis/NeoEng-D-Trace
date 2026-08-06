# Política de Qualidade e Evidências

## Classificação de resultados

- **APROVADO:** requisito comprovado por procedimento reproduzível.
- **REPROVADO:** requisito executado e não atendido.
- **BLOQUEADO:** execução impedida por causa identificada.
- **NÃO TESTADO:** validação ainda não executada.
- **PARCIAL:** apenas parte do requisito foi comprovada.

## Regras de integridade

- Resultado antigo, cache, documentação ou captura sem commit não constituem prova.
- Teste instável é falha até que a causa seja identificada.
- `skip` e `xfail` exigem motivo, responsável e condição de remoção.
- Mock não substitui validação de arquivo, interface ou exportador real quando o comportamento real é o objeto do teste.
- Mensagem de sucesso só pode ocorrer depois da confirmação do efeito solicitado.
- Exceções não podem ser capturadas silenciosamente quando o resultado puder estar incorreto.

## Regra de parada

Interromper a etapa diante de perda de dados, regressão, build quebrado, divergência não explicada entre plataformas, comportamento não determinístico, queda de cobertura ou alteração fora do escopo.

## Relatório de evidência

Cada relatório em `docs/evidence/` deve conter:

1. objetivo e escopo;
2. commit e branch;
3. ambiente;
4. comandos executados;
5. entradas e respectivos hashes;
6. resultados brutos ou referência aos artefatos do CI;
7. cobertura;
8. falhas e causa raiz;
9. limitações;
10. decisão formal.

## Critério de merge

Um PR só pode ser considerado apto quando o diff estiver limitado ao escopo, todos os checks obrigatórios passarem, não houver regressão conhecida sem aprovação explícita e as evidências estiverem anexadas.

## Documentos vivos e snapshots históricos

- `README.md`, `CHANGELOG.md`, `docs/PLANO_MESTRE_ESTABILIZACAO.md`, `docs/MATRIZ_RISCOS_ESTABILIZACAO.md` e `docs/evidence/README.md` são documentos vivos e devem ser revisados em toda transição relevante.
- auditorias datadas, ADRs e relatórios em `docs/evidence/` são snapshots históricos; não devem ser reescritos retroativamente para aparentar que o estado antigo já continha correções posteriores;
- um documento histórico com instruções ou estados superados deve exibir aviso explícito e apontar para as fontes vivas;
- todo estado vivo deve indicar data, commit/base ou condição de verificação;
- CI de um SHA anterior não pode ser apresentado como validação de um novo HEAD ou de alterações ainda não commitadas;
- documentação não pode declarar `APROVADO`, `ENCERRADO`, `INTEGRADO` ou `PRONTO` antes do gate correspondente;
- divergência documental comprovada é defeito de processo e bloqueia Ready for review até correção ou classificação formal.

## Completude do pacote de evidências

- `git diff` não inclui arquivos untracked; portanto, não é evidência suficiente quando o escopo contém arquivos novos;
- todo pacote de validação deve incluir a lista de estado, hashes, tamanhos e snapshots integrais de todos os arquivos do escopo;
- quando houver arquivo untracked autorizado, o pacote deve incluir também um patch completo ou representação equivalente que permita revisar seu conteúdo;
- a contagem do escopo, o manifesto e o conteúdo arquivado devem concordar exatamente.
- métricas do relatório permanente devem ser preenchidas a partir da execução corrente; copiar contagens, horários ou decisões de um corrector anterior é divergência documental bloqueante.

## Ciclo de vida de gestos transacionais

- Undo, Redo, Escape, troca de ferramenta e cancelamento devem dar ao gesto ativo a primeira oportunidade de restaurar ou abandonar sua prévia antes de operar o histórico global;
- uma prévia não pode criar entrada no histórico; sua consolidação deve produzir no máximo uma entrada;
- se o modelo divergir durante o gesto, a ferramenta não pode restaurar um snapshot antigo sobre um estado externo já aceito; deve abandonar o gesto local, recarregar o modelo e registrar o conflito por teste;
- a sincronização deve comparar o estado canônico relevante, sem rejeitar um projeto válido apenas porque o polígono persistido usa densidade de amostragem diferente.

## Invariante do polígono Bézier amostrado

- criação e edição devem aceitar controles desenhados em qualquer sentido e normalizar o polígono persistido para orientação anti-horária;
- área zero, auto-interseção ou outra amostra inválida deve ser rejeitada antes de qualquer mutação observável ou entrada no histórico;
- uma prévia contínua inválida pode permanecer visível nos nós da ferramenta, mas não pode substituir o último estado válido aceito pelo modelo;
- criação, edição por comando e API direta da cena devem compartilhar a mesma preparação canônica para impedir divergência entre caminhos.
- a decisão de validade não pode depender de Shapely ou de outra dependência opcional não declarada no ambiente bloqueado; o validador determinístico deve ser a única autoridade de validade e detectar cruzamentos próprios, contatos de extremidade e sobreposição colinear entre arestas não adjacentes.
- coordenadas booleanas, não numéricas, não finitas ou não representáveis, vértices consecutivos duplicados, área não positiva e aritmética de área não finita devem ser rejeitados por conversão numérica central, sem exceção bruta ou mutação parcial, inclusive na amostragem direta da cena e na exportação de sprite.
- a avaliação cúbica deve preservar finitude para controles finitos por interpolação numericamente estável sem alterar o arredondamento histórico no domínio ordinário; a amostragem pública, exportação e sincronização visual devem passar pelo mesmo invariante canônico.
- reparo geométrico é estritamente opt-in: quando `auto_repair` estiver desativado, entradas inválidas devem ser rejeitadas antes de qualquer heurística; quando ativado, falha de conversão ou de reparo deve resultar em rejeição controlada.
- índices estruturais de edição, incluindo `handle_index`, devem exigir inteiro estrito e não booleano antes de qualquer teste de conjunto ou indexação; floats numericamente equivalentes e valores não hashable devem ser rejeitados de forma controlada, sem mutação parcial ou entrada no histórico.
- uma curva fechada válida pode repetir o primeiro ponto apenas como terminal da amostragem; esse terminal duplicado deve ser removido antes da validação e persistência.
