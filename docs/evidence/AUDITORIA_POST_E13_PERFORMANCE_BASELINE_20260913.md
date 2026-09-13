# Auditoria pós-E13 — baseline de desempenho do viewport

**ID:** `AUD-POST-E13-PERFORMANCE-BASELINE-20260913`

**Versão:** `1.0`

**Data:** `2026-09-13`

**Estado:** `IN_PROGRESS`

**Source commit da baseline:** `caba951b8e62c33acd0e5d00fb1f795dc04856fc`

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

Enquanto a análise causal e a decisão de implementação permanecem abertas, o
estado correto desta etapa é `IN_PROGRESS`.

## Resultado da baseline atual

O produtor canônico `scripts/benchmark_p2d_05_o2_preview.py` executou a matriz
completa no commit acima. O relatório é
`artifacts/audit-post-e13-performance-20260913-r1/o2-baseline-post-e13.json`,
com SHA-256
`9DADEBF8C3BBE5818532E3FD5837472D1053876B9C9500B9ACC7A9B12E647DB5`.

| Verificação | Resultado observado |
|---|---|
| estado do produtor | `PASS` |
| workloads | `26/26` (24 principais + 2 estruturais) |
| amostras | `50` por operação, `5` warm-ups |
| erros de operação | `0` |
| falhas de determinismo | `0` |
| memória | `20` observações separadas por workload |
| ambiente | Windows 10, Python 3.11.9, AMD64, 16 CPUs lógicas, Qt `offscreen` |
| GPU | `not_measured`; o caminho QGraphicsView não fornece contador integrado |

O único aviso de inicialização foi o Qt informar que o diretório de fontes não
estava disponível no modo `offscreen`. A execução continuou e terminou com
`PASS`; o aviso não foi ocultado e não é evidência de desempenho nativo de
janela.

## Achados quantitativos

Os valores abaixo são p95 em milissegundos e permanecem diagnósticos, não
orçamentos normativos:

| Caminho | Pior p95 observado | Carga |
|---|---:|---|
| `asset_update` | `1096,20 ms` | unique, 512 objetos, 1920×1080 |
| `group_membership_toggle` | `1088,62 ms` | unique, 512 objetos, 1920×1080 |
| `object_add_remove` | `1086,95 ms` | unique, 512 objetos, 1920×1080 |
| `full_sync` | `943,49 ms` | unique, 512 objetos, 1280×720 |
| `preview_toggle` | `922,87 ms` | unique, 512 objetos, 1280×720 |
| `user_gesture_cycle` | `333,81 ms` | shared, 512 objetos, 1280×720 |
| `incremental_refresh` | `122,40 ms` | shared, 512 objetos, 1280×720 |
| `preview_frame_build` | `15,82 ms` | shared, 512 objetos, 1280×720 |

Em baixa escala, o custo é muito menor; em alta escala, a degradação não é
explicada por resolução isolada. O contraste entre `shared` e `unique` aponta
para a cadeia de resolução, validação de hash, leitura e decodificação de
assets, mas o perfil abaixo é a evidência causal usada para essa classificação.

Memória por workload, em observação de 20 refreshes fora do timing:

- crescimento Python observado entre `47.153` e `140.764` bytes;
- maior delta de Working Set: `663.552` bytes;
- maior delta de Private Bytes: `745.472` bytes;
- mínimo de Working Set: `-790.528` bytes e de Private Bytes:
  `-823.296` bytes.

Essa série não constitui veredito de leak; não houve crescimento grande nesta
janela curta, mas também não há prova de estabilidade nativa em sessão longa.

## Profiling CPU causal, local e sanitizado

Foram gerados quatro perfis locais. Eles não entram no commit porque podem
conter referências internas do profiler; seus hashes são registrados para
rastreabilidade:

| Perfil | SHA-256 | Evidência causal |
|---|---|---|
| `profiles/o2-post-e13-full-sync-512-unique.prof` | `AD77B07933E8C51B9CD55CF78A0342BF80ED979FC237A564F86959AC83379D3C` | `resolve_scene_asset` acumulou `4,009 s`, `Path.resolve` `2,092 s`, hash `1,449 s`, leitura `0,826 s` em cinco chamadas |
| `profiles/o2-post-e13-incremental-512-shared.prof` | `4C9B9F060A508A2175717DBDE5973A98E805B5ADD83BE052D15386E83D0D0D64` | `_refresh_transforms` acumulou `3,593 s`; o gerador de iluminação/oclusores em `scene_authoring_viewport.py:1776` acumulou `2,630 s` em 20 refreshes |
| `profiles/o2-post-e13-frame-512-shared.prof` | `00A4CD09A26B870A9C711A028DB3011F7B38F186DB3E3FF205AF8B4591207DF1` | `build_scene_authoring_preview` acumulou `2,083 s`; `parallax_camera.project` `1,005 s` em 50 frames |
| `profiles/o2-post-e13-structural-512-unique.prof` | `47E6620F6A1689C20D27ACFC53280CB129E6F7A40514E22C226992486FB278AC` | `sync` acumulou `4,709 s`; resolução de assets `3,143 s`; snapshots/histórico também aparecem no caminho estrutural |

O perfil confirma dois hot spots distintos. Primeiro, mudanças estruturais e
troca para preview revalidam assets únicos em cada reconstrução, apesar do
cache de `QPixmap` já existente. Segundo, o refresh incremental recalcula a
iluminação e todos os oclusores para o documento inteiro mesmo quando o
conjunto de objetos solicitado é restrito. Isso justifica investigar uma
redução localizada no viewport, mantendo a semântica atual.

## Falha de tooling preservada

O script legado
`scripts/profile_p2d_05_o2_preview.py` não pode ser usado no HEAD atual: sua
importação referencia `scripts.benchmark_p2d_05_o2_preview_reuse.py`, arquivo
que não existe nesta árvore. A reprodução do comando terminou com
`ModuleNotFoundError`; a falha é de tooling e não foi convertida em `PASS`.
Os perfis acima foram produzidos diretamente pelo produtor canônico existente,
com o mesmo harness e os mesmos caminhos medidos. Corrigir ou substituir esse
profiler deve ser tratado como melhoria de infraestrutura, com teste próprio.

## Classificação da baseline e decisão de implementação

| Alvo | Estado atual | Conclusão permitida |
|---|---|---|
| matriz de medição | `PASS` | baseline reproduzível no commit registrado |
| desempenho perceptível em 512 unique | `FAIL` | excede claramente uma interação profissional; hot spot confirmado |
| determinismo/erros | `PASS` | nenhuma falha funcional foi encontrada nesta matriz |
| memória curta | `PENDING_EVIDENCE` | observação pequena, sem prova de estabilidade longa |
| GPU/runtime externo | `PENDING_EVIDENCE` | não medidos nesta etapa |
| profiler legado | `FAIL` | dependência ausente; não usar até correção do tooling |

O próximo subestágio autorizado é uma correção estreita no viewport para
eliminar trabalho de iluminação fora do conjunto solicitado e, separadamente,
avaliar cache de identidade de asset com invalidação verificável. Nenhuma
otimização será feita sem teste de equivalência, proteção contra asset
modificado/ausente, benchmark antes/depois e nova captura real do fluxo. Se a
invalidação segura não puder ser demonstrada, a decisão correta para esse alvo
será `NO_CHANGE`.
