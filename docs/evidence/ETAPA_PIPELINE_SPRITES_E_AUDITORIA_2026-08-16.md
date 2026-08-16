# Auditoria de implementação e evidências — pipeline de sprites

Data: 2026-08-16
Branch: codex/export-pipeline-completion
Base auditada: origin/main em 535122bf7128f584328d058295006758f7134615
Commit do conteúdo funcional e das evidências: 8dc60a4. O relatório é vinculado a esse commit por um commit documental posterior.

## Escopo

Foram verificadas as sete etapas recomendadas para o fluxo de sprites, colisão e exportação. A regra de aprovação foi: comportamento real executado pelo projeto, testes automatizados, artefatos com manifesto SHA-256 e nenhum bypass de cobertura ou de validação.

## Resultado das etapas

| Etapa | Resultado | Evidência |
|---|---|---|
| Pivô/âncora e exportação | APPROVED | pivot-*.json e testes de contrato |
| Atlas com pixel extrusion/bleed | APPROVED | atlas/atlas_0.png, atlas_0.json e teste de duplicação real de bordas |
| Colisores compostos | APPROVED / REVALIDATED | compound-collision.json, compound-project.ndtproj, 3 partes convexas e round-trip |
| Snapping de vértices | APPROVED | snapping.json, testes de origem, grade, meio-termo e integração no canvas |
| Preparação de tileset | APPROVED | tileset/tileset.json e duas células PNG |
| Detecção em lote de animação | APPROVED | animation/animation.json, dois frames reais, ordenação natural e coerência por reamostragem/alinhamento |
| Plugins nativos Godot/Unity | NOT_APPLICABLE | A definição do produto v1.0 mantém perfis JSON/GLTF como contrato; plugins nativos ficam fora do escopo publicado |

A etapa de colisores compostos já existia no projeto. Ela foi revalidada com o fluxo existente, sem duplicar implementação nem declarar como nova uma funcionalidade que já estava presente.

## Testes e gates

- Suíte completa: 1070 passed, 10 warnings, sem falhas.
- Cobertura oficial: passou com linhas >= 90%, branches >= 85% e módulos mensuráveis >= 30%.
- flake8: passou.
- Black: passou; 193 arquivos inalterados pelo verificador.
- isort: passou.
- mypy: passou, sem problemas em 88 arquivos.
- compileall: passou.
- git diff --check: passou; os avisos apresentados são apenas normalização LF/CRLF do Git.
- Bandit: passou.
- pip-audit: nenhuma vulnerabilidade conhecida encontrada; o pacote local não publicado foi explicitamente reportado pela ferramenta como não auditável no PyPI.
- Saída bruta da suíte: docs/evidence/artifacts/export-pipeline-audit/full-test-results.txt.

## Evidência funcional do pipeline

O script scripts/audit_export_pipeline.py foi executado após as alterações finais. O manifesto está em docs/evidence/artifacts/export-pipeline-audit/manifest.json e contém hashes dos PNGs, JSONs e projeto gerados.

Os artefatos comprovam, respectivamente:

- pivô consistente nos perfis genérico, Godot, Unity e Phaser;
- bleed de 1 px no atlas;
- colisor composto persistido e exportado;
- snapping aplicado;
- slicing completo e colisão de tiles;
- processamento de frames em ordem natural e manifesto de animação;
- escritas atômicas dos manifestos.

## Auditoria visual da MainWindow

O script scripts/audit_ui_capture.py foi executado nativamente no Windows para evitar o falso positivo tipográfico observado no backend Qt offscreen.

Foram capturados os estados sem projeto, projeto com painéis, validação, modal e feedback do gizmo em:

- 1920x1080;
- 1366x768;
- 1280x720.

As PNGs e o manifesto estão em docs/evidence/artifacts/ui-audit-export-pipeline/. O manifesto registra tanto o tamanho lógico solicitado quanto o tamanho físico real do PNG devido à escala DPI do Windows.

A inspeção visual não encontrou clipping de texto, sobreposição do canvas pelos painéis ou inconsistência relevante no tema escuro nas três resoluções. O estado de validação exibiu a mensagem real: “No collision shapes registered. Use Auto-Generate first.” A diferença entre tamanho lógico da janela e tamanho físico das capturas foi registrada, não mascarada.

Limitação registrada: o backend Qt offscreen produz texto ilegível com o QSS atual por limitação do renderer/font database; isso não foi tratado como aprovação visual. A evidência visual aprovada é a captura nativa Windows.

## Auditoria dos últimos 10 merges de main

Foram examinados os dez merges de primeiro nível em origin/main, do PR #67 ao PR #54. Para cada um foram verificados o commit de merge, os arquivos alterados, o histórico de evidências e os checks remotos test e test-windows.

Resultado: os dez merges apresentavam ambos os checks remotos como SUCCESS. Os documentos históricos preservam falhas, limitações, warnings e estados RELEASE_APPROVED=NO quando aplicável. Não foi encontrada evidência de xfail, skip indevido, alteração do critério de cobertura, scanner adulterado ou falso artefato usado para aprovar uma etapa.

Observações importantes da auditoria:

- o PR #67 delimita o gizmo como contextual 2D; ele não prova um gizmo 3D completo;
- plugins nativos das engines não devem ser apresentados como existentes, pois permanecem fora do escopo v1.0;
- limitações do ambiente offscreen e falhas históricas foram documentadas, não ocultadas;
- a implementação está vinculada ao commit 8dc60a4; a aprovação remota depende dos checks do novo PR.

## Decisão

As alterações funcionais e os gates locais estão aprovados. O commit funcional foi criado como 8dc60a4. O push e o merge permanecem condicionados à aprovação dos checks remotos do novo PR.
