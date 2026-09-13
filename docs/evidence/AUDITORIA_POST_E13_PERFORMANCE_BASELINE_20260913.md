# Auditoria pós-E13 — baseline de desempenho do viewport

**ID:** `AUD-POST-E13-PERFORMANCE-BASELINE-20260913`

**Versão:** `1.2`

**Data:** `2026-09-13`

**Estado:** `IN_PROGRESS`

**Source commit da baseline:** `caba951b8e62c33acd0e5d00fb1f795dc04856fc`

**Source commit qualificado após as correções estreitas:** `8f5bbb5002bc94ecb7106858b2de36fcf4ba794e`

**Commits de correção qualificados:** `9599ae3625cde4c3c967e04688af8cea2de9f3af` (cache/resolução e iluminação incremental) e `8f5bbb5002bc94ecb7106858b2de36fcf4ba794e` (snapshot de estrutura e repintura condicional)

**Build nativa qualificada usada na verificação:** `build/post-e13-performance-build-20260913-r2`

**SHA-256 do executável:** `245A66B8E2C29A2180B9514F8579DB3679899A6C1EE4F06F13B863ACF9055238` (`10.879.926` bytes)

**SHA-256 do pacote portátil:** `F46A7481D94194A0BA143FEB9A6A960059D772270094C752FA8440DA3EBF86A0` (`142.942.057` bytes)

**SHA-256 do manifesto de release:** `AAB0FDFFD264BE85D5333A33C6EAFDF5451ECF46681B9F89039DEC58A57B7F50`

**SHA-256 da proveniência de continuidade:** `9942EECF23A60CCCDD377609C460B918FD7EB29F4395CC4AA26CC5C615254237`

**Status da proveniência/build:** `PASS` (`continuity-provenance.json`) e `SUCCESS` (`smoke/portable-smoke-report.json`)

**Governança:** [`GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md`](../GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md)

**Contrato técnico:** [`DECISAO_P2D_05_OTIMIZACAO_PERFORMANCE_2026-08-30.md`](../DECISAO_P2D_05_OTIMIZACAO_PERFORMANCE_2026-08-30.md)

**Contrato de viewport:** [`DECISAO_P2D_05_O2_PREVIEW_VIEWPORT_2026-08-30.md`](../DECISAO_P2D_05_O2_PREVIEW_VIEWPORT_2026-08-30.md)

O build e a captura anteriores permanecem preservados para comparação histórica:
`build/post-e13-performance-build-20260913-r1`, executável SHA-256
`F467B2FE6CA1FF1744D40A582143D08A250CFE9CC2732A4444A687FE55025728`, pacote
SHA-256 `64BC1530218E677399B6ED3D5545783AE673546E9A677D72AF484727CFDB6B07`.
Eles não são a qualificação corrente desta versão.

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
- saída da baseline: `artifacts/audit-post-e13-performance-20260913-r1/`;
- saída pós-correção inicial: `artifacts/audit-post-e13-performance-20260913-r2/`;
- saída pós-correção de visibilidade/repintura: `artifacts/audit-post-e13-performance-20260913-r5/`;
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

## Correção estreita executada e verificada

No commit `9599ae3625cde4c3c967e04688af8cea2de9f3af` foi aplicada somente a
correção delimitada pela análise causal:

- resolução/validação de asset passou a reutilizar cache indexado por identidade
  (`id`, caminho e SHA) e fingerprint do arquivo, com invalidação pelo watcher e
  descarte seguro quando o fingerprint muda;
- o refresh incremental passou a calcular iluminação apenas para os IDs
  solicitados, preservando o conjunto completo de oclusores e a semântica visual;
- o profiler local passou a usar o produtor canônico e exige explicitamente o
  commit esperado;
- foram adicionados testes para invalidar o cache após modificação do arquivo e
  para garantir que o refresh de um objeto não sombreie objetos não solicitados.

Os testes focados do contrato O-2 totalizaram `10 passed`; a suíte focalizada de
viewport/UX totalizou `37 passed`. A regressão oficial completa, sem filtros,
terminou com `2623 passed, 2 skipped, 5 warnings` em `77,74 s`. Os dois skips e
os cinco avisos pertencem ao pacote oficial existente e permanecem registrados;
nenhum bypass foi introduzido.

## Resultado pós-correção

O produtor canônico executou novamente a matriz completa com `50` amostras,
`5` warm-ups e `20` observações de memória. O relatório é
`artifacts/audit-post-e13-performance-20260913-r2/o2-after-viewport-fix.json`,
com SHA-256
`83FE593AB51F683D76AC78D15E4C32EE7D74C6905DD3F2E6558D231F4046FD5E`.

| Verificação | Resultado observado |
|---|---|
| estado do produtor | `PASS` |
| source commit esperado/observado | `9599ae3...` / `9599ae3...` |
| workloads | `26/26` (24 principais + 2 estruturais) |
| medições comparáveis | `254` |
| amostras | `50` por operação, `5` warm-ups |
| erros de operação | `0` |
| falhas de determinismo | `0` |
| memória | `20` observações separadas por workload |

Reduções de p95 observadas no mesmo workload, comparando a baseline
`9DADEBF8C3BBE5818532E3FD5837472D1053876B9C9500B9ACC7A9B12E647DB5`:

| Caminho | Antes | Depois | Variação |
|---|---:|---:|---:|
| `incremental_refresh`, shared, 512, 1280×720 | `122,40 ms` | `87,38 ms` | `-28,61%` |
| `preview_frame_build`, shared, 512, 1280×720 | `15,82 ms` | `10,29 ms` | `-34,99%` |
| `user_gesture_cycle`, shared, 512, 1280×720 | `333,81 ms` | `106,76 ms` | `-68,02%` |
| `full_sync`, unique, 512, 1280×720 | `943,49 ms` | `210,08 ms` | `-77,73%` |
| `preview_toggle`, unique, 512, 1280×720 | `922,87 ms` | `190,98 ms` | `-79,31%` |
| `asset_update`, unique, 512, 1920×1080 | `1096,20 ms` | `351,57 ms` | `-67,93%` |
| `group_membership_toggle`, unique, 512, 1920×1080 | `1088,62 ms` | `356,45 ms` | `-67,26%` |
| `object_add_remove`, unique, 512, 1920×1080 | `1086,95 ms` | `357,34 ms` | `-67,12%` |

O ganho confirma que os dois hot spots investigados eram reais e corrigíveis,
mas não encerra a queixa de responsividade: os caminhos estruturais em `512`
objetos ainda têm p95 de centenas de milissegundos. O resultado é, portanto,
uma melhoria comprovada e incremental, não uma declaração de desempenho final
ou de 60 FPS.

## Profiling pós-correção

O profiler local corrigido executou com `--expected-source-commit
9599ae3625cde4c3c967e04688af8cea2de9f3af`; a falha histórica de importação foi
preservada na seção abaixo e não foi apagada. Os perfis não entram no commit,
pois podem conter referências internas; seus hashes são:

| Perfil | SHA-256 | Observação causal |
|---|---|---|
| `profiles/o2-full-sync-512-unique.prof` | `35D34C0D8A735B911CDEADAEA1B0802A07E131BF9BFFE2A3D04CEB9A698D21CC` | `sync` caiu para `1,645 s`; o fingerprint ainda aparece como custo esperado da validação inicial |
| `profiles/o2-incremental-refresh-512-shared.prof` | `5926E66E80785CEEC1BE39576175229DFE951C62B8510C0ECB458AD6BEEECA46` | o refresh total desse workload continua deliberadamente completo; a otimização é observável no gesto incremental |
| `profiles/o2-preview-frame-512-shared.prof` | `2885082793950538474D3FD19FD1F44F72897F7E5F6215CE6A82DE4B77A7CE7E` | `build_scene_authoring_preview` e `parallax_camera.project` continuam sendo custos do frame |
| `profiles/o2-structural-isolation-512-unique.prof` | `D06F57822F040562BCAB1E9B44C9E034E620EE4F0BB9C9F6D9A4F3DC2631A5F3` | o caminho que invalida/repopula o cache permanece mais caro, porém abaixo da baseline |
| `profiles/o2-post-e13-gesture-512-shared.prof` | `9726B2CF0EA2C8F97D23736FD613BE8284DD1368E455E7A196C86B239755B8AB` | `refresh_transforms` ficou em `0,016529 s` acumulado no gesto; o próximo custo dominante é a verificação de visibilidade/grupos |

## Segunda correção estreita: snapshot de estrutura e repintura condicional

No commit `8f5bbb5002bc94ecb7106858b2de36fcf4ba794e` foi aplicada uma segunda
correção limitada ao viewport, após confirmar que o custo de repintura e uma
varredura redundante de visibilidade ainda apareciam no caminho incremental.
Nenhuma alteração foi feita em `SceneAuthoringSession`, no schema, na
persistência, no QSS/layout ou nos adapters de engine.

- `_on_session_change` passou a usar o snapshot estrutural já calculado para
  decidir se a apresentação mudou, sem recalcular a visibilidade efetiva de
  todos os objetos antes da comparação;
- `_refresh_after_model_change` recebeu `repaint_viewport`, e a notificação de
  sessão só força repintura global quando há mudança de apresentação; gestos de
  transformação/seleção dependem da invalidação de item do Qt, enquanto chamadas
  diretas e resize preservam o padrão de repintura global;
- a semântica de visibilidade, isolamento, ordem, seleção, gizmo, parallax e
  oclusores foi mantida; o teste focado confirmou que transformação não faz
  repintura global e que mutação de câmera continua fazendo.

Os testes focados do viewport/O-2 totalizaram `11 passed`; `py_compile` e
`git diff --check` passaram. A suíte oficial completa, sem filtros, terminou
com `2624 passed, 2 skipped, 5 warnings` em `79,71 s`. Os dois skips e os cinco
avisos continuam pertencendo ao pacote oficial existente; não foram usados
como bypass.

### Benchmark qualificado no commit limpo

O produtor canônico foi executado novamente com `--expected-source-commit
8f5bbb5002bc94ecb7106858b2de36fcf4ba794e`. O relatório é
`artifacts/audit-post-e13-performance-20260913-r5/o2-after-second-viewport-fix.json`,
com SHA-256
`2BB6FD6AFDF0406960864D31E2F6DF492F41DEC0E44A15AF351D79FC342D780E`.

| Verificação | Resultado observado |
|---|---|
| estado do produtor | `PASS` |
| source commit esperado/observado | `8f5bbb5...` / `8f5bbb5...` |
| workloads | `26/26` (24 principais + 2 estruturais) |
| erros de operação | `0` |
| falhas de determinismo | `0` |
| memória | `20` observações separadas por workload, sem erro de medição |
| alterações rastreadas durante a medição | `0` |

P95s representativos do workload compartilhado de `512` objetos em `1280×720`:

| Caminho | p95 |
|---|---:|
| `full_sync` | `103,14 ms` |
| `incremental_refresh` | `52,93 ms` |
| `preview_frame_build` | `7,73 ms` |
| `preview_toggle` | `58,65 ms` |
| `user_gesture_cycle` | `145,85 ms` |

Nos workloads estruturais de `512` objetos em `1920×1080`, a maior medição
compartilhada foi `object_add_remove` em `232,75 ms`; com assets únicos, a maior
foi `layer_visibility_toggle` em `1041,52 ms` (seguida de
`group_visibility_toggle` em `1034,35 ms`). Assim, a melhoria de repintura é
comprovada, mas a degradação estrutural com assets únicos continua sendo um
`FAIL` de desempenho percebido em alta escala, não um orçamento normativo.

### Profiling causal no mesmo commit

Os quatro perfis locais foram gerados pelo profiler corrigido, com o commit
esperado exato. Permanecem fora do commit por poderem conter caminhos internos;
seus hashes e sinais causais são:

| Perfil | SHA-256 | Sinal causal observado |
|---|---|---|
| `profiles/o2-full-sync-512-unique.prof` | `3CB0E653C6C209694679084324B3098FB273FFBB3B879C56B196C94AE95D594D` | `resolve_scene_asset` acumulou `3,992 s`; `Path.resolve` `2,051 s`, hash `1,489 s` e leitura `0,872 s` em cinco reconstruções |
| `profiles/o2-incremental-refresh-512-shared.prof` | `7908960E297F8988157DD7ED407AA726D16AAD384A2B3FE8367CA7C1F36D340B` | `processEvents` acumulou `0,534 s`, `paintEvent` `0,476 s`, refresh pós-modelo `0,283 s` e transformação `0,212 s` em vinte operações |
| `profiles/o2-preview-frame-512-shared.prof` | `572403C6F962C7E990521C6BCC1E7838137A362BF0249B1CE836BB89425DA886` | `build_scene_authoring_preview` acumulou `1,527 s`; `parallax_camera.project` `0,696 s` em cinquenta frames |
| `profiles/o2-structural-isolation-512-unique.prof` | `D9475CA4975BC0C240A815C6B3113B97437A39A7D1E767A104461A882C3345AF` | isolamento acionou `sync` por `3,465 s`; resolução de assets acumulou `2,781 s` — custo residual fora da fronteira de `SceneAuthoringSession` |

O profile confirma que a segunda correção reduziu o trabalho de pintura do
viewport, mas não autoriza reabrir O-1: o custo dominante restante no gesto é o
snapshot/histórico (`begin_gesture`/`snapshot`), tratado como fronteira do
contrato O-2. O caminho estrutural de assets únicos continua candidato a uma
etapa posterior somente com novo contrato, perfil, equivalência e aceitação.

O benchmark intermediário `r4`, SHA-256
`C93D99E9E3C780F402E59319734A72748EFA21EFEBB9CE5BE09F266E4A5DF6D9`, também
permanece preservado. Ele foi executado em árvore com `tracked_changes=2` sobre
`0973b36`; por isso serve como evidência histórica, não como qualificação do
commit corrente.

## Captura real no build qualificado

O binário `r2` foi executado com automação Win32 real usando a janela nativa e
captura por handle/`PrintWindow`, sem substituir a aplicação por mock. O pacote
de evidências é `artifacts/audit-post-e13-binary-performance-20260913-r2/` e
contém `15` capturas PNG hashadas e o manifesto `manifest.json` (SHA-256
`959A96B95351A9A7780D53E389E6D3F66975281E93454DFA5FCCCF27972363D6`). A
execução retornou código `0` e registrou: `window: captured by PrintWindow from
binary window handle`.

Fluxo observado nas capturas:

1. abertura do executável e carregamento direto do fixture;
2. entrada no Editor de Cenário canônico, com moldura de referência, grid,
   timeline e inspector PT-BR visíveis;
3. abertura da biblioteca e seleção do asset `vector-source`;
4. detecção real do contorno (`4 vértices`), edição e criação do objeto;
5. aplicação de um clipe de câmera com valores visíveis;
6. salvamento, `Recarregar` e reapresentação do clipe persistido.

Hashes das capturas que comprovam as transições principais:

| Evidência | Arquivo | SHA-256 |
|---|---|---|
| editor canônico pós-carga | `03-main-after-project-load.png` | `C1E64C58F37947BF07E4B9BA23B8191DDC31F4197306E1D478955EEC67178A2C` |
| biblioteca pronta | `05-asset-library-ready.png` | `C2852055F9D1A7D15F619F9E550458AFAE0860586834DFF5F4631BD7BD3099D3` |
| contorno detectado | `11-vector-contour-detected.png` | `25228B72E61E69DAC46566B1DE0AE458838776D3B2E218EF65C7D632F4B8A611` |
| câmera salva | `14-vector-contour-saved.png` | `A409652280A14EB3C5875CF7B2409DA3968EE757A3D60DA3FB9D0FF5AB3AEC7E` |
| câmera recarregada | `15-vector-contour-reloaded.png` | `792244DAA3B09B208FB1900868D6A7A68C9208C77D881D0C631E6750F66360B0` |

Esta execução comprova o caminho funcional coberto no binário e a persistência
visual do clipe. Ela não fornece contador nativo de frame/GPU nem substitui o
soak test de memória ou a equivalência de runtime Godot/Unity; esses itens
continuam explicitamente abertos.

A captura anterior do build `r1` permanece em
`artifacts/audit-post-e13-binary-performance-20260913-r1/` com `13` PNGs e
execução `0`; ela é referência histórica e não foi sobrescrita.

## Falha de tooling histórica preservada

Na baseline, o script legado
`scripts/profile_p2d_05_o2_preview.py` importava
`scripts.benchmark_p2d_05_o2_preview_reuse.py`, arquivo ausente nesta árvore. A
reprodução terminou com `ModuleNotFoundError`; essa falha histórica permanece
registrada e não foi convertida em `PASS` retroativamente. No commit qualificado
o profiler foi corrigido para usar o produtor canônico, passou a exigir o
source commit esperado e executou com sucesso. A correção foi acompanhada por
teste focado e pelos cinco perfis hashados na seção anterior.

## Classificação da baseline e decisão de implementação

| Alvo | Estado atual | Conclusão permitida |
|---|---|---|
| matriz de medição | `PASS` | baseline reproduzível no commit registrado |
| correções estreitas de cache/iluminação, snapshot de estrutura e repintura condicional | `PASS` | redução reproduzível, cobertura de equivalência protegida, regressão oficial aprovada e benchmark qualificado no commit limpo |
| desempenho perceptível em 512 unique | `FAIL` | houve redução de `67%`–`79%`, mas os p95 estruturais ainda excedem centenas de milissegundos |
| determinismo/erros | `PASS` | nenhuma falha funcional foi encontrada nesta matriz |
| memória curta | `PENDING_EVIDENCE` | observação pequena, sem prova de estabilidade longa |
| GPU/runtime externo | `PENDING_EVIDENCE` | não medidos nesta etapa |
| profiler histórico | `FAIL` | falha da baseline preservada; o tooling atual corrigido possui execução `PASS` separada |
| build portátil qualificada pós-correção | `PASS` | `r2` identificada no commit `8f5bbb5`, proveniência `PASS`, smoke `SUCCESS` e fluxo Win32 coberto sem abort/erro |
| equivalência runtime Godot/Unity | `PENDING_EVIDENCE` | não comprovada pelo fluxo editorial nem pelo benchmark offscreen |

O próximo subestágio autorizado é a otimização do custo residual de
visibilidade/grupos e do caminho estrutural, condicionada a perfil causal,
teste de equivalência, benchmark antes/depois e nova captura real. A etapa
permanece `IN_PROGRESS` enquanto memória longa, GPU/janela nativa, runtime
Godot/Unity e responsividade estrutural em alta escala não tiverem evidência
adequada. O gizmo, a produção de modelos, a decisão sobre o editor independente
e os demais itens fora da fronteira continuam adiados.
