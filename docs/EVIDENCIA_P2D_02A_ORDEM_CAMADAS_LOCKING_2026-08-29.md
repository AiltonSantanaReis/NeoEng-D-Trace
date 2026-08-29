# NeoEng-D-Trace — Evidência P2D-02A

**Status:** PASS LOCAL — subetapa pronta para commit e requalificação
**Data:** 29/08/2026 (UTC-03)
**Baseline de entrada:** `eb941e60a06a065c54433f852970a50b7ebeb56a`
**Subetapa:** P2D-02A — ordem visual, camadas, visibilidade e bloqueio seguro
**Decisão:** `docs/DECISAO_P2D_02A_ORDEM_CAMADAS_LOCKING_2026-08-29.md`

## 1. Resultado

P2D-02A foi implementada e verificada localmente. O editor profissional agora
usa uma ordem visual determinística derivada da ordem persistida das camadas:
primeira camada = `back`, última camada = `front`; objetos da mesma camada
preservam a ordem de `document.objects`. O valor não é gravado no documento e
`transform.position.z` permanece inalterado.

A tentativa de editar objeto ou seleção bloqueada deixou de propagar uma
exceção técnica. A operação é rejeitada com mensagem de usuário, sem alteração
de posição, sem gesto ativo e sem nova entrada de undo/redo.

## 2. Fronteira de código

Arquivos pertencentes à subetapa:

- `src/core/scene_authoring_order.py` — contrato único da ordenação;
- `src/core/scene_authoring_preview.py` — projeção em ordem de camadas;
- `src/ui/scene_authoring_viewport.py` — z visual, ressincronização e lock UX;
- `src/ui/scene_authoring_layer_stack.py` — indicação explícita `Back → Front`;
- `tests/test_p2d_02a_layer_flow.py` — fluxo Qt, preview, persistência e lock;
- `scripts/audit_p2d_02a_layer_flow.py` — auditoria end-to-end da janela;
- este registro e a decisão técnica correspondente.

Nenhum arquivo do editor principal, do modelo legado, do schema, dos adapters,
dos menus globais ou das linhas independentes foi alterado.

## 3. Gates executados

| Gate | Resultado |
|---|---:|
| `git diff --check` | PASS |
| compilação dos módulos e auditor | PASS |
| testes focados P2D-02A | 2 passed |
| regressão profissional + P2D-01B | 60 passed |
| suíte completa | 1776 passed / 2 skipped / 0 failed |
| auditoria Qt end-to-end offscreen | exit 0 |
| auditoria Qt end-to-end Windows | exit 0 |
| exceção na tentativa bloqueada | nenhuma |
| documento inalterado na tentativa bloqueada | true |
| histórico inalterado na tentativa bloqueada | true |
| gesto ativo após rejeição | false |

Comando da suíte completa:

```text
$env:QT_QPA_PLATFORM='offscreen'
.\.venv\Scripts\python.exe -m pytest -q
1776 passed, 2 skipped in 48.99s
```

Comando da auditoria de fluxo:

```text
$env:QT_QPA_PLATFORM='windows'
.\.venv\Scripts\python.exe scripts\audit_p2d_02a_layer_flow.py \
  --output WORKSPACE_ROOT/tmp-p2d-02a-flow-windows-20260829
exit 0
```

O relatório do fluxo registrou `qt_platform=windows`, resolução lógica
`1280×820`, `exception=null`, `document_unchanged=true`,
`history_unchanged=true` e `gesture_active=false`.

## 4. Fluxo de usuária comprovado

1. Abrir projeto salvo e entrar na janela profissional.
2. Confirmar asset real e dois objetos sobrepostos no viewport.
3. Selecionar a camada `Foreground` na lista.
4. Acionar `Up` e observar a ordem declarada e a cobertura visual mudarem.
5. Ocultar a camada e confirmar que somente seus objetos saem do viewport.
6. Reexibir a camada.
7. Bloquear a camada, selecionar o objeto e tentar movê-lo/girá-lo pelo gizmo.
8. Confirmar mensagem objetiva, nenhum traceback e nenhum estado parcial.
9. Salvar o cenário, recarregar e confirmar ordem e lock persistidos.

Capturas nativas revisadas manualmente:

```text
WORKSPACE_ROOT/tmp-p2d-02a-flow-windows-20260829/captures/00-initial.png
WORKSPACE_ROOT/tmp-p2d-02a-flow-windows-20260829/captures/01-after-reorder.png
WORKSPACE_ROOT/tmp-p2d-02a-flow-windows-20260829/captures/02-layer-hidden.png
WORKSPACE_ROOT/tmp-p2d-02a-flow-windows-20260829/captures/03-locked-rejected.png
WORKSPACE_ROOT/tmp-p2d-02a-flow-windows-20260829/captures/04-after-reload.png
```

Observações visuais: `Render order: Back → Front` aparece junto ao layer
stack; reorder altera a silhueta/cobertura do viewport; a camada bloqueada
exibe `[locked]`; o status informa `Cannot edit ... its layer is locked.`;
save/reload conserva a composição e o estado de lock. Não foram observados
clipping, deslocamento estrutural ou delta fora da janela profissional.

As diferenças medidas entre os frames foram classificadas como esperadas:

```text
initial_vs_reorder: changed_pixels=42896 bbox=(746, 726, 2518, 1636)
reorder_vs_hidden: changed_pixels=7021 bbox=(746, 726, 1781, 1343)
reorder_vs_locked: changed_pixels=7266 bbox=(1753, 834, 2518, 1636)
locked_vs_reload: changed_pixels=40191 bbox=(746, 726, 2518, 1636)
```

## 5. Pendências honestas

Esta evidência não aceita P2D-02 completo. Permanecem deliberadamente fora de
P2D-02A:

- grupos e desagrupamento;
- hierarquia de objetos e membership editing;
- isolamento/s solo de camada ou grupo;
- pastas, tags e filtros de hierarquia.

Esses itens exigirão P2D-02B com contrato, modelo, UI, persistência e fluxo
próprios. Não há declaração de que estejam implementados.

## 6. Próxima decisão operacional

Antes do commit, deve ser feita a prova final de branch/HEAD/tracked boundary e
o stage deve conter somente os oito arquivos listados na seção 2. Depois do
commit, repetir suíte, auditoria Windows e captura pós-commit; só então marcar
P2D-02A como fechada. Push remoto, tag ou merge continuam dependentes de
autorização explícita.
