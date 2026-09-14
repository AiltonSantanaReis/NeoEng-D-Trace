# Evidência — soak controlado de memória e disponibilidade GPU pós-E13

**ID:** `EVD-POST-E13-SOAK-MEMORIA-GPU-CONTROLADO-20260913`
**Status do soak de memória:** `PASS`
**Status do workload GPU controlado:** `PASS` no escopo CUDA controlado
**Status GPU do caminho QGraphicsView:** `NOT_APPLICABLE`
**Data:** 2026-09-13
**Commit da fonte montada:** `e727e9d470b3256b05800cda59d9aa2401a1959f`
**Decisão autorizadora:** `docs/evidence/DECISAO_POST_E13_LIMITE_PERFORMANCE_SOAK_CONTROLADO_20260913.md`

## Governança e escopo

A governança ativa foi relida integralmente antes da execução. O checkpoint de
retorno permanece preservado em `checkpoint/post-e13-pre-gizmo-20260912`; o
editor canônico, a produção e os thresholds não foram alterados pelo soak.

Esta evidência cobre a lacuna de memória longa do requisito
`REQ-POST-E13-VIEWPORT-SCALE-20260913`. O teste de symlink não foi repetido, pois
seu pacote definitivo já está qualificado e a decisão de reexecução não mudou.

## Ambiente controlado

- Docker Desktop Server `29.5.3`, imagem local
  `neoeng-qt-linux:latest`, ID
  `sha256:b5f129e4a2c8a1e857518d0439b949bcb5773e0c09c2c867af6d458348ed2bb1`;
- Linux WSL2 `5.15.167.4-microsoft-standard-WSL2`, x86_64, Python `3.11.9`;
- PySide6 real, `QT_QPA_PLATFORM=offscreen` e `QT_OPENGL=software`;
- rede `none`, checkout montado como somente leitura, saída montada
  separadamente, `8 GiB`, `4 CPUs`, `--cap-drop ALL`,
  `no-new-privileges`, `pids-limit 512` e `tmpfs` somente para temporários;
- o container não possui `git`; por isso o relatório interno informa
  `source_commit=unavailable`. O SHA exato da fonte foi capturado antes/depois
  no host e permaneceu inalterado em `e727e9d...`.

Comando lógico:

```text
python scripts/benchmark_p2d_05_o2_preview.py
  --iterations 50 --warmup 5 --memory-iterations 250
  --object-counts 64,128,256,512 --asset-modes shared,unique
  --expected-source-commit unavailable --output /out/report.json
```

O produtor foi executado sem filtros de carga: `24` workloads regulares mais
`2` workloads estruturais de `512` objetos em `1920×1080`, totalizando `26`
cargas e `6.500` ciclos de refresh de memória.

## Resultado observado

Relatório final:
`artifacts/audit-post-e13-performance-soak-controlled-20260913-r2/report.json`

SHA-256 do relatório:
`662334FD286684FEE5C808EC896159E85AC02938DEAC40F4AA0EA50166AF9DD3`

| Critério | Resultado |
|---|---:|
| Status do produtor | `PASS` |
| Workloads | `26/26` |
| Erros de operação | `0` |
| Determinismos falsos | `0` |
| Ciclos por workload | `250` |
| RSS/private inicial e final disponíveis | `26/26` |
| Delta RSS por workload | `-11.534.336` a `+40.960` bytes |
| Maior RSS final observado | `315.854.848` bytes |
| Crescimento `tracemalloc` | `63.984` a `197.782` bytes |
| Maior pico `tracemalloc` | `420.578` bytes |

O observador Linux usa `/proc/self/smaps_rollup`: `Rss` para working set e a
soma de `Private_Clean`/`Private_Dirty` para memória privada. Deltas negativos
representam liberação de memória/cache após GC e não foram convertidos em erro.
As observações continuam sendo evidência de estabilidade deste ciclo, não uma
prova isolada de ausência de vazamento em todo sistema operacional.

O teste focado do contrato passou com `1 passed` e zero warnings quando o cache
foi direcionado ao `tmpfs`. O helper Windows existente permaneceu preservado;
hashes dos produtores usados no pacote:

- `scripts/calibrate_p2d_05.py`:
  `242DD241CF40D0CE9F9A063AA03F9BBCA5CF7A5DC476471CD3D66899C06AA844`;
- `scripts/benchmark_p2d_05_o2_preview.py`:
  `1F02A2424508BFBE5522D23C7300FD2094CCD8CB98E399EC7695394F6A143AC1`;
- `tests/test_post_e13_process_memory.py`:
  `186A2CA4ABB8B43C9658D76BDB54255154547718871164FF3726E058215F5EB5`.

## GPU controlada — workload de driver

Uma qualificação separada foi executada em `python:3.11-slim`, com a RTX 3070 Ti
transportada para o container por `--gpus all`. O runner hashado executou uma
alocação CUDA de 256 MiB e repetiu `cuMemsetD8` síncrono por 20 segundos,
enquanto `nvidia-smi` coletava telemetria a cada 0,5 segundo.

Relatório:
`artifacts/audit-post-e13-performance-gpu-controlled-20260913-r1/report.json`

SHA-256 do relatório:
`E0B368982ED14A69A21410B1480E31799552857AB6CE14590CB96E5F1B98423E`

Commit que promoveu runner, relatório e ponteiros:
`8db308df6bcef380a22ef362f28b6d403f9032a7`.

| Critério | Resultado |
|---|---:|
| Status | `PASS` no escopo CUDA controlado |
| Driver CUDA | `cuInit`, contexto, alocação e liberação: `0` |
| Dispositivo | `NVIDIA GeForce RTX 3070 Ti`, 1 dispositivo |
| Operações | `36.408` em `20,0 s` |
| Amostras | `38`, sem erros de telemetria |
| Utilização GPU | `37%`–`91%` |
| Memória observada | `2865 MiB` de `8192 MiB` |
| Utilização de memória | `34%`–`100%` |

O container foi executado sem rede, com filesystem read-only, workspace read-only,
limite de memória de 1 GiB e `pids-limit=128`. As duas tentativas preliminares
contra a imagem do produtor Qt terminaram com exit `127` porque ela não expõe
`python` nem `python3` no entrypoint; nenhum workload foi executado nessas
tentativas. A execução corrigida usou a imagem Python já presente localmente e
passou; os exits preliminares ficam registrados como limitação do harness.

## GPU do viewport — limitação objetiva

O workload acima prova transporte CUDA, alocação, execução e telemetria reais no
ambiente controlado. Ele não mede a renderização do editor. O produtor Qt
continua configurado com `QT_QPA_PLATFORM=offscreen` e `QT_OPENGL=software`, e
o próprio relatório registra:

```text
gpu.status=not_measured
gpu.reason=no GPU counter is part of the controlled QGraphicsView path
```

Assim, o contador de frames/GPU do viewport é `NOT_APPLICABLE` neste ambiente,
com justificativa e autorização formal. O workload GPU dedicado é um PASS
separado e não é promovido a equivalência de renderer/FPS. A probe CuPy anterior
comprovou apenas o kernel opcional X-Ray em GPU; ela não autoriza tornar CuPy
dependência oficial.

## Regra de reexecução

Reexecutar o soak de memória ou o workload GPU somente se o helper/runner, o
produtor, o contrato medido, a imagem/digest/ambiente controlado, o driver ou o
caminho real do viewport mudar. Alterações apenas de documentação, localização,
assets ou UI sem impacto no caminho medido não exigem repetição.
