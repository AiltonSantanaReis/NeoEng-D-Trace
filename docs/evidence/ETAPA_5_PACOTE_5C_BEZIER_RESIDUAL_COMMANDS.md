# Evidência — Etapa 5, Pacote 5C: Bézier e comandos residuais

## Identificação

- repositório: `AiltonSantanaReis/NeoEng-D-Trace`;
- branch: `feat/etapa-5-pacote-5c-bezier-residual-contracts`;
- base integrada: `ee38a2f1dc85093e34140ddd087312629b4ecb43`;
- HEAD autorizado antes do novo commit: `4802e24d6dd91a20dda4b56ae526ba33e5544322`;
- PR: `#27`, draft e não integrada;
- risco: `R-004`, aberto;
- corrector local: v3.8.

## Objetivo e escopo

O pacote consolida:

- criação atômica de objeto Bézier com seleção e uma notificação final;
- edição de handles com prévia contínua e uma única entrada de histórico;
- Undo, Redo, Escape, cancelamento e menu de contexto consumindo primeiro o gesto ativo;
- sincronização da Caneta quando a seleção ou o mesmo objeto muda externamente;
- abandono seguro da prévia quando o modelo diverge, sem restaurar snapshot antigo sobre estado externo aceito;
- aceitação de polígonos persistidos com densidade de amostragem diferente quando os controles Bézier continuam válidos;
- normalização do polígono Bézier amostrado para orientação anti-horária em criação e edição;
- rejeição de área zero, auto-interseção e outras amostras inválidas antes de mutação ou histórico;
- validação determinística no ambiente bloqueado, sem decisão condicionada a Shapely opcional, incluindo cruzamento próprio, contato de extremidade e sobreposição colinear entre arestas não adjacentes;
- rejeição controlada de coordenadas Bézier não representáveis e de aritmética de área não finita por conversão central no núcleo, sem `OverflowError` exposto na amostragem da cena e exportação de sprite ou mutação parcial;
- remoção do vértice terminal duplicado produzido por uma curva fechada válida antes da persistência;
- prévia inválida restrita aos nós visuais, preservando o último estado válido aceito pelo modelo;
- rejeição de snapshots obsoletos antes da classificação de no-op;
- cobertura nominal de `HandleMoveCommand`, `UpdateObjectGeometryCommand` e `ExpandContractCommand`;
- reconciliação documental e evidência autossuficiente dos 20 arquivos do escopo.

## Persistência Bézier comprovada

A afirmação anterior de que os pontos de controle não eram persistidos estava incorreta para o estado atual do repositório.

O schema v1 contém `SceneObjectRecord.beziers`; `build_project_document()` serializa os segmentos e `load_project_into_scene()` os restaura. O pacote mantém regressão de criação por `CreateBezierObjectCommand`, salvamento `.ndtproj`, reabertura e comparação exata dos segmentos e do polígono amostrado.

Não são persistidos o histórico de Undo/Redo, a seleção transitória ou um gesto de handle ainda não consolidado; essas exclusões são intencionais e não equivalem à perda dos segmentos Bézier do objeto salvo.

## Achados e correções

A revisão do primeiro commit identificou criação observável em estado intermediário, seleção antiga mantida pela Caneta e no-op aceito antes da validação de obsolescência. As correções instalaram o estado Bézier completo antes de notificar, sincronizaram a seleção e moveram as guardas de estado obsoleto antes do no-op.

A revisão pós-v3.1 identificou que o patch de evidência não incluía o teste untracked e que Undo/Redo global podia deixar nós visuais antigos no mesmo objeto selecionado. O pacote passou a arquivar patch completo, snapshots e manifesto dos 19 arquivos, além de recarregar os controles quando o modelo muda.

A revisão pós-v3.3 reproduziu dois defeitos adicionais: o gesto de handle ativo não consumia primeiro Undo, Redo ou Escape, e a soltura podia tentar consolidar uma prévia depois de divergência externa. Também comprovou divergência documental: embora o gate v3.3 tenha passado com 50 testes focais, 9 documentais e 465 totais, o relatório permanente ainda exibia 48/6/460 porque o template não usava os valores da execução corrente.

O v3.4 adicionou hooks transacionais para Undo, Redo e Escape, cancelamento prioritário no menu de contexto, guarda de conflito antes da consolidação, regressões de ciclo de vida e placeholders preenchidos pelo próprio gate. O gate Windows passou com 59 testes focais, 10 documentais e 475 totais.

A revisão pós-v3.4 comprovou dois invariantes ausentes: a criação atômica rejeitava uma curva válida desenhada no sentido oposto em vez de normalizar o polígono, e `HandleMoveCommand` aceitava amostras com área zero, orientação inválida ou auto-interseção. O v3.5 centraliza a preparação geométrica na cena, normaliza o sentido e rejeita a amostra inválida antes de alterar o modelo ou o histórico; durante arraste, uma forma inválida permanece apenas visual. O gate Windows v3.5 passou com 67 testes focais, 11 documentais, 484 totais e 65% de cobertura.

A revisão pós-v3.5 executou o caminho efetivo sem Shapely e reproduziu uma curva auto-intersectante aceita pelo fallback baseado em `ccw` estrito. Esse algoritmo não reconhecia todos os contatos de extremidade e casos colineares. O v3.6 substituiu esse fallback por validação determinística inclusiva, rejeitou coordenadas inválidas e duplicidades consecutivas e removeu apenas o terminal duplicado de uma curva fechada válida. O gate Windows v3.6 passou com 71 testes focais, 12 documentais, 489 totais e 65% de cobertura.

A revisão pós-v3.6 comprovou que a independência ainda não era absoluta: quando Shapely estivesse disponível, seu resultado continuava podendo alterar a decisão do validador. Também reproduziu `OverflowError` para coordenadas de controle inteiras fora da representação de `float` e área geométrica não finita. O v3.7 torna o validador determinístico a única autoridade, rejeita área aritmeticamente não finita e converte overflow de coordenadas em rejeição controlada nos caminhos da cena, dos comandos e da Caneta.

A execução Windows do corrector v3.7 foi bloqueada no dry-run antes de escrever qualquer arquivo: o teste `test_deterministic_validator_does_not_consult_optional_shapely` tentava substituir `scene_module.Polygon`, mas esse símbolo já havia sido removido intencionalmente do módulo. O v3.8 preserva o mesmo código funcional e corrige somente o harness com `monkeypatch.setattr(..., raising=False)`, permitindo instalar uma sentinela que falhará apenas se o caminho opcional voltar a ser consultado.

O gate Windows v3.8 passou com 77 testes focais, 13 documentais, 496 totais e 66% de cobertura. A revisão pós-gate reproduziu um caminho residual: `canonical_point()` ainda convertia inteiros diretamente para `float`, e `Scene.sample_beziers_to_polygon()` era usada pela exportação de sprite sem uma guarda intermediária; um controle como `10**400` expunha `OverflowError` bruto. O v3.9 centraliza essa conversão em `src/core/bezier_geometry.py`, transformando a falha em `ValueError` controlado para o núcleo, a cena, os comandos, a Caneta, a amostragem da cena e exportação de sprite.

O gate Windows v3.9 passou com 80 testes focais, 14 documentais, 500 totais e 66% de cobertura. A revisão pós-gate reproduziu duas falhas adicionais. Primeiro, a fórmula Bernstein produzia `inf` intermediário mesmo quando os quatro controles eram finitos e iguais a `sys.float_info.max`, fazendo a amostragem, a cena e a exportação exporem falha aritmética. Segundo, `Scene.add_object()` chamava `_attempt_repair()` antes de conferir `auto_repair`, de modo que um polígono com inteiro não representável podia expor `OverflowError` mesmo com reparo desativado. O v4.0 preserva a fórmula Bernstein e seu arredondamento no domínio ordinário, usa De Casteljau com interpolação estável quando os controles entram no domínio extremo, exige o invariante canônico na amostragem pública e na sincronização da Caneta e torna o reparo estritamente opt-in com rejeição controlada.

O gate Windows v4.0 passou com 89 testes focais, 15 documentais, 510 totais e 66% de cobertura. A revisão pós-gate reproduziu um contrato de tipo residual: `replace_handle()` e `HandleMoveCommand` usavam pertencimento em `{1, 2}` sem validar o tipo antes. Em Python, `True` e `1.0` colidem com o inteiro `1`, enquanto listas e dicionários são não hashable e podiam expor `TypeError`. O v4.1 exige um inteiro estrito e não booleano antes da verificação de faixa, converte todas essas entradas em `ValueError` ou `CommandStatus.REJECTED` e comprova ausência de mutação e de entrada no histórico.

## Histórico dos correctors

- v1: bloqueado no dry-run pelo contrato de tipo de `SceneObject.beziers`; nenhum arquivo escrito;
- v2: testes e tipagem aprovados, mas `git diff --check` bloqueou duas linhas em branco excedentes depois de oito arquivos escritos; nenhum commit ou push;
- v3: bloqueado no dry-run por trailing whitespace documental; nenhum arquivo escrito;
- v3.1: gate Windows aprovado com 48 testes focais, 6 documentais e 460 totais; 19 arquivos escritos; nenhum commit ou push;
- v3.2: bloqueado no dry-run pelo mypy antes de escrever arquivos;
- v3.3: gate Windows aprovado com 50 testes focais, 9 documentais, 465 totais e 65% de cobertura; evidência completa gerada; revisão pós-gate bloqueou commit pelos achados de gesto e relatório descritos acima;
- v3.4: gate Windows aprovado com 59 testes focais, 10 documentais, 475 totais e 65% de cobertura; a revisão pós-gate bloqueou commit pelos invariantes geométricos descritos acima;
- v3.5: gate Windows aprovado com 67 testes focais, 11 documentais, 484 totais e 65% de cobertura; a revisão pós-gate bloqueou commit pelo fallback geométrico incompleto descrito acima;
- v3.6: gate Windows aprovado com 71 testes focais, 12 documentais, 489 totais e 65% de cobertura; a revisão pós-gate bloqueou commit pela dependência decisória opcional e pelo domínio numérico não controlado descritos acima;
- v3.7: bloqueado no dry-run com 1 falha e 76 aprovações focais, antes de qualquer escrita, porque o teste de independência pressupunha incorretamente a existência de `scene_module.Polygon`;
- v3.8: gate Windows aprovado com 77 testes focais, 13 documentais, 496 totais e 66% de cobertura; a revisão pós-gate bloqueou commit pelo caminho residual de overflow na amostragem/exportação;
- v3.9: gate Windows aprovado com 80 testes focais, 14 documentais, 500 totais e 66% de cobertura; a revisão pós-gate bloqueou commit pelos achados de avaliação cúbica extrema e reparo não opt-in descritos acima;
- v4.0: gate Windows aprovado com 89 testes focais, 15 documentais, 510 totais e 66% de cobertura; revisão pós-gate bloqueou commit pelo contrato não estrito do índice de handle;
- v4.1: linha corretiva atual, com `handle_index` inteiro estrito no núcleo e em `HandleMoveCommand`, rejeição controlada de booleanos, floats e valores não hashable, sem mutação nem histórico; escopo final mantido em 20 arquivos; métricas abaixo preenchidas dinamicamente pela execução.

## Resultados da validação local v4.1

- testes focais do Pacote 5C: `95 passed`;
- testes de contrato documental: `16 passed`;
- suíte completa: `517 passed`;
- cobertura global exibida: `66%`;
- baseline: `263` arquivos;
- `poetry check --lock`: `APPROVED`;
- compileall: `APPROVED`;
- Flake8 fatal: `APPROVED`;
- Black: `APPROVED`;
- isort: `APPROVED`;
- mypy: `APPROVED`;
- `git diff --check`: `APPROVED`;
- sistema: `Windows-10-10.0.26200-SP0`;
- Python: `3.11.9`;
- data/hora local: `2026-08-06T05:48:12.694515-03:00`.

## Estado depois do gate local

```text
PACKAGE5C_CORRECTION_LOCAL=APPROVED_FOR_DIFF_REVIEW_ONLY
FILES_WRITTEN=YES
COMMIT_CREATED=NO
PUSH_EXECUTED=NO
PR27_READY_FOR_REVIEW=NO
MERGE_EXECUTED=NO
PACKAGE5C_INTEGRATED=NO
R004_CLOSED=NO
STAGE5_COMPLETED=NO
STAGE6_STARTED=NO
```

## Próximos gates

1. revisar integralmente o diff final e o pacote de evidências v4.1;
2. realizar validação visual focal de criação nos dois sentidos, arraste válido e inválido, Undo, Redo, Escape, troca de seleção e round-trip Bézier;
3. obter autorização específica para commit e push;
4. exigir novo CI Linux e Windows no novo HEAD;
5. revisar comentários, reviews e threads;
6. decidir separadamente sobre Ready for review;
7. merge, encerramento de `R-004`, conclusão da Etapa 5 e início da Etapa 6 permanecem transições independentes.

## Decisão

`APPROVED FOR DIFF REVIEW ONLY: o gate local Windows foi concluído, mas não houve commit, push, Ready for review, merge, fechamento de R-004, conclusão da Etapa 5 ou início da Etapa 6.`
