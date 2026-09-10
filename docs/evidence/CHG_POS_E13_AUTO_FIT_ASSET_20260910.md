# Registro de mudança pós-E13 — enquadramento inicial de asset

**ID:** CHG-POS-E13-001  
**Status:** `PASS`
**Data:** 2026-09-10  
**Escopo:** ajuste fino do estúdio de cenários/parallax após o fechamento do E13  
**Worktree:** `build/e01-independent-scene-20260908`  
**Branch:** `Ailton/e08-renderer-20260908`

## Autoridade e dependências

- [Governança de integridade e antialucinação](../GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md)
- [Base ativa pós-E13](BASE_ATIVA_POS_E13_2026-09-09.md)
- [Proposta de pacotes de assets próprios](PROPOSTA_PACOTES_ASSETS_PROPRIOS_20260910.md)
- [Piloto de assets Floresta](PACK_01_03_PILOTO_FLORESTA_20260910.md)

Este registro não reabre nem reclassifica o E13. Ele documenta uma mudança de
produto dentro do ajuste fino pós-E13.

## Motivação baseada em evidência

Na execução nativa do build de localização anterior, a inserção do primeiro
asset de 1254×1254 px criava o objeto com escala autoral `1,0000` e zoom de
navegação `1,00x`. O objeto era renderizado, mas podia exceder o viewport e ficar
parcialmente fora da área visível. A ação existente **Enquadrar Seleção** foi
executada com cliques reais e enquadrou o mesmo objeto em `0,48x`, sem alterar a
escala persistida.

## Comparação antes/depois

| Aspecto | Antes | Depois |
|---|---|---|
| Primeiro asset em cena vazia | Inseria em escala 1:1 e exigia enquadramento manual | Insere em escala 1:1 e enquadra a navegação automaticamente |
| Dados autorais | `scale = (1, 1, 1)` | Preservado em `(1, 1, 1)` |
| Câmera/zoom persistido | Não alterado | Não alterado; somente o zoom transitório do viewport é ajustado |
| Assets seguintes | Mantinham o enquadramento atual | Mantêm o enquadramento atual; não reenquadram a cada inserção |
| Schema, IDs, hashes e assets | Sem alteração | Sem alteração |
| Mensagens PT-BR | Enquadramento podia aparecer em inglês | Enquadramento, inserção e importação passam a aparecer em português |

## Implementação

Módulo alterado: `src/ui/scene_authoring_viewport.py`.

- Adicionado `_frame_initial_asset()`, acionado somente quando a cena passa a
  conter exatamente um objeto.
- Aplicado aos caminhos de biblioteca, MIME de asset existente e importação por
  arquivo arrastado.
- O método reutiliza `fit_selection()`, que altera apenas o estado transitório
  de navegação e não abre uma transação de transformação.
- Status de enquadramento e de inserção/importação alinhados ao idioma PT.

## Impacto e proteção contra regressão

- Contratos preservados: `SceneTransformRecord`, persistência da cena, undo/redo,
  biblioteca de assets, parallax e enquadramento manual.
- Não há migração de schema nem alteração de conteúdo dos seis PNGs do piloto.
- Risco residual: o enquadramento automático é uma decisão de navegação local;
  cenas já povoadas não têm seu zoom alterado por novas inserções.
- Rollback: reverter o commit desta mudança; nenhum arquivo de usuário precisa ser
  removido ou convertido.

## Testes executados

Execução focada (`DIAGNOSTIC_ONLY`) no commit `9e0c50cc5375a063e1322c38ebe0e5ace3fa49c9`:

- `tests/test_asset_packs.py`
- `tests/test_stage3_professional_scene_editor.py`
- `tests/test_p2d_03c_viewport.py`
- Resultado: **31 passed**.

Suíte oficial completa, sem filtros: **2168 passed, 2 skipped, 1 warning**.

O warning é a depreciação já conhecida do construtor `QMouseEvent` em
`tests/test_merge_coverage_authoring_contracts.py:1341`; não foi ocultado nem
reclassificado.

Os testes cobrem escala 1:1, zoom transitório, mensagem PT-BR, importação por
arquivo e inserção pela biblioteca. O resultado oficial está preservado em
`artifacts/asset-fit-loaded-content-pytest-20260910.log`.

## Evidência nativa e artefatos

- Build limpa gerada a partir do commit `9e0c50cc5375a063e1322c38ebe0e5ace3fa49c9`.
- Executável: `build/_clean-asset-fit-20260910/release/asset-fit-loaded-content-20260910/portable/NeoEng-D-Trace/NeoEng-D-Trace.exe`.
- SHA-256 do executável: `40BF5770A3AA25248BBBB3C922057F486FB27D8C2A8C0C70C101B37E95765C4F`.
- Pacote portátil SHA-256: `2716086E85A67731245A2C97BD0463457A3710342E1D81588C141F82B163AFF8`.
- `continuity-provenance.json`: `PASS`; `portable-smoke-report.json`: `SUCCESS`, 11 checks.

No executável nativo, com cliques reais, o primeiro asset foi inserido pela
Biblioteca. O Cogumelos ficou totalmente visível no viewport, com `Escala X/Y/Z
= 1,0000`, `1 objeto` na camada `Default` e status `Asset colocado`. O mesmo
projeto foi salvo, fechado, reaberto e capturado novamente; o viewport reenquadrou
o conteúdo carregado sem alterar o transform autoral.

O sidecar da fixture de revisão foi conferido antes e depois da reabertura:
`schema_version: 2`, seis assets, um objeto, escala `1,1,1` e SHA-256
`E9D056FD2E05FD1AF970B6C858A4F81D9FFA7A63F4BFDB29DFACAF7B9DDF41C1` em ambas
as leituras. As capturas foram exibidas pelo estado real da janela nativa durante
a sessão; não foram substituídas por mock ou imagem de referência.

## Aprovação e encerramento

A solicitação do usuário autorizou operacionalmente a aplicação do ajuste. Os
critérios desta mudança estão `PASS` no commit, nos testes, no build, na execução
nativa, na captura humana e na persistência/reabertura. Isso não aprova o pacote
visual nem encerra uma etapa do projeto: a revisão artística dos PNGs e outras
pendências de catálogo continuam governadas pelo registro do piloto.
