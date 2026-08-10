# Evidência — Etapa 6: exportação de colisões

## Identificação

- base integrada: `79cb885382d642e17cc3eedb46056276a9a6a71f`;
- branch: branch técnica isolada da Etapa 6;
- commit técnico validado: `3c80bb7f0f72a26f5f4972c5aeb483b8d16e2e98`;
- sistema: Windows 11;
- Python: 3.11.9;
- dependências: `poetry.lock` vigente;
- risco: `R-005 — Exportação de colisão inconsistente`;
- estado: **APROVADO LOCALMENTE / NÃO INTEGRADO**.

## Objetivo e escopo

Unificar os caminhos JSON de colisão da toolbar, do painel de física e dos
metadados genéricos em um contrato único, versionado, determinístico e
validado. O formato TXT permanece como visão derivada do mesmo documento e
passa a usar substituição atômica.

## Causa raiz reproduzida

Antes desta alteração coexistiam três contratos incompatíveis:

1. a toolbar exportava diretamente o mapa interno `{object_id: pontos}`;
2. o painel exportava outro objeto com `collision_shapes`,
   `collision_results` e `statistics`;
3. os metadados genéricos de cena e objeto não incluíam a colisão.

O TXT escrevia diretamente no destino, criando janela de perda caso a escrita
falhasse. Geometrias não finitas, degeneradas ou órfãs não eram validadas por
uma autoridade comum antes da exportação.

## Contrato implementado

- `format_id`: `neoeng-d-trace-collisions`;
- `schema_version`: `1`;
- espaço de coordenadas explícito: `image`;
- `shapes`: lista ordenada por `object_id`;
- forma: polígono com pontos finitos, três vértices distintos e área não nula;
- `results`: pares, estado de colisão e MTV opcional normalizados;
- `statistics`: somente valores JSON válidos e números finitos;
- metadados genéricos de cena e objeto usam o mesmo registro canônico;
- JSON e TXT preservam o destino existente em falha de substituição.

## Arquivos técnicos e hashes SHA-256

| Arquivo | Bytes | SHA-256 |
|---|---:|---|
| `src/exporters/collision_exporter.py` | 6877 | `5c28a5921932e8b022be38a56aa27e64756be1d65802a1dab1d9be1981041338` |
| `src/exporters/json_exporter.py` | 6681 | `d8badde48a40ec889f6ce1a77b83086b1cac76308f15cf7e7bbab0f75296626d` |
| `src/ui/main_window.py` | 48854 | `f78c9559c706ae4027945bfc5c392baeb70d62a33eb75aff169fc00150b111c7` |
| `tests/test_stage_6_collision_export_schema.py` | 7190 | `63739a1268ffbca78bffb9d8d7628fae7cfe6881a427e9677945a895a2420694` |
| `tests/test_json_exporter_contract.py` | 4280 | `71b4bf7dc8c819bf067411815d70388c139400d416f47de1ff12161bc79931ee` |
| `tests/test_audit_closure_contracts.py` | 7422 | `8a8951d7576abb4286925d8fecaecb37d269395fe60797680b4beda27540e180` |

Os hashes acima correspondem ao candidato técnico antes da inclusão deste
relatório e da atualização da baseline.

## Comandos executados

```text
poetry run python -m py_compile src/exporters/collision_exporter.py src/exporters/json_exporter.py src/ui/main_window.py tests/test_stage_6_collision_export_schema.py
poetry run pytest tests/test_stage_6_collision_export_schema.py tests/test_json_exporter_contract.py tests/test_audit_closure_contracts.py -q
poetry run pytest --cov=src --cov-branch --cov-fail-under=62 --cov-report=term-missing:skip-covered --cov-report=xml
poetry run mypy src
poetry run flake8 src tests tools app.py pack_for_ai.py
poetry run isort --check-only --diff src tests tools app.py pack_for_ai.py
```

## Resultados locais

- testes focais: `32 passed`;
- suíte oficial: `542 passed`, `0 failed`, `0 skipped`;
- cobertura combinada: `62.45%`, acima do piso vigente de `62%`;
- `src/exporters/collision_exporter.py`: `84%` combinado;
- `src/exporters/json_exporter.py`: `93%` combinado;
- `src/ui/main_window.py`: `76%` combinado;
- mypy: zero erros em 66 arquivos;
- Flake8 e isort: aprovados.

## Regressões cobertas

- toolbar e painel com a mesma raiz de schema;
- inclusão canônica em metadados genéricos de cena e objeto;
- reabertura real do JSON exportado;
- ordenação determinística;
- rejeição de menos de três pontos, área zero, não finitos e referências órfãs;
- falha fechada antes do diálogo para geometria inválida;
- escrita TXT atômica e preservação do arquivo anterior quando `os.replace`
  falha;
- reconciliação explícita dos hashes contratuais JSON alterados pela inclusão
  intencional da colisão.

## Limitações e riscos residuais

- perfis específicos Godot e Unity permanecem para a Etapa 10;
- validação geométrica ampla, incluindo auto-interseção de colisões, permanece
  vinculada às Etapas 8 e 9;
- metas finais de cobertura continuam em `R-003`/Etapa 11;
- build standalone e release permanecem bloqueados;
- esta evidência não encerra `R-005` antes de commit, CI da PR, merge e CI
  pós-merge da `main`.

## Decisão

**APROVADO LOCALMENTE / NÃO INTEGRADO.** O candidato pode avançar para revisão
de diff, commit e CI. `R-005` permanece aberto até a comprovação pós-merge.
