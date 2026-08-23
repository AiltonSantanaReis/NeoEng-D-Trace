# Etapa 2 — Matriz DPI da biblioteca de ícones

Status local: **PASS**

A matriz executa a MainWindow e uma galeria do catálogo vetorial em processos Qt separados nas escalas 100%, 125%, 150% e 200%.

| Escala | Fator | Worker | Auditor visual |
|---:|---:|---|---|
| 100% | 1.0 | 0 | PASS |
| 125% | 1.25 | 0 | PASS |
| 150% | 1.5 | 0 | PASS |
| 200% | 2.0 | 0 | PASS |

O relatório JSON, os manifests, as capturas, as galerias e os logs são indexados por SHA-256 no `artifact-index.json`.

A árvore modificada durante a coleta não é tratada como validação pós-commit; o gate Git-blob e o CI permanecem obrigatórios.
