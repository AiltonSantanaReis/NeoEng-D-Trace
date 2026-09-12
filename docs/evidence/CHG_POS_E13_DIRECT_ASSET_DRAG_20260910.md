# Registro de mudança pós-E13 — arraste direto de asset para o viewport

**ID:** CHG-POS-E13-003  
**Status:** `PASS`
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
segundo caminho de mutação. A proteção escolhida foi:

- declarar explicitamente a lista de assets como `DragOnly` com ação `Copy`;
- habilitar drops tanto no `QGraphicsView` quanto no `viewport()` interno do
  `QAbstractScrollArea`, que é a superfície que recebe o gesto do sistema;
- encaminhar os eventos do viewport por `viewportEvent`, o ponto canônico do
  `QGraphicsView` para o ciclo nativo `DragEnter`/`DragMove`/`DragLeave`/`Drop`;
- manter a criação transacional em `dropEvent`/`place_asset_from_library`, sem
  alterar schema, IDs, transform ou conteúdo dos assets.

## Impacto e proteção contra regressão

- Módulos afetados: `src/ui/scene_asset_panel.py`,
  `src/ui/scene_authoring_viewport.py` e o contrato focado em
  `tests/test_p2d_01b_asset_lifecycle.py`.
- Contratos preservados: MIME `application/x-neoeng-scene-asset`, inserção por
  botão/menu, undo/redo, persistência V2 e enquadramento pós-E13.
- Nenhuma remoção ou conversão de asset é necessária.
- O teste nativo abaixo foi executado no binário limpo gerado a partir do
  commit auditado; os testes Qt permanecem proteção complementar e não foram
  usados como substituto da prova visual.

## Estado de verificação

Os testes automatizados foram executados no worktree ativo e no pacote oficial:

- Suíte focada `tests/test_p2d_01b_asset_lifecycle.py`: **9 passed**.
- Suíte oficial sem filtros: **2169 passed, 2 skipped, 1 warning**.
- Registro completo: `artifacts/asset-drag-viewport-event-official-20260910.log`.
- Commit auditado: `0a2f18e235b4f99cb66d40d205242bb52c28884b`.
- Build limpa: `asset-drag-viewport-event-20260910`.
- Executável SHA-256: `450435514AFB636899737C5C1260CB05A57432AA6CF421FEF2D8B6A37989DB86`.
- ZIP portátil SHA-256: `E42E5F82CC062DAFDC53DA03A85FABAF57D30881508CCF4920F1428495BEBD8A`.
- Smoke de empacotamento: `SUCCESS`, **11 checks**; continuidade: `PASS`.

### Execução nativa e captura humana

Foi usado o executável acima, com caminho absoluto, e o projeto isolado
`artifacts/native-asset-direct-drag-forward-20260910/floresta-native-interactions.ndtproj`.
As capturas exibidas durante a sessão foram da janela nativa em execução, em
português, e mostraram as miniaturas reais da Biblioteca — Pinheiro, Pedra,
Arbusto, Tronco, Samambaia e Cogumelos — com `Assets: 6`, `Problemas: 0`.

O fluxo observado foi:

1. abrir o projeto e o Editor de Cenário no binário limpo;
2. abrir `Biblioteca` e arrastar `asset_cd430cd35519a18e` (Pedra) para o
   viewport;
3. completar o release nativo no ponto de soltura; o editor exibiu `Asset
   colocado: asset_cd430cd35519a18e`, selecionou o asset no Inspetor e atualizou
   a Biblioteca para `Em uso: 3` e Pedra `1 objeto`;
4. salvar pela barra nativa, com status `Cenário salvo`;
5. fechar o Editor e a janela principal, relançar o mesmo executável e observar
   a cena reaberta com `Default ... 3 objetos` e `Enquadrar Tudo: 3 objeto(s)`;
6. abrir novamente a Biblioteca e observar Pinheiro, Pedra e Cogumelos com
   `1 objeto` cada.

O helper de automação deixou o preview visual ativo após `sky.drag`; um clique
real adicional no mesmo ponto completou o release. Isso é uma limitação da
instrumentação da captura, registrada explicitamente, e não foi substituído
por `Inserir na cena`, edição do JSON ou mutação fora da UI. O objeto só foi
aceito após o ciclo nativo de drop e foi confirmado na reabertura.

O sidecar persistido após o save registrou:

- SHA-256: `49EDB896603375DEB3F47FB7E78C08AEA2A2C55D6563C4D161F6873AF8173485`;
- 6 assets e 3 objetos;
- `asset_a41ce9477ac7886c:asset_a41ce9477ac7886c`;
- `asset_97a6dc8960cf81dc:asset_97a6dc8960cf81dc`;
- `asset_cd430cd35519a18e:asset_cd430cd35519a18e`.

O resultado anterior do build `49d598bc` e a falha histórica do build
`9e0c50c` permanecem preservados como evidência de diagnóstico; não foram
apagados nem reclassificados. O critério do arraste direto neste build é
`PASS`.

E13 permanece fechado.
