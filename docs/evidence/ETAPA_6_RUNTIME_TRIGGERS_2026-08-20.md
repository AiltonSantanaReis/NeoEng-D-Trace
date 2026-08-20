# Evidência pré-merge — Etapa 6 do ADR de runtime: triggers

**Estado:** IMPLEMENTAÇÃO LOCAL VALIDADA; AUDITORIA LIMPA PASS; AGUARDANDO CI E PR
**Data:** 20 de agosto de 2026
**ADR vigente:** `docs/ADR_RUNTIME_CENARIOS_EFEITOS_2026-08-20.md`
**Base:** checkpoint `67db343eef4adeb084eb96fa8b372ad9c7fa35cb` em `main`
**Branch:** `main`

## Escopo executado

A Etapa 6 foi iniciada no escopo exato do ADR de runtime: sidecar versionado
`runtime.triggers`, separado do `.ndtproj` e dos contratos autorais existentes.
A implementação local contém:

- contrato canônico UTF-8/LF, schema, API e algoritmo versionados;
- vínculo SHA-256 ao export de cenário-runtime;
- zonas AABB determinísticas com prioridade e ordem estável;
- condições `eq`, `neq`, `gt`, `gte`, `lt`, `lte`, `truthy` e `falsy`;
- eventos `enter`, `stay` e `exit`, incluindo saída quando uma observação deixa
  de existir;
- limites explícitos para IDs, zonas, eventos, payloads, passo fixo,
  catch-up e replay;
- ciclo de vida explícito `ready`, `running`, `paused` e `stopped`;
- cancelamento antes do commit lógico, sem mutação parcial;
- replay determinístico vinculado ao hash do documento e à versão do algoritmo;
- persistência atômica com preservação dos bytes anteriores em falha;
- capacidade `runtime.triggers` anunciada pelo host;
- auditor fail-closed reproduzível, sem asserções permissivas ou mascaramento.

Não foi alterado silenciosamente o schema `.ndtproj`, o editor principal, os
exportadores, o gizmo, Undo/Redo ou qualquer adaptador de engine.

## Bytes candidatos do worktree

Os hashes abaixo são dos bytes locais antes do checkpoint. Eles não substituem
a validação posterior pelos blobs efetivamente versionados pelo Git.

| Arquivo | Bytes | SHA-256 |
|---|---:|---|
| `src/runtime/triggers.py` | 31430 | `0c2d016f900e0f34557a0135926d77bc354e50c40815b87dda5f30285ca0a1ae` |
| `src/runtime/__init__.py` | 9075 | `5313c3adf5aebdd56ba21e59747cb2b578b9baea59ade8456b6aefd9a5f8f4f9` |
| `src/runtime/scene_runtime.py` | 18222 | `b931346c869d9a603e53b8407a5443c4c1c8b7013dd4eb27baf901fd380c49b0` |
| `tests/test_stage6_runtime_triggers.py` | 17479 | `1ca9ce9ea6c8ba266428e10e1198947bbebf533b942a6aa6687eeaa8eb18de9f` |
| `scripts/audit_runtime_triggers_phase6.py` | 13573 | `a7094789cd58e259980a1fb5b36e1bab64604607127089f307405bc3ea9cb53d` |
| `docs/ADR_RUNTIME_CENARIOS_EFEITOS_2026-08-20.md` | 12162 | `d867b5c27015cc25c79928d96c953739a1b204338ff516c6cac4253281f8f305` |

## Testes e gates locais

Execuções reais no Windows, com Python 3.11.9 do ambiente Poetry:

```text
python -m pytest -q tests/test_stage6_runtime_triggers.py
28 passed

python -m pytest -q tests/test_stage1_runtime_base.py tests/test_stage2_runtime_lighting.py tests/test_stage2_runtime_lighting_hardening.py tests/test_stage3_runtime_shaders.py tests/test_stage4_runtime_particles.py tests/test_stage5_runtime_post_processing.py tests/test_stage6_runtime_triggers.py
95 passed

python -m pytest -qq
1520 passed, 2 skipped

python -m pytest -qq --cov=src --cov-branch --cov-fail-under=90 --cov-report=term --cov-report=xml
1520 passed, 2 skipped; total coverage 91.09%; branch-rate do XML: 85.21%

python tools/check_coverage_policy.py coverage.xml
PASS — total lines >= 90%; total branches >= 85%; measurable modules >= 30%

black --check; isort --check-only; flake8; mypy src; mypy auditor
PASS

python -m compileall -q -f app.py src tests pack_for_ai.py tools scripts/audit_runtime_triggers_phase6.py
PASS

pip-audit
PASS — nenhuma vulnerabilidade; o pacote local não publicado no PyPI foi
classificado pelo próprio auditor como não auditável por essa ferramenta

bandit -q -r src -lll
PASS
```

Os dois skips são os skips históricos autorizados para os testes de symlink no
Windows; não foram criados pela Etapa 6.

## Auditoria reproduzível

Comando:

```text
python scripts/audit_runtime_triggers_phase6.py --output <novo-diretorio>
```

Resultado no worktree modificado:

- `source_tree_clean`: FAIL legítimo, pois a implementação ainda não estava
  versionada em um checkpoint;
- todos os 12 checks funcionais: PASS;
- `privacy`: PASS;
- `status` geral: FAIL exclusivamente por `source_tree_clean`.

Esse FAIL não foi convertido em PASS. Após os checkpoints `6ab5b5d` e
`67db343`, o auditor foi executado novamente em árvore limpa e passou com os 13
checks, incluindo `source_tree_clean=true`:

- relatório: `status=PASS`;
- commit observado: `67db343eef4adeb084eb96fa8b372ad9c7fa35cb`;
- branch: `main`;
- árvore limpa: `true`;
- checks funcionais: todos `true`;
- privacidade: `true`.

A execução limpa não substitui CI, PR, merge ou validação pós-merge.

## Correções descobertas durante a validação

A execução real encontrou e corrigiu três problemas antes desta evidência:

1. erros de `NaN`, observações não iteráveis e contextos não serializáveis agora
   atravessam a fronteira como erros controlados do runtime;
2. saída de observação ausente gera `exit` determinístico e não remove estado de
   forma silenciosa;
3. o auditor deixou de aceitar replay apenas por possuir eventos; ele compara
   exatamente os eventos registrados com os eventos reproduzidos.

Cada correção foi seguida por novos testes negativos, lint, tipagem e execução da
suíte correspondente.

## Limitações declaradas

- O componente implementado é um dispatcher determinístico de CPU; não é engine
  gráfica, física ou de rede.
- Adaptadores de triggers para Godot e Unity não estão implementados nesta fase.
- Streaming, entrega de eventos por rede, sincronização multiplayer e agenda de
  frames específica de engine permanecem fora da Etapa 6.
- A fase não está aprovada nem integrada até passar por blobs Git, baseline,
  árvore limpa, evidências hashadas, CI, PR, merge normal e validação pós-merge.

## Artefatos versionados da auditoria limpa

Pacote: `docs/evidence/artifacts/runtime-triggers-phase6-2026-08-20/`.

- `stage6-runtime-triggers-report.json` — `2102` bytes — SHA-256 `86f93afebb0535f3027ed861336530e9046f21fb248790696d606445af983697`;
- `trigger-replay.json` — `948` bytes — SHA-256 `fc79e329eb2ac448755af95e7843dfb7bb45f2d24d0decedc1ea1a8a3eb8e28a`;
- `trigger-sidecar.json` — `2005` bytes — SHA-256 `22e2699d6ebc04d069fbe7a3b0d7c7d1c1100663bfe6e6d3bc7e4e857c24035c`;
- `triggers.json` — `2005` bytes — SHA-256 `22e2699d6ebc04d069fbe7a3b0d7c7d1c1100663bfe6e6d3bc7e4e857c24035c`;
- `artifact-index.json` — `651` bytes — SHA-256 `5b1625033c20c248bfcfe2466d02dafc252cdba60196e5d8d674f96c031ebad1`.

## Decisão

**VALIDADA LOCALMENTE NO ESCOPO DA IMPLEMENTAÇÃO; NÃO INTEGRADA.**

A implementação, os testes, a auditoria limpa, a baseline Git-blob e a
integridade de evidências estão concluídas neste checkpoint. Ainda faltam CI
obrigatório Linux/Windows, revisão final de diff, PR, merge normal e validação
pós-merge. Nenhuma release ou suporte de engine é declarado por esta evidência.