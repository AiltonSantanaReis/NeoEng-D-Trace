# NeoEng-D-Trace — Evidência P2D-01B

## Biblioteca de assets, relink/replace/missing e uso no produto

**Data:** 2026-08-29 (UTC-03)
**Linha:** P2D-COMP-01 / P2D-01B
**Estado:** GATE AUTOMATIZADO PASS — REVISÃO HUMANA FINAL PENDENTE
**Parent checkpoint:** 11b6970be7b44d22fa44105043915d12e335a179
**Commit de implementação:** 6c051020fd5b35c2c2e41cb0fff7a85d96caf76f
**P2D-COMP-01:** OPEN — esta evidência não representa aceite do produto completo.
**P2D-01:** OPEN — P2D-01B ainda requer revisão humana final para aceite formal.

## 1. Decisão aplicada

A decisão aprovada em `DECISAO_P2D_01B_BIBLIOTECA_LIFECYCLE_2026-08-29.md` foi implementada no editor profissional de composição 2D:

- a biblioteca lista assets registrados na cena, inclusive `missing`, `modified`, `invalid` e `unavailable`;
- cada item exibe estado, caminho operacional, quantidade de objetos usuários, dimensões quando decodificáveis e diagnóstico acionável;
- `Relink` repara a referência de um asset sem trocar seu ID e sem romper os objetos que o utilizam;
- `Replace` troca intencionalmente o conteúdo mantendo o ID, os vínculos dos objetos, transformações, camadas, grupos, ordem, seleção e histórico transacional;
- `Refresh` revalida a presença, o hash e a decodificação do asset;
- asset ausente é aberto em modo diagnóstico no editor profissional, sem fallback silencioso e sem mutação parcial;
- `Undo` e `Redo` cobrem relink e replace pelo ciclo transacional da sessão;
- a resolução operacional continua limitada ao caminho relativo controlado e ao SHA-256 persistido; `source_path` continua sendo apenas provenance;
- a UI está hospedada exclusivamente no editor profissional de cenário e não altera o editor principal de imagem, o visualizador de máscaras ou painéis legados.

## 2. Alterações delimitadas

| Área | Resultado |
|---|---|
| `src/core/scene_asset_library.py` | inspeção determinística de estado e diagnóstico de asset |
| `src/core/scene_authoring_model.py` | atualização validada de registro preservando o ID |
| `src/core/scene_authoring_session.py` | relink/replace transacionais com Undo/Redo |
| `src/ui/scene_asset_panel.py` | biblioteca visual, estados, diagnóstico, import, relink, replace e refresh |
| `src/ui/scene_authoring_viewport.py` | sincronização do render quando o registro de asset muda |
| `src/ui/scenario_editor_window.py` | integração da biblioteca e abertura diagnóstica de cena com asset ausente |
| `tests/test_p2d_01b_asset_lifecycle.py` | testes focalizados de estados, ciclo de vida, integração e regressão |
| `scripts/audit_p2d_01b_asset_library.py` | captura Windows em três resoluções, auditoria visual e comprovação de uso real |

Não foram alterados tilemaps, colisão de cenário, NavMesh, entidades/componentes/prefabs, iluminação, VFX, renderer externo, C3, tolerâncias, auditores canônicos ou as linhas independentes futuras.

## 3. Evidência executada

| Verificação | Resultado |
|---|---|
| Python | `.venv\\Scripts\\python.exe`, Python 3.11.9 |
| Commit/worktree final | `6c051020fd5b35c2c2e41cb0fff7a85d96caf76f`; branch `modernization/multiaxis-ui`; tracked clean |
| Testes focalizados e integração | **69 passed, 0 failed** |
| Suíte completa pós-commit | **1774 passed, 2 skipped, 0 failed** |
| Gate visual pré-commit | PASS; 4 PNGs; auditoria com 0 findings |
| Gate visual pós-commit | PASS; 4 PNGs; auditoria com 0 findings |
| Comparação pré/pós | 4/4 nomes iguais, 0 name delta, 0 hash delta; `ALL_EQUAL=True` |
| Estado READY | uso observado; `Relink` desabilitado; `Replace` habilitado |
| Estado MISSING | diagnóstico presente; `Relink` e `Replace` habilitados |
| Relink | estado retorna a `ready`; mesmo asset ID; objetos preservados |
| Replace | mesmo asset ID; objetos preservados; pixmap atualizado para `220x144` |
| Regressão de abertura | sidecar com asset ausente abre o editor em modo diagnóstico; não há fallback silencioso |
| Higiene de diff | `git diff --check` PASS; nenhum arquivo tracked modificado após o commit |

As capturas foram produzidas em 1280x720, 1366x768 e 1920x1080. O quarto frame é o estado de overlays/diagnóstico em 1366x768 e comprova visualmente o caso `missing` no produto real.

## 4. Resultado do gate

O código e a evidência automatizada de P2D-01B estão aprovados para a etapa de revisão final:

- biblioteca visível no editor profissional;
- asset pronto e asset ausente distinguidos na interface;
- diagnóstico e ações disponíveis conforme o estado;
- relink e replace exercitados com preservação de identidade e uso;
- ciclo de renderização atualizado após substituição;
- nenhum delta visual entre a captura pré-commit e a captura pós-commit do mesmo produto;
- suíte completa sem regressões.

Este resultado não mascara nem aprova polígonos, assets inválidos ou referências ausentes. A validação continua bloqueante quando o conteúdo não é decodificável ou não pode ser resolvido com segurança.

## 5. Revisão humana obrigatória

O aceite formal ainda depende da revisão humana da build/capturas em Windows. A revisão deve confirmar, nas resoluções-alvo:

- legibilidade dos estados `ready`, `missing`, `modified`, `invalid` e `unavailable`;
- clareza dos diagnósticos e das ações `Relink`, `Replace` e `Refresh`;
- ausência de clipping, sobreposição, deslocamento inesperado ou ambiguidades na biblioteca;
- preservação de foco, teclado, navegação e comportamento do editor profissional;
- distinção visual suficiente entre asset pronto, asset ausente e asset com conteúdo alterado.

Até essa revisão, o estado correto é `GATE AUTOMATIZADO PASS — REVISÃO HUMANA FINAL PENDENTE`; não é correto declarar P2D-01B como `ACCEPTED`.

## 6. Build, remoto e próximo passo

A build portátil candidata foi gerada a partir do commit `09c8de90181e15089e2b9d38703702bf8a35b793` em checkout temporário limpo, sem tocar nos artefatos untracked do workspace principal.

| Verificação da build | Resultado |
|---|---|
| PyInstaller | 6.22.0; build concluído |
| Python | 3.11.9 da .venv; 3.11.9 |
| Smoke test oficial | SUCCESS; 11 checks; 13 artefatos |
| Manifest | 314 arquivos; SHA-256 14CD0370A8E607EE500245C63F21273C29AA52267B48B87982C6C10DD707F56C |
| ZIP | 124035432 bytes; SHA-256 9522F8537C698753399B6BFE1390CF9E9C882305C3C2DE80BE7593AAEEEEB565 |
| Extração independente | 314/314 arquivos verificados; 0 falhas |

O próximo passo é a revisão humana da build e das capturas em Windows. O ciclo remoto só deve ocorrer depois de:

1. revisão humana final aprovada;
2. build portátil e smoke test aprovados;
3. reconciliação do estado tracked clean;
4. eventual seal de evidência concluído.

Por autorização do usuário, o ciclo remoto poderá então executar somente a publicação segura da branch atual em `origin`, sem force-push, merge, tag ou limpeza de untracked, salvo nova autorização explícita.

## 7. Não implementado por decisão de escopo

P2D-01B não adiciona tilesets/tilemaps, pincéis, balde, borracha, autotiling, grids isométricos/hexagonais, colliders de cenário, NavMesh, entidades/componentes/prefabs, iluminação, sombras, VFX, 2.5D ou 3D. Esses itens permanecem nas linhas independentes e etapas posteriores do plano.

## 8. Rollback e imutáveis

O rollback do código de P2D-01B é o commit `11b6970be7b44d22fa44105043915d12e335a179`. C3, baselines, tolerâncias, auditores, contratos G/V/B e artefatos selados anteriores não foram modificados. Nenhum push, tag, merge ou limpeza de untracked foi executado nesta etapa até a revisão humana final.
