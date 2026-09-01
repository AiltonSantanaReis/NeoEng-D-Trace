# Evidência P2D-05 — investigação de performance

**Status:** `INVESTIGATION COMPLETE — OPTIMIZATION CONTRACT PENDING`
**Data:** 30/08/2026 (UTC-03)
**Branch:** `p2d-05-quality-hardening`
**HEAD-fonte:** `fc59ff571e4e4d99ddd40a8ec318d50b8edd77f3`
**Escopo:** investigação somente leitura; nenhum algoritmo do produto foi alterado nesta investigação.

Este registro transforma a recomendação aceita de profiling em evidência
reproduzível. Ele não cria uma nova etapa do plano, não aprova novos limites e
não autoriza otimização, commit ou publicação. A próxima mudança de performance
deverá ser aberta no identificador já previsto pelo plano vigente, sem inventar
um estágio fora dele.

## 1. Integridade da investigação

- branch e HEAD foram confirmados antes das medições;
- a árvore tracked permaneceu com as mesmas 13 mudanças do lote P2D-05;
- `git diff --check`: `PASS`;
- nenhuma alteração de código do produto foi realizada para obter os resultados;
- bytes canônicos, exportações e estado funcional não foram modificados;
- todos os workloads concluíram com erro zero e determinismo preservado;
- nenhum push, tag, merge, commit ou build foi realizado nesta investigação.

Ferramentas e artefatos:

- benchmark de operações: `scripts/benchmark_p2d_05.py`;
- cargas: `artifacts/p2d05/benchmark-investigation-128.json`,
  `benchmark-investigation-256.json` e
  `benchmark-investigation-512.json`;
- profiling CPU geral: `artifacts/p2d05/profile-p2d05-512.prof`;
- profiling isolado do preview: `artifacts/p2d05/profile-preview-512.prof`;
- profiling isolado do gesto: `artifacts/p2d05/profile-gesture-512.prof`.

Os arquivos `.prof` são evidência bruta local. Eles não devem entrar em
review package, commit ou seal sem uma inspeção de privacidade própria.

## 2. Varredura de cargas

A mesma fixture determinística foi medida com 128, 256 e 512 objetos. Cada carga
usou 20 repetições medidas e o benchmark existente, que também registra
determinismo, erros e memória Python.

| Objetos | Bytes da cena | Serialize p95 | Load/validate p95 | Save/recovery p95 | Edit/history p95 | Preview sync p95 | Export genérico p95 | Export Godot p95 | Export Unity p95 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 128 | 78.161 | 32,729 ms | 11,905 ms | 73,218 ms | 29,557 ms | 76,021 ms | 154,495 ms | 185,206 ms | 220,475 ms |
| 256 | 155.187 | 65,624 ms | 20,882 ms | 110,602 ms | 56,692 ms | 135,639 ms | 284,036 ms | 284,578 ms | 284,003 ms |
| 512 | 309.129 | 129,206 ms | 39,978 ms | 188,905 ms | 110,781 ms | 274,684 ms | 557,397 ms | 617,418 ms | 682,356 ms |

Todos os pontos acima registraram:

- `error_count=0`;
- bytes canônicos e exportações determinísticos;
- conclusão `PASS` do benchmark.

Os números variam entre execuções, portanto a tabela deve ser interpretada como
sinal de escala e não como orçamento final. Em especial, o p95 com apenas 20
amostras é uma medida preliminar.

## 3. Hot spots confirmados por profiling

### 3.1 Histórico e transações

No profiling geral do workload de 512 objetos:

- 111.044.424 chamadas totais em 64,151 s;
- `SceneAuthoringSession.snapshot` acumulou 38,672 s;
- `copy.deepcopy` acumulou 38,867 s;
- `SceneAuthoringSession.apply` e `_record` aparecem como chamadores
  do custo;
- o benchmark seleciona apenas um objeto para a edição, mas o snapshot copia
  o documento inteiro.

Conclusão: este é um gargalo estrutural comprovado do caminho de histórico,
não um problema de quantidade de objetos realmente editados. A alternativa
profissional a investigar é histórico por comando/delta ou copy-on-write, mas
só pode ser aceita quando cobrir todas as operações undoáveis e preservar a
atomicidade atual.

### 3.2 Preview, pintura e visibilidade

No profiling isolado de cinco `sync()` do viewport com 512 objetos:

- `sync`: 0,355 s acumulados;
- `processEvents`: 0,285 s;
- `paintEvent`: 0,271 s;
- `SceneObjectGraphicsItem.paint`: 0,224 s;
- `QPainter.drawPixmap`: 0,145 s;
- `object_is_effectively_visible`: 0,084 s;
- foram criados/processados 2.560 itens de objeto, correspondentes a
  512 objetos em cinco ciclos.

O código atual limpa a cena e reconstrói os itens em
`src/ui/scene_authoring_viewport.py:630`. A pintura de cada item e a
verificação de visibilidade também aparecem no perfil.

Conclusão: a primeira otimização deve ser atualização incremental por IDs
alterados, preservação de itens estáveis e coalescência segura de atualizações.
Culling espacial só deve ser adicionado depois de separar o custo de criação,
visibilidade e pintura.

### 3.3 Preview durante arraste/gizmo

No profiling isolado de 20 chamadas do fluxo de preview:

- `preview_transform_selected`: 0,012 s;
- `transform_selected`: 0,008 s;
- validações Pydantic: 0,006 s;
- `restore_gesture_base`: 0,004 s;
- `_restore`: 0,004 s.

O método de preview restaura o estado-base em cada evento antes de calcular o
novo transform. Em cenas grandes, esta validação recorrente deve ser eliminada
do caminho de cada movimento, mantendo o estado-base imutável durante o gesto e
validando a transação final no release.

### 3.4 Serialização e exportação

No profiling geral:

- `json.dumps/encode`: aproximadamente 16,3 s acumulados;
- `serialize_scene_authoring_export`: aproximadamente 15,2 s;
- `build_scene_authoring_export`: aproximadamente 11,6 s;
- `serialize_scene_authoring`: aproximadamente 9,6 s;
- `_validate_export`: aproximadamente 7,9 s.

A implementação corrente valida o documento, calcula hash canônico, valida o
payload e serializa novamente. O caminho é correto, mas existe trabalho
repetido. A otimização segura a investigar é um pipeline por revisão imutável:
uma validação, uma preparação, um hash e uma serialização, com invalidação
determinística após cada mutação.

O `fsync` da gravação atômica não deve ser removido para reduzir tempo.
A melhoria adequada é separar a preparação do payload da gravação durável e,
quando aplicável, executar a operação fora da thread visual.

## 4. O que ainda não foi demonstrado

Esta investigação não permite concluir que:

- GPU é um gargalo;
- instancing é necessário;
- culling é o maior custo;
- paralelismo reduzirá o tempo total;
- a memória nativa do Qt está estável;
- os números atuais são adequados para um hardware diferente.

Limitações controladas:

- o benchmark mede operações Python/Qt, não contadores de GPU;
- `tracemalloc` está ativo na medição de operações e pode alterar o tempo;
- a memória registrada é memória Python, não Working Set/Private Bytes completos;
- a fixture utiliza um único PNG de 1x1 compartilhado, não uma biblioteca real de
  assets;
- 20 amostras produzem p95 com baixa robustez estatística;
- o preview medido é `sync + processEvents`, não uma medição de frame contínuo
  completa em todas as interações do usuário.

## 5. Decisão técnica recomendada

A ordem de otimização deve ser:

1. recalibrar a metodologia: 50 ou 100 amostras, sem `tracemalloc` para
   timing, e uma execução separada para memória;
2. adicionar fixtures realistas com assets únicos/compartilhados, tamanhos reais,
   grupos, camadas e proporção de objetos visíveis;
3. otimizar o caminho de gesto e histórico;
4. otimizar `sync` com atualização incremental e cache de assets limitado,
   indexado por identidade/hash;
5. eliminar serializações/validações duplicadas por revisão;
6. mover I/O, validação e exportação para worker seguro quando isso melhorar a
   responsividade, sem mover mutações Qt ou do modelo para fora da thread correta;
7. somente então medir culling, spatial index, GPU ou instancing.

Os orçamentos anteriormente propostos para 64 objetos continuam úteis como
referência inicial, mas não devem ser aceitos como metas definitivas com esta
metodologia. Deve ser acrescentado um orçamento específico para interação
contínua, porque um `preview_sync` de 38 ms no workload de referência já
ultrapassa um frame de 16,7 ms, embora a operação medida não seja idêntica ao
frame completo.

## 6. Próximo passo governado

O próximo passo não é editar o produto. É abrir, usando o identificador já
existente no plano, o contrato específico de otimização com:

- invariantes de bytes, schema, undo/redo, atomicidade e thread Qt;
- matriz completa de operações afetadas;
- workload e hardware de referência;
- métricas separadas de CPU, frame, memória Python e memória nativa;
- metas normativas somente após a calibração;
- testes de equivalência antes/depois;
- evidência de usuário para arraste, seleção, preview, save e export;
- rollback e limites explícitos.

Até esse contrato ser aceito, o estado correto é investigação concluída,
produto inalterado e otimização pendente.
