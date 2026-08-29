# NeoEng-D-Trace — Evidência P2D-01A

## Assets controlados, provenance e renderização real

**Data:** 2026-08-29 (UTC-03)
**Linha:** P2D-COMP-01 / P2D-01A
**Estado:** ACCEPTED — SUBETAPA FECHADA
**Parent checkpoint:** 9cb39fbc629931b4e88d3108bca3319453277673
**Commit P2D-01A:** e4af231c3c490245240d90e70857b98995446581
**P2D-COMP-01:** OPEN — esta evidência não representa aceite do produto completo.

## 1. Decisão aplicada

A política aprovada no registro `DECISAO_P2D_01_ASSETS_ORIGINAIS_E_IMPORTACAO_2026-08-29.md` foi aplicada ao primeiro sublote:

- assets externos são validados, copiados atomicamente para `assets/scene/` e referenciados somente pelo caminho relativo controlado;
- o SHA-256 do arquivo efetivamente persistido é obrigatório;
- o caminho original é preservado em `source_path` apenas como provenance e nunca é usado para carregar a cena;
- assets já dentro da raiz do projeto mantêm o caminho relativo existente e não são duplicados;
- colisão de nome/hash não sobrescreve arquivo existente;
- raster (`PNG`, `JPG`, `JPEG`, `WEBP`, `BMP`, `GIF`) e SVG são aceitos somente quando o Qt consegue decodificá-los;
- missing, tamper, conteúdo inválido e caminho inseguro geram diagnóstico explícito;
- limpeza automática de cópias não utilizadas não foi implementada, para não criar remoção destrutiva fora do escopo.

## 2. Alterações delimitadas

| Área | Resultado |
|---|---|
| `src/core/scene_asset_library.py` | validação, hash, resolução, cópia content-addressed e retorno determinístico |
| `src/persistence/scene_authoring_schema.py` | `source_path` opcional, não portátil e validado |
| `src/persistence/scene_authoring_io.py` | canonicalização legada permanece estável quando provenance é ausente |
| `src/ui/scene_authoring_viewport.py` | drop controlado, carregamento raster/SVG, pintura do asset real e diagnóstico |
| testes | cobertura focada do contrato e atualização do caso que antes exigia rejeição externa |
| scripts/audit_p2d_01_scene_assets.py | capturador focal com nomes atuais, overlay real e verificação de pixmap |
| captura Windows 1:1 | PASS; 6 PNGs em três resoluções, 0 findings; manifest SHA-256 c5151733036c965e65469cb059dbb22a350b90a36d7e9506beed2c885b6d89b5 |
| captura Windows pós-commit | PASS; 6/6 PNGs byte-identical ao pré-commit; manifest SHA-256 e20ccfa609e4b04558912b5f102368dabb29d8f97bebd900d118029794ce872b |

Não foram alterados camada, ordem de desenho, seleção, gizmo, transformações, exportadores, colisão, NavMesh, entidades, iluminação, VFX, C3 ou gates G/V/B.

## 3. Evidência executada

| Verificação | Resultado |
|---|---|
| Python | `.venv\\Scripts\\python.exe`, Python 3.11.9 |
| Sintaxe | `py_compile` dos módulos alterados: PASS |
| Suíte P2D-01A + stages 2–5 | **77 passed, 0 failed** |
| Cópia externa | PASS; destino `assets/scene/`, conteúdo e hash verificados |
| Reuso por hash | PASS; segunda preparação não duplica arquivo |
| Asset interno | PASS; caminho relativo preservado, sem provenance externo |
| Tamper/missing | PASS; resolução retorna diagnóstico e não fallback silencioso |
| Raster real | PASS; viewport pinta pixels do PNG verificado |
| SVG original | PASS; viewport carrega dimensões e pinta SVG via `QSvgRenderer` |
| Rollback de importação | registro da cena permanece transacional; cópia órfã não é apagada automaticamente |

## 4. Resultado final da subetapa

P2D-01A está ACCEPTED e fechada:

- o gate visual pré-commit executou em Windows com escala determinística 1:1;
- as resoluções lógicas e físicas coincidiram em 1280x720, 1366x768 e 1920x1080;
- Pillow/OpenCV, dimensões, transparência, SHA-256, clipping, geometria, overlap e paleta passaram;
- o viewport carregou o asset como pixmap real de 180x120;
- o overlay profissional foi ativado para exercer a cor interativa no estado real;
- o auditor produziu 0 findings no pré-commit e 0 findings no pós-commit;
- a comparação commit-to-commit produziu 6/6 PNGs byte-identical, sem delta visual fora do estado controlado;
- a full suite pós-commit produziu 1768 passed, 2 skipped, 0 failed.

A captura anterior em escala 200% permanece preservada como evidência de variância DPI e não foi usada para forçar PASS.

### 4.1 Fechamento e próximo estágio

O commit e4af231c3c490245240d90e70857b98995446581 é o fechamento da subetapa P2D-01A. A subetapa seguinte é P2D-01B, ainda pendente, para biblioteca/UX de assets, lifecycle de relink/replace/missing e evidência de uso no produto. P2D-01 maior e P2D-COMP-01 continuam OPEN.

## 5. Não implementado por decisão de escopo

Esta subetapa não adiciona tilesets/tilemaps, pincéis, balde, borracha, autotiling, grids isométricos/hexagonais, colliders de cenário, NavMesh, entidades/componentes/prefabs, iluminação, sombras, VFX, 2.5D ou 3D. Esses itens permanecem nas linhas independentes ou etapas posteriores documentadas.

## 6. Rollback e imutáveis

O rollback é o parent checkpoint indicado acima. C3, baselines, tolerâncias, auditores e artefatos selados não foram modificados. Nenhum push, tag, merge, limpeza de untracked ou mutação remota foi executado.
