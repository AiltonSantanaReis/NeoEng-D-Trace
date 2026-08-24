# Auditoria de conformidade — texto-fonte versus Etapas 0–9

**Data da auditoria:** 2026-08-23  
**Repositório:** NeoEng-D-Trace  
**Branch auditada:** `Ailton/stage9-postmerge-documentation`  
**Código funcional auditado:** merge SHA `98ffba1353941fd67ce46fc06be77f2f2abfcbb5`  
**HEAD documental:** `479be8e`  
**Objeto:** verificar se o texto-fonte colado foi aplicado integralmente nas Etapas 0–9, distinguindo implementação existente, escopo deliberadamente reduzido e requisito sem comprovação.

## 1. Parecer executivo

**Conclusão: o texto-fonte não foi seguido integralmente como contrato de completude das Etapas 0–9.**

O trabalho técnico está substancialmente implementado e possui boa disciplina de compatibilidade, testes e evidências pós-merge. Entretanto, os encerramentos anteriores foram aprovados em **escopos declarados mais estreitos** do que o texto-fonte completo. Por isso, “Etapa aprovada” nos documentos existentes não equivale a “todos os itens do texto-fonte atendidos”.

Classificação consolidada:

| Etapa | Parecer contra o texto-fonte | Síntese |
|---|---|---|
| 0 | **Parcial / não totalmente comprovada** | Baseline reproduzível comprovada; inventário completo, sinais públicos, cobertura, tempo de suíte e acessibilidade não ficaram demonstrados de forma auditável. |
| 1 | **Conforme no escopo implementado** | Tokens, QSS centralizado, estados, contraste e testes foram implementados; não há rastreabilidade item a item para toda a lista do texto-fonte. |
| 2 | **Parcial** | Biblioteca vetorial, fallback, tamanhos e matriz DPI existem; faltam chaves semânticas explícitas para `grid`, `scenario` e `validation`. |
| 3 | **Parcial** | Barra esquerda funcional para nove ferramentas; grupos de navegação e parte do grupo de colisão do texto-fonte não estão na barra esquerda. |
| 4 | **Parcial** | Arquivo, edição, view, render, exportação e Ctrl+K existem; grid/snap/configurações/busca de ferramentas/ações recentes não estão completos na organização exigida. |
| 5 | **Parcial** | View/zoom/snap e estado básico estão presentes; cursor, grade, gizmo, seleção e coordenadas de transformação não formam o HUD completo exigido. |
| 6 | **Parcial, majoritariamente implementada** | Transações, cancelamento, undo/redo, vertex gizmo e feedback numérico têm cobertura; a matriz DPI específica das interações do gizmo não foi comprovada. |
| 7 | **Parcial** | Quatro painéis e suas ações principais foram fechados; busca e o inspetor completo do texto-fonte não estão comprovados no editor principal. |
| 8 | **Conforme** | Editor separado, isolamento, camadas, inspeção, preview, persistência e exportação têm cobertura funcional e pós-merge. |
| 9 | **Parcial / evidência inconsistente** | Matriz 3 × 4 e geometria foram auditadas; menus na tela, scroll interativo e vários critérios funcionais não foram exercitados, e o artefato funcional bruto permanece `FAIL`/`NOT_CONFIRMED`. |

Portanto, a resposta objetiva é: **as etapas foram aplicadas parcialmente; não é tecnicamente correto declarar conformidade integral com o texto-fonte.**

## 2. Base e método

Foram confrontados:

1. O texto-fonte completo fornecido pelo usuário — 409 linhas, Etapas 0–9.
2. O plano derivado em `docs/PLANO_INTERFACE_MODERNA_PROFISSIONAL_2026-08-21.md`.
3. Código de produção em `src/`.
4. Testes focados e suíte registrados nas evidências.
5. Evidências versionadas em `docs/evidence/`, incluindo os encerramentos pós-merge.
6. Estado Git e diferença entre o merge funcional `98ffba1` e o HEAD atual.

O HEAD atual contém somente a reconciliação documental posterior ao merge: `CHANGELOG.md`, este conjunto documental e `docs/evidence/README.md`. Não foram identificadas alterações funcionais posteriores ao merge #160 durante esta auditoria.

Legenda usada:

- **Conforme:** requisito demonstrado por implementação e evidência compatível.
- **Parcial:** parte implementada, mas há requisito explícito ausente, deslocado para outro componente ou sem teste suficiente.
- **Não comprovado:** não foi possível concluir existência ou ausência; faltam inventário, teste ou evidência.
- **Divergência documental:** o texto narrativo declara mais do que o artefato técnico comprova.

## 3. Achados por etapa

### Etapa 0 — Baseline, governança e inventário

**Atendido:** há baseline reproduzível em três resoluções lógicas, estados de janela relevantes, manifestos com hashes, dimensões, transparência, geometria Qt, clipping, overlap, paleta e auditoria visual. A evidência também registra branch, SHA, worktree, limitações e a regra de não alterar produção.

**Lacunas contra o texto-fonte:**

- Não há inventário explícito e completo de todos os sinais públicos, nomes públicos e contratos usados por testes e outras telas.
- A evidência não apresenta um catálogo auditável de todas as ações da `MainWindow`, ferramentas da `ToolPalette`, abas, painéis, X-Ray, gizmo, navegação, editor de cenário, inspetores, menus, atalhos, status bar e exportadores.
- Cobertura de baseline, duração da suíte e critérios de acessibilidade básica não aparecem como resultados formais equivalentes aos demais campos do manifesto.
- A revisão humana consta como `NOT_CONFIRMED` na evidência de baseline.

**Parecer:** a caracterização visual foi realizada; a Etapa 0 completa, conforme o checklist detalhado do texto-fonte, ficou **parcialmente comprovada**.

### Etapa 1 — Tokens e camada visual

**Atendido:** `src/ui/theme_tokens.py` centraliza canvas, superfícies, bordas, textos, accent, selection, focus, success, warning e error. O QSS é gerado a partir dos tokens; os testes cobrem estados hover/pressed/checked/disabled/focus, contraste e cores não autorizadas. A evidência registra correção da integridade de baseline sem enfraquecimento de limiar.

**Ressalvas:**

- A paleta de cores do texto-fonte foi apresentada como exemplo conceitual; não é possível exigir identidade numérica com aqueles valores.
- Existem cores semânticas diretas na área de cena/gizmo. A evidência as trata como cores de desenho da cena, não como chrome QSS; isso é aceitável, mas a separação deveria estar registrada em uma matriz de conformidade.
- Não há uma tabela de rastreabilidade que mostre, para cada requisito visual do texto-fonte, o teste e o artefato correspondente.

**Parecer:** **conforme no escopo técnico implementado**, sem evidência de violação relevante da camada visual centralizada.

### Etapa 2 — Biblioteca vetorial de ícones e DPI

**Atendido:** há biblioteca SVG interna, versionada no código, sem fonte externa, com fallback textual, tooltip/nome acessível, tamanhos 16/20/24/32 e matriz Qt 100/125/150/200. O encerramento pós-merge registra PR #150, CI aprovado, 109 manifestos e `1617 passed, 2 skipped`.

**Achado objetivo:** confrontando o catálogo exigido com `ICON_SPECS` em `src/ui/icon_library.py`, não foram encontradas chaves semânticas explícitas para:

- `grid`;
- `scenario`;
- `validation`.

A matriz DPI prova renderização dos ícones existentes; ela não prova um catálogo completo quando esses conceitos não têm especificação própria. O texto-fonte também exige Windows em DPI 100/150/200 e revisão física de monitor; a evidência registra que essa parte não foi confirmada integralmente, especialmente porque a execução foi offscreen/reduzida.

**Parecer:** **parcial**. A infraestrutura de ícones está correta, mas o catálogo do texto-fonte não foi fechado integralmente.

### Etapa 3 — Barra lateral de ferramentas

**Atendido:** `ToolPalette` é uma barra vertical icon-only, com largura mínima de 56 px, ações exclusivas, tooltips, nomes acessíveis, atalhos, separadores e compatibilidade com `tool_manager`, `tool_buttons`, aliases `btn_*` e sinais existentes. Os testes exercitam as nove ferramentas presentes.

**Divergências contra o agrupamento exigido:**

- A barra esquerda contém seleção/contorno e collision brush, mas não contém o grupo de navegação exigido (`move`, `zoom`, `fit`, `focus`). Esses comandos ficam em outras barras/controles.
- O texto-fonte exige no grupo de colisão edição de collider e validação; a barra não expõe esse conjunto completo como ferramentas próprias.
- A existência funcional de comandos em outra área não é equivalente à exigência explícita de agrupamento na barra esquerda.

**Parecer:** **parcial**. A barra foi implementada com boa compatibilidade, mas não corresponde integralmente à composição funcional descrita no texto-fonte.

### Etapa 4 — Barra superior, menus e comandos

**Atendido:** existem grupos de arquivo, edição, view, exportação, contexto e render; há separadores nativos, ícones, preservação de identidade das `QAction`, undo/redo, fit, 1:1, focus, Lit, X-Ray, exportação e busca Ctrl+K integrada à command palette.

**Lacunas ou deslocamentos:**

- `Grid` e `Snap` não aparecem como ações do grupo View da barra superior; ficam no chrome inferior/viewport.
- A ação de configurações não está presente como comando visível equivalente no agrupamento implementado.
- A busca existente é busca de comandos; não foi encontrada busca de ferramentas separada.
- Ações recentes não aparecem como grupo/ação dedicado na barra superior.
- O texto-fonte pede uma hierarquia específica entre controles compactos, menus e palette; os testes existentes comprovam grupos e identidade, mas não todos os critérios de frequência/organização da lista original.

**Parecer:** **parcial**. A barra superior funciona e preserva compatibilidade, mas a organização não fecha todos os itens literais do texto-fonte.

### Etapa 5 — HUD, viewport e status

**Atendido:** View/Zoom, Fit, 1:1, Lit/X-Ray e Snap estão presentes; o status persistente exibe `VIEW` e `ZOOM`; há testes de atualização em tempo real e três resoluções.

**Lacunas contra o HUD exigido:**

- O status implementado em `src/ui/viewport_status.py` é essencialmente `VIEW | ZOOM`.
- Não há demonstração equivalente, no HUD persistente, de cursor/coordenadas, estado da grade, estado do gizmo e status de seleção.
- Coordenadas de transformação próximas ao gizmo não foram comprovadas como parte do HUD da Etapa 5.
- Os testes focados cobrem zoom/Lit/X-Ray/status, mas não exercitam integralmente todos esses campos nem a expiração de mensagens temporárias.

**Parecer:** **parcial**. O subescopo view/zoom foi entregue; o HUD completo do texto-fonte não foi.

### Etapa 6 — Gizmo e transformações

**Atendido:** a implementação cobre handles, limites visuais, seleção múltipla, snapping, nudge transacional, undo/redo, modos de cenário, vertex gizmo, transformação numérica, cancelamento, estado sem seleção e feedback visual. A evidência pós-merge do fechamento de lacunas registra PR #152, CI aprovado, `1621 passed, 2 skipped`, 109 manifestos e 24 capturas.

**Lacuna de prova:**

- A exigência de DPI 100/150/200 para as interações detalhadas do gizmo não está coberta por uma matriz independente de gestos. A matriz da Etapa 9 exercita responsividade geral, mas não substitui arrastar cada tipo de handle, cancelar, confirmar e desfazer em cada DPI.
- A revisão visual humana e os testes funcionais comprovam boa parte do comportamento, mas não existe uma matriz completa que ligue cada gesto do texto-fonte a cada escala DPI.

**Parecer:** **parcial, majoritariamente implementada**. O risco é de comprovação incompleta, não de ausência geral da lógica transacional.

### Etapa 7 — Painéis laterais e inspetores

**Atendido:** os quatro painéis são alcançáveis em resolução compacta. Há seleção real de objetos, toolbars compactas, visibilidade/lock/order em layers/groups, ações contextuais, scroll no painel de objetos, transformação e testes de colisão. O encerramento pós-merge registra PR #154, CI aprovado, 110 manifestos e `1625 passed, 2 skipped`.

**Lacunas contra o texto-fonte completo:**

- Os painéis de objetos e layers não apresentam campo de busca demonstrado nos testes/código auditados.
- O `SidePanel` principal expõe Properties, Transform, Modify Shape e Export; não há nele a lista completa de seções de inspetor exigida pelo texto-fonte, especialmente Pivot, Snap, Parallax, Sockets e Metadata.
- Parallax e Sockets foram encontrados em `src/ui/scene_authoring_inspector.py`, pertencente ao editor de cenário da Etapa 8, não como fechamento do inspetor principal da Etapa 7.
- O painel de colisão possui teste, estatística, estratégias e geração/exportação como controles internos, mas os próprios testes de conclusão registram `export_btn` e `auto_gen_btn` ocultos na apresentação compacta. Isso não demonstra o critério de ações críticas primárias visíveis do texto-fonte.
- A recomendação de evitar excesso de `QGroupBox` e manter separadores sutis não possui teste estrutural ou métrica visual específica.

**Parecer:** **parcial**. A entrega dos quatro painéis foi real e validada; a conformidade integral com o inspetor e o conjunto de detalhes do texto-fonte não foi demonstrada.

### Etapa 8 — Editor de cenário separado

**Atendido:** `ScenarioEditorWindow` é uma `QMainWindow` própria, com identidade, toolbar, status, viewport, stack de layers, inspector, preview, overlays, parallax, sockets, undo/redo, save/load/export e ciclo de vida independente. A evidência apresenta 16 critérios funcionais, três resoluções, revisão visual, 17 testes focados e encerramento pós-merge da PR #158 com CI Linux/Windows aprovado, `1644 passed, 2 skipped` e 112 manifestos.

**Parecer:** **conforme** com o texto-fonte, dentro dos critérios identificados.

### Etapa 9 — Responsividade, matriz e auditoria final

**Atendido:** existe matriz de 3 resoluções lógicas (`1280x720`, `1366x768`, `1920x1080`) por 4 escalas Qt (`100`, `125`, `150`, `200`), com capturas, hashes, geometria, clipping, overlap e widgets críticos. O encerramento pós-merge da PR #160 registra CI Linux/Windows aprovado, `1647 passed, 2 skipped`, 119 manifestos e baseline de 2878 arquivos.

**Lacunas de cobertura funcional:**

- `scripts/audit_stage9_functional_ui.py` exercita ferramentas, Lit/X-Ray, toggle do gizmo, ações de layer do cenário e modos do Mask Viewer, mas não abre menus nas bordas da tela.
- Não há evidência equivalente, por célula da matriz, de menu permanecendo on-screen, scroll efetivo do inspetor, teste de texto truncado após interação, nem arraste dos diferentes handles do gizmo.
- O auditor de responsividade verifica dimensões, widgets críticos, abas e artefatos; isso não cobre sozinho todos os critérios funcionais detalhados do texto-fonte.

**Inconsistência de proveniência:**

- O relatório funcional bruto em `docs/evidence/artifacts/stage9-responsive-dpi-local-20260823/dpi_100/functional/report.json` permanece com `status: FAIL`.
- Nesse relatório, as ações funcionais e a geometria passam, mas `human_review` é `NOT_CONFIRMED` e `source_tree_clean` é `false`.
- `HUMAN_REVIEW_REQUIRED.md` permanece com os itens não marcados.
- O agregador `stage9-worker-report.json` considera a execução automatizada aprovada porque avalia as ações funcionais/geometria e não exige aqueles dois campos. A narrativa posterior declara revisão humana aprovada, mas o pacote bruto não contém uma confirmação marcada equivalente.

Isso não invalida automaticamente os resultados visuais, mas impede chamar o pacote inteiro de PASS sem uma reconciliação explícita da discrepância.

**Parecer:** **parcial / não totalmente comprovada**. A matriz técnica existe e é valiosa, mas não cobre todos os critérios do texto-fonte e possui divergência entre artefato bruto, agregador e encerramento narrativo.

## 4. Qualidade do plano derivado

O arquivo `docs/PLANO_INTERFACE_MODERNA_PROFISSIONAL_2026-08-21.md` é útil e contém, na seção consolidada posterior, muitos requisitos que se aproximam do texto-fonte. Porém, ele não funciona hoje como rastreabilidade completa por estas razões:

1. As seções operacionais de execução condensam vários detalhes do texto-fonte; não existe uma matriz requisito → implementação → teste → evidência → commit.
2. A linha de status superior ainda declara “Etapas 8–14 planejadas e não iniciadas”, embora existam encerramentos pós-merge das Etapas 8 e 9.
3. O histórico vivo registra o encerramento pós-merge da Etapa 7, mas não foi reconciliado com PR #158 e PR #160.
4. O plano mistura snapshots históricos, aprovações por escopo e requisitos completos sem uma coluna que diferencie “atendido”, “fora do escopo” e “não comprovado”.
5. A seção consolidada contém requisitos importantes, mas não elimina a necessidade de comparar o texto-fonte original, que continua sendo mais detalhado em vários critérios de inventário, HUD, organização de comandos, painel e auditoria.

**Parecer documental:** o plano derivado é uma boa especificação operacional parcial, mas não é uma cópia fiel nem uma matriz de conformidade completa do texto-fonte.

## 5. Riscos e prioridade de correção

### Prioridade alta — fechar antes de declarar conformidade integral

- Completar o catálogo de ícones com `grid`, `scenario` e `validation`, incluindo tooltip, fallback e testes.
- Decidir se navegação e validação devem realmente estar na barra esquerda; se sim, adicionar as ações preservando os contratos públicos.
- Completar o HUD com cursor/coordenadas, grade, gizmo, seleção e transformação, ou registrar formalmente uma decisão de escopo diferente.
- Reexecutar a Etapa 9 com menus abertos nas bordas, scroll real dos inspetores e gestos representativos do gizmo em 100/125/150/200.
- Reconciliar `report.json`, `HUMAN_REVIEW_REQUIRED.md`, agregador e documento pós-merge em uma única decisão auditável.

### Prioridade média

- Adicionar busca em Objects/Layers, se o requisito do texto-fonte permanecer obrigatório.
- Tornar exportação e auto-geração de colisão verificavelmente acessíveis no modo compacto, ou justificar o uso de menu contextual.
- Explicitar no plano a separação entre inspetor principal e inspetor do editor de cenário.

### Prioridade documental

- Atualizar o status superior do plano para refletir as Etapas 8 e 9.
- Criar uma matriz de rastreabilidade das 10 etapas, preservando o texto-fonte como referência normativa e apontando cada lacuna sem convertê-la em aprovação genérica.

## 6. Limites da auditoria

Esta auditoria foi baseada em inspeção do código, testes versionados, manifestos, relatórios e histórico Git existentes. Não foram alterados código de produção, contratos ou testes funcionais. A auditoria não substitui uma nova execução física em monitores Windows com DPI do sistema; justamente por isso, os pontos de DPI físico e revisão humana foram classificados como limitação quando não havia artefato verificável.

## 7. Conclusão final

O ciclo técnico concluído é consistente para os **escopos que foram explicitamente aprovados** e possui evidências pós-merge fortes para as Etapas 1, 2, 3, 4, 5, 6, 7, 8 e 9 em diferentes níveis. Contudo, o texto-fonte solicitava um conjunto mais amplo e detalhado.

A declaração profissional correta neste momento é:

> **Etapas 0–9 implementadas parcialmente e aprovadas apenas nos escopos comprovados; conformidade integral com o texto-fonte ainda não demonstrada.**

O principal próximo passo não é repetir genericamente a suíte, mas fechar os itens concretos acima e atualizar a reconciliação documental para que cada requisito original tenha uma decisão verificável.
