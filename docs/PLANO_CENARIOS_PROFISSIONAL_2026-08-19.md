# Plano de extensão profissional de cenários — NeoEng-D-Trace

**Data de início:** 19 de agosto de 2026
**Estado:** Etapa 1 em execução
**Base integrada:** `487ae11` (merge da PR `#103`)
**Plano relacionado:** `docs/PLANO_CENARIOS_PARALLAX_E_PALETA_2026-08-18.md`

## Motivo da extensão

O plano anterior concluiu o MVP de autoria lateral, câmera/parallax, overlays,
persistência e exportação JSON. Ele não prometia um editor profissional de
cenários em tempo real. A nova solicitação amplia o produto para autoria visual
de cenários: arrastar e soltar objetos, selecionar e transformar elementos,
visualizar o resultado em tempo real, editar camadas/profundidade, registrar
marcadores de iluminação e VFX, salvar o cenário e permitir intercâmbio com
outras engines.

Esta extensão preserva o MVP e seus contratos. Não altera silenciosamente o
schema `.ndtproj` v1, `SceneObject.position.z`, colisores, exportadores atuais,
gizmo do editor 2D, menus, atalhos ou Undo/Redo do editor principal.

## Resultado profissional esperado

O módulo será uma janela de autoria separada, com viewport próprio e estado de
edição transacional. O usuário poderá:

- importar assets por seleção e arrastar/soltar para o cenário;
- selecionar um ou vários objetos, agrupar, mover, girar, escalar, espelhar e
  aplicar snapping configurável;
- editar posição, rotação, escala, pivô, camada e profundidade por gizmo e
  inspector numérico;
- observar câmera/parallax, molduras e overlays em tempo real;
- posicionar sockets declarativos de luz, VFX e triggers sem simular efeitos
  que pertencem ao runtime da engine;
- salvar, reabrir, validar e exportar um documento versionado sem perda de
  dados, com rollback atômico;
- importar/exportar formatos suportados por adaptadores explícitos, com
  diferenças de capacidade reportadas pelo produto.

Iluminação, partículas, shaders e pós-processamento poderão ter preview quando
houver implementação determinística no D-Trace. O documento também poderá
transportar parâmetros e sockets para engines, mas não será apresentado como
runtime completo antes de existir consumidor real validado.

## Ordem e gates

1. Baseline real, reconciliação documental, contratos e caracterização.
2. Modelo de cena editável: objetos, assets, transformações, seleção múltipla,
   grupos e snapping.
3. Editor profissional separado: viewport em tempo real, drag-and-drop,
   gizmos, inspector e Undo/Redo.
4. Camadas/parallax, iluminação, VFX e trigger sockets com preview determinístico.
5. Persistência versionada, importação/exportação e adaptadores Godot/Unity e
   formatos genéricos.
6. Testes reais, auditoria visual automatizada, desempenho, evidências
   hashadas, CI, PR e merge.

Cada etapa exige implementação integral do seu escopo, testes positivos e
negativos, artefatos reproduzíveis, hashes, privacidade, cobertura sem redução,
árvore limpa e rollback documentado. Falha, lacuna ou comportamento não
testado mantém a etapa aberta.

## Contratos de compatibilidade

- O documento lateral atual `neoeng-d-trace-scenario` schema v1 permanece
  legível e imutável.
- Uma evolução de cenário usará versão explícita e migração validada; nenhum
  campo será reinterpretado silenciosamente.
- A profundidade de autoria/parallax continuará separada do `position.z` usado
  pelo projeto e pelos exportadores existentes até ADR de migração.
- Assets serão referenciados por caminhos portáveis e identificadores
  verificáveis; caminhos absolutos locais não serão persistidos.
- Toda alteração de cena passará pelo histórico isolado do editor de cenário e
  terá recuperação em caso de erro de persistência.
- Capacidade de uma engine será declarada por adaptador e teste real. Ausência
  de suporte nativo não será tratada como falha do editor, mas também não será
  mascarada como suporte existente.

## Fora do escopo automático

Não serão adicionados nesta extensão, sem contrato e decisão próprios, editor
de imagem, modelagem 3D, runtime completo de jogo, streaming de assets,
simulação física de partículas ou efeitos não determinísticos.

\n