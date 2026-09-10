# Registro de mudança pós-E13 — enquadramento inicial de asset

**ID:** CHG-POS-E13-001  
**Status:** `IN_PROGRESS`  
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

Execução focada (`DIAGNOSTIC_ONLY`):

- `tests/test_asset_packs.py`
- `tests/test_stage3_professional_scene_editor.py`
- `tests/test_p2d_03c_viewport.py`
- Resultado: **30 passed**.

Suíte oficial completa, sem filtros: **2167 passed, 2 skipped, 1 warning**.

O warning é a depreciação já conhecida do construtor `QMouseEvent` em
`tests/test_merge_coverage_authoring_contracts.py:1341`; não foi ocultado nem
reclassificado.

Os testes novos cobrem escala 1:1, zoom transitório inferior a 1, mensagem PT-BR
e importação real pelo caminho de drop. A build nativa e a captura humana do
comportamento pós-mudança ainda estão pendentes neste registro.

## Aprovação e encerramento

A solicitação do usuário autoriza operacionalmente a aplicação do ajuste. O
registro permanece `IN_PROGRESS` até haver um novo commit, build identificada,
execução nativa com cliques reais, captura humana, persistência/reabertura e
revisão dos artefatos. Não declarar este registro, o pacote de assets ou uma
etapa do projeto como `COMPLETED` antes dessas evidências.
