# Auditoria pós-E13 — baseline de desempenho do viewport

**ID:** `AUD-POST-E13-PERFORMANCE-BASELINE-20260913`

**Versão:** `1.0`

**Data:** `2026-09-13`

**Estado:** `IN_PROGRESS`

**Governança:** [`GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md`](../GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md)

**Contrato técnico:** [`DECISAO_P2D_05_OTIMIZACAO_PERFORMANCE_2026-08-30.md`](../DECISAO_P2D_05_OTIMIZACAO_PERFORMANCE_2026-08-30.md)

**Contrato de viewport:** [`DECISAO_P2D_05_O2_PREVIEW_VIEWPORT_2026-08-30.md`](../DECISAO_P2D_05_O2_PREVIEW_VIEWPORT_2026-08-30.md)

## Fronteira da etapa

Esta etapa mede o estado pós-E13 do viewport canônico para confirmar, com
dados atuais, a queixa de degradação percebida quando há muitos objetos,
assets, camadas, grupos, sockets, parallax e mudanças de navegação. É uma
baseline `DIAGNOSTIC_ONLY`: não fecha O-2, não transforma números em orçamento
normativo e não autoriza alterar o produto por inferência.

O gizmo, a produção de modelos, tilemap, iluminação real, partículas completas,
runtime Godot/Unity e a decisão sobre o editor independente permanecem fora da
fronteira. E13 permanece fechado.

## Análise de impacto antes da medição

| Área | Módulo/caminho | Tratamento nesta etapa | Contrato preservado |
|---|---|---|---|
| sincronização | `src/ui/scene_authoring_viewport.py` — `sync`, refresh incremental, pintura e navegação | observar custo e alocações; não alterar | itens, ordem, seleção, transformações, visibilidade, isolamento, parallax, sockets e thread Qt |
| projeção | `src/core/scene_authoring_preview.py` | medir determinismo do frame; não alterar | mesma projeção, z-order, grupos e estados de preview |
| histórico/gesto | `src/core/scene_authoring_session.py` | observar apenas; O-1 não será reaberto por inferência | undo/redo, cancelamento, atomicidade e semântica do documento |
| persistência/exportação | contratos P2D-05 | não incluir otimização nesta baseline | schema V1/V2, bytes canônicos, SHA-256, recovery, fsync e adapters |
| UI/UX | viewport canônico e inspector | capturar custo e responsividade; sem redesign | dimensões, QSS, ações, atalhos e localização PT-BR |

Riscos que a medição precisa detectar antes de qualquer correção: reconstrução
integral desnecessária, resolução/hash de assets repetida, repintura de itens
estáveis, visibilidade/parallax recalculados sem mudança, retenção de objetos Qt,
divergência entre authoring/preview e degradação que só apareça em resolução ou
modo de asset específico.

## Protocolo planejado

- `50` amostras por operação, após `5` warm-ups;
- memória em observação separada, com `20` iterações por workload;
- cargas de `64`, `128`, `256` e `512` objetos;
- assets `shared` e `unique`;
- resoluções `1280×720`, `1366×768` e `1920×1080`;
- fixture com camadas, grupos, memberships, sockets e parâmetros de parallax;
- p50, p95, p99, pior caso, erros, determinismo e memória Python/nativa;
- profiling CPU somente local e sanitizado, sem publicar caminhos pessoais;
- saída prevista: `artifacts/audit-post-e13-performance-20260913-r1/`;
- source commit, ambiente e hashes serão registrados após a execução.

O resultado só poderá ser classificado como `PASS` se a matriz completa
executar sem erro, os frames forem determinísticos e as limitações forem
declaradas. Um ganho ou uma meta de latência só será considerado tecnicamente
válido depois de equivalência funcional/visual, persistência quando aplicável,
regressão oficial e captura real do fluxo afetado.

## Decisões reservadas para o final

1. `NO_CHANGE` se a medição não comprovar hot spot corrigível com segurança;
2. abertura de correção incremental apenas se o hot spot e a cobertura forem
   confirmados, preservando os contratos acima;
3. eventual orçamento normativo somente com workload, hardware, amostras,
   percentis, margem e comportamento de excedência documentados.

Até a baseline atual ser executada e analisada, o estado correto desta etapa é
`IN_PROGRESS`.
