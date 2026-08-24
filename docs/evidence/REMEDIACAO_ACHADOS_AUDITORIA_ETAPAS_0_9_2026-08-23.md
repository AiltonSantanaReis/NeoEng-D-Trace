# Remediação dos achados — auditoria das Etapas 0–9

Projeto: NeoEng-D-Trace  
Data: 2026-08-23  
Branch: Ailton/stage9-postmerge-documentation  
SHA de código auditado: 9903e82  
Commits de remediação: 976d077, 163ae83, 9903e82

## Decisão

Resultado técnico automatizado: PASS.  
Resultado visual humano: PENDENTE.  
Árvore local: NÃO LIMPA, por artefatos históricos e relatórios locais não rastreados preservados no workspace.

A decisão PASS é restrita aos checks automatizados abaixo. Ela não transforma a revisão visual humana, a execução em monitor físico ou o CI dos commits locais em fatos já comprovados.

## Correções aplicadas

| Etapa | Achado corrigido | Implementação | Gate |
|---|---|---|---|
| 0 | inventário público incompleto | inventário versionado de ações, sinais, painéis, atalhos, exportadores e estados | documento de inventário |
| 2 | chaves de ícone ausentes | chaves SVG próprias para grid, cenário, validação, mover, zoom e collider edit; tooltip, acessibilidade e fallback | test_stage2_ui_icons |
| 3 | rail sem navegação/validação | cinco ações auxiliares reais, separadores, dispatch canônico e rail de referência 56–72 px | test_stage3_ui_toolbar; auditor funcional |
| 4 | Settings, Grid, Snap e busca recente incompletos | Settings real com diálogo; Grid/Snap no View; IDs de ferramentas; recent_ids na command palette | tests de Stage 2–4; 40 testes focados |
| 5 | HUD incompleto | estado completo com cursor, grid, gizmo, seleção, snap e zoom; representação compacta e tooltip completo | test_stage5_viewport_hud |
| 6 | gesto do gizmo sem matriz funcional suficiente | auditor agora executa begin/preview/finish/undo de transformação real | test_stage6_gizmo_gap_closure; auditor DPI |
| 7 | busca e inspetor incompletos | busca Objects/Layers, Pivot, Snap, Metadata e resumo de validação de colisão | test_stage7_side_panels_completion |
| 9 | clipping e cobertura funcional insuficiente | correção QSS do rail, menus on-screen, scroll efetivo, gesto do gizmo e matriz DPI | auditor funcional e matriz responsiva |

A Etapa 1 e a Etapa 8 não exigiram alteração funcional neste ciclo; seus escopos previamente comprovados permanecem históricos e não são reclassificados por esta remediação.

## Execuções reproduzidas

### Suíte ampla

Comando:

    QT_QPA_PLATFORM=offscreen .venv/Scripts/python.exe -m pytest -q

Resultado final:

    1649 passed, 2 skipped, 0 failed
    duração observada: 39.94 s
    total coletado: 1651

A suíte passou também pelos gates de higiene de referências, limite arquitetural de MainWindow e sizing bilíngue do ToolPalette.

### Foco de interface

Comando equivalente executado com os contratos de Stage 2, 3, 4, 5, 6, 7 e command palette.

Resultado:

    40 passed

### Auditor funcional de Stage 9

Comando:

    .venv/Scripts/python.exe scripts/audit_stage9_functional_ui.py <output-local>

Resultado automatizado:

    functional_actions = true
    visual_geometry = true
    visual.findings = []
    automated_status = PASS
    status = PASS_AUTOMATED_HUMAN_PENDING

Cenários adicionais exercitados:

- todas as nove ferramentas históricas;
- Lit e X-Ray 1/2/3;
- toggle do gizmo;
- gesto real de translação com commit e undo;
- menu de referência dentro da tela;
- rolagem efetiva dos inspetores;
- adicionar/remover layer do editor de cenário;
- Mask Viewer em quatro modos;
- 1280×720, 1366×768 e 1920×1080;
- zero clipping e zero overlap.

Hash SHA-256 do report.json local reproduzido: 22AFF873FD37C652C79FE841429B250EBFC1A404E0C33013920FFE7DEF25EE10. O arquivo foi gerado fora do repositório e não foi copiado como evidência binária permanente.

### Matriz responsiva e DPI

A matriz executada pelo agregador contém:

- resoluções 1280×720, 1366×768 e 1920×1080;
- escalas 100%, 125%, 150% e 200%;
- dimensões físicas, widgets críticos, abas, artefatos visuais e ações funcionais.

Resultado:

    4 workers PASS
    12 células de resolução por DPI PASS
    automated_status = PASS

Hashes locais:

- relatório agregado: 50C9E5208D2E6696B38E545BE545C041333ABCF1058890E4181933D4DCE052B2;
- índice de artefatos: C76D64A401BBA2744B1FF361C5B1C085A807A2712682DA2F6DE3D11146FEB3ED.

Hash dos scripts usados:

- audit_stage9_functional_ui.py: 1b00a294b0e2bf9fcacdc3fda98b2f3830fd160b;
- audit_stage9_responsive_dpi.py: a2c002e6a2beb8dfb60be5f53a3fd11ec4e713d2.

## Correções de regressões durante a remediação

A primeira execução ampla encontrou três falhas legítimas:

1. rail textual estreito para rótulos portugueses;
2. MainWindow acima do limite arquitetural de 1200 linhas;
3. hygiene scanner detectando caminho pessoal no documento da auditoria.

As três foram corrigidas e a execução ampla final passou. O sizing textual legado foi separado do rail icon-only de referência; os adaptadores de ações foram extraídos; o documento foi sanitizado sem remover conteúdo técnico.

## Limitações residuais

- A revisão visual humana exigida pelo auditor continua não confirmada.
- A matriz Qt offscreen não substitui a observação em monitor físico Windows.
- O CI apresentado pelo usuário cobre o merge anterior; não foi executado nesta sessão para os commits locais 976d077, 163ae83 e 9903e82.
- O worktree contém artefatos locais históricos não rastreados; eles foram preservados e não entram nos commits.
- O inventário comprova identidade e presença; não equivale a uma aprovação de usabilidade humana.