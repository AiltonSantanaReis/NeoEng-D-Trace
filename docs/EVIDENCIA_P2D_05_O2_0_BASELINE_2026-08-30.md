# NeoEng-D-Trace — Evidência O-2-0 de preview e viewport

**Etapa:** P2D-05/O-2-0 — baseline de preview e viewport
**Status:** `BASELINE COMPLETE — HOT SPOTS CONFIRMED — IMPLEMENTATION DECISION PENDING`
**Data:** 30/08/2026 (UTC-03)
**Branch:** `p2d-05-quality-hardening`
**Source commit:** `15300a0d580a57110828d8511ae48a0f68326e3a`
**Expected source commit:** `15300a0d580a57110828d8511ae48a0f68326e3a`
**Contrato:** `docs/DECISAO_P2D_05_O2_PREVIEW_VIEWPORT_2026-08-30.md`
**Relatório canônico:** `artifacts/p2d05/o2-0-baseline-20260830-restarted.json`
**Produtor canônico:** `scripts/benchmark_p2d_05_o2_preview.py`

Esta evidência registra a execução integral da baseline O-2-0. Ela não fecha
O-2, não autoriza implementação, commit, build ou publicação. O resultado
`PASS` significa que a matriz executou sem erro e que o frame determinístico
foi repetível; não transforma nenhum número em orçamento normativo.

## 1. Normalização do produtor e histórico de execução

O contrato citava `scripts/benchmark_p2d_05_o2_preview.py`. O primeiro produtor
criado para esse caminho recriava um `QGraphicsView` independente para cada
operação e foi descartado como medição inválida depois de demonstrar pressão de
memória do próprio harness. O produtor corrigido reutiliza um viewport por
workload, restaura a fixture fora da janela cronometrada e foi copiado
mecanicamente para o caminho canônico.

Os dois arquivos do produtor foram conferidos byte a byte antes da execução:

```text
SHA-256 benchmark_p2d_05_o2_preview.py       9f6ff0eb1e2bea3b9d8ef9aba708da91f5ab2ab808df324fe229f34e8dedc091
SHA-256 benchmark_p2d_05_o2_preview_reuse.py 9f6ff0eb1e2be a3b9d8ef9aba708da91f5ab2ab808df324fe229f34e8dedc091
```

O segundo valor acima deve ser interpretado sem o espaço visual inserido nesta
linha: a igualdade foi confirmada pelo comando de hash, com resultado
`EQUAL=True`. Os smoke tests canônicos passaram, mas não são evidência final.
O smoke artificial com um objeto gerou `FAIL` por tentar selecionar um segundo
ID inexistente; ele não pertence à matriz aceita e não foi usado como baseline.

## 2. Comando e protocolo efetivos

O comando final foi executado a partir da raiz do repositório:

```text
$env:QT_QPA_PLATFORM='offscreen'
$env:PYTHONPATH=(Resolve-Path '.').Path
.\.venv\Scripts\python.exe scripts\benchmark_p2d_05_o2_preview.py --output artifacts\p2d05\o2-0-baseline-20260830-restarted.json --iterations 50 --warmup 5 --memory-iterations 20 --object-counts 64,128,256,512 --asset-modes shared,unique
```

Parâmetros e cobertura:

- `50` amostras de timing por operação e workload;
- `5` warm-ups por operação;
- `20` observações de memória separadas por workload;
- `time.perf_counter_ns`, sem `tracemalloc` no timing;
- quatro cargas: `64`, `128`, `256` e `512` objetos;
- dois modos: assets `shared` e `unique`;
- três resoluções: `1280x720`, `1366x768` e `1920x1080`;
- 24 workloads na matriz principal;
- dois workloads estruturais adicionais em `512` objetos e `1920x1080`, um
  por modo de asset;
- fixture com três camadas, dois grupos, memberships, três sockets
  (`light`, `vfx`, `trigger`) e parâmetros de parallax;
- Working Set, Private Bytes e `tracemalloc` observados separadamente;
- GPU não medida, pois o caminho Qt/QGraphicsView não possui contador GPU
  integrado;
- `normative_performance_status` permanece
  `MEASURED_ONLY_PENDING_EXPLICIT_BUDGET_ACCEPTANCE`.

## 3. Integridade da execução

| Verificação | Resultado |
|---|---:|
| Status do relatório | `PASS` |
| Source commit | exatamente o HEAD O-2 aceito |
| Workloads principais | `24/24` |
| Workloads estruturais | `2/2` |
| Total de workloads | `26/26` |
| Erros de operação | `0` |
| Frames repetidos iguais | `26/26` |
| Amostras por operação | `50` |
| Memória por workload | `20` observações |
| GPU | `not_measured` |
| Resultado normativo | pendente de orçamento explícito |

O relatório JSON preserva todos os p50, p95, p99, pior caso, contagens,
erros, memória e determinismo. Nenhum relatório parcial ou smoke test foi
promovido à baseline.

## 4. Resultado p95 da matriz principal

Valores em milissegundos. `full_sync` inclui reconstrução da cena, resolução
de assets e processamento de eventos. `incremental` é o caminho de atualização
de transforms/gizmo/pintura. `frame` é o construtor determinístico sem Qt.

| Workload | full_sync | incremental | seleção | preview toggle | zoom | pan | fit | resize | frame | gesto/cancel |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| shared:64 @ 1280x720 | 11,771 | 5,027 | 1,210 | 8,414 | 1,339 | 0,381 | 0,428 | 5,725 | 1,399 | 14,549 |
| shared:64 @ 1366x768 | 13,054 | 5,733 | 1,590 | 9,507 | 1,748 | 0,482 | 0,453 | 6,362 | 1,957 | 14,776 |
| shared:64 @ 1920x1080 | 13,826 | 6,759 | 1,622 | 8,806 | 2,121 | 0,675 | 0,495 | 9,219 | 1,786 | 18,459 |
| shared:128 @ 1280x720 | 21,722 | 9,264 | 3,100 | 15,921 | 2,733 | 0,632 | 1,072 | 8,836 | 3,459 | 26,232 |
| shared:128 @ 1366x768 | 21,384 | 8,970 | 2,635 | 15,132 | 2,523 | 0,642 | 0,918 | 8,962 | 2,977 | 25,427 |
| shared:128 @ 1920x1080 | 21,296 | 9,625 | 2,550 | 15,237 | 2,848 | 0,787 | 1,152 | 11,567 | 3,033 | 27,235 |
| shared:256 @ 1280x720 | 39,546 | 15,835 | 6,070 | 30,647 | 3,889 | 1,062 | 1,800 | 14,097 | 6,887 | 53,957 |
| shared:256 @ 1366x768 | 38,143 | 15,653 | 5,874 | 30,660 | 3,829 | 1,067 | 1,670 | 13,982 | 7,069 | 51,729 |
| shared:256 @ 1920x1080 | 39,087 | 17,117 | 6,276 | 30,200 | 4,205 | 1,190 | 1,794 | 17,119 | 7,154 | 54,315 |
| shared:512 @ 1280x720 | 78,567 | 30,002 | 15,421 | 65,505 | 7,375 | 2,006 | 3,209 | 25,509 | 18,520 | 127,101 |
| shared:512 @ 1366x768 | 81,968 | 29,553 | 15,308 | 66,241 | 7,086 | 1,994 | 3,469 | 26,065 | 17,880 | 130,873 |
| shared:512 @ 1920x1080 | 78,178 | 34,175 | 16,831 | 67,763 | 7,965 | 2,277 | 3,693 | 30,880 | 20,295 | 135,836 |
| unique:64 @ 1280x720 | 120,257 | 5,565 | 1,502 | 114,885 | 1,581 | 0,389 | 0,482 | 5,994 | 1,648 | 15,065 |
| unique:64 @ 1366x768 | 119,463 | 5,727 | 1,640 | 114,875 | 1,765 | 0,437 | 0,443 | 6,441 | 1,672 | 15,239 |
| unique:64 @ 1920x1080 | 118,834 | 6,582 | 1,564 | 113,058 | 2,057 | 0,640 | 0,487 | 10,854 | 1,596 | 17,802 |
| unique:128 @ 1280x720 | 237,557 | 9,160 | 3,043 | 229,676 | 3,442 | 0,767 | 1,249 | 8,986 | 3,613 | 27,143 |
| unique:128 @ 1366x768 | 255,914 | 9,008 | 2,944 | 229,395 | 2,589 | 0,633 | 0,965 | 9,324 | 3,722 | 27,039 |
| unique:128 @ 1920x1080 | 255,722 | 10,514 | 2,954 | 227,990 | 3,076 | 0,820 | 1,097 | 11,826 | 3,350 | 29,800 |
| unique:256 @ 1280x720 | 477,816 | 15,481 | 6,591 | 457,599 | 3,965 | 1,285 | 1,855 | 14,133 | 7,328 | 52,970 |
| unique:256 @ 1366x768 | 474,353 | 16,004 | 6,274 | 490,848 | 4,312 | 1,072 | 1,925 | 14,903 | 9,042 | 65,619 |
| unique:256 @ 1920x1080 | 479,638 | 17,299 | 6,563 | 460,051 | 4,438 | 1,459 | 1,892 | 19,678 | 7,427 | 55,911 |
| unique:512 @ 1280x720 | 945,923 | 31,030 | 15,521 | 921,016 | 7,805 | 2,043 | 3,963 | 24,923 | 18,999 | 150,655 |
| unique:512 @ 1366x768 | 945,358 | 31,619 | 15,791 | 938,358 | 7,810 | 2,339 | 3,642 | 25,411 | 19,100 | 159,178 |
| unique:512 @ 1920x1080 | 959,496 | 31,444 | 16,509 | 933,139 | 7,622 | 2,333 | 3,702 | 28,329 | 18,838 | 165,881 |

## 5. Probes estruturais p95

Esses probes foram executados em `512` objetos, `1920x1080`, nos dois modos
de asset. Os máximos abaixo ocorreram em `unique`:

| Operação | p95 máximo | Interpretação observada |
|---|---:|---|
| object add/remove | 1.157,235 ms | reconstrução estrutural completa |
| asset update | 1.144,260 ms | mudança de referência mais reconstrução |
| layer visibility | 1.085,158 ms | filtragem de visibilidade mais reconstrução |
| layer reorder | 1.138,948 ms | mudança de ordem canônica mais reconstrução |
| group visibility | 1.018,283 ms | filtragem por grupo mais reconstrução |
| group membership | 201,852 ms | caminho transacional de membership e refresh |
| group isolation | 919,138 ms | filtragem por isolamento mais reconstrução |

## 6. Profiling CPU direcionado, somente local

Foram produzidos quatro perfis brutos locais, sem inclusão nesta evidência,
commit ou seal:

```text
artifacts/p2d05/o2-full-sync-512-unique.prof
artifacts/p2d05/o2-incremental-refresh-512-shared.prof
artifacts/p2d05/o2-preview-frame-512-shared.prof
artifacts/p2d05/o2-structural-isolation-512-unique.prof
```

O profiling foi lido por um inspetor que removeu caminhos pessoais e exibiu
somente arquivo-base, linha, função, chamadas e tempos.

### 6.1 Full sync e alterações estruturais

Em cinco `full_sync` de `unique:512`:

- `SceneAuthoringViewport.sync`: `5,008118 s` acumulados;
- `resolve_scene_asset`: `3,941616 s`;
- `pathlib.Path.resolve`: `1,946403 s`;
- `sha256_file`: `1,561702 s`;
- leitura de arquivos: `1,012820 s`;
- `_load_asset_pixmap`: `0,551830 s`;
- `paintEvent`: `0,135937 s`.

O finding confirmado é a validação/resolução/hash/leitura repetida de assets em
cada reconstrução, seguida da decodificação e criação de itens. O maior custo
não é, neste caso, o desenho Qt isolado.

### 6.2 Atualização incremental

Em vinte `incremental_refresh` de `shared:512`:

- `processEvents`: `0,583457 s`;
- `paintEvent`: `0,523630 s`;
- `SceneObjectGraphicsItem.paint`: `0,348903 s`;
- `QPainter.drawPixmap`: `0,165091 s`;
- `_refresh_transforms`: `0,278027 s`;
- `set_selected_style`/`_refresh_style`: aproximadamente `0,058454 s`;
- `_layer_parallax`: `0,090879 s`.

O finding confirmado é que o caminho incremental ainda percorre e repinta
todos os objetos, mesmo quando a alteração efetiva é limitada. A pintura e a
atualização de transforms são mais relevantes que pan/fit isolados.

### 6.3 Frame determinístico

Em cinquenta construções do frame `shared:512`:

- `build_scene_authoring_preview`: `2,563529 s`;
- `object_is_effectively_visible`: `0,940293 s`;
- `parallax_camera.project`: `0,722691 s`;
- `_world_points`: `0,447130 s`;
- `scene_authoring_preview._point`: `0,247171 s`;
- `_parallax`: `0,220253 s`.

O finding confirmado é recomputação repetida de visibilidade/grupos,
parallax, validações e projeções por objeto. O p95 do frame foi `20,295 ms` no
stress shared e `19,100 ms` no stress unique de `1366x768`, sem transformar
16,7 ms em meta normativa.

## 7. Memória e interpretação

O relatório contém Working Set, Private Bytes e crescimento Python por cada um
dos 26 workloads. A etapa de memória executou 20 refreshes incrementais por
workload, fora do timing, e os valores de `tracemalloc` ficaram em crescimento
observacional pequeno, na ordem aproximada de `0,021` a `0,083 MiB` nos
workloads principais e estruturais.

Essas medições não constituem veredito de leak. A ausência de crescimento
grande nesta série não prova estabilidade nativa em uma sessão longa; uma série
de soak test continua sendo manutenção posterior se o produto exigir essa
garantia.

## 8. Classificação técnica do O-2-0

| Alvo | Classificação O-2-0 | Limite |
|---|---|---|
| full sync / troca para preview | `FIX CANDIDATE CONFIRMED` | investigar cache de asset com invalidação íntegra e reuso seguro |
| refresh incremental | `FIX CANDIDATE CONFIRMED` | reduzir recalculo/repintura somente com equivalência visual/funcional |
| frame determinístico | `FIX CANDIDATE SECONDARY` | otimizar índices/contexto sem alterar frame, grupos ou parallax |
| seleção e gesto/cancelamento | `MONITOR / DEPENDS ON INCREMENTAL` | não reabrir O-1 nem alterar `SceneAuthoringSession` |
| zoom, pan e fit | `NO_CHANGE FOR NOW` | p95 máximo isolado abaixo de 8 ms |
| resize | `MONITOR` | p95 máximo 30,880 ms; profiling dedicado seria necessário antes de mudar |
| group membership | `OUT OF O-2 IMPLEMENTATION` | caminho transacional envolve histórico geral; não alterar Session por inferência |
| GPU, culling, worker, paralelismo | `NOT DEMONSTRATED` | sem implementação ou decisão adicional |

## 9. Comparação com as etapas anteriores

O-0 usou o calibrador histórico com oito workloads, 50 amostras, 5
warm-ups, 20 observações de memória e viewport fixo `640x480`. O-1 repetiu
essa base para demonstrar a otimização de histórico e rejeitou formalmente a
variante incremental do preview por regressão. O-2-0 não reutiliza esses
números como baseline: ele vincula o resultado ao HEAD `15300a0...`, adiciona
as três resoluções, fixture estrutural e operações específicas de viewport.

Assim, a compatibilidade com o método anterior foi preservada onde é
comparável, mas a expansão de O-2 foi executada explicitamente e não inferida.

## 10. Próxima decisão obrigatória

O-2-0 está concluído como auditoria e baseline. A próxima ação governada é
abrir a decisão de implementação de um único lote controlado, limitado a:

1. cache/reuso seguro de resolução e pixmap com invalidação que preserve o
   diagnóstico de asset ausente, inválido ou alterado;
2. atualização incremental apenas dos itens efetivamente afetados, se a
   equivalência puder ser demonstrada;
3. redução de recomputação do frame determinístico, somente se permanecerem
   iguais objetos, ordem, z-order, transform, sockets, visibilidade,
   isolamento e parallax.

Não está autorizado nesta etapa alterar schema, Session/O-1, persistência,
exportação, coordenadas, QAction, layout, aparência, engines, GPU, culling,
threads ou paralelismo. O-3 continua bloqueado.

Antes de implementar, deve ser produzido o contrato específico do lote com
testes focais, equivalência, privacidade, benchmark pós-implementação,
rollback e critério PRECOMMIT. Nenhum código de produto foi alterado para
produzir esta baseline.
