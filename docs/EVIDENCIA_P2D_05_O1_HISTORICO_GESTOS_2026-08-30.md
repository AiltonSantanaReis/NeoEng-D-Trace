# Evidência P2D-05 — O-1 histórico e gestos

**Data:** 2026-08-30
**Lote:** P2D-05-OTIMIZAÇÃO
**Fase:** O-1 — otimização isolada de histórico/gestos
**Status:** `QUALIFICATION COMPLETE — PRECOMMIT DECISION PENDING`
**Branch:** `p2d-05-quality-hardening`
**Source commit:** `fc59ff571e4e4d99ddd40a8ec318d50b8edd77f3`
**Estado:** alteração ainda não commitada; nenhuma publicação remota realizada.

## 1. Resultado executivo

O-1 foi implementado e qualificado como uma otimização restrita ao histórico de transforms e à finalização de gestos. O caminho de preview visual não foi alterado após o A/B demonstrar regressão no fast path incremental proposto.

O resultado é tecnicamente positivo para o gargalo medido: `edit_history` usa estado delta de transforms em vez de snapshots profundos da cena inteira, e o fechamento de um gesto também registra somente os transforms afetados quando a operação permanece dentro do contrato seguro.

Não foram alterados schema, bytes de exportação, validações, limites, árvore de widgets, renderização, comportamento de preview visual ou contratos G/V/B.

## 2. Fronteira exata da implementação

Arquivo de produto alterado:

- `src/core/scene_authoring_session.py`

Arquivos de teste e medição adicionados:

- `tests/test_p2d_05_o1_history.py`
- `scripts/calibrate_p2d_05.py`
- `scripts/benchmark_p2d_05_o1_gesture.py`
- `scripts/benchmark_p2d_05_o1_gesture_finish.py`

O estado de histórico agora possui dois tipos de entrada:

1. snapshot completo (`_HistoryEntry`) para operações gerais, que continuam com a semântica anterior;
2. registro delta (`_TransformHistoryEntry`) para `translate_selected`, `transform_selected`, `update_transform` e finalização segura de gestos.

O delta armazena transforms imutáveis por ID e a seleção antes/depois. Undo e redo revalidam o documento, preservam ordem, referências, seleção e demais campos, e continuam compatíveis com entradas completas intercaladas.

Se uma operação de transform recebe ID ausente, segue pelo caminho transacional completo anterior. Se uma operação geral ou alteração de seleção ocorre durante um gesto, o gesto deixa de ser elegível ao delta e retorna ao snapshot completo. Isso evita aplicar a otimização fora das invariantes demonstradas.

O preview continua usando restauração completa do snapshot de gesto. Essa decisão é deliberada e baseada em medição, não em suposição.

## 3. Testes funcionais e regressão

Testes focais após a implementação:

```text
16 passed in 1.61s
```

Suíte completa após a implementação final:

```text
1863 passed, 2 skipped, 1 warning in 54.34s
```

Os quatro testes dedicados cobrem:

- entrada delta e round-trip de undo/redo com operação geral intercalada;
- preview de gesto com restauração completa e histórico delta no fechamento;
- fallback completo quando há operação geral dentro do gesto;
- falha de transform bloqueada sem mutação nem entrada de histórico.

Verificações estáticas do código e dos testes:

- `py_compile`: PASS;
- `flake8`: PASS;
- `black --check`: PASS;
- `isort --check-only`: PASS;
- `git diff --check`: PASS; os avisos restantes são somente de line endings já conhecidos.

## 4. Matriz de performance — `edit_history`

Comparação contra a calibração O-0 com os mesmos 8 workloads, 50 amostras por operação, 5 warm-ups e timing sem `tracemalloc`.

| Workload | O-0 p95 (ms) | O-1 p95 (ms) | Variação |
|---|---:|---:|---:|
| shared:64 | 5,77 | 2,49 | -56,84% |
| shared:128 | 11,65 | 5,47 | -53,05% |
| shared:256 | 28,80 | 11,82 | -58,96% |
| shared:512 | 60,94 | 29,82 | -51,06% |
| unique:64 | 7,02 | 2,54 | -63,86% |
| unique:128 | 12,96 | 5,49 | -57,60% |
| unique:256 | 31,94 | 11,90 | -62,75% |
| unique:512 | 67,15 | 29,79 | -55,63% |

O relatório completo pós-O-1 é `artifacts/p2d05/calibration-o1-final-20260830.json`. Ele preserva p50, p95, p99, pior amostra, erros, memória, hashes e bytes por workload.

## 5. A/B de finalização de gesto

O benchmark `artifacts/p2d05/o1-gesture-finish-ab-20260830.json` mede somente o tempo de `finish_gesture`, com o mesmo gesto preparado antes da janela cronometrada.

| Workload | Snapshot completo p95 (ms) | Delta O-1 p95 (ms) | Variação |
|---|---:|---:|---:|
| shared:64 | 1,918 | 0,039 | -97,97% |
| shared:128 | 3,657 | 0,044 | -98,81% |
| shared:256 | 8,604 | 0,052 | -99,39% |
| shared:512 | 18,554 | 0,066 | -99,65% |
| unique:64 | 2,144 | 0,042 | -98,06% |
| unique:128 | 4,255 | 0,042 | -99,01% |
| unique:256 | 12,183 | 0,059 | -99,51% |
| unique:512 | 21,089 | 0,085 | -99,60% |

O A/B teve zero erros em todos os 8 workloads. O resultado é uma comparação do custo de finalização do histórico; não é um orçamento normativo de performance.

## 6. Experimento rejeitado: restauração incremental do preview

Foi testada uma variante que restaurava somente transforms a cada chamada de preview. Ela foi rejeitada e removida porque ficou mais lenta que a restauração completa existente:

- shared:64: -13,36% de desempenho relativo;
- shared:128: -18,80%;
- shared:256: -25,19%;
- shared:512: -28,33%;
- unique:64: -18,00%;
- unique:128: -12,25%;
- unique:256: -25,66%;
- unique:512: -32,18%.

O relatório bruto preservado é `artifacts/p2d05/o1-gesture-ab-20260830.json`. A conclusão é que o `model_validate` usado pelo caminho atual é suficientemente otimizado nesse caso, enquanto a reconstrução parcial adicionava custo. O preview não foi declarado otimizado nem alterado pelo O-1.

## 7. Integridade funcional e determinismo

Na comparação O-0 versus O-1:

- diferenças de tamanho de cena: `0`;
- diferenças de bytes de cena: `0`;
- diferenças de hashes de exportação genérico, Godot e Unity: `0`;
- erros nos 8 workloads finais: `0`;
- determinismo de cena e dos três exportadores: `8/8`;
- campos Working Set e Private Bytes: presentes em `8/8` workloads.

Esses resultados confirmam que a otimização não modifica o conteúdo persistido ou exportado. A memória observada continua sendo evidência de checkpoints, não um veredito independente de vazamento.

## 8. Limites preservados

- GPU não foi medida;
- nenhum orçamento operacional foi aprovado;
- não foram introduzidos threads, GPU, culling, batching ou instancing;
- operações gerais continuam com snapshot completo;
- nenhum schema, limite, formato, validação ou contrato de engine foi alterado;
- não houve build, commit, push, merge, tag ou release neste fechamento.

## 9. Fingerprints do estado atual

Como o lote ainda está no worktree, o commit de origem permanece `fc59ff...`; o fingerprint do arquivo de produto alterado é:

```text
src/core/scene_authoring_session.py
SHA-256: 9e5e8ddd5277450163681b4d90127cba8594ac54d8645dc5f3dbc97726d094c0
```

Os fingerprints dos testes e do benchmark de finalização estão registrados no log operacional da execução. Antes do commit, a fronteira deve ser revista para confirmar que apenas os arquivos previstos serão staged.

## 10. Disposição

`O-1` está qualificado localmente e pronto para a etapa PRECOMMIT. A decisão seguinte é revisar a fronteira final, executar os gates obrigatórios do lote, e somente com `PRECOMMIT ACCEPT` consolidar o commit. O-2 e O-3 permanecem pendentes e não foram antecipados.
