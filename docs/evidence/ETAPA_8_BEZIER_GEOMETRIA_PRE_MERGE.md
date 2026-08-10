# Evidência — Etapa 8: Bézier e geometria pré-merge

## Identificação

- commit técnico: `d11cd3dc0bd0063e325a53dd30fc439feda9dd24`;
- data: 10 de agosto de 2026;
- branch: trabalho local da Etapa 8, não integrada à `main`;
- estado: validação local aprovada, ainda não integrada;
- `R-007`: aberto até merge e CI pós-merge Linux/Windows;
- release: não aprovada.

## Ambiente

- Windows build 26200;
- Python 3.11.9;
- pytest 9.1.1 e pytest-cov 7.1.0;
- dependências resolvidas pelo `poetry.lock` com SHA-256
  `b7e94da9a7074347d5a4432cc68ae1f59953af60d1aa62dc970ee7f98579d7b7`.

## Objetivo e escopo

Validar matematicamente o núcleo Bézier e corrigir a triangulação de polígonos
côncavos sem depender do backend opcional. O escopo cobre entradas malformadas,
continuidade, amostragem determinística, degeneração, orientação, área,
convexidade, índices produzidos pelo backend e reconciliação estrita dos testes
históricos.

Não pertencem a este pacote a auditoria ampla de APIs da Etapa 9, os limites
operacionais da Etapa 12, a refatoração Qt da Etapa 13 nem a release da Etapa 14.

## Reprodução e causa raiz

Com o backend Earcut desativado, o fallback anterior não verificava se o vértice
candidato era convexo e presumia orientação anti-horária. Nos fixtures executados,
o mesmo polígono invertido produziu soma de áreas `6` para área de entrada `5` e
`14` para área de entrada `10`. Portanto, a implementação era dependente do
sentido e podia devolver triângulos sobrepostos.

A correção:

- canonicaliza coordenadas finitas e orientação anti-horária;
- rejeita vértices repetidos e área nula;
- exige convexidade positiva antes de remover uma orelha;
- exige exatamente `n - 2` triângulos não degenerados;
- compara a soma das áreas com a área do polígono;
- rejeita índices malformados ou fora do intervalo vindos do backend opcional;
- usa `float64` quando disponível e mantém compatibilidade controlada com
  `float32`.

O fixture legado chamado de “L shape” possui uma aresta vertical sobreposta a
outra aresta. Ele agora é rejeitado de forma controlada. As duas divergências
históricas correspondentes foram registradas por ID e assinatura exatos, com
testes substitutos, sem alterar os snapshots legados.

## Entradas e hashes

| Arquivo | Bytes | SHA-256 |
|---|---:|---|
| `src/physics/convex_decomp.py` | 13284 | `414030f3dc13cb16eeced86230a84fda8a7aedde75fe0d74be64bb96807f2e6d` |
| `src/core/bezier_geometry.py` | 9303 | `eba16963ed721814a46d100bf0d8d0a33b04c07030d6daac36e40112b6773881` |
| `tests/test_stage_8_bezier_geometry.py` | 8301 | `e9f60d15adebfb232b5ed192f5b8d837f8763f2cda6f63f4747765f166ca7372` |
| `quality/legacy_tests/reconciliation.json` | 20210 | `296ca97f07341eedd99ef8aae57d7053fe6110bdddbc01a55b872d3bf20fb493` |
| `coverage.xml` da execução técnica com 660 testes | 549554 | `676ead8155d760fcc238bad88b532b4af6c55ff2aec46321802f3e4898c3e69b` |
| `coverage.xml` do pacote pré-merge com 661 testes | 549554 | `9d196edffe77a0c6a86ac16f030a94402e45bd25685be5bf5a265e3ed3a6fa81` |

`coverage.xml` é resultado bruto local e não é usado como prova remota; o CI deve
publicar o relatório ligado ao HEAD da PR.

## Comandos executados

```text
python -m compileall -q src tests tools app.py pack_for_ai.py
flake8 src tests tools app.py pack_for_ai.py
black --check --diff src tests tools app.py pack_for_ai.py
isort --check-only --diff src tests tools app.py pack_for_ai.py
mypy src
pip-audit
bandit -q -r src -lll
pytest tests/test_stage_8_bezier_geometry.py tests/test_stage_5_package_5c_bezier_history.py tests/test_stage_0_5_2e_core.py --cov=src.core.bezier_geometry --cov=src.physics.convex_decomp --cov-branch --cov-report=term-missing
pytest --cov=src --cov-branch --cov-fail-under=62 --cov-report=term --cov-report=xml
python tools/run_legacy_tests.py --group all
python tools/baseline_integrity.py --verify
```

## Resultados locais

- testes focais: `125 passed`, zero falhas, skips ou bloqueios;
- suíte oficial no commit técnico: `660 passed`; pacote pré-merge: `661 passed`; zero falhas, skips ou bloqueios;
- suíte legada preservada: `196` executados, `27/27` divergências previstas
  reconciliadas, zero inesperadas e zero ausentes;
- mypy: zero erros em 66 arquivos;
- Flake8, Black, isort, compilação e Bandit de severidade alta: aprovados;
- `pip-audit`: nenhuma vulnerabilidade conhecida nas dependências auditáveis; o
  pacote local do projeto não existe no PyPI e foi explicitamente informado como
  não auditável;
- cobertura global combinada exibida pelo pytest-cov: `68.98%`;
- cobertura global XML: `72.95%` de linhas e `56.48%` de branches;
- núcleo geométrico combinado: `95.59%` de linhas e `93.29%` de branches;
- `bezier_geometry.py`: 122/129 linhas e 56/58 branches;
- `convex_decomp.py`: 203/211 linhas e 97/106 branches.

## Falhas encontradas durante o gate

1. O primeiro gate integral falhou porque um teste documental congelava a
   reconciliação em 26 entradas. O teste foi corrigido para exigir IDs únicos e
   a presença explícita das duas divergências geométricas. A repetição integral
   passou com `660/660`; após adicionar o contrato documental pré-merge, o
   pacote final passou com `661/661`.
2. A revisão do diff encontrou falta de validação de índices fora do intervalo
   produzidos pelo backend opcional. A entrada agora falha fechada com
   `ValueError` e possui regressão dedicada.

## Limitações e riscos residuais

- a meta global final de 90% de linhas e 85% de branches não foi atingida;
- `R-003` permanece aberto;
- esta execução local não substitui CI Linux/Windows nem validação pós-merge;
- `R-007` não pode ser encerrado antes da integração e do CI pós-merge;
- nenhuma release foi construída, instalada ou aprovada neste pacote.

## Decisão

**APROVADO LOCALMENTE / NÃO INTEGRADO.** O pacote pode seguir para PR e CI. A
Etapa 8 e `R-007` permanecem abertos até merge e validação pós-merge do commit
resultante. `RELEASE_APPROVED=NO`.
