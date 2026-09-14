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

## Correção aplicada

- Quebra mecânica de expressões, chamadas, literais e mensagens longas para o
  limite configurado de 88 colunas.
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
Baseline verified: 3901 files
```

PENDENTE DE EVIDÊNCIA: a execução local do comando `poetry run flake8` e dos
testes pytest não está disponível neste checkout porque `poetry` e `pytest`
não estão instalados. O novo CI deverá executar o comando oficial nos dois
ambientes e será a prova final desta mudança; ausência local não será tratada
como sucesso.

## Impacto e não regressão

A mudança é restrita à apresentação do código e à remoção de um import morto.
Não altera contratos de runtime, schemas, persistência, renderer, UI, formato
de asset, seleção oficial de testes ou limites de cobertura. O baseline foi
regenerado a partir do conteúdo staged e verificado contra blobs Git para
incluir os hashes dos arquivos corrigidos.

## Dependências documentais

- [Governança de Integridade, Execução e Antialucinação](../GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md)
- [Índice Documental Ativo Canônico](../INDICE_DOCUMENTAL_ATIVO_CANONICO_2026-08-24.md)
- [Registro Canônico de IDs](../REGISTRO_IDS_PRODUTO_PROFISSIONAL_CANONICO_2026-08-24.yaml)
- `baseline_manifest.json`
- `CHG_POST_E13_BASELINE_RECONCILIACAO_20260914.md`
