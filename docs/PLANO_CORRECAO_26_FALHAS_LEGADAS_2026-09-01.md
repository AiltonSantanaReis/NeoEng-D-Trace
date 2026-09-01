# Plano integral de engenharia — correção e reconciliação das 26 falhas legadas

**Projeto:** NeoEng-D-Trace
**Etapa:** Reconciliação técnica pós-auditoria — 26 falhas legadas restantes
**Identificador operacional:** `P2D-COMP-01/LEGACY-26-RECON`
**Data de abertura:** 01/09/2026 (America/Sao_Paulo)
**Status:** `PLANO ACEITO — IMPLEMENTAÇÃO NÃO INICIADA`
**Aceite do proprietário:** recebido nesta conversa em 01/09/2026, incluindo as recomendações para os 26 casos
**Branch de trabalho:** `fix/legacy-27-functional-regressions`
**Base de reprodução:** `7f3799c1b29835f6db5ab6d35c0cab5deda5765b`
**Snapshot histórico de origem:** `cf749564ab5d961772d66dc363d0e990cebf8da3`
**Documento de diagnóstico:** `docs/AUDITORIA_27_FALHAS_TECNICAS_2026-09-01.md`

Este documento é um plano vivo de execução. Ele registra a decisão de aceitar as
recomendações técnicas, mas não declara implementação, teste, evidência,
reconciliação, aprovação, commit, push ou merge. A etapa somente poderá ser
encerrada quando todos os critérios deste documento forem comprovados em um
pacote integral e reproduzível.

## 1. Regra de governança antes de qualquer decisão

Antes de decidir sobre código, fixture, teste, harness, reconciliação,
evidência, commit ou merge, a equipe deverá consultar, na versão efetivamente
presente no branch, pelo menos:

1. `docs/POLITICA_NAO_REGRESSAO.md`;
2. `docs/POLITICA_QUALIDADE_E_EVIDENCIAS.md`;
3. `docs/evidence/README.md`;
4. `tools/run_legacy_tests.py`;
5. `quality/legacy_tests/manifest.json`;
6. `quality/legacy_tests/reconciliation.json`;
7. `docs/AUDITORIA_27_FALHAS_TECNICAS_2026-09-01.md`;
8. as decisões e evidências vigentes de `P2D-05/O-2` quando uma alteração
   puder afetar cache, incremental, frame, viewport, histórico ou desempenho.

Cada decisão deverá registrar no relatório:

- regra consultada e versão/commit observado;
- fato verificável que motivou a decisão;
- alternativas consideradas;
- impacto sobre funcionalidade, dados, compatibilidade, desempenho e segurança;
- teste ou evidência que comprovará a decisão;
- condição de rollback;
- responsável pela revisão, quando houver revisão formal.

### 1.1 Regras absolutas desta etapa

- `quality/legacy_tests/manifest.json` e os arquivos históricos referenciados
  são snapshots imutáveis. Não serão editados, regenerados ou removidos para
  reduzir falhas.
- `quality/legacy_tests/reconciliation.json` não será alterado para obter
  `PASS`. Qualquer mudança será uma decisão formal de harness, acompanhada de
  testes substitutos reais e revisão explícita.
- Nenhum `skip`, `xfail`, filtro, threshold, tolerância, timeout ou critério de
  aceite será alterado para transformar uma falha em aprovação.
- Nenhuma funcionalidade, caminho de rollback, validação, mensagem de erro,
  histórico, exportação ou formato será removido ou ignorado para fazer um
  teste passar.
- Mock somente poderá representar uma fronteira estreita e explicitamente
  isolada. Mock genérico não será aceito como substituto de `Scene`,
  `CommandManager`, `CanvasView`, `QImage`, exportador ou pipeline assíncrono
  quando esse comportamento real for o objeto do teste.
- Exceções deverão permanecer observáveis no teste e no log. O estado anterior
  deverá ser preservado quando a operação não puder ser confirmada.
- Não será aceita implementação parcial, suíte parcial ou pacote de evidências
  parcial como resultado final. Lotes internos poderão existir apenas como
  mecanismo de segurança de desenvolvimento; nenhum lote poderá ser declarado
  concluído isoladamente nem poderá ser merged antes do fechamento integral.
- Qualquer resultado não executado será classificado como `NÃO TESTADO`;
  impedimento identificado como `BLOQUEADO`; cobertura incompleta como
  `PARCIAL`. Nenhuma dessas classificações equivale a `APROVADO`.
- Diante de perda de dados, regressão, divergência não explicada,
  não determinismo, falha de build, queda de cobertura, risco de segurança ou
  alteração fora do escopo, o fluxo será interrompido e a etapa será registrada
  como bloqueada até haver causa e decisão formal.

## 2. Estado de entrada e fronteira

### 2.1 Fatos já comprovados

- A reprodução histórica inicial registrou `196 testes, 27 falhas, 0 erros e
  0 skips`.
- Após as correções de robustez já aplicadas, a reprodução legada final registra
  `196 testes, 26 falhas, 0 erros e 0 skips`.
- O caso histórico `polygonal_lasso.test_commit_selection_converts_to_integers`
  passou e permanece protegido por teste; ele não faz parte dos 26 casos desta
  etapa, mas continua no inventário para impedir regressão.
- A reconciliação final ainda está `failed`: `15/27` assinaturas coincidentes,
  `11` assinaturas alteradas e `12` falhas esperadas ausentes.
- A suíte oficial, cobertura, verificações estáticas e baseline foram executadas
  com aprovação no estado atual, mas isso não substitui a reconciliação formal
  dos snapshots legados.
- O gate de evidências ainda identifica um `manifest.json` não rastreado
  preexistente em `docs/evidence/artifacts/stage10-accessibility-20260824/...`.
  Esse arquivo não será removido nem incluído automaticamente; sua propriedade,
  escopo, integridade e tratamento deverão ser decididos formalmente.

### 2.2 Escopo incluído

Estão incluídos exatamente os 26 casos históricos ainda falhos: `#1–#9`,
`#11–#27`. O caso `#10` é uma regressão já resolvida, não deve ser descartado
do registro e deverá continuar sendo executado no conjunto de não regressão.

Estão incluídos:

- criação de fixtures reais e determinísticas;
- testes substitutos equivalentes ou superiores;
- correções de produto somente quando houver defeito de produto demonstrado;
- correções do harness quando a divergência for de fixture, contrato ou
  integração histórica;
- testes de erro, preservação de estado, undo/redo e rollback;
- equivalência geométrica, visual, de exportação, cache e comportamento;
- execução Windows/Qt, quando aplicável;
- reconciliação formal, integridade de evidências e gates finais.

### 2.3 Fora do escopo sem decisão nova

- alterar o contrato aprovado de `P2D-05/O-2` por conveniência;
- adicionar culling, spatial index, paralelismo ou nova otimização sem evidência
  e aprovação próprias;
- aceitar geometrias inválidas, imagens falsas ou objetos parciais para reduzir
  falhas;
- remover APIs, funcionalidades, formatos ou caminhos antigos;
- corrigir unrelated changes do workspace;
- modificar artefatos históricos só porque estão fora do estado atual;
- executar commit, push, merge, tag, release ou avanço de etapa antes dos gates.

## 3. Matriz integral dos 26 casos

Cada linha abaixo terá uma ficha de execução no relatório final. A coluna
“aceite específico” é obrigatória: passar somente no teste unitário isolado não
encerra uma linha que exige integração, dados, Qt ou exportação.

| Caso | Diagnóstico de entrada | Trabalho obrigatório | Aceite específico e evidência |
|---:|---|---|---|
| 1 | Fixture de `convex_decompose_l_shape` possui auto sobreposição; a geometria não é um L simples válido. | Criar fixture L simples, não auto-intersectante, com orientação controlada; manter teste negativo para a fixture inválida. | Rejeição determinística da entrada inválida sem mutação; decomposição válida preserva área e produz peças convexas. Registrar coordenadas, hash da entrada, área antes/depois e traceback. |
| 2 | `ear_clipping_concave_l_shape` usa a mesma geometria inválida; aceitar triângulos incorretos seria regressão. | Usar polígono côncavo válido em ambas as orientações e preservar o validador estrito. | Triangulação termina, cobre exatamente a área, não cria triângulos fora do polígono e é independente da orientação. Manter a rejeição explícita do fixture histórico. |
| 3 | O teste histórico exige `float64`, enquanto o contrato atual operacional é `float32` sem clipping. | Atualizar somente o teste substituto para o contrato aprovado; não alterar dtype nem inserir conversão cosmética no produto. | `ndarray` com dtype, shape e finitude corretos; valores preservados dentro da tolerância do contrato e nenhum clipping silencioso. Medir custo de conversão e registrar ausência de regressão. |
| 4 | O teste histórico espera dois atlas porque rotação ainda não existia; o exportador atual acomoda os sprites em um atlas. | Usar sprites reais com e sem rotação e validar packing físico, rotação, UV e metadados. | Um atlas quando permitido pelo packing, dimensões físicas corretas, metadado de rotação coerente e round-trip de importação/exportação. Comparar bytes/estrutura conforme o contrato, não a contagem histórica obsoleta. |
| 5 | `handle_move_undo_redo` cria polígono colinear de três pontos; `Scene` deve rejeitá-lo. | Criar caso positivo com geometria Bézier não colinear e caso negativo colinear; exercitar criação, movimento, undo e redo no manager real. | Entrada inválida falha antes da mutação/histórico; entrada válida produz exatamente uma operação desfazível e refazível, preservando parâmetros e seleção. |
| 6 | Lasso usa Canvas/Scene `Mock` e manager sem `CommandResult`; o commit não pode ser confirmado. | Fixture com `QApplication`, `CanvasView`, `Scene` e `CommandManager` reais; caminho válido e caminho de falha controlada. | Release confirma seleção somente após resultado real; erro preserva seleção/nós e registra diagnóstico. Capturar estado antes/depois e histórico. |
| 7 | Pen usa modelo `Mock` sem manager válido; não há criação confirmável. | Fixture real de Scene/manager, controles válidos, conversão canônica e comando real. | Commit retorna resultado real, objeto persistido é válido, seleção e parâmetros são preservados, undo/redo são equivalentes. O teste negativo deve provar ausência de mutação parcial. |
| 8 | Duplo clique da pen depende do mesmo manager inválido; limpar nós ocultaria a falha. | Usar eventos Qt reais e curva fechável válida; testar também finalização inválida. | Duplo clique válido consolida uma entrada; inválido preserva nós e último estado válido, mostra/loga erro e não cria histórico parcial. |
| 9 | Duplo clique do laço poligonal usa Mock de Qt/Scene incompatível com o caminho atual. | Testar com CanvasView/Scene reais, quantidade mínima de vértices e eventos Qt reais. | Fechamento válido cria a seleção/objeto correto; fechamento inválido permanece fail-closed; estado e histórico são observáveis. |
| 11 | Release do retângulo usa Mock como parent e Scene; commit não é confirmação de produto. | Criar retângulo real com dimensões não nulas sobre Scene real e parent QWidget válido. | Seleção é persistida uma vez, undo/redo restauram exatamente os estados, e mensagens não produzem erro secundário de Qt. |
| 12 | Release da elipse tem a mesma incompatibilidade de fixture/Scene. | Repetir o fluxo com elipse real, dimensões válidas, sinais/eventos Qt e manager real. | Elipse válida é confirmada com área/parâmetros esperados; entrada degenerada é rejeitada sem alteração observável. |
| 13 | Integração do lasso usa Scene parcial; snapshot e comando exigem protocolo completo. | Fixture de integração compartilhada com Scene concreta, histórico real, seleção e serialização. | A operação produz exatamente uma entrada, exporta estado válido, desfaz/refaz sem divergência e mantém estado após erro. |
| 14 | Integração do laço poligonal usa o mesmo protocolo incompleto. | Executar caminho real de vértices, normalização e comando, usando a mesma fixture de integração. | Polígono válido passa por uma única preparação canônica; seleção, histórico e round-trip permanecem equivalentes. |
| 15 | Integração da elipse usa Scene falsa e não exercita o contrato real. | Integrar elipse, seleção e histórico com objetos concretos e eventos determinísticos. | Estado de cena, geometria, seleção e undo/redo são iguais após o ciclo completo; erro não deixa mutação parcial. |
| 16 | Manager real é usado sobre Scene falsa; a sequência de múltiplas operações não pode ser validada. | Construir sequência real de operações heterogêneas e snapshots de estado canônico. | A sequência completa desfaz/refaz na ordem correta, sem perder objetos, seleção, parâmetros ou listeners; comparar estados antes/depois por token determinístico. |
| 17 | `get_image_array` recebe Mock que apenas imita QImage; o adapter aceita ndarray/QImage reais. | Criar casos com ndarray válido, QImage válido, formatos/dimensões suportados e entradas inválidas. | Conversão correta, dtype/shape esperados, ownership seguro e falha clara para objeto incompatível; nenhuma aceitação de Mock genérico como imagem. |
| 18 | Sem imagem válida não existe edge map/cache determinístico. | Usar imagem sintética fixa, gerar mapa, repetir para hit e alterar imagem para invalidar. | Miss/hit/invalidação são observáveis, determinísticos e associados à chave correta; ausência de imagem termina fail-closed sem estado inválido. |
| 19 | Press do Magnetic Lasso pressupõe resolução síncrona e imagem falsa. | Exercitar worker/engine com imagem real, anchors válidos, token de geração e entrega por sinal. | Segmento só é aplicado quando a resposta correspondente chega; resposta atrasada/obsoleta é descartada sem corromper preview ou histórico. |
| 20 | Move verifica preview antes da entrega assíncrona e sem fonte de imagem válida. | Usar event loop/ponte Qt, timeout determinístico e espera por sinal explícito; proibir `sleep` arbitrário. | Preview muda apenas para o resultado correto, não bloqueia UI, não aceita resposta fora de ordem e mantém último preview válido em erro. |
| 21 | Duplo clique histórico não forma caminho fechado válido e usa manager Mock. | Construir anchors, caminho fechado e Scene reais; testar fechamento válido e inválido. | Fechamento válido consolida uma seleção; caminho inválido não executa comando, preserva nós e registra motivo. |
| 22 | Caminho com edge map usa imagem falsa; solver retorna vazio corretamente. | Gerar edge map real e executar solver determinístico com parâmetros registrados. | Caminho não vazio somente quando geometricamente suportado; cache reutilizado corretamente; ausência/invalidade do mapa permanece fail-closed. |
| 23 | Teste exige oito pontos por padrão, mas o contrato atual usa piso explícito via `min_points`. | Parametrizar teste de default e teste opt-in com `min_points=8`; não artificialmente alterar simplificação padrão. | Default respeita contrato mínimo; opt-in respeita piso solicitado; curva e área permanecem válidas e finitas. |
| 24 | Teste exige zoom fixo `1.0`, mas reset atual faz fit/center da viewport. | Testar imagens e viewports com aspect ratios distintos, DPI e dimensões pequenas/grandes. | Reset calcula escala/centro esperados, sem drift, e permanece equivalente após resize; nenhum número fixo é usado como substituto da regra. |
| 25 | Snapshot recursivo de Mock causava `RecursionError`; o snapshot cycle-safe já foi corrigido, mas a Scene falsa continua inválida. | Manter regressão direta de ciclo e executar integração com Scene/manager reais; preservar estado privado real. | Snapshot finito, determinístico e sensível a mudanças relevantes; comando real não recursa nem omite estado funcional; erro de Scene permanece visível. |
| 26 | Integração do retângulo usa Fake Scene sem mutação, seleção e retorno exigidos. | Reusar fixture concreta de Scene/CommandManager e eventos Qt reais. | Criação, seleção, undo/redo, serialização e erro controlado passam no mesmo fluxo de produção. Nenhum fallback bypassa histórico. |
| 27 | Integração Magnetic combina caminho síncrono falso, imagem ausente e Scene incompleta. | Teste end-to-end real: ndarray/QImage, edge cache, worker, sinais, Scene, CommandManager, commit e undo/redo. | O pipeline completo é determinístico dentro do timeout, respeita cancelamento/ordem, gera uma entrada de histórico e preserva estado em qualquer falha. |

## 4. Arquitetura obrigatória das fixtures e dos contratos substitutos

### 4.1 Geometria e exportação

- As entradas serão declaradas como dados fixos, versionados e hasháveis.
- Cada fixture terá classificação `válida`, `inválida por auto-interseção`,
  `inválida por área zero`, `degenerada` ou `fora do formato`.
- A preparação canônica será a mesma usada pela criação, edição, API direta e
  exportação.
- Asserções incluirão área assinada, orientação, interseções, contagem de
  vértices, finitude, dimensões físicas, metadados e round-trip.
- Tolerâncias serão derivadas do contrato documentado, fixas e justificadas;
  não serão ajustadas caso a caso para obter aprovação.

### 4.2 Scene, comandos e histórico

- O caminho principal usará `Scene` concreta, `CommandManager` real e objetos
  com estado completo.
- Testes de adapter poderão usar doubles somente quando a fronteira estiver
  explicitamente isolada e com `spec_set`/protocolo restrito.
- Cada operação verificará estado antes, estado após, tamanho do histórico,
  undo, redo, seleção, listeners e persistência.
- Uma falha deverá deixar o último estado válido intacto e fornecer traceback,
  código/mensagem e estado observável.
- O token de snapshot deverá observar estado funcional relevante; somente
  referências efêmeras comprovadamente não semânticas poderão ser excluídas,
  com justificativa e teste.

### 4.3 Qt e viewport

- Testes que cobrem parent, eventos, sinais, widget, viewport ou diálogo usarão
  `QApplication` e `QWidget` reais no ambiente controlado.
- O fluxo assíncrono será sincronizado por sinal, geração, sequência ou condição
  explícita com timeout. `sleep` arbitrário não será evidência de entrega.
- Falhas de plataforma, plugin ou display serão classificadas como bloqueio de
  ambiente, com log completo; não serão convertidas em skip silencioso.
- Capturas visuais deverão indicar resolução, DPI, viewport, commit, hash e
  comparação usada.

### 4.4 Imagens e Magnetic Lasso

- Imagens sintéticas serão determinísticas, pequenas o suficiente para testes e
  suficientemente expressivas para produzir bordas e caminhos.
- Cada imagem terá formato, shape, dtype, hash e expectativa de conversão
  registrados.
- Cache terá testes de miss, hit, invalidação por conteúdo/parâmetro e
  isolamento entre imagens.
- Worker terá testes de sucesso, erro, cancelamento, resposta obsoleta,
  timeout e encerramento seguro.
- O solver determinístico será testado separadamente da ponte Qt, mas o teste
  end-to-end deverá confirmar a integração real.

## 5. Sequência completa de execução

Esta sequência é obrigatória. O avanço entre fases não significa aprovação
parcial; significa somente que o pacote intermediário passou o controle de
segurança necessário para continuar.

### Fase 0 — gate de entrada e congelamento da fronteira

1. Consultar novamente todas as políticas listadas na seção 1.
2. Registrar branch, HEAD, Python, PySide6/Qt, OpenCV, sistema operacional,
   variáveis de ambiente relevantes e estado completo da árvore.
3. Confirmar hashes dos snapshots legados e não tocar em seus bytes.
4. Separar arquivos controlados desta etapa de alterações/untracked preexistentes.
5. Registrar o `manifest.json` não rastreado como bloqueador de evidência até
   haver decisão de propriedade e escopo.
6. Confirmar que não há autorização implícita para excluir, mover, sobrescrever
   ou limpar artefatos do usuário.
7. Criar um plano de rollback e uma cópia/referência verificável dos artefatos
   de entrada.

**Saída obrigatória:** relatório de entrada `APROVADO` ou etapa `BLOQUEADA`.
Sem saída aprovada, nenhuma implementação será iniciada.

### Fase 1 — contratos substitutos e fábrica de fixtures

1. Definir helpers reais para Scene/CommandManager/CanvasView/QImage/ndarray.
2. Definir eventos Qt e sincronização assíncrona determinística.
3. Criar fixtures válidas e inválidas com hashes e expectativas.
4. Criar testes de caracterização do estado atual antes de alterar produto.
5. Executar somente os testes de contrato da fábrica e verificar que eles não
   dependem de Mock genérico ou estado global implícito.

**Saída obrigatória:** todos os contratos da fábrica passam sem skips e sem
   erro; qualquer divergência é corrigida ou classificada antes da Fase 2.

### Fase 2 — geometrias, bordas, exportação e viewport

1. Tratar os casos `#1`, `#2`, `#3`, `#4`, `#5`, `#23` e `#24`.
2. Não alterar produto quando o comportamento atual for o contrato correto.
3. Corrigir somente defeito demonstrado por comparação com a especificação.
4. Executar testes unitários, caracterização, exportação/round-trip e viewport.
5. Repetir os casos negativos para provar rejeição sem mutação parcial.

**Saída obrigatória:** cada caso tem diagnóstico, teste substituto aprovado,
resultado bruto e classificação `CORRIGIDO`, `NO_CHANGE` formal ou `BLOQUEADO`.

### Fase 3 — ferramentas síncronas e histórico

1. Tratar `#6`, `#7`, `#8`, `#9`, `#11`, `#12`, `#13`, `#14`, `#15`, `#16`,
   `#25` e `#26`.
2. Usar objetos reais para confirmação; nenhum fallback poderá fabricar
   `CommandResult` ou ignorar o histórico.
3. Verificar commit único por gesto, cancelamento, troca de ferramenta,
   undo/redo e preservação em erro.
4. Executar também o caso `#10` como não regressão, sem removê-lo do inventário.

**Saída obrigatória:** cada fluxo passa por criação, erro, undo, redo e estado
   persistido quando aplicável; nenhum teste depende de estado não declarado.

### Fase 4 — Magnetic Lasso, cache e assincronia

1. Tratar `#17`, `#18`, `#19`, `#20`, `#21`, `#22` e `#27`.
2. Separar solver determinístico, conversão de imagem, cache e ponte Qt.
3. Exercitar sucesso, erro, timeout, cancelamento e resposta fora de ordem.
4. Registrar os sinais, tokens, tempos, geração e estado de cache observados.
5. Repetir o fluxo em Windows com `QApplication` real e ambiente controlado.

**Saída obrigatória:** solver, cache, worker e integração passam separadamente e
   no end-to-end; qualquer ausência de entrega ou timeout é falha/bloqueio
   explícito, nunca skip.

### Fase 5 — reconciliação formal

1. Executar novamente o runner histórico integral sem alterar snapshots.
2. Executar todos os testes substitutos referenciados, não apenas os focais.
3. Para cada caso, comparar assinatura histórica, causa raiz, substituto e
   comportamento atual.
4. Registrar explicitamente os casos sem bug de produto como `NO_CHANGE` com
   justificativa verificável.
5. Registrar o caso `#10` como resolvido sem apagar seu histórico.
6. Somente após todos os substitutos passarem, propor alteração formal no
   mecanismo/manifesto de reconciliação, se o schema atual não representar
   corretamente casos resolvidos ou assinaturas substituídas.
7. Testar a própria reconciliação, inclusive ids, referências, mensagens,
   duplicatas, ausências e mudança de assinatura.

**Saída obrigatória:** reconciliação `accepted=true` ou bloqueio formal com
   divergência listada. O resultado histórico bruto continuará sendo publicado
   separadamente do resultado dos substitutos.

### Fase 6 — pacote de evidências e auditoria de integridade

O pacote deverá conter, no mínimo:

- relatório vivo desta etapa atualizado com resultados reais;
- branch, commit/HEAD e base de rollback;
- ambiente completo e comandos exatos;
- lista de arquivos, tamanhos, hashes e fronteira staged;
- snapshots históricos e prova de que não foram alterados;
- logs/JUnit/tracebacks completos dos 26 casos;
- dump/stack nativo quando houver crash, hang, abort ou falha de processo;
- para falha determinística sem crash, entrada hashable, traceback, estado
  antes/depois e teste equivalente reproduzível;
- resultados de cobertura, performance, memória e determinismo;
- capturas visuais/Qt quando aplicável;
- limitações e itens `NÃO TESTADO`/`BLOQUEADO`;
- decisão formal por caso;
- plano e prova de rollback.

O `manifest.json` não rastreado deverá ser auditado quanto a:

1. proprietário e origem;
2. pertencimento ou não à etapa;
3. conteúdo, bytes, hash e referências;
4. risco de exposição de dados locais;
5. forma correta de rastrear, excluir do escopo ou classificar como bloqueio;
6. confirmação de que nenhuma ação destrutiva foi tomada sem autorização.

O pacote somente será considerado íntegro quando `tools/evidence_integrity.py
--require-tracked --git-blob` passar sobre o escopo real, incluindo seus
manifests e referências.

### Fase 7 — gates finais e decisão de integração

Executar na mesma revisão candidata:

1. suíte oficial completa;
2. suíte substituta completa dos 26 casos;
3. runner histórico integral, sem skip/xfail adicionado;
4. reconciliação formal aceita;
5. cobertura de linhas, branches e módulos conforme política;
6. compile/import;
7. flake8, Black, isort e mypy;
8. Bandit e auditoria de dependências;
9. testes Windows/Qt e exportação/round-trip;
10. benchmark comparável ao baseline, incluindo cache/incremental/frame;
11. determinismo em repetição e ausência de race/timeout;
12. diff check e revisão de exclusões acidentais;
13. baseline integrity;
14. evidence integrity;
15. revisão de privacidade e segurança do pacote.

Uma única falha desconhecida, assinatura não explicada, arquivo fora da
fronteira, teste faltante, regressão de performance, evidência incompleta ou
manifest não resolvido impede a decisão de merge.

## 6. Evidência nativa, determinística e de diagnóstico

### 6.1 Quando dump/stack nativo é obrigatório

Para crash de processo, abort nativo, hang, violação de acesso, encerramento
do Qt, worker que não termina ou comportamento dependente de plataforma, será
obrigatório coletar dump/stack nativo, identificação do processo, símbolos
disponíveis, comando, ambiente e hash do binário/código testado.

### 6.2 Quando a prova determinística é equivalente

Para rejeição geométrica, mismatch de contrato, retorno inválido, estado
parcial, assinatura de snapshot ou falha de fixture sem crash, a prova poderá
ser determinística equivalente, contendo:

- entrada serializável e hash;
- comando exato;
- traceback completo;
- estado canônico antes/depois;
- expectativa do contrato;
- teste substituto reproduzível;
- repetição que confirme a mesma assinatura;
- razão técnica para não ser necessária uma captura nativa.

Nunca será afirmado que houve dump nativo quando apenas houve traceback Python,
nem que houve equivalência quando somente um smoke test passou.

## 7. Desempenho, memória e segurança

### 7.1 Desempenho

- Comparar com a mesma metodologia do baseline e com o mesmo conteúdo de
  entrada.
- Medir p50/p95 quando o contrato exigir, além de tempo total, contagem de
  recomputações, cache hit/miss, memória e duração do worker.
- Confirmar que a correção de fixtures não esconde custo de produção.
- Repetir o benchmark para separar ruído, aquecimento e não determinismo.
- Qualquer regressão relevante em cache, incremental, frame ou UI bloqueia a
  etapa, mesmo que os testes funcionais passem.

### 7.2 Segurança e privacidade

- Não executar arquivos de entrada não confiáveis fora dos mecanismos previstos.
- Sanitizar caminhos locais, nomes de usuário, tokens e conteúdo sensível dos
  logs e dumps antes de versionar evidências.
- Não incluir dados pessoais em fixtures ou capturas.
- Validar limites de tamanho, formato, finitude, dtype e alocação das imagens.
- Confirmar que erro de imagem, exportação ou comando não grava arquivo parcial,
  não sobrescreve dado válido e não deixa cache contaminado.
- Executar Bandit, auditoria de dependências e inspeção de permissões no pacote.

## 8. Riscos, bloqueadores e rollback

### 8.1 Riscos conhecidos

- Modernizar fixtures pode revelar defeitos reais antes mascarados pelo Mock.
- A assincronia do Magnetic Lasso pode expor races que não aparecem no solver
  unitário.
- Alterar o harness de reconciliação pode criar divergência entre o histórico
  imutável e o estado vivo.
- O manifest não rastreado pode impedir o gate mesmo que o código passe.
- Testes Qt podem depender de Windows, plugin ou event loop específico.

### 8.2 Condições de parada

Parar imediatamente e registrar `BLOQUEADO` diante de:

- perda ou sobrescrita de dados;
- regressão funcional ou de compatibilidade;
- divergência entre plataformas sem causa;
- não determinismo ou race não explicado;
- crash/hang sem diagnóstico suficiente;
- alteração fora da fronteira;
- falha de integridade de snapshot, baseline ou evidência;
- ausência de fixture real, ambiente ou artefato necessário;
- necessidade de alterar regra, threshold, skip, xfail ou snapshot para passar.

### 8.3 Rollback

- A base funcional de rollback é `7f3799c1b29835f6db5ab6d35c0cab5deda5765b`,
  sem reset destrutivo da árvore do usuário.
- O lote corretivo deverá ser isolado em commit(s) pequenos o suficiente para
  revisão, mas nenhum commit será considerado integrável antes do fechamento
  integral desta etapa.
- O rollback formal será feito por revert do commit candidato ou por aplicação
  de patch reversível e verificado; não será usado `git reset --hard`,
  `git checkout --` ou limpeza ampla para ocultar estado.
- Untracked e evidências preexistentes serão preservados durante rollback.
- Após rollback, repetir baseline, integridade e smoke mínimo para provar que o
  produto retornou ao estado anterior.

## 9. Critérios formais de encerramento

A etapa só poderá receber `APROVADO / CONCLUÍDO` quando todos os itens forem
verdadeiros na mesma revisão candidata:

- os 26 casos possuem diagnóstico, decisão e teste substituto correspondente;
- o caso #10 continua passando e documentado como não regressão;
- nenhum snapshot histórico foi alterado;
- nenhuma falha foi escondida por skip, xfail, filtro ou mudança de threshold;
- todas as fixtures são reais, determinísticas e adequadas ao contrato;
- testes unitários, integração, Qt, exportação, round-trip e assíncronos
  aplicáveis passam integralmente;
- falhas negativas provam preservação de estado e ausência de histórico parcial;
- reconciliação formal está aceita e testada;
- manifest não rastreado está resolvido ou formalmente classificado, sem violar
  o gate de evidências;
- suíte oficial, cobertura, estática, segurança, performance e baseline passam;
- evidências contêm comandos, entradas, hashes, resultados, limitações e
  decisão, com integridade verificável;
- revisão final confirma que funcionalidades, dados, formatos, mensagens,
  compatibilidade e rollback foram preservados;
- somente depois disso haverá autorização operacional para commit, push e merge.

Qualquer item falso mantém a etapa `EM EXECUÇÃO` ou `BLOQUEADA`; não existe
estado intermediário apresentado como conclusão.

## 10. Decisões explicitamente registradas nesta abertura

1. O proprietário aceitou as recomendações técnicas para os 26 casos.
2. A execução seguirá fixtures reais, contratos substitutos, reconciliação
   formal, auditoria do manifest e todos os gates antes de integração.
3. Snapshots históricos continuarão representando o comportamento antigo e não
   serão alterados para obter pass.
4. O caso #10 permanece no conjunto de não regressão, embora já esteja passando.
5. O trabalho atual não está autorizado a declarar implementação, testes ou
   evidências completos por execução parcial.
6. Nenhum commit, push ou merge está autorizado antes dos critérios da seção 9.
7. A consulta às regras é obrigatória antes de cada decisão de engenharia e
   deverá ser citada no registro da decisão correspondente.

## 11. Próximo passo exato

O próximo passo é executar somente a **Fase 0 — gate de entrada e congelamento
da fronteira**. Ela deverá produzir o relatório de entrada com regras
consultadas, hashes dos snapshots, inventário completo da árvore, classificação
do manifest não rastreado, ambiente e rollback. Se qualquer item não puder ser
comprovado, a etapa será registrada como `BLOQUEADA` e nenhuma implementação de
fixture, produto, teste ou evidência será iniciada.

Este plano não autoriza alterar snapshots, mascarar falhas, aceitar resultados
parciais ou realizar commit/push/merge.
