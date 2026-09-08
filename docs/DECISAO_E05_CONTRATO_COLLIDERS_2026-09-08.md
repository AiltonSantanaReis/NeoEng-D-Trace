# Decisão E05 — contrato de colisores próprios de cenário

**Data:** 2026-09-08  
**Estado:** `ACTIVE_TECHNICAL_CONTRACT`  
**Base:** Plano Mestre `52e9896d2ecf1bc928fb27aca5b8091890c580d7`, seção 12;
Governança de integridade; E04 técnico selado em `4a09aa5`.

## Escopo autorizado

E05 implementa uma coleção de colisores de cenário separada dos visuais e do
estado legado `scene.collision_shapes`. O lote cobre caixas, círculos,
polígonos, segmentos/cadeias e triggers, com vínculo opcional a entidade,
transformação local, categoria/máscara e material físico apenas como dados
contratados. Não cria dinâmica física, solver ou NavMesh antecipados.

## Contrato de dados e transação

- Cada colisor tem ID estável, tipo, geometria, transform local, layer física,
  category/mask, `is_trigger`, visibilidade do overlay e versão.
- A camada física é independente da camada visual; mover um objeto visual não
  muta um colisor sem comando explícito de vínculo.
- Criar, editar, mover, duplicar, remover e alternar overlay são operações
  transacionais, com Undo/Redo por deltas e rejeição atômica antes da mutação.
- O formato persistido é versionado e não interpreta automaticamente dados
  legados como colisores próprios.

## Validação canônica

O validador comum a UI, comando, API e exportador rejeita degeneração,
winding não determinístico, auto-interseção, vértices acima do limite, cadeia
inválida, raio não positivo, escala de círculo não representável e IDs ou
categorias inválidos. Cada erro identifica o colisor e a correção esperada.

## Fluxo e negativos

O fluxo mínimo é cenário vazio ou tilemap → criar formas → editar junto e
separado do visual → salvar/reabrir → consumir em um teste real mínimo de
overlap/trigger → Undo/Redo. O lote deve provar caixas, círculos, polígonos,
segmentos/cadeias e triggers. Export parcial é proibido quando qualquer
colisor é inválido.

Rollback preserva as colisões legadas e remove somente o registro novo do lote;
nenhuma conversão destrutiva de contorno de imagem é permitida.
