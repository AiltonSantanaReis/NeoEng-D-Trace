# Evidência da Etapa 4 — Barra superior

## 1. Identificação e escopo

- Plano de origem: `docs/PLANO_INTERFACE_MODERNA_PROFISSIONAL_2026-08-21.md`.
- Escopo executado: `Etapa 4 — Barra superior`.
- Branch de trabalho: `Ailton/interface-stage4-top-toolbar`.
- Base observada antes do commit: `640fed7c0361da8537d29f1528f228bf77480f79`.
- Estado: implementação técnica aprovada localmente; fechamento formal depende do ciclo Git remoto, CI e validação pós-merge.

Esta etapa reorganiza a barra superior em grupos semânticos, usando separadores nativos, ícones determinísticos, tooltips e nomes acessíveis, preservando a identidade das `QAction`s, menus tradicionais e atalhos já existentes. As três toolbars públicas (`main_toolbar`, `navigation_toolbar` e `xray_toolbar`) continuam disponíveis para compatibilidade.

Ficam explicitamente fora desta etapa: reposicionamento do HUD/Gizmo no viewport, refatoração dos painéis laterais e criação/alteração do editor separado de cenários. Esses itens pertencem às etapas correspondentes do plano e não foram misturados nesta implementação.

## 2. Alterações verificadas

- `src/ui/top_toolbar.py`: coordenador da composição, grupos, separadores nativos, metadados acessíveis e ícones inline determinísticos.
- `src/ui/icon_library.py`: integração do coordenador sem aumentar o acoplamento do `MainWindow`.
- `tests/test_stage4_ui_top_toolbar.py`: testes de ordem, identidade, separadores, ícones, acessibilidade e propriedades das toolbars.
- `scripts/audit_stage4_ui_top_toolbar.py`: auditoria funcional ao vivo, captura, execução do auditor visual e relatório com fonte, ambiente, limitações e status.
- `docs/evidence/artifacts/ui-modernization-stage4-20260822/`: capturas PNG, manifestos, hashes, relatório JSON/Markdown, imagens anotadas e logs.

O desenho preserva as ações existentes; não houve remoção silenciosa de menus ou atalhos. O contrato auditado declara `stage=4`, `native_separators=true`, `action_identity_preserved=true` e os papéis `commands`, `context` e `render`.

## 3. Testes reais executados

### 3.1 Testes funcionais

- Testes focados da UI e da Etapa 4: `21 passed`.
- Suite completa: `1592 passed, 2 skipped`.
- Cobertura com branches: `91,21%`.
- Política de cobertura: PASS (`total lines >= 90%`, `total branches >= 85%`, módulos mensuráveis conforme a política).
- Compilação dos módulos alterados: PASS.
- Black/isort/flake8 dos arquivos novos: PASS.
- `git diff --check`: PASS.

Durante a validação, a suite detectou uma regressão real e temporária no limite arquitetural de linhas do `MainWindow` (`1201 < 1200`). A integração foi reposicionada para o ponto de extensão existente em `icon_library.py`; a reexecução completa terminou com `1592 passed, 2 skipped`. O teste não foi enfraquecido nem removido.

### 3.2 Auditoria e capturas

O auditor executou o aplicativo Qt real em modo `offscreen`, gerou capturas e executou Pillow/OpenCV sobre os PNGs. Foram validados decodificação, dimensões, transparência, hashes SHA-256, clipping, geometrias Qt, sobreposição, paleta QSS e imagens anotadas.

- Auditoria funcional da barra: `PASS`, `failure_count=0`.
- Captura: retorno `0`.
- Auditor visual: `PASS`, `finding_count=0`, retorno `0`.
- Resoluções efetivas: `1920x1080`, `1366x768` e `1280x720`.
- Estados capturados: sem projeto, projeto com painéis, validação e feedback do Gizmo.
- Artefatos anotados: gerados para cada PNG auditado.

Os relatórios registram que o layout compacto altera a visibilidade responsiva das toolbars conforme a largura disponível. Isso é comportamento observado pelo aplicativo, não foi convertido em falso defeito. A inspeção visual humana das capturas reais não identificou clipping ou sobreposição evidente na barra superior. O backend Qt `offscreen` pode produzir diferenças de fonte em relação à janela Windows com DPI nativo; essa limitação permanece declarada e não é apresentada como validação de DPI nativo.

## 4. Proveniência e hashes

Os valores abaixo foram calculados sobre os arquivos existentes no workspace após a execução dos auditores:

| Artefato | SHA-256 |
|---|---|
| `raw-captures/manifest.json` | `E22E77F154807CBCEEA83AAB67C4CB8AF378F8BC4D4533AC56D31CCA1D1BCB8C` |
| `visual-audit/visual-audit-report.json` | `2A5FC2FD72D391C45B05324998DADEF6851032A58F480AA6548D313F7A95EEDC` |
| `stage4-top-toolbar-report.json` | `DC56FB8A10811DAA72CAED180224B93E6249985BCB93BBDA55F0312636A21E2E` |
| `artifact-index.json` | `A5D045EE6494F50A6719659ACFD4F30DCBB3784E15C66FB47F8F87D877A6F1A3` |

Os hashes individuais dos PNGs estão no manifesto bruto e no relatório visual. O relatório técnico registra a fonte como `640fed7c...` e `worktree_clean=false` porque foi produzido antes do commit; isso é uma condição de proveniência explícita, não uma tentativa de ocultar alterações. A auditoria deverá ser repetida após o commit para registrar o SHA efetivo e confirmar a árvore limpa.

## 5. Limitações e decisão

Não há evidência de regressão funcional nesta etapa após a correção verificada do limite arquitetural. A implementação está completa dentro do escopo da barra superior. A aprovação formal da Etapa 4 fica condicionada a: commit sem alterações não relacionadas, reauditoria pós-commit, baseline Git-blob, push, PR, CI verde nos jobs oficiais, revisão dos artefatos, merge sem force e validação pós-merge.
