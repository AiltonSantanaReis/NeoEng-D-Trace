# Registro de mudança — correção do lint do pacote de consolidação

**ID:** `CHG-POST-E13-CI-LINT-CORRECTION-20260914`
**Status:** `IN_PROGRESS`
**Data:** 2026-09-14
**Escopo:** correção de qualidade estática identificada pelo CI do PR #174
**Requisitos afetados:** `REQ-F12-QUALITY-GATES`
**Feature/componente:** `FEAT-QA-EVIDENCE-PACKAGE`, módulos de UI e ferramentas de evidência 3D
**Testes afetados:** `TEST-QA-EVIDENCE-COMMIT`, `TEST-QA-EVIDENCE-MANIFEST`

## Causa comprovada

O commit remoto `f24bd9b` passou pelos gates de baseline, manifesto de
evidências, lock de dependências e compilação, mas falhou no passo oficial
`Run full lint` do PR #174, execução `34881395619`, nos jobs Linux
`104101286454` e Windows `104101286209`.

O comando oficial foi:

```text
poetry run flake8 src tests tools app.py pack_for_ai.py
```

O log apontou somente violações `E501` de comprimento de linha nos arquivos
de autoria/UI, testes e geradores/validadores de asset 3D, além de um `F401`
para o import `os` não utilizado em `tools/create_reference_3d_asset.py`.
Não houve erro funcional, de compilação, de dependência ou de baseline nesse
run.

Na execução seguinte `34884085236`, o `flake8` passou nos dois ambientes, mas
o passo oficial `Check formatting` também foi reprovado nos jobs Linux
`104110264166` e Windows `104110264428`. O diff do Black identificou seis
arquivos que ainda precisavam da formatação canônica: o painel vetorial, os
testes de symlink, o teste de viewport, o teste do harness Unity e os dois
geradores/validadores de asset 3D.

Na execução `34885099513`, lint, Black e isort passaram nos dois ambientes,
mas `mypy src` falhou nos jobs Linux `104113680758` e Windows `104113680941`
com sete diagnósticos em `src/core/unity_integration.py` e
`src/ui/unity_integration_settings.py`. Os diagnósticos eram de inferência de
tipo no reuso de uma variável `str | None` como `Path` e de passagem de um
`str` genérico onde a API exige `ExecutableKind` (`"hub"` ou `"editor"`).

Na execução `34886148389`, lint e Black passaram nos dois ambientes e mypy não
foi alcançado por causa da falha anterior de isort. O único diagnóstico de
isort foi a ordem dos nomes na importação de `src/ui/unity_integration_settings.py`:
as constantes `UNITY_*` devem preceder `ExecutableKind` conforme o perfil
canônico do projeto.

Na execução `34887077924`, os gates anteriores passaram, mas o passo oficial de
cobertura funcional falhou nos jobs Linux `104120265823` e Windows
`104120265537`. O Linux executou `2651` testes (`2650 passed, 1 failed,
2 skipped`), atingiu `91.29%` de cobertura e reprovou a asserção de
`tests/test_reference_3d_asset.py::test_reference_asset_generation_and_contract`
(`mesh_count == 23`; observado `22`). O Windows reproduziu a mesma causa no
shard `test_post_e13_boundary_contracts.py`, encerrando com `839` testes,
`0` failures, `1` error e `2` skips. A falha não era de threshold: era um
defeito funcional no gerador do asset. O `parts.append(boot)` estava fora do
laço bilateral, portanto somente `Boot_R` era publicado e `Boot_L` era
silenciosamente perdido.

## Correção aplicada

- Quebra mecânica de expressões, chamadas, literais e mensagens longas para o
  limite configurado de 88 colunas.
- Aplicação do diff indicado pelo `black --check --diff`, incluindo somente
  agrupamento de expressões, normalização de linhas em testes controlados e
  espaços em branco.
- Separação explícita entre o valor textual de ambiente e a raiz `Path` do
  editor, além da tipagem dos métodos UI com o alias `ExecutableKind`; o fluxo
  de descoberta e seleção permanece o mesmo.
- Reordenação da importação Unity conforme o diff oficial do isort; nenhum
  símbolo foi adicionado ou removido.
- Correção da publicação bilateral de botas em `build_parts`: o registro de
  cada bota agora ocorre dentro do laço `L/R`, restaurando as duas malhas e o
  contrato de 23 componentes; o teste também fixa explicitamente a presença de
  `Boot_L` e `Boot_R`.
- Remoção somente do import `os` comprovadamente não utilizado.
- Renomeação de um identificador de teste excessivamente longo, sem mudar o
  cenário, as asserções ou o contrato verificado.
- Nenhuma regra de lint foi relaxada, nenhum `noqa`, `skip`, `xfail`, filtro ou
  bypass foi adicionado.
- Nenhum arquivo de produto, evidência histórica ou artefato foi removido.

## Validação local disponível

PASS:

```text
git diff --check
python -m compileall -q -f app.py src tests pack_for_ai.py tools
verificação de comprimento: nenhum arquivo tocado possui linha > 88 colunas
tools/baseline_integrity.py --verify --git-blob
Baseline verified: 3902 files
```

PENDENTE DE EVIDÊNCIA: a execução local de `poetry run flake8`,
`poetry run black --check`, `poetry run isort --check-only`, `poetry run mypy`
e dos testes pytest não está disponível neste
checkout porque `poetry`, Black e pytest não estão instalados. O novo CI deverá
executar os comandos oficiais nos dois ambientes e será a prova final desta
mudança; ausência local não será tratada como sucesso.

## Impacto e não regressão

A mudança combina correções de qualidade estática com uma correção funcional
localizada no gerador de asset de referência. Ela não altera schemas,
persistência, renderer, UI, seleção oficial de testes ou limites de cobertura;
apenas deixa de descartar a bota esquerda que já fazia parte do contrato
esperado. O baseline será regenerado a partir do conteúdo staged e verificado
contra blobs Git para incluir os hashes dos arquivos corrigidos.

## Dependências documentais

- [Governança de Integridade, Execução e Antialucinação](../GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md)
- [Índice Documental Ativo Canônico](../INDICE_DOCUMENTAL_ATIVO_CANONICO_2026-08-24.md)
- [Registro Canônico de IDs](../REGISTRO_IDS_PRODUTO_PROFISSIONAL_CANONICO_2026-08-24.yaml)
- `baseline_manifest.json`
- `CHG_POST_E13_BASELINE_RECONCILIACAO_20260914.md`
