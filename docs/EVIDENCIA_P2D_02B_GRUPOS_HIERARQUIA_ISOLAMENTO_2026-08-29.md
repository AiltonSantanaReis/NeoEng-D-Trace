# NeoEng-D-Trace — Evidência P2D-02B: grupos, hierarquia, membership e isolamento

**Status:** ACCEPTED LOCAL — P2D-02B fechada e requalificada pós-commit
**Data:** 29/08/2026 (UTC-03)
**Baseline de entrada:** `d152b214b1bccb717911001396936c1f93b23714`
**Commit da subetapa:** `af02f3ef513487bd176c939085fea0ca56a7da6b`
**Branch:** `modernization/multiaxis-ui`
**Subetapa:** P2D-02B — grupos, hierarquia/membership e isolamento
**Decisão:** `docs/DECISAO_P2D_02B_GRUPOS_HIERARQUIA_ISOLAMENTO_2026-08-29.md`

## 1. Escopo e disposição

P2D-02B implementa o primeiro sistema profissional de grupos do editor de
composição 2D baseado em objetos. O escopo é restrito ao editor profissional
de cenários e preserva o contrato V1, os modelos legados, os menus globais,
as linhas independentes e as baselines multiaxiais existentes.

O lote entrega:

- grupos persistidos com ID, nome, visibilidade, lock e membership explícita;
- hierarquia `grupo -> subgrupo -> objeto` por `parent_group_id` em schema V2;
- seleção de grupo com seleção dos objetos descendentes;
- criação, renomeação, exclusão, reordenação e reparenting undoable;
- inclusão e remoção de objetos do membership;
- visibilidade e lock herdados pelos descendentes;
- isolamento transitório de um grupo na viewport;
- limpeza do isolamento em reload/reset, sem dirty state e sem undo/redo;
- árvore Qt real integrada ao inspector profissional;
- mensagens de bloqueio sem traceback e sem estado parcial;
- persistência e round-trip do parent, membership, visibilidade e lock.

Não foram implementados neste lote pastas, tags, filtros, transformações de
grupo, alteração de camada/z-order, tilemap, colisão de cenário, NavMesh,
entidades/componentes/prefabs, iluminação ou VFX.

## 2. Contrato técnico verificado

O schema V1 permanece com `SceneGroupAuthoringRecord` sem parentagem. O schema
V2 usa `SceneGroupAuthoringRecordV2` com `parent_group_id` opcional. A
validação rejeita parent desconhecido e ciclos. Membership referencia somente
IDs de objetos existentes e pode ser múltiplo para preservar compatibilidade
com o comportamento anterior.

A exclusão de grupo preserva os objetos, remove somente o grupo e promove os
subgrupos para o parent do grupo removido. Reordenação altera apenas a ordem
persistida entre irmãos. Nenhuma operação altera transform, asset, camada,
ID de objeto, QAction, atalho ou árvore do editor legado.

Visibilidade e lock são avaliados por helpers puros compartilhados pelo modelo,
preview e viewport. Um objeto fica invisível ou bloqueado quando o próprio
objeto, sua camada, seu grupo direto ou qualquer ancestral determinar isso. A
mensagem de lock identifica o grupo efetivamente responsável, inclusive quando
o objeto pertence apenas a um subgrupo.

O isolamento é estado de sessão: não é serializado, não cria snapshot, não
altera `is_dirty` e não cria entrada de undo/redo. Um ID isolado inexistente é
rejeitado; reload/reset limpa o estado.

## 3. Fronteira de arquivos

Arquivos de produto, teste e documentação pertencentes ao lote:

- `src/persistence/scene_authoring_schema.py` — record V2 e validação de parentagem;
- `src/core/scene_authoring_groups.py` — semântica única de grupos, herança e isolamento;
- `src/core/scene_authoring_model.py` — mutações undoable e invariantes de membership;
- `src/core/scene_authoring_session.py` — wrappers transacionais e isolamento de sessão;
- `src/core/scene_authoring_preview.py` — projeção de visibilidade efetiva;
- `src/ui/scene_authoring_group_stack.py` — árvore e controles do inspector;
- `src/ui/scene_authoring_viewport.py` — visibilidade/lock efetivos e mensagem de bloqueio;
- `src/ui/scenario_editor_window.py` — integração exclusiva na janela profissional;
- `tests/test_p2d_02b_group_hierarchy_flow.py` — schema, operações, UI e isolamento;
- `scripts/audit_p2d_02b_group_hierarchy_flow.py` — fluxo end-to-end Qt;
- `docs/DECISAO_P2D_02B_GRUPOS_HIERARQUIA_ISOLAMENTO_2026-08-29.md` — decisão normativa;
- este documento — evidência do lote.

Também foi corrigida uma referência de caminho absoluto no registro aceito do
P2D-02A para satisfazer o contrato de higiene documental. Essa correção não
altera o conteúdo técnico, a evidência, o artefato ou a baseline do P2D-02A.

## 4. Fluxo de usuária comprovado

O auditor abriu a janela profissional com uma cena contendo três objetos,
selecionou dois objetos e criou o grupo `Composition`. Em seguida, criou o
subgrupo `Group 2` com parent `Composition` e membership do objeto
`foreground_object`.

O fluxo observou:

1. a árvore profissional com grupo raiz, subgrupo e objetos;
2. seleção do grupo e seleção dos descendentes;
3. isolamento do subgrupo, deixando somente `foreground_object` na viewport;
4. limpeza do isolamento sem alterar o documento salvo;
5. ocultação do grupo raiz, retirando seus descendentes e mantendo o objeto sem grupo;
6. lock do grupo raiz, herdado pelo objeto descendente;
7. tentativa de mover o objeto bloqueado rejeitada sem exceção, alteração de documento,
   alteração de histórico ou gesto ativo;
8. save/reload preservando grupos, parentagem, memberships, visibilidade e lock;
9. reload limpando o isolamento e restaurando os três objetos na viewport.

Mensagem observada no bloqueio:

```text
Cannot edit 'foreground_object': group 'Composition' is locked.
```

## 5. Gates e resultados

| Gate | Resultado |
|---|---:|
| compilação dos módulos, testes e auditor | PASS |
| testes focados P2D-02B | 3 passed |
| auditoria end-to-end Qt Windows | exit 0 |
| auditoria end-to-end Qt offscreen | exit 0 |
| suíte completa | 1779 passed / 2 skipped / 0 failed |
| `git diff --check` | PASS, somente avisos de line ending do Git |
| documento inalterado após tentativa bloqueada | `true` |
| histórico inalterado após tentativa bloqueada | `true` |
| gesto ativo após tentativa bloqueada | `false` |
| isolamento após reload | `null` |
| resolução nativa auditada | `1280×820` |

Comando da suíte final desta fase de precommit:

```text
$env:QT_QPA_PLATFORM='offscreen'
$env:PYTHONPATH=WORKSPACE_ROOT
WORKSPACE_ROOT/.venv/Scripts/python.exe -m pytest -q
1779 passed, 2 skipped in 48.67s
```

Auditoria Windows:

```text
WORKSPACE_ROOT/tmp-p2d-02b-flow-windows-20260829-r2
```

Auditoria offscreen:

```text
WORKSPACE_ROOT/tmp-p2d-02b-flow-offscreen-20260829-r2
```

Cada diretório contém `report.json`, a cena round-trip e sete capturas:
`00-initial.png`, `01-group-created.png`, `02-hierarchy.png`,
`03-isolated-subgroup.png`, `04-group-hidden.png`,
`05-locked-inherited-rejected.png` e `06-after-reload.png`.

## 6. Revisão visual técnica

As capturas nativas foram inspecionadas no fluxo real. A árvore de grupos e o
subgrupo aparecem no inspector; o isolamento reduz somente a projeção da
viewport; o estado bloqueado permanece visível na árvore e a mensagem aparece
no status; o reload restaura a composição sem reter isolamento. Não foram
observados clipping, deslocamento de viewport, alteração de camada, mudança de
transform ou delta fora dos estados deliberadamente exercitados.

Esta auditoria cobre a resolução lógica `1280×820`. A validação em outras
resoluções-alvo permanece uma atividade posterior de revisão visual, não sendo
declarada por este documento.

## 7. Critérios de aceite e estado atual

Os critérios de schema, modelo, session, árvore, membership, herança de
visibilidade/lock, isolamento transitório, undo/redo, round-trip, testes e
fluxo Windows foram satisfeitos nesta evidência pós-commit.

O lote foi fechado localmente após a revisão da fronteira staged, o commit
funcional, a requalificação pós-commit e a confirmação da árvore rastreada.
Nenhuma mutação remota foi realizada durante esta consolidação.

## 8. Requalificação pós-commit e fechamento

| Gate pós-commit | Resultado |
|---|---:|
| HEAD/branch | af02f3ef513487bd176c939085fea0ca56a7da6b / modernization/multiaxis-ui |
| tracked status após commit funcional | 0 modificações |
| suíte completa | 1779 passed / 2 skipped / 0 failed em 47.01s |
| auditoria Qt Windows | exit 0 |
| auditoria Qt offscreen | exit 0 |
| resolução auditada | 1280×820 |
| tentativa em grupo bloqueado | exception=null |
| documento/histórico após rejeição | true / true |
| gesto ativo após rejeição | false |
| isolamento após reload | null |
| igualdade das sete capturas pré/pós-commit | 7/7 SHA-256 idênticas |

Auditoria Windows pós-commit:

WORKSPACE_ROOT/tmp-p2d-02b-flow-windows-postcommit-20260829

Auditoria offscreen pós-commit:

WORKSPACE_ROOT/tmp-p2d-02b-flow-offscreen-postcommit-20260829

A evidência precommit e pós-commit foi preservada nos diretórios de auditoria.
A implementação não altera o modelo legado, o schema V1, transformações,
camadas, assets, menus globais ou linhas independentes.

O resultado fecha a subetapa P2D-02B — grupos, hierarquia/membership e
isolamento — como ACCEPTED LOCAL. Push, tag e merge permanecem limitados à
branch desta linha e ao procedimento de autorização explícita.

## 9. Continuidade segura

Se uma requalificação futura divergir, a decisão de aceite deverá ser reaberta
formalmente usando os relatórios preservados; não se deve alterar tolerância,
baseline, auditor ou o contrato V1 para forçar aprovação.

Após o fechamento de P2D-02B, P2D-02 continuará aberta somente para os itens
explicitamente previstos em estágio posterior, sem reabrir este lote sem novo
finding ou decisão formal.
