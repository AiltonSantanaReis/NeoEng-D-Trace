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
- Testes focados pós-limpeza de metadados e localização: 38 aprovados (`test_asset_packs`, editor profissional de cena, contrato parallax e autoria de material).
- Suíte oficial: 2.166 aprovados, 2 ignorados, 1 warning de depreciação; log em `artifacts/pack-pilot-pytest-20260910-localization.log`.

## Critérios observados

- `PASS` no contrato de manifesto, caminhos contidos, dimensões declaradas e hashes SHA-256.
- `PASS` na busca sem acento, carregamento de miniaturas, seleção e prévia Qt.
- `PASS` na importação repetida sem duplicação, cópia para o projeto, posicionamento, undo/redo e reabertura portátil.
- `PASS` na rejeição de asset adulterado sem mutação do projeto.
- `PASS` na disponibilidade do catálogo sem projeto salvo e bloqueio da importação nesse estado.
- `PASS` no fluxo nativo comprovado de catálogo → prévia → importação → inserção por clique → salvamento → fechamento → reabertura, descrito abaixo.
- `PASS` no menu contextual localizado da Biblioteca de assets, com `Inserir na cena` e `Atualizar` observados no binário atual.
- `PENDING_EVIDENCE` para arraste direto no binário novo, menu contextual do viewport/editor de cenário, captura em DPI real, desempenho de catálogo grande e revisão artística.

## Evidência nativa histórica preservada

Esta seção mantém a execução anterior para rastreabilidade; ela não é a build de
aceite da correção de localização atual.

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

## Evidência nativa do build atual — localização e persistência

Build executada fora do checkout a partir do commit
`23cfed0f646cbe141a2e774da9ca7f3231105bc0`:

- Diretório: `release/asset-packs-floresta-localization-20260910/`.
- Executável: `portable/NeoEng-D-Trace/NeoEng-D-Trace.exe`.
- SHA-256 do executável: `B639C46144B2D6C9237B9E8B07C57480134FDF4F9EC5D0B6015B4000568D486C`.
- Pacote portátil: `NeoEng-D-Trace-0.3.0-win64-portable.zip`.
- SHA-256 do pacote portátil: `15197E1082338AA201A5171CDAD534D814FCF498A5B24B51C6F4C2562CC108B9`.
- Smoke report: `release/asset-packs-floresta-localization-20260910/smoke/portable-smoke-report.json`, `SUCCESS`.
- Proveniência: `release/asset-packs-floresta-localization-20260910/continuity-provenance.json`, `PASS`, commit de origem e hash do executável conferidos.

Fixture nativo utilizado: `artifacts/native-asset-localization-project/floresta-localization-pilot.ndtproj`.
As capturas abaixo foram exibidas pelo estado real do aplicativo nativo durante a
sessão; não são mocks nem imagens de referência.

1. A abertura inicial do editor exibiu `Camada/profundidade: —`, `Nenhum objeto selecionado`, `Profundidade Z`, `Z00 Default ... 0 objetos` e `Autoria de cenário` em português.
2. `Biblioteca` → `Pacotes NeoEng` abriu `Floresta · 0.1.0-piloto` com seis miniaturas. A busca real `arvores` reduziu a grade a `Pinheiro`; a prévia exibiu `Árvores · 1254 × 1254 px`, PNG com canal alpha e descrição localizada.
3. `Adicionar ao projeto` exibiu `Pinheiro: adicionado na biblioteca do projeto. Volte à biblioteca para arrastar até uma moldura.`; a Biblioteca registrou `Assets: 1`, `Exibindo: 1`, `Problemas: 0`, `Em uso: 0` e `0 objetos`.
4. O clique direito real sobre a linha do asset exibiu o menu contextual localizado com `Inserir na cena` e `Atualizar`.
5. `Inserir na cena` pelo menu contextual renderizou o Pinheiro, selecionou `asset_97a6dc8960cf81dc`, exibiu `Asset colocado: asset_97a6dc8960cf81dc — alterações não salvas`, e atualizou a Biblioteca para `Em uso: 1` e `1 objeto`.
6. `Salvar` exibiu `Cenário salvo`. O editor foi fechado, o aplicativo foi reaberto com o mesmo fixture e a captura confirmou o Pinheiro no viewport, `Z00 Default ... 1 objeto`, `Assets: 1`, `Em uso: 1`, `Problemas: 0` e `1 objeto`.
7. Após a reabertura, o processo foi encerrado nativamente e não restou janela do executável na enumeração final.

O sidecar observado em `artifacts/native-asset-localization-project/floresta-localization-pilot.ndtscene.json` contém `schema_version: 2`, o asset com SHA-256, `layer_default`, um objeto em `objects` e uma entrada em `parallax_layers`. Isso comprova a persistência do estado salvo, não apenas a aparência da captura.

## Pendências observadas na execução nativa

- O arraste direto da linha da biblioteca para o viewport foi tentado na execução anterior e permaneceu em `0 object(s)`. O resultado foi preservado como falha observada; o botão de inserção é um fallback híbrido funcional, não uma correção declarada do arraste.
- O clique direito no viewport não abriu menu contextual e deixou a mensagem inglesa `Objects moved`. O sidecar permaneceu sem alteração (`x=-1`, `y=-1`, `z=0`). A localização e o contrato de menu contextual continuam pendentes.
- A primeira execução oficial após a adição do botão foi preservada em `artifacts/pack-pilot-pytest-20260910-place-button.log`; ela falhou na higiene de referências porque os PNGs gerados carregavam metadados C2PA com o termo proibido. Os metadados foram removidos sem alterar pixels, dimensões, modo ou alpha; a execução histórica posterior registrou `2165 passed`, antes da correção de localização atual.
- A execução oficial mais recente, após a correção de localização, está preservada em `artifacts/pack-pilot-pytest-20260910-localization.log` com `2166 passed, 2 skipped, 1 warning` e código de saída 0. O warning é a depreciação conhecida de `QMouseEvent` em `tests/test_merge_coverage_authoring_contracts.py:1341`.

## Limitações preservadas

Os seis objetos são um piloto visual assistido por IA para avaliação interna. O
acabamento de bordas/halos ainda precisa de revisão humana, especialmente no
tronco. A árvore gerada com fundo quadriculado foi rejeitada e não entrou no
catálogo. Ainda não foram incluídos os planos de parallax, terreno/tileset, cena
exemplo, instalador de pacotes ou as coleções Ruínas e Cidade futurista.

O validador nativo genérico continua `INCOMPLETE` porque espera eventos do editor
de referência que não pertencem a este fluxo; portanto ele não é usado como prova
de aceite do catálogo. Também permanecem pendentes a medição de DPI/desempenho e a
revisão artística humana.

## Próxima prova obrigatória

Corrigir e comprovar o arraste direto com uma captura nativa, definir o contrato do
menu contextual do editor de cenário e repetir a suíte completa. Depois disso ainda
serão necessárias a revisão humana dos seis PNGs, a medição de catálogo grande e os
pacotes Ruínas/Cidade futurista. O estado do piloto permanece `PENDING_EVIDENCE`.
