# Evidência P2D-05 — calibração O-0 de performance

**Data:** 2026-08-30
**Lote:** P2D-05-OTIMIZAÇÃO
**Fase:** O-0 — calibração de timing, memória, workloads e Qt
**Status:** `CALIBRATION COMPLETE — MEASURED ONLY; EXPLICIT BUDGET ACCEPTANCE PENDING`
**Branch:** `p2d-05-quality-hardening`
**Source commit:** `fc59ff571e4e4d99ddd40a8ec318d50b8edd77f3`
**Relatório canônico:** `artifacts/p2d05/calibration-o0-20260830.json`

## 1. Decisão de escopo

Esta evidência registra somente a calibração autorizada pelo contrato de otimização aceito. Nenhum algoritmo do produto, schema, formato exportado, limite, regra de validação, semântica de undo/redo ou contrato G/V/B foi alterado durante a medição.

O resultado `PASS` significa que a matriz foi executada integralmente, sem erros de workload e com determinismo confirmado. Não significa que uma meta normativa de performance foi aprovada: qualquer orçamento operacional continua pendente de aceite explícito após revisão dos dados.

## 2. Método reproduzível

Comandos executados a partir da raiz do repositório:

```text
.\\.venv\\Scripts\\python.exe -m py_compile scripts\\calibrate_p2d_05.py
$env:QT_QPA_PLATFORM = 'offscreen'
& .\\.venv\\Scripts\\python.exe scripts\\calibrate_p2d_05.py --output artifacts\\p2d05\\calibration-o0-20260830.json --iterations 50 --warmup 5 --memory-iterations 20 --object-counts 64,128,256,512 --asset-modes shared,unique
```

Parâmetros efetivos:

- 8 workloads: 4 cargas (`64`, `128`, `256`, `512`) × 2 modos de assets (`shared`, `unique`);
- 50 amostras de timing por operação e workload, depois de 5 amostras de warm-up;
- 20 observações na etapa de memória por workload;
- relógio monotônico `time.perf_counter_ns`;
- `tracemalloc` desabilitado durante timing e usado somente na etapa de memória;
- Qt em `offscreen` para eliminar dependência da janela nativa durante a calibração;
- Working Set e Private Bytes do processo medidos quando disponíveis no Windows;
- GPU: não medida, pois o caminho atual de calibração Qt/QGraphicsView não possui contador GPU integrado;
- percentis registrados: p50, p95, p99 e pior amostra.

O modo `shared` usa um único asset de teste reutilizado pelos objetos. O modo `unique` usa um asset determinístico por objeto para representar o custo de uma cena com referências distintas. Os assets são fixtures de calibração e não são assets de produto.

As operações medidas foram: `serialize`, `load_validate`, `save_atomic_recovery`, `reload`, `edit_history`, `preview_sync`, `export_generic`, `export_godot` e `export_unity`.

## 3. Resultado de execução

| Verificação | Resultado |
|---|---:|
| Status do relatório | `PASS` |
| Workloads concluídos | 8/8 |
| Erros de workload | 0 |
| Timing com `tracemalloc` | `False` |
| Determinismo da serialização da cena | 8/8 |
| Determinismo do export genérico | 8/8 |
| Determinismo do export Godot | 8/8 |
| Determinismo do export Unity | 8/8 |
| GPU | `not_measured` |
| Referência de frame | 16,7 ms para 60 FPS; não medida por esta calibração |

Todos os hashes e tamanhos de cena/exportação de cada workload estão preservados no relatório JSON canônico. As repetições produziram bytes iguais em todos os casos.

## 4. Timing — p95 em milissegundos

Os valores abaixo são p95; o relatório JSON também preserva p50, p99, pior amostra e contagem de 50 amostras para cada operação.

| Workload | Cena (bytes) | Serialize | Load/validate | Save atomic/recovery | Reload | Edit/history | Preview sync | Export genérico | Export Godot | Export Unity |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| shared:64 | 39.563 | 2,20 | 3,27 | 22,39 | 3,08 | 5,77 | 11,11 | 21,27 | 20,97 | 21,45 |
| shared:128 | 77.784 | 4,38 | 4,17 | 26,44 | 4,23 | 11,65 | 19,08 | 30,67 | 30,39 | 30,81 |
| shared:256 | 154.426 | 8,52 | 8,40 | 38,99 | 8,33 | 28,80 | 35,90 | 49,18 | 49,18 | 52,58 |
| shared:512 | 307.600 | 17,28 | 15,85 | 53,74 | 15,93 | 60,94 | 75,59 | 97,61 | 96,05 | 95,30 |
| unique:64 | 51.725 | 2,68 | 82,10 | 23,47 | 84,16 | 7,02 | 111,44 | 103,09 | 102,64 | 102,29 |
| unique:128 | 102.298 | 4,93 | 167,85 | 27,84 | 165,67 | 12,96 | 223,19 | 199,03 | 198,80 | 203,12 |
| unique:256 | 203.644 | 9,64 | 341,62 | 36,19 | 337,17 | 31,94 | 443,58 | 393,17 | 381,83 | 381,67 |
| unique:512 | 406.226 | 19,21 | 678,95 | 59,75 | 669,89 | 67,15 | 908,37 | 756,02 | 749,21 | 766,44 |

## 5. Memória — observação inicial/final

As variações abaixo são observacionais dentro do processo de calibração; não constituem, isoladamente, um veredito de leak. O relatório preserva os valores absolutos inicial/final, pico e crescimento do `tracemalloc`.

| Workload | Working Set inicial → final | Δ Working Set | Private Bytes inicial → final | Δ Private Bytes | Pico Python | Crescimento Python |
|---|---:|---:|---:|---:|---:|---:|
| shared:64 | 63.418.368 → 65.257.472 | +1.839.104 | 39.137.280 → 41.459.712 | +2.322.432 | 1.578.752 | +594.145 |
| shared:128 | 66.920.448 → 67.899.392 | +978.944 | 42.876.928 → 43.069.440 | +192.512 | 2.041.170 | +1.082.647 |
| shared:256 | 72.851.456 → 74.723.328 | +1.871.872 | 49.041.408 → 49.905.664 | +864.256 | 3.958.172 | +2.063.552 |
| shared:512 | 81.342.464 → 89.104.384 | +7.761.920 | 57.188.352 → 65.568.768 | +8.380.416 | 7.796.396 | +4.025.865 |
| unique:64 | 85.073.920 → 85.467.136 | +393.216 | 63.455.232 → 63.852.544 | +397.312 | 3.669.217 | +2.581.291 |
| unique:128 | 85.409.792 → 86.216.704 | +806.912 | 61.915.136 → 62.914.560 | +999.424 | 2.318.848 | +1.220.087 |
| unique:256 | 88.526.848 → 87.216.128 | -1.310.720 | 65.216.512 → 63.954.944 | -1.261.568 | 4.530.770 | +2.352.800 |
| unique:512 | 91.570.176 → 97.886.208 | +6.316.032 | 67.899.392 → 73.547.776 | +5.648.384 | 8.938.632 | +4.593.788 |

## 6. Findings de engenharia

1. O fluxo de medição é reprodutível e não apresentou erros, nem alteração de bytes entre repetições.
2. `shared:512` já apresenta custo elevado em `edit_history` (p95 60,94 ms), `preview_sync` (75,59 ms) e exportação (aproximadamente 95–98 ms). Como `preview_sync` é uma operação de sincronização completa, esse número não deve ser convertido diretamente em FPS; ele é, porém, evidência suficiente para priorizar a investigação de rebuild/paint no preview.
3. O modo `unique` evidencia um caso de carga mais severa: em 512 objetos, `load_validate` p95 678,95 ms, `preview_sync` p95 908,37 ms e exportação genérica p95 756,02 ms. Isso justifica separar custo de assets distintos do custo estrutural de objetos antes de qualquer otimização.
4. A memória do processo cresce observacionalmente nos maiores workloads, com variações de aproximadamente 5,6–8,4 MiB no Working Set/Private Bytes entre os checkpoints de 512 objetos. Isso requer uma série dedicada de repetição/estabilização antes de qualquer conclusão de leak.
5. O profiling anterior converge com a calibração: cópia profunda no histórico, rebuild/paint/visibilidade do preview e serialização/validação/exportação são as áreas prioritárias. Os perfis preservados são `artifacts/p2d05/profile-p2d05-512.prof`, `artifacts/p2d05/profile-preview-512.prof` e `artifacts/p2d05/profile-gesture-512.prof`.

## 7. Limites e decisões preservadas

- Nenhum orçamento de operação foi declarado aprovado por esta evidência.
- Não houve medição de GPU; portanto não há base para afirmar gargalo ou ganho de GPU.
- Não houve autorização para paralelizar, instanciar, introduzir culling ou alterar o modelo de dados; essas técnicas permanecem condicionais a um finding e a uma decisão de escopo.
- Não há conclusão de vazamento de memória a partir destas observações.
- A próxima etapa deve começar por O-1, com uma alteração isolada e mensurável no histórico/gesto, preservando snapshot semântico, undo/redo, determinismo, thread affinity e o contrato de bytes.

## 8. Critério de encerramento O-0

O-0 é considerado tecnicamente concluído porque a matriz definida no contrato foi executada integralmente com a versão final do calibrador, o relatório canônico foi produzido, os timings foram coletados sem instrumentação de memória, a memória foi observada em etapa separada e as propriedades de determinismo foram verificadas. A aceitação de metas operacionais e a implementação O-1/O-3 permanecem etapas posteriores.
