# Registro de mudança pós-E13 — arraste direto de asset para o viewport

**ID:** CHG-POS-E13-003  
**Status:** `IN_PROGRESS`  
**Data:** 2026-09-10  
**Escopo:** ajuste fino do estúdio de cenários/parallax após o fechamento do E13  
**Worktree:** `build/e01-independent-scene-20260908`  
**Branch:** `Ailton/e08-renderer-20260908`

## Autoridade e dependências

- [Governança de integridade e antialucinação](../GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md)
- [Base ativa pós-E13](BASE_ATIVA_POS_E13_2026-09-09.md)
- [Piloto de assets Floresta](PACK_01_03_PILOTO_FLORESTA_20260910.md)

Este registro não reabre nem reclassifica o E13. Ele preserva a falha observada
no fluxo de usuário pós-E13 e controla a correção separadamente.

## Evidência que motivou a mudança

No build `9e0c50cc5375a063e1322c38ebe0e5ace3fa49c9`, uma execução nativa com
cliques reais abriu a Biblioteca, iniciou o arraste de `asset_97a6dc8960cf81dc`
e soltou o item dentro do viewport. A captura mostrou o preview de interação,
mas a hierarquia permaneceu com somente um objeto já existente; nenhum novo
objeto foi criado e o sidecar não foi salvo. O menu contextual e o botão
`Inserir na cena` continuaram funcionais. A falha não foi ocultada nem tratada
como sucesso por causa do fallback.

## Decisão profissional

O contrato de drag/drop já existente deve chegar ao viewport nativo sem criar um
segundo caminho de mutação. A proteção escolhida é:

- declarar explicitamente a lista de assets como `DragOnly` com ação `Copy`;
- habilitar drops tanto no `QGraphicsView` quanto no `viewport()` interno do
  `QAbstractScrollArea`, que é a superfície que recebe o gesto do sistema;
- manter a criação transacional em `dropEvent`/`place_asset_from_library`, sem
  alterar schema, IDs, transform ou conteúdo dos assets.

## Impacto e proteção contra regressão

- Módulos afetados: `src/ui/scene_asset_panel.py` e
  `src/ui/scene_authoring_viewport.py`.
- Contratos preservados: MIME `application/x-neoeng-scene-asset`, inserção por
  botão/menu, undo/redo, persistência V2 e enquadramento pós-E13.
- Nenhuma remoção ou conversão de asset é necessária.
- Risco residual: a eficácia final depende de nova execução nativa no binário
  gerado a partir deste commit; os testes Qt não substituem essa prova.

## Estado de verificação

Os testes automatizados foram executados no worktree ativo:

- Suíte focada: **28 passed**.
- Suíte oficial sem filtros: **2168 passed, 2 skipped, 1 warning**.
- Registro completo: `artifacts/asset-drag-pytest-20260910.log`.

A nova build limpa e a captura nativa ainda precisam ser executadas. Até a
captura nativa comprovar a criação do objeto por arraste direto, este registro
permanece `IN_PROGRESS` e o critério do piloto permanece `PENDING_EVIDENCE`.

E13 permanece fechado.
