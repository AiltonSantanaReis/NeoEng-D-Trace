# Etapa 0.5 — Plano de restauração e reconciliação dos testes

## 1. Problema confirmado

O commit HEAD rastreava 24 arquivos com 196 testes detectáveis.

A árvore atual apresenta 36 testes detectáveis.

A diferença não deve ser tratada como simples limpeza. Os testes históricos
registram contratos, casos extremos e comportamentos que podem ter sido
alterados.

## 2. Resultado da execução histórica não gráfica

Foram recuperados do bundle 16 arquivos sem dependência direta de Qt,
totalizando 113 testes.

Resultado:

- 100 testes coletados;
- 92 aprovados;
- 8 falharam;
- 13 ficaram bloqueados durante a coleta por incompatibilidade de API SAT.

### Falhas que exigem decisão

| Arquivo | Falhas | Observação inicial |
|---|---:|---|
| `test_convex_decomp.py` | 1 | Polígono côncavo não foi decomposto como a expectativa antiga |
| `test_edge_utils.py` | 1 | Resultado atual usa `float32`; histórico exigia `float64` |
| `test_exporters.py` | 4 | Rotação do atlas mudou e metadados de engines divergiram |
| `test_handle_command.py` | 1 | Fixture antiga cria polígono colinear hoje rejeitado |
| `test_mask_utils_curvature.py` | 1 | Simplificação atual manteve menos pontos que o limite antigo |

### Teste SAT bloqueado

`test_sat2d.py` importa:

- `project`;
- `polygon_edges`.

A API atual expõe:

- `project_polygon`;
- `overlap_intervals`;
- `sat_polygon_vs_polygon`.

A incompatibilidade pode ser resolvida por alias de compatibilidade ou migração
do teste, mas nenhuma decisão será aplicada sem verificar chamadas externas e o
contrato pretendido para polígonos vazios e degenerados.

## 3. Falha não significa automaticamente regressão

Exemplos:

- o teste antigo de rotação esperava dois atlas porque a rotação ainda não
  funcionava; produzir um atlas pode ser melhoria;
- o teste de alça usava três pontos colineares, hoje rejeitados pela validação;
- `float32` pode ser uma otimização válida, desde que o contrato e a precisão
  sejam definidos.

Por outro lado, ausência de campos específicos de Godot, Unity e Phaser pode
representar perda real de interoperabilidade.

Cada falha será classificada como:

1. regressão;
2. melhoria com teste obsoleto;
3. mudança de contrato aprovada;
4. teste inválido;
5. comportamento ainda indefinido.

## 4. Testes Qt pendentes

Existem 83 testes históricos que dependem diretamente de PySide6:

- export preview;
- laço livre;
- laço magnético;
- Mask Viewer;
- caneta;
- laço poligonal;
- seleção retangular e elíptica;
- integração das ferramentas.

Eles deverão ser executados no Windows/Python 3.11 antes do baseline definitivo.

## 5. Método seguro de restauração

Os testes históricos não serão copiados diretamente para `tests/`, pois isso
poderia quebrar imediatamente a coleta oficial.

Sequência:

1. extrair os testes do bundle para uma área de quarentena versionada;
2. manter o commit de origem de cada arquivo;
3. executar em suíte separada;
4. registrar incompatibilidades;
5. adaptar um teste por vez;
6. mover para a suíte oficial somente quando a expectativa estiver aprovada;
7. nunca apagar o teste original sem registrar seu substituto.

## 6. Estrutura futura sugerida

```text
quality/
├── legacy_tests/
│   ├── README.md
│   └── tests/
├── fixtures/
├── golden/
└── reports/
```

O `pytest` oficial continuará coletando apenas `tests/` até a reconciliação.

## 7. Critério de equivalência

Um teste histórico poderá ser substituído quando o novo conjunto comprovar:

- o mesmo requisito;
- casos positivos e negativos equivalentes;
- erros e limites equivalentes;
- undo/redo quando aplicável;
- comportamento em arquivos antigos;
- comportamento no Windows;
- evidência da relação entre o teste antigo e o novo.

## 8. Critério de conclusão

A reconciliação termina quando os 196 testes históricos estiverem classificados,
mesmo que nem todos permaneçam ativos.

Nenhum teste será removido apenas para aumentar a taxa de aprovação.
