# Registro de mudança pós-E13 — enquadramento de conteúdo carregado

**ID:** CHG-POS-E13-002  
**Status:** `PASS`
**Data:** 2026-09-10  
**Escopo:** ajuste fino do estúdio de cenários/parallax após o fechamento do E13  
**Worktree:** `build/e01-independent-scene-20260908`  
**Branch:** `Ailton/e08-renderer-20260908`

## Autoridade e dependências

- [Governança de integridade e antialucinação](../GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md)
- [Base ativa pós-E13](BASE_ATIVA_POS_E13_2026-09-09.md)
- [CHG-POS-E13-001 — enquadramento inicial de asset](CHG_POS_E13_AUTO_FIT_ASSET_20260910.md)
- [Piloto de assets Floresta](PACK_01_03_PILOTO_FLORESTA_20260910.md)

Este registro não reabre nem reclassifica o E13. Ele documenta uma correção
observada durante a auditoria real de persistência do ajuste fino pós-E13.

## Evidência que motivou a mudança

No build nativo baseado no commit `650d46ea9c096ae5da576275de6ac72cc4e529ee`,
o fluxo real inseriu o Pinheiro, enquadrou-o corretamente e salvou o cenário.
Após fechar pela interface e reabrir o mesmo projeto, a camada `Default` e o
objeto persistiram, mas o viewport iniciou com a navegação padrão e mostrou o
asset muito pequeno. O sidecar continuou correto: um objeto, asset do Pinheiro
e escala autoral `(1, 1, 1)`.

Esta é uma falha de apresentação inicial do editor, não uma falha de
persistência do transform. O comportamento observado foi preservado como
limitação da build anterior; não foi reclassificado como sucesso.

## Decisão profissional

Ao abrir uma cena já povoada, o viewport deve enquadrar o conteúdo visível uma
vez usando somente o estado transitório de navegação. A correção não deve:

- alterar `SceneTransformRecord`;
- alterar posição, escala, rotação ou pivô authored;
- alterar câmera persistida, schema, IDs ou hashes;
- reenquadrar a cada novo asset inserido;
- emitir enquadramento para uma cena realmente vazia.

## Implementação

- `SceneAuthoringViewport.frame_loaded_content()` enquadra todos os objetos
  carregados somente quando há conteúdo.
- `ScenarioEditorWindow` agenda essa operação após o layout inicial, para usar
  as dimensões reais do viewport.
- O status usa a tradução existente (`Enquadrar Tudo` em PT-BR).

## Impacto e proteção contra regressão

- Contratos preservados: persistência V2, biblioteca de assets, parallax,
  câmera authored, undo/redo e enquadramento manual.
- O ajuste é de navegação e não abre transação de edição.
- Cenas vazias permanecem vazias e não recebem aviso de enquadramento.
- Rollback: reverter o commit desta mudança; não é necessário remover ou
  converter nenhum arquivo de usuário.

## Testes executados

Execução focada (`DIAGNOSTIC_ONLY`) após a correção:

- `tests/test_asset_packs.py`
- `tests/test_stage3_professional_scene_editor.py`
- `tests/test_p2d_03c_viewport.py`
- Resultado: **31 passed**.

O teste novo confirma que conteúdo carregado reduz o zoom transitório,
preserva integralmente o transform e emite `Enquadrar Tudo` em português.

A build nativa, a reabertura real após a correção e a suíte oficial completa
continuam pendentes neste registro.

## Evidência final do commit e do build

- Commit auditado: `9e0c50cc5375a063e1322c38ebe0e5ace3fa49c9`.
- Suíte focada: **31 passed**; suíte oficial sem filtros: **2168 passed, 2 skipped, 1 warning**.
- Build limpa: `build/_clean-asset-fit-20260910/release/asset-fit-loaded-content-20260910/`.
- SHA-256 do executável: `40BF5770A3AA25248BBBB3C922057F486FB27D8C2A8C0C70C101B37E95765C4F`.
- Smoke portátil: `SUCCESS` em 11 checks; continuidade: `PASS`.

Na execução nativa com cliques reais, o cenário com seis assets foi salvo e
fechado. Na reabertura do mesmo projeto, a captura mostrou `Z00 Default · 1
objeto`, o asset totalmente enquadrado no viewport e o status `Enquadrar Tudo:
1 objeto(s) enquadrado(s)`. O inspetor não reintroduziu seleção nem transformou
os dados; o sidecar manteve `schema_version: 2`, seis assets, um objeto, escala
`1,1,1` e o mesmo SHA-256 antes/depois (`E9D056FD2E05FD1AF970B6C858A4F81D9FFA7A63F4BFDB29DFACAF7B9DDF41C1`).

Os critérios desta mudança estão `PASS`. E13 permanece fechado; a classificação
do piloto visual continua separada e ainda é `PENDING_EVIDENCE`.
