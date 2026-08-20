# Evidência pré-merge — Etapa 5 do ADR de runtime: pós-processamento

**Estado:** IMPLEMENTAÇÃO LOCAL VALIDADA; NÃO APROVADA PARA MERGE
**Data:** 20 de agosto de 2026
**ADR vigente:** `docs/ADR_RUNTIME_CENARIOS_EFEITOS_2026-08-20.md`
**Base:** `main` no merge `27b2baffa7701ae5ad90f458c3ba5923a030157f`
**Branch:** `main`

## Escopo executado

Foi implementado o sidecar versionado `runtime.post_processing`, separado do
manifesto `.ndtproj` e do contrato de cenário existente. O escopo real desta
execução contém:

- contrato canônico UTF-8/LF com schema e algoritmo versionados;
- vínculo SHA-256 ao manifesto de cenário;
- cadeia ordenada e determinística de `exposure`, `grayscale`, `tint`,
  `vignette` e `box_blur`;
- limites explícitos de efeitos, pixels, raio de blur e exposição;
- preservação do canal alfa;
- estado habilitado/desabilitado observável;
- backend nativo limitado ao preview CPU determinístico;
- fallback explícito `cpu-preview`, `disable` ou `reject` para backends sem
  adaptador nativo;
- escrita atômica com preservação dos bytes anteriores em falha;
- capacidade `runtime.post_processing` registrada no host base;
- auditor reproduzível fail-closed.

Não foi declarado suporte nativo de Godot, Unity, GPU, VRAM, driver, FPS ou
rasterização de pós-processamento nesta etapa. Esses comportamentos permanecem
`NÃO TESTADOS` ou fora do escopo, conforme aplicável.

## Arquivos candidatos e hashes do worktree

Os hashes abaixo foram calculados sobre os bytes do worktree candidato, antes
de commit. Eles não substituem a validação posterior por blobs Git.

| Arquivo | Bytes | SHA-256 |
|---|---:|---|
| `src/runtime/post_processing.py` | 20888 | `b93fea10a1d9f9f025d7211627cb1ecd6e15cd78a9737f5516549d1cdfef2c8c` |
| `src/runtime/__init__.py` | 7292 | `6fd12f162d9cf31f9a8de258292bd1ddb5ca218157e44e50f610aa4226efc2ed` |
| `src/runtime/scene_runtime.py` | 18193 | `40ae80628a1bcbbb79fe1769867d2c506419c1ea6f0ff6009a95aece3e646a39` |
| `tests/test_stage5_runtime_post_processing.py` | 8485 | `2c9820699e0003d9da6e800db110d31b26bfa310d20e57aa732d1191832ab95f` |
| `scripts/audit_runtime_post_processing_phase5.py` | 11108 | `145ed4c628348f02eb90b3de836af2b7e51d73e2c2d2b0f58e3f8e4128bd554b` |

## Testes e gates executados

Comandos reais no Windows, usando Python 3.11.9 do ambiente do projeto:

```text
python -m pytest -q tests/test_stage5_runtime_post_processing.py
9 passed

python -m pytest -q tests/test_stage1_runtime_base.py tests/test_stage2_runtime_lighting.py tests/test_stage2_runtime_lighting_hardening.py tests/test_stage3_runtime_shaders.py tests/test_stage4_runtime_particles.py tests/test_stage5_runtime_post_processing.py
82 passed

python -m pytest -qq
1492 passed, 2 skipped

python -m pytest -qq --cov=src --cov-branch --cov-fail-under=90 --cov-report=term --cov-report=xml
1492 passed, 2 skipped; total coverage 91.00%; branch policy passed

python tools/check_coverage_policy.py coverage.xml
PASS

python -m compileall -q -f app.py src tests pack_for_ai.py tools
PASS

black --check; isort --check-only; flake8; mypy
PASS

pip-audit
PASS — no known vulnerabilidades; pacote local não publicado no PyPI foi
classificado pelo próprio auditor como não auditável por esse motivo

bandit -q -r src -lll
PASS
```

## Auditoria reproduzível

Comando:

```text
python scripts/audit_runtime_post_processing_phase5.py --output <novo-diretorio-temporario>
```

Resultado observado no worktree modificado:

- `canonical_sidecar_roundtrip`: PASS;
- `source_binding_is_hash_bound`: PASS;
- `ordered_effects_are_deterministic`: PASS;
- `disabled_effect_is_reported`: PASS;
- `alpha_is_preserved`: PASS;
- `limits_are_enforced`: PASS;
- `fallback_is_explicit`: PASS;
- `atomic_persistence_preserves_previous_bytes`: PASS;
- `privacy`: PASS;
- `source_tree_clean`: FAIL, porque a implementação ainda não estava
  versionada em um commit candidato.

O relatório geral foi corretamente `FAIL`. Esse resultado não foi alterado,
mascarado ou convertido em PASS. A auditoria deverá ser repetida depois do
checkpoint versionado e novamente sobre os bytes rastreados pelo Git.

## Falha encontrada e corrigida durante a execução

O primeiro teste da etapa usava `model_copy(update=...)` esperando revalidação
do Pydantic. A execução real mostrou que esse método não revalida o modelo. O
teste foi corrigido para construir o documento pelo construtor estrito; a nova
execução passou sem alterar qualquer limiar ou regra de validação.

## Limitações e decisão

O backend CPU é uma capacidade real e testada de preview estrutural, não uma
promessa de pós-processamento nativo nas engines. Não houve execução Godot ou
Unity específica para esse recurso, pois não existe adaptador de pós-processamento
implementado nesta etapa. Não há evidência de regressão reproduzida nas
Etapas 1–4: a suíte de não regressão passou com 82 testes.

**Decisão:** `PARCIAL / NÃO APROVADA`. A implementação local e os testes
funcionais passaram, mas faltam checkpoint versionado, auditoria com árvore
limpa, manifestos de evidência por blobs Git, revisão documental, CI, PR e
validação pós-merge. Nenhum merge ou release é autorizado por este documento.
