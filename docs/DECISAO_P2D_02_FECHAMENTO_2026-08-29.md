# NeoEng-D-Trace — Decisão de fechamento P2D-02

**Status:** ACCEPTED — macroetapa fechada localmente
**Data:** 29/08/2026 (UTC-03)
**Macroetapa:** P2D-02 — ordem visual, camadas, grupos e isolamento
**Baseline de entrada:** `eb941e60a06a065c54433f852970a50b7ebeb56a`
**Commit final publicado:** `59a326c4b602878bed22cea4f4a1222fe56640b9`
**Evidência consolidada:** `docs/EVIDENCIA_P2D_02_CONSOLIDACAO_2026-08-29.md`

## 1. Finalidade

Esta decisão consolida formalmente as subetapas P2D-02A e P2D-02B. Ela não
introduz funcionalidade nova; registra que a ordem visual, as camadas, o
bloqueio seguro, os grupos, a hierarquia/membership e o isolamento foram
implementados, testados, auditados e documentados em suas próprias decisões e
evidências.

## 2. Composição da macroetapa

| Subetapa | Escopo | Implementação | Fechamento documental |
|---|---|---|---|
| P2D-02A | ordem visual, camadas, visibilidade e locking seguro | `2118266df6daeafee8eafa82e80c953abc866b00` | `d152b214b1bccb717911001396936c1f93b23714` |
| P2D-02B | grupos, hierarquia/membership e isolamento | `af02f3ef513487bd176c939085fea0ca56a7da6b` | `59a326c4b602878bed22cea4f4a1222fe56640b9` |

Os dois conjuntos foram publicados na branch `modernization/multiaxis-ui`.
O remoto foi verificado sem divergência após a publicação do último commit.

## 3. Critérios consolidados de aceite

P2D-02 é aceita porque todos os critérios abaixo possuem evidência própria:

1. a ordem visual derivada de camadas é observável e não altera transformações;
2. camadas podem ser reordenadas, ocultadas e bloqueadas com rejeição segura;
3. grupos possuem ID, nome, membership, visibilidade e lock persistidos;
4. hierarquia de grupos é validada, sem parent desconhecido ou ciclo;
5. seleção e operações de membership são observáveis na árvore profissional;
6. visibilidade e lock são herdados pelos descendentes;
7. isolamento é transitório, não suja o documento e não aparece no JSON salvo;
8. exclusão de grupo preserva objetos e promove subgrupos de forma determinística;
9. save/reload conserva os estados editoriais persistentes;
10. tentativas bloqueadas não deixam exceção, alteração parcial ou gesto ativo;
11. a janela profissional permanece separada do editor legado;
12. testes, auditorias Qt Windows/offscreen e revisão visual foram concluídos;
13. decisões, evidências, índice e plano estão reconciliados com os commits.

## 4. Limites preservados

Este aceite não declara que o editor possui tilemap, pintura de tiles,
autotiling, grids isométricos/hexagonais, NavMesh, entidades/componentes,
prefabs, iluminação/VFX ou colisão de cenário. Esses recursos continuam em
linhas independentes e não foram misturados à P2D-02.

Também não altera C3, o modelo legado, o schema V1, os adapters G/V/B, menus
globais, assets, transformações, exportadores ou a política de evidência.

## 5. Decisão

Com base na evidência consolidada e nos registros das duas subetapas, a
macroetapa **P2D-02 — ordem visual, camadas, grupos e isolamento** fica marcada
como **ACCEPTED / CLOSED**.

P2D-03 é o próximo estágio do plano. Nenhum item de P2D-03 é considerado
implementado por este fechamento. Push adicional, tag, merge ou release não
fazem parte desta decisão.
