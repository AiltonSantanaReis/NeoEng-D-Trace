# PACK-01 / PACK-03 — Piloto Floresta e catálogo

**Estado:** `PENDING_EVIDENCE`
**Data:** 2026-09-10
**Base:** pós-E13, branch `Ailton/e08-renderer-20260908`
**Escopo:** primeiro incremento adicional; não reabre nem altera E13.

## Rastreamento

- Requisito: catálogo local de conteúdo próprio e importação controlada.
- Features: `PACK-01` (proveniência do piloto), `PACK-03` (catálogo), `PACK-04` (importação).
- Implementação: `src/core/asset_packs.py`, `src/ui/asset_pack_dialog.py`, integração em `src/ui/scene_asset_panel.py`.
- Conteúdo: `assets/scene/packs/floresta/manifest.json` e seis PNGs RGBA.
- Testes focados pós-limpeza de metadados: 27 aprovados (`test_asset_packs`, higiene de referências, ciclo P2D-01 e contrato de build).
- Suíte oficial: 2.165 aprovados, 2 ignorados, 1 warning de depreciação; log em `artifacts/pack-pilot-pytest-20260910-place-button-rerun.log`.

## Critérios observados

- `PASS` no contrato de manifesto, caminhos contidos, dimensões declaradas e hashes SHA-256.
- `PASS` na busca sem acento, carregamento de miniaturas, seleção e prévia Qt.
- `PASS` na importação repetida sem duplicação, cópia para o projeto, posicionamento, undo/redo e reabertura portátil.
- `PASS` na rejeição de asset adulterado sem mutação do projeto.
- `PASS` na disponibilidade do catálogo sem projeto salvo e bloqueio da importação nesse estado.
- `PASS` no fluxo nativo comprovado de catálogo → prévia → importação → inserção por clique → salvamento → fechamento → reabertura, descrito abaixo.
- `PENDING_EVIDENCE` para arraste direto no binário novo, menu de contexto do editor de cenário, captura em DPI real, desempenho de catálogo grande e revisão artística.

## Evidência nativa do binário

Build executada a partir do commit `8c14aac8c4dfcc7b30d2c966dc401845090c9033`:

- Diretório: `release/asset-packs-floresta-click-20260910/`.
- Executável: `portable/NeoEng-D-Trace/NeoEng-D-Trace.exe`.
- SHA-256 do executável: `A59BD5DC78E84D8D55404EC688E475FAB65FE6AD419C29064ACAC04063CE211B`.
- Smoke report: `release/asset-packs-floresta-click-20260910/smoke/portable-smoke-report.json`, `SUCCESS`.
- Suíte nativa genérica: aplicação abriu e fechou com código 0; o resumo permaneceu `INCOMPLETE` porque espera eventos do editor de referência que não fazem parte deste fluxo de cenário. O log também registra o fallback explícito de CPU por ausência de CuPy.

As capturas exibidas durante a sessão foram feitas no executável nativo com ações reais de ponteiro, sem mock de widget:

1. `Pacotes NeoEng` abriu a coleção `Floresta · 0.1.0-piloto` com seis miniaturas visíveis.
2. A busca `arvores` filtrou para `Pinheiro`; a prévia mostrou `1254 × 1254 px`, PNG com canal alpha e a descrição localizada.
3. `Adicionar ao projeto` exibiu `Pinheiro: adicionado na biblioteca do projeto`; a biblioteca passou a registrar `Assets: 1`, `Problemas: 0`, `Em uso: 0` e `0 object(s)`.
4. O botão híbrido `Inserir na cena` foi acionado por clique. O resultado observado foi `Asset colocado: asset_97a6dc8960cf81dc`, `Em uso: 1`, `1 object(s)`, seleção do mesmo ID no inspetor e o Pinheiro renderizado no viewport.
5. `Salvar` exibiu `Scenario saved`. O editor foi fechado e o sidecar `artifacts/native-asset-pilot-project/floresta-pilot.ndtscene.json` foi criado com `schema_version: 2`, um asset, um objeto em `layer_default` e a configuração parallax.
6. O mesmo binário foi relançado com o mesmo projeto. A captura de reabertura mostrou `Z00 Default · 1 objects`, o Pinheiro no viewport e a Biblioteca com `Assets: 1`, `1 object(s)`, `Em uso: 1` e `Problemas: 0`.

## Pendências observadas na execução nativa

- O arraste direto da linha da biblioteca para o viewport foi tentado na execução anterior e permaneceu em `0 object(s)`. O resultado foi preservado como falha observada; o botão de inserção é um fallback híbrido funcional, não uma correção declarada do arraste.
- O clique direito no viewport não abriu menu contextual e deixou a mensagem inglesa `Objects moved`. O sidecar permaneceu sem alteração (`x=-1`, `y=-1`, `z=0`). A localização e o contrato de menu contextual continuam pendentes.
- A primeira execução oficial após a adição do botão foi preservada em `artifacts/pack-pilot-pytest-20260910-place-button.log`; ela falhou na higiene de referências porque os PNGs gerados carregavam metadados C2PA com o termo proibido. Os metadados foram removidos sem alterar pixels, dimensões, modo ou alpha; a nova execução é a registrada como `2165 passed` acima.

## Limitações preservadas

Os seis objetos são um piloto visual assistido por IA para avaliação interna. O
acabamento de bordas/halos ainda precisa de revisão humana, especialmente no
tronco. A árvore gerada com fundo quadriculado foi rejeitada e não entrou no
catálogo. Ainda não foram incluídos os planos de parallax, terreno/tileset, cena
exemplo, instalador de pacotes ou as coleções Ruínas e Cidade futurista.

## Próxima prova obrigatória

Corrigir e comprovar o arraste direto com uma captura nativa, definir o contrato do
menu contextual do editor de cenário e repetir a suíte completa. Depois disso ainda
serão necessárias a revisão humana dos seis PNGs, a medição de catálogo grande e os
pacotes Ruínas/Cidade futurista. O estado do piloto permanece `PENDING_EVIDENCE`.
