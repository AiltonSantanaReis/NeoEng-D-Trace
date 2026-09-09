# Base ativa pós-E13

Este é o registro operacional para os ajustes finos após o fechamento técnico
do E13.

- Worktree único: `C:\Users\atnco\Pictures\NeoEng-D-Trace\build\e01-independent-scene-20260908`
- Branch única: `Ailton/e08-renderer-20260908`
- Escopo atual: seleção contextual e múltipla de objetos/polígonos/vértices,
  edição vetorial, tradução e validação visual nativa.
- Build e capturas devem ser geradas novamente a partir do commit que contém a
  correção; artefatos anteriores são evidência histórica, não entrada de teste.
- Os documentos E00–E13 continuam preservados para rastreabilidade, mas não
  são bases alternativas de código nem autorização para reabrir etapas.
- A validação de symlink permanece reservada para a auditoria final conforme a
  decisão vigente; não é usada como bloqueio do lote pós-E13.

## Limite de modelo conhecido

O modelo atual representa um `SceneObject` com um único contorno poligonal.
Assim, “Excluir polígono” é uma exclusão de objeto-polígono; “Excluir vértice”
e “Excluir vértices” alteram o contorno preservando o objeto. Suportar vários
contornos persistidos dentro de um mesmo objeto exige uma mudança de contrato,
serialização, renderização e colisão e não será introduzido silenciosamente
durante este ajuste fino.
