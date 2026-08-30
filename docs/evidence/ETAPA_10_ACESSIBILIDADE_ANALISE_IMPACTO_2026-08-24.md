# Etapa 10 — Análise de impacto e auditoria inicial de acessibilidade

**Documento:** `EVID-F10-ACCESSIBILITY-IMPACT-20260824`
**Status:** `IN_PROGRESS`
**Versão:** 1.0
**Etapa:** 10 — Acessibilidade e usabilidade
**Requisito:** `REQ-F10-UI-ACCESSIBILITY`
**Feature:** `FEAT-UI-ACCESSIBILITY`
**Commit de caracterização:** `2151ef1aed06e2660a5e04f1d9d0b4651cb5bcce`

## 1. Dependências documentais ativas

- [Governança de Integridade, Execução e Antialucinação](../GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md)
- [Índice Documental Ativo](../INDICE_DOCUMENTAL_ATIVO_2026-08-24.md)
- [Registro de IDs do produto](../REGISTRO_IDS_PRODUTO_PROFISSIONAL_2026-08-24.yaml)
- [Adendo Normativo de Automação e IDs](../ADENDO_NORMATIVO_AUTOMACAO_E_IDS_2026-08-24.md)
- [Plano de Interface Moderna e Profissional](../PLANO_INTERFACE_MODERNA_PROFISSIONAL_2026-08-21.md)

Este documento registra diagnóstico e impacto; não altera requisitos, thresholds, baseline ou critérios de aceite.

## 2. Critério executado

A Etapa 10 exige que controles reais da interface possuam nome acessível, descrição acionável quando aplicável, tooltip, foco de teclado, ordem de tabulação, atalhos funcionais, feedback de estado que não dependa somente de cor, contraste verificável e mensagens de erro acionáveis. Mouse e teclado são verificados em fluxos separados.

## 3. Módulos e contratos afetados

| Módulo | IDs | Contrato preservado | Ampliação controlada |
|---|---|---|---|
| Barra de referência | `MOD-EDITOR-SCENE-VIEWPORT` | QActions, menus, atalhos e labels existentes | nomes/descrições atualizados após localização |
| Inspetor lateral | `MOD-EDITOR-INSPECTOR` | comandos de transformação, colisão, forma e exportação | foco, nomes e descrições nos controles e campos reais |
| Viewport/HUD | `MOD-EDITOR-CANVAS-VIEW` | View, Zoom, Snap e estado do viewport | metadados acessíveis e descrição do estado atual |
| Pilha de painéis | `MOD-EDITOR-LAYER-STACK` | abas desktop/compacto e troca de painel | nome e descrição dos `QTabBar` reais |
| Tema | `MOD-TOOLS-EVIDENCE` | tokens e contraste previamente aprovados | teste de regressão de contraste e foco |

## 4. Achados observados antes da correção

A introspecção executada sobre a janela Qt real no SHA acima observou controles existentes sem o contrato completo de acessibilidade:

1. botões de ação do inspetor lateral sem `accessibleName` e sem foco de teclado;
2. campos numéricos do inspetor e seus `QLineEdit` internos sem metadados acessíveis;
3. botões View/Zoom do HUD sem nome acessível;
4. `QTabBar` interno sem nome acessível;
5. labels acessíveis da barra de referência não eram atualizados de forma explícita após localização.

A suíte focada prévia das etapas 4, 5 e 9 passou, mas isso não constituía prova da Etapa 10. O diagnóstico foi mantido como `DIAGNOSTIC_ONLY`.

## 5. Correção autorizada

A correção reutiliza as ações, comandos e widgets existentes. Não cria caminho paralelo, não substitui o renderer, não altera persistência, não desabilita teste, não reduz cobertura e não modifica os critérios de aprovação. Os contratos adicionados são:

- `TEST-UI-ACCESSIBILITY-METADATA`;
- `TEST-UI-KEYBOARD-FOCUS`;
- `TEST-UI-MOUSE-FEEDBACK`;
- `TEST-UI-ERROR-FEEDBACK`;
- `TEST-UI-CONTRAST-STATES`.

## 6. Proteções contra regressão e escopo futuro

A correção se limita à semântica e ao foco dos controles já existentes. A ordem dos comandos, identidade das `QAction`, menus, atalhos, viewport, painéis e modelo de dados permanecem preservados. O contrato não presume que o renderer atual seja o renderer final e não fixa modelo de dados, schema ou domínio a um widget.

## 7. Próxima evidência

A auditoria executável deverá produzir `EVID-F10-ACCESSIBILITY-AUDIT` com capturas reais, interações, ambiente, commit, relatório, manifesto e `hashes.sha256`. Qualquer falha deverá deixar o pacote em `FAIL`; somente o resultado observado poderá ser usado para o fechamento da etapa.