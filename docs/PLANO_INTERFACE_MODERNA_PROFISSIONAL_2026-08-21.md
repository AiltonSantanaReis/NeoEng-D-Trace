# Plano Vivo e Fonte de Verdade — Interface Moderna e Profissional

**Projeto:** NeoEng-D-Trace
**Data de criação:** 2026-08-21
**Status do plano:** ETAPAS 0, 1, 2, 3, 4 e 5 APROVADAS NOS ESCOPOS COMPROVADOS / ETAPAS 6 e 7 PARCIAIS FRENTE AO PLANO DETALHADO / ETAPAS 8–14 PLANEJADAS
**Tipo:** documento vivo de planejamento; não é evidência de execução, não é aprovação de release e não autoriza merge automaticamente.

## 1. Finalidade e autoridade

Este documento é a fonte de verdade do plano de modernização da interface do NeoEng-D-Trace. Ele organiza escopo, ordem, critérios de aceitação, evidências e ciclo de entrega das melhorias visuais e de usabilidade.

Ele é subordinado às regras globais do repositório, especialmente:

- \`docs/POLITICA_QUALIDADE_E_EVIDENCIAS.md\`;
- \`docs/PLANO_MESTRE_ESTABILIZACAO.md\`;
- \`docs/MATRIZ_RISCOS_ESTABILIZACAO.md\`;
- \`.github/pull_request_template.md\`;
- workflows e validadores presentes no repositório;
- ADRs e contratos técnicos aplicáveis.

Nenhuma seção deste plano pode reduzir, substituir ou relativizar uma governança global. Em caso de conflito, a governança global prevalece; o conflito deve ser registrado e este documento deve ser corrigido antes de qualquer implementação afetada.

Este plano não é uma autorização para alterar regras, thresholds, scanners, contratos de evidência, cobertura, CI, histórico Git, dados do usuário ou escopo de runtime.

## 2. Estado real no momento do registro

O estado vivo atual foi reconciliado após a Etapa 0 no merge \`61165a58bfa6d5b6a10bcbee89dd8d7e7c6fe643\`, com \`main\` local sincronizado a \`origin/main\`.

O histórico recente registra correções responsivas e auditorias de painéis. Isso não é tratado como validação deste novo plano. A auditoria funcional anterior permaneceu fail-closed quando a revisão humana e a árvore limpa não estavam comprovadas. A Etapa 0 foi concluída somente como caracterização reproduzível da baseline. A Etapa 1 foi formalmente encerrada após CI, merge e validação pós-merge. A Etapa 2 foi formalmente encerrada após PR #133, CI, merge e validação pós-merge. As Etapas 3, 4 e 5 foram posteriormente encerradas no escopo aprovado, cada uma após implementação, evidências, CI, merge e validação pós-merge, conforme os snapshots pós-merge correspondentes em `docs/evidence/`. A Etapa 6 foi integrada no `main` pelo merge `c1bf40c273038a2bbeb35b4d450c10724f6c84ea` após PR, CI e validação pós-merge reproduzida. A revisão visual humana das capturas anotadas foi realizada e aprovada pelo proprietário do projeto; a Etapa 6 está formalmente concluída no escopo aprovado. A Etapa 7 permanece planejada e depende de autorização própria.

Na reconciliação de 2026-08-22, o `main` observado foi o merge `425f21df2bbf9a67c01a577b59ae6bbba25995b7`, que incorpora a documentação pós-merge da Etapa 5. A branch de trabalho do baseline da Etapa 6 parte desse mesmo conteúdo. Os diretórios locais de artefatos históricos não rastreados foram preservados e não são usados como evidência de árvore limpa, release ou aprovação.

Na leitura do estado local, foram encontrados diretórios de artefatos de auditoria não rastreados. Portanto, a árvore não foi considerada limpa; essa condição foi preservada e declarada. A validação pós-merge da Etapa 6 não dependeu de uma alegação de árvore limpa local.

As capturas, hashes e resultados de auditorias existentes continuam sendo evidências de seus respectivos commits e escopos. Não são evidência automática das etapas deste plano. A evidência local atual da Etapa 6 é válida apenas para a branch e o worktree identificados no relatório correspondente.

Reconciliação viva de 2026-08-22: o `main` local e `origin/main` estão sincronizados no merge `b5bacf8a598716d28ed6035da97c2c6b49e3ce1f`. A Etapa 7 foi implementada, revisada visualmente, aprovada pelo CI, mesclada e validada pós-merge somente no escopo do `GroupsPanel`; frente ao plano detalhado original, os demais painéis continuam parciais. A reconciliação completa das Etapas 0–7 está em `docs/evidence/RECONCILIACAO_PLANO_INTERFACE_ETAPAS_0_7_2026-08-22.md`. As Etapas 8–14 continuam planejadas. Diretórios locais não rastreados continuam preservados e não são evidência de árvore limpa.

## 3. Regras imutáveis de integridade e anti-alucinação

### 3.1 Fatos, inferências e indisponibilidade

1. Só pode ser declarado como executado o comando que tiver sido realmente executado no ambiente identificado, com saída preservada ou artefato verificável.
2. Nunca inventar caminho, hash, commit, branch, número de PR, run de CI, versão de engine, contagem de testes, cobertura, captura ou resultado visual.
3. Se um dado não estiver disponível, declarar \`NÃO TESTADO\`, \`BLOQUEADO\` ou \`PARCIAL\`, conforme a causa. Não preencher a lacuna com estimativa.
4. Separar explicitamente fatos observados, resultados reproduzidos, inferências técnicas e limitações.
5. Documento, comentário, captura antiga, cache de build ou saída de outra branch não prova o comportamento do HEAD atual.
6. Toda afirmação de funcionamento deve cruzar implementação, teste, artefato e origem Git correspondente. Quando a funcionalidade for visual, deve haver captura atual e análise visual automatizada; revisão humana continua necessária quando a política exigir julgamento visual.
7. CI verde prova que os checks executados passaram para um SHA específico. Não prova, sozinho, usabilidade, qualidade visual, ausência de clipping, correção de todos os fluxos ou aprovação de release.
8. Um texto \`PASS\` produzido por uma ferramenta não substitui a decisão formal nem autoriza ocultar findings, limitações ou testes ausentes.

### 3.2 Proibição de desvio e de alteração oportunista

1. Não alterar regras, governanças, thresholds, cobertura mínima, validadores, scanners ou tolerâncias visuais para obter \`PASS\`.
2. Não remover testes, enfraquecer asserções, converter falhas em \`skip\`/\`xfail\`, fragmentar strings, ofuscar dados, remover campos de auditoria ou usar valores como \`redacted\` para escapar de um scanner.
3. Não usar bypass, \`--no-verify\`, desativação de jobs, exclusão de fixtures, mocks no lugar de comportamento real ou qualquer mecanismo que produza falso positivo.
4. Não pular, reordenar ou declarar concluída uma etapa sem autorização documentada e sem cumprir todos os gates da etapa anterior.
5. Não ampliar o escopo para editor de imagem, engine de jogo, redesign de contratos de runtime ou alteração de matemática do gizmo sem plano e aprovação específicos.
6. Dúvida, divergência documental, artefato ausente, falha intermitente não explicada ou diferença entre plataformas interrompe a progressão; não é motivo para maquiar o relatório.
7. Snapshots históricos são imutáveis. Correções devem ser feitas em documento vivo ou em novo adendo datado, preservando a proveniência do snapshot original.

### 3.3 Git, CI e merge

1. É proibido \`push --force\`, \`push --force-with-lease\`, merge forçado, reescrita de histórico, \`reset --hard\` não autorizado ou exclusão ampla de arquivos/branches.
2. Todo commit deve conter somente alterações escopadas e revisadas; arquivos temporários, dados de identidade, caminhos pessoais e artefatos sem proveniência não entram no commit.
3. A branch e os SHAs base/head devem ser registrados antes da PR. O CI precisa ser associado ao SHA exato que será revisado.
4. Falha de CI é falha legítima até causa raiz comprovada e correção real. Não se repete o job indefinidamente para procurar um resultado favorável.
5. CI verde não autoriza merge automaticamente. A revisão deve confirmar diff, testes, evidências, hashes, findings, limitações e compatibilidade com as governanças.
6. Merge só ocorre após autorização explícita, checks obrigatórios aprovados, revisão da evidência e ausência de pendência conhecida não autorizada.
7. Após merge, é obrigatório validar o SHA resultante no \`main\`, executar os checks pós-merge definidos, gerar evidência pós-merge e reconciliar os documentos vivos. Se o pós-merge falhar, o estado é bloqueado e não pode ser chamado de concluído.

## 4. Contrato mínimo de evidência por etapa

Cada etapa deve gerar um relatório versionado, com conteúdo completo e manifestos referentes aos bytes efetivamente testados. O relatório deve conter:

- objetivo, escopo e itens explicitamente fora do escopo;
- baseline, branch e SHA exato de origem;
- causa raiz confirmada por reprodução, quando houver correção;
- arquivos alterados e justificativa de cada alteração relevante;
- sistema operacional, Python, Qt/PySide6, dependências, backend gráfico, DPI, locale e modo headless/nativo;
- comandos completos, entradas, fixtures, parâmetros, seeds e relógio simulado quando aplicável;
- saída bruta ou referência rastreável aos logs e artefatos;
- contagem de testes \`passed\`, \`failed\`, \`skipped\`, \`xfail\`, \`blocked\` e \`not tested\`;
- cobertura antes/depois, incluindo branches, sem comparar números de execuções diferentes;
- hashes SHA-256 dos inputs, outputs, capturas, relatórios, manifestos e builds;
- verificação de bytes via Git blob quando o artefato estiver versionado;
- auditoria automática, findings anotados e revisão humana identificada quando necessária;
- riscos residuais, limitações reais, divergências de plataforma e motivo de cada skip;
- decisão formal: \`APROVADO\`, \`REPROVADO\`, \`BLOQUEADO\`, \`NÃO TESTADO\` ou \`PARCIAL\`;
- procedimento de rollback e condição objetiva para retomada.

Os arquivos de evidência devem usar UTF-8 e LF, não conter caminhos absolutos pessoais ou dados sensíveis e não omitir informações necessárias à reprodução. Sanitização de apresentação não pode destruir a proveniência; dados indisponíveis devem ser declarados como indisponíveis.

## 5. Reprodução obrigatória

Uma pessoa diferente deve conseguir reproduzir o resultado com o commit, dependências, comandos, fixtures e parâmetros registrados. Toda execução deve distinguir:

- execução local no worktree;
- execução contra bytes do Git;
- build limpo;
- execução remota no CI;
- validação pós-merge no \`main\`.

Não é permitido reutilizar métricas de uma execução anterior para aprovar um novo SHA. A evidência só é válida quando o manifest, o conteúdo e o commit declarado concordam byte a byte.

Para a UI, registrar também resolução lógica, escala de DPI, tamanho físico da captura, backend Qt, estado da janela, projeto carregado, seleção, painéis abertos e ação que gerou cada estado. Para cada finding visual, guardar a captura anotada, o relatório JSON e o hash.

## 6. Ciclo obrigatório de cada etapa e de cada entrega

O ciclo abaixo é obrigatório e não pode ser abreviado:

### Fase A — Governança e baseline

Ler as políticas globais, plano mestre, matriz de riscos, template de PR, workflows, contratos e documentos vivos relacionados. Confirmar o SHA e o estado da árvore. Identificar trabalho não rastreado sem apagá-lo.

### Fase B — Implementação completa

Implementar somente o escopo autorizado, incluindo estados de erro, limites, persistência, acessibilidade e rollback quando aplicáveis. Não deixar placeholder, caminho silencioso ou funcionalidade parcial declarada como pronta.

### Fase C — Testes focados e negativos

Testar o fluxo nominal, entradas inválidas, limites, ausência de seleção, janela compacta, DPI alto, redimensionamento, foco/teclado, persistência, reversão e falhas de recurso. Falha deve interromper a etapa até a causa raiz ser corrigida.

### Fase D — Gates completos

Executar suíte integral, cobertura com a política vigente, lint, formatação, tipagem, compilação, segurança, integridade de baseline/evidências e checks específicos do projeto. Os gates não podem ser reconfigurados para obter aprovação.

### Fase E — Artefatos reais

Gerar build limpa quando a etapa envolver distribuição. Executar o aplicativo real e os fluxos reais; mocks são apenas complementares. Validar artefatos finais e hashes contra os bytes efetivamente produzidos.

### Fase F — Auditoria visual e humana

Executar o auditor visual reprodutível em todas as resoluções e estados definidos. Inspecionar dimensões, alpha, clipping, sobreposição, geometria Qt, paleta, legibilidade e consistência. Onde a automação não puder concluir, registrar revisão humana com captura, observação concreta e decisão; nunca converter ausência de revisão em \`PASS\`.

### Fase G — Evidência e reconciliação

Gerar manifestos, hashes e relatório da execução atual. Conferir que referências existem, estão rastreadas quando exigido, usam LF e correspondem ao commit. Atualizar somente documentos vivos; preservar snapshots históricos.

### Fase H — Revisão pré-commit

Revisar diff, \`git diff --check\`, status, escopo, arquivos temporários, segredos, caminhos pessoais, testes alterados e coerência documental. Confirmar que nenhum teste ou regra foi enfraquecido.

### Fase I — Commit e pós-commit

Fazer commit somente depois de a etapa estar completa e comprovada. Registrar o SHA. Reexecutar os gates essenciais contra o SHA do commit com árvore limpa ou declarar precisamente por que a limpeza não foi possível. Um commit local não é push, PR, merge nem release.

### Fase J — Push e PR

Com autorização, fazer push normal, sem force. Verificar SHA remoto. Abrir PR com base/head exatos, evidências e limitações. Manter a PR em draft enquanto a revisão técnica e documental não estiver completa.

### Fase K — CI e revisão da PR

Revisar todos os jobs, logs, artefatos, warnings e o SHA testado. Reproduzir localmente falhas relevantes. CI verde é requisito necessário, nunca evidência única de funcionamento.

### Fase L — Merge autorizado

Somente após os gates e a revisão completa, solicitar/usar autorização explícita para merge normal segundo a política do repositório. Não usar force, bypass ou merge de uma PR com pendência conhecida.

### Fase M — Pós-merge

Atualizar o \`main\`, confirmar o merge SHA, executar a validação pós-merge, gerar evidência independente, revisar a árvore e reconciliar o estado vivo. Só então a etapa pode receber \`APROVADO\` no escopo definido.

## 7. Plano de modernização da interface

### Etapa 0 — Baseline visual e contrato de escopo

**Estado:** \`APROVADO\` somente no escopo de caracterização, após PR #129, CI Linux/Windows e validação pós-merge no SHA \`61165a5\`. O encerramento vivo está em \`docs/evidence/ETAPA_0_INTERFACE_MODERNA_ENCERRAMENTO_POS_MERGE_2026-08-21.md\`.

Catalogar a interface real atual em 1920×1080, 1366×768 e 1280×720, com DPI nativo e estados sem projeto, projeto carregado, painéis abertos, máscara/raio-X, gizmo e validação. Registrar geometria Qt, clipping, sobreposição, paleta, tamanhos e problemas reproduzidos. Congelar o contrato de que o redesign não altera \`.ndtproj\`, runtime, exportadores, atalhos, undo/redo ou matemática do gizmo sem aprovação separada.

**Gate:** baseline hashado, auditor automático executado, findings reproduzíveis e relatório \`APROVADO\` apenas para a caracterização; problemas encontrados não são mascarados.

### Etapa 1 — Tokens visuais e tema

Criar tokens únicos para fundo, superfície, borda, texto, texto secundário, destaque, estados hover/pressed/checked/disabled, erro e sucesso. Consolidar QSS sem depender de tema externo não controlado. Garantir contraste, foco visível, escalabilidade de fonte, consistência de ícones e ausência de bordas laranja fixas sem função.

**Gate:** testes de paleta e contraste, captura comparativa, nenhuma regressão funcional, sem duplicação de cores arbitrárias.

**Estado em 2026-08-21:** APROVADA após PR #131 (merge 71b1c44), PR documental #132 (merge aea54aa), CI Linux/Windows e validação pós-merge.

### Etapa 2 — Biblioteca de ícones e ações

Definir ícones licenciados ou nativos, tamanho, padding, tooltip, texto acessível e fallback textual. Padronizar ações Open, Save, Export, Clean, Fit, Zoom, X-Ray, Gizmo e ferramentas. Não remover texto de acessibilidade para economizar espaço.

**Gate:** todos os ícones carregam no build real, tooltips e atalhos funcionam, fallback é testado, ícones não dependem de caminho local.

**Estado reconciliado em 2026-08-23:** APROVADA no escopo da matriz visual completa de DPI 100/125/150/200, catálogo, fallback, tooltips, acessibilidade, hashes, clipping e auditoria visual. PR #150, merge `bcb0951ee05c41b03eae2a66e712d1f041cde7f8`, CI Linux/Windows PASS e validação pós-merge registrados em `docs/evidence/ETAPA_2_ICONES_DPI_2026-08-23.md`. A aprovação não é aprovação de release. A troca física de monitor/DPI do Windows continua fora desta evidência.

**Estado pós-merge em 2026-08-23:** `APROVADA NO ESCOPO COMPROVADO` após PR #150, merge `bcb0951ee05c41b03eae2a66e712d1f041cde7f8`, CI Linux/Windows PASS, baseline de 2571 arquivos, 109 manifests íntegros e suíte pós-merge `1617 passed, 2 skipped`. A matriz Qt foi executada em processos independentes nas escalas 100/125/150/200%, com 144 células por escala, hashes, clipping 0 e auditor visual PASS. A escala foi controlada por `QT_SCALE_FACTOR` em backend offscreen e não representa troca do DPI global do Windows.

### Etapa 3 — Barra esquerda de ferramentas

Migrar ferramentas para \`QToolBar\`/ações agrupadas ou componente equivalente sem quebrar a seleção atual. Lasso, Pen, Rect, Polygon, Brush, Gizmo e máscara devem possuir estado ativo evidente, hover discreto, foco de teclado, tooltip e atalho. Não permitir seleção de ferramenta bloqueada sem feedback.

**Gate:** testes de cada ação, teclado/mouse, estados checked/disabled, resolução compacta e captura sem borda dominante.

### Etapa 4 — Barra superior

Agrupar Arquivo, Edição, Visualização, Renderização e Exportação com separadores nativos. Padronizar ícone/texto, espaçamento, overflow e menus. Preservar menus tradicionais e atalhos. O comando de preview de cenário deve abrir uma janela/editor separado quando essa for a funcionalidade planejada, não misturar os contextos.

**Gate:** cada ação é acionável e rastreável, menus e atalhos permanecem equivalentes, sem botão órfão ou espaço irregular não intencional.

### Etapa 5 — Viewport e HUD

Separar estado persistente da cena, informações de zoom/view e comandos temporários. Mover status de zoom/view para status bar ou overlay discreto com contraste e proteção contra sobreposição. Garantir que texto não fique sob gizmo, painéis, canvas ou bordas.

**Gate:** captura real em três resoluções, auditoria de clipping/sobreposição, zoom/fit/1:1 e X-Ray funcionando no contexto correto de máscaras.

### Etapa 6 — Gizmo profissional

Preservar a matemática e o contrato existentes enquanto melhorar hit-test, posicionamento, modos, feedback e acessibilidade. O gizmo deve respeitar seleção de objeto/vértice, translação, rotação, escala, snapping e leitura numérica, quando já suportados. O layout deve reposicionar o gizmo conforme o viewport, sem ocultar textos.

**Gate:** testes geométricos e de interação, limites, DPI, redimensionamento, seleção múltipla, undo/redo e capturas reais anotadas.

**Estado reconciliado em 2026-08-23:** PASS_LOCAL frente às lacunas anteriormente declaradas. A implementação local cobre hit-test, translação XY, rotação Z, escalas, snapping, feedback, seleção múltipla, undo/redo, edição de vértice individual pelo gizmo, inspector numérico editável e proteção contra clipping por rolagem. A matriz Windows real produziu 24 capturas em três resoluções com 0 findings. PR, CI, merge, pós-merge e revisão visual humana continuam pendentes; o status formal permanece aberto até esses gates.

### Etapa 7 — Painéis laterais

Corrigir tamanho mínimo, rolagem, hierarquia, estados disabled/enabled e separação entre inspector principal, camadas do projeto e cenário. Substituir grades de botões por barras de ferramentas compactas quando não houver perda de descoberta; manter menus de contexto e tooltips. Nada pode ficar esmagado ou inacessível.

**Gate:** geometrias Qt reais, ações clicáveis, seleção de itens, propriedades editáveis, painéis visíveis em DPI/resoluções alvo e ausência de falsos positivos do auditor.

**Estado reconciliado em 2026-08-22:** PARCIAL frente ao plano detalhado original. A aprovação pós-merge anterior cobre somente a toolbar compacta do `GroupsPanel`. `Objects`, `Layers`, `Collision` e o inspector ainda não possuem a comprovação integral exigida pelo plano detalhado.

### Etapa 8 — Editor de cenário separado

Criar ou consolidar uma janela de autoria de cenário separada do editor principal. Ela deve possuir layer stack selecionável, inspector, viewport próprio, marcações/overlays, sockets e controles de câmera conforme contratos existentes. Abrir, fechar, redimensionar e transferir contexto sem misturar estado de projeto e estado de cenário.

**Gate:** fluxo completo de abrir/editar/salvar/reabrir, isolamento de estado, cancelamento sem perda, capturas de cada estado e testes de regressão no editor principal.

### Etapa 9 — Responsividade e DPI

Validar layout em resoluções mínimas e altas, escala 100/125/150/200%, fontes grandes, maximização, restauração e mudança de monitor. Usar \`QSizePolicy\`, layouts reais e rolagem; não mascarar clipping reduzindo fonte abaixo do limite legível.

**Gate:** matriz de capturas com dimensões lógicas e físicas, auditor de geometria/pixels, nenhum painel ou controle inacessível.

### Etapa 10 — Acessibilidade e usabilidade

Garantir foco, ordem de tabulação, atalhos, tooltips, nomes acessíveis, contraste, indicação não apenas por cor, ações destrutivas confirmáveis e mensagens de erro acionáveis. Testar mouse e teclado separadamente.

**Gate:** testes automatizados de foco/atalhos e revisão humana documentada dos fluxos principais.

### Etapa 11 — Auditor visual no projeto

Estender o auditor para validar PNGs com Pillow/OpenCV, dimensões, alpha, hashes, clipping, sobreposição, geometrias Qt, paleta e áreas suspeitas anotadas. O relatório deve ser determinístico e fail-closed, sem depender apenas de inspeção humana.

**Gate:** fixtures positivos e negativos reais, relatório PASS/FAIL reproduzível, hash dos relatórios e confirmação de que o auditor não foi enfraquecido para aceitar a interface.

### Etapa 12 — Desempenho e estabilidade

Medir tempo de abertura, resize, troca de painel, seleção, zoom, captura e uso lógico de memória. Usar cenários determinísticos, sem transformar métricas dependentes de hardware em gate sem política. Warnings devem ser classificados e acompanhados.

**Gate:** comparação contra baseline atual, ausência de regressão funcional e visual, limites documentados e nenhuma otimização que degrade acessibilidade ou precisão.

### Etapa 13 — Build e distribuição

Reproduzir build limpa, verificar ícones, QSS, fontes, recursos, manifestos, executáveis e inicialização em ambiente separado. Registrar warnings de empacotamento sem escondê-los; só classificá-los como não bloqueantes quando houver impacto analisado e evidência.

**Gate:** smoke test real, hashes dos artefatos, integridade recursiva, sem dados pessoais, origem Git exata e rollback disponível.

### Etapa 14 — Entrega e pós-merge

Concluir somente após PR revisada, CI aprovada no SHA exato, evidências completas, autorização de merge e validação independente no \`main\`. Atualizar o plano vivo com o estado real, preservar snapshots e não anunciar release automaticamente.

## 8. Critérios formais de conclusão

Uma etapa só pode ser \`APROVADA\` quando implementação, testes positivos e negativos, análise de artefatos, evidências hashadas, auditoria visual, revisão humana necessária, documentação, CI no SHA exato e validação pós-merge estiverem concluídos no escopo declarado.

Qualquer item ausente recebe \`PARCIAL\`, \`NÃO TESTADO\` ou \`BLOQUEADO\`; não recebe aprovação por aproximação. A conclusão de uma etapa não autoriza concluir etapas posteriores.

O plano completo só estará encerrado quando todas as etapas tiverem decisão formal individual e uma auditoria final reconciliar código, testes, evidências, documentos vivos, Git e CI.

## 9. Estados permitidos e regra de parada

- \`PLANEJADO / NÃO INICIADO\`: não há implementação autorizada ou comprovada.
- \`EM IMPLEMENTAÇÃO\`: há alterações, mas os gates ainda não foram concluídos.
- \`PARCIAL\`: parte do escopo funciona ou foi testada, mas há lacuna conhecida.
- \`BLOQUEADO\`: uma falha, divergência ou dependência impede progressão.
- \`NÃO TESTADO\`: a execução necessária não ocorreu ou não é reproduzível.
- \`APROVADO\`: todos os critérios formais da etapa foram comprovados.

Ao primeiro resultado incompatível, a etapa para. Não se altera o relatório, a regra ou o teste para transformar o estado em \`PASS\`.

## 10. Registro de mudanças do documento

| Data | Alteração | Estado |
|---|---|---|
| 2026-08-21 | Criação deste plano vivo, com escopo, etapas, contrato de evidência e ciclo anti-bypass. Nenhuma implementação foi declarada. | \`PLANEJADO / NÃO INICIADO\` |
| 2026-08-21 | Etapa 0 validada após PR #129, CI 32521765023, merge 61165a5, suíte pós-merge, evidências, auditor visual e baseline Git-blob em worktree limpa. Findings de design preservados; Etapa 1 não iniciada. | ETAPA 0 APROVADA / ETAPAS 1–14 PLANEJADAS |
| 2026-08-21 | Etapa 1 encerrada após PR #131, merge 71b1c44, PR documental #132, merge aea54aa, CI Linux/Windows e validação pós-merge. Etapa 2 implementada localmente com evidências reais; ciclo remoto pendente. | ETAPA 0–1 APROVADAS / ETAPA 2 PASS_LOCAL |
| 2026-08-21 | Etapa 2 encerrada após PR #133, merge ff66ffd, CI run 32536763488, baseline/evidência por blobs Git e suíte pós-merge. Próxima etapa: Etapa 3. | ETAPAS 0–2 APROVADAS / ETAPAS 3–14 PLANEJADAS |
| 2026-08-22 | Etapa 3 encerrada no escopo da barra esquerda após PR #136, merge `adb36398b5c239ded610afa07932de7ff9bff340`, CI e validação pós-merge. Gizmo, Mask Viewer e painéis laterais permaneceram fora do escopo da etapa. | ETAPAS 0–3 APROVADAS / ETAPAS 4–14 PLANEJADAS |
| 2026-08-22 | Etapa 4 encerrada no escopo da barra superior após PR #138, merge `c85171a59774f709d2541dc6a75e9eb8a9416955`, CI Linux/Windows e validação pós-merge. Viewport/HUD, gizmo e painéis laterais permaneceram nas etapas próprias. | ETAPAS 0–4 APROVADAS / ETAPAS 5–14 PLANEJADAS |
| 2026-08-22 | Etapa 5 encerrada no escopo de viewport, HUD e iconografia após PR #140, merge `1f4c2abc59d8015506ecda559ea138f163be4f90`, CI run 32580477614 e validação pós-merge. A reconciliação documental foi integrada no merge `425f21df2bbf9a67c01a577b59ae6bbba25995b7` após PR #141. | ETAPAS 0–5 APROVADAS / ETAPAS 6–14 PLANEJADAS |
| 2026-08-22 | Baseline da Etapa 6 iniciado a partir de `425f21df2bbf9a67c01a577b59ae6bbba25995b7`. A implementação do gizmo profissional ainda não foi iniciada; capacidades, contratos, duplicidade de implementações e lacunas de teste ficam registradas em `ETAPA_6_GIZMO_BASELINE_2026-08-22.md`. | ETAPAS 0–5 APROVADAS / ETAPA 6 BASELINE / IMPLEMENTAÇÃO NÃO INICIADA |
| 2026-08-22 | Baseline da Etapa 6 validado pós-merge da PR #142 no SHA `c42542ee428bd81c79257d10e62546694442b9a0`: baseline 2238 arquivos, evidências 99 manifests e suíte completa 1600 passed/2 skipped. O gizmo profissional continua sem implementação; capturas específicas da Etapa 6 permanecem não testadas. | ETAPAS 0–5 APROVADAS / ETAPA 6 PLANEJADA / BASELINE PÓS-MERGE VALIDADO |

| 2026-08-22 | Implementação local da Etapa 6 validada na branch `Ailton/stage6-gizmo-professional`: 1609 passed/2 skipped, cobertura XML 92,99% linhas e 85,19% branches, política PASS, gates estáticos PASS, baseline Git-blob com 2270 arquivos, evidências com 100 manifests e auditor nativo Windows com 12 capturas/0 findings. Causa raiz real de hit-test e compatibilidade de dublês corrigida. PR, CI, merge e pós-merge continuam pendentes; revisão humana visual não confirmada por ACL do visualizador. | ETAPAS 0–5 APROVADAS / ETAPA 6 PASS_LOCAL / ETAPAS 7–14 PLANEJADAS |
| 2026-08-22 | Etapa 6 integrada na PR #144, com CI Linux/Windows aprovado e merge `d01e42f7348265f4cfe4df65a8d6c2761e0730e8`. Pós-merge local reproduzido no `main`: baseline 2270 arquivos, evidências 100 manifests, 30 testes focados e suíte completa 1609 passed/2 skipped. A revisão visual humana foi posteriormente aprovada pelo proprietário do projeto. | ETAPA 6 APROVADA NO ESCOPO DEFINIDO |
| 2026-08-22 | Reconciliação pós-aprovação visual versionada após PR #145, merge `c1bf40c273038a2bbeb35b4d450c10724f6c84ea`, CI Linux/Windows aprovado e validação documental pós-merge. A Etapa 7 continua planejada e não foi iniciada. | ETAPAS 0–6 APROVADAS / ETAPAS 7–14 PLANEJADAS |
| 2026-08-22 | Etapa 7 validada localmente no checkpoint `9ee591615d30f98037e8506f513c4c2635fb207d`: GroupsPanel normalizado para toolbar compacta mantendo oito comandos, testes focados 22/22, suíte 1612 passed/2 skipped, gates estáticos PASS, capturas nativas Windows em três resoluções, auditor visual geral e auditor específico com 0 findings, integridade 104 manifests e privacidade PASS. Falha intermediária de log com caminhos locais foi rejeitada e preservada fora do pacote versionado. PR, CI, merge e pós-merge pendentes; revisão humana não declarada. | ETAPAS 0–6 APROVADAS / ETAPA 7 PASS_LOCAL / ETAPAS 8–14 PLANEJADAS |
| 2026-08-22 | Reconciliação do plano detalhado original: Etapas 0, 1, 3, 4 e 5 permanecem aprovadas nos escopos comprovados; Etapas 2, 6 e 7 são parciais frente aos requisitos detalhados. A Etapa 8 não pode iniciar antes do fechamento documentado dessas lacunas. Relatório: docs/evidence/RECONCILIACAO_PLANO_INTERFACE_ETAPAS_0_7_2026-08-22.md. | ETAPAS 0, 1, 3, 4 e 5 APROVADAS / ETAPAS 2, 6 e 7 PARCIAIS / ETAPAS 8–14 PLANEJADAS |
| 2026-08-23 | Etapa 2 retomada para fechar a matriz DPI. Auditor `audit_stage2_icon_dpi_matrix.py` executado no commit `033278c`; quatro escalas Qt observadas, 144 células por escala, clipping 0, auditor visual PASS, suíte integral `1617 passed, 2 skipped`. Evidência: `ETAPA_2_ICONES_DPI_2026-08-23.md` e pacote r3. | ETAPAS 0, 1, 2, 3, 4 e 5 APROVADAS / ETAPAS 6 e 7 PARCIAIS / ETAPAS 8–14 PLANEJADAS |

| 2026-08-23 | Encerramento pós-merge da Etapa 2: PR #150, merge `bcb0951ee05c41b03eae2a66e712d1f041cde7f8`, CI run `32613109759` com Linux/Windows PASS, baseline 2571 arquivos, 109 manifests íntegros e suíte pós-merge `1617 passed, 2 skipped`. A aprovação permanece limitada à matriz DPI, catálogo real, clipping, hashes e auditoria visual; release e DPI físico do Windows não são declarados. | ETAPAS 0, 1, 2, 3, 4 e 5 APROVADAS / ETAPAS 6 e 7 PARCIAIS / ETAPAS 8–14 PLANEJADAS |
### Addendum vivo — 2026-08-23 — Etapa 6

A lacuna local da Etapa 6 foi fechada no checkpoint fec2ee1b068b46d2cfe096519a0526ea576059ec. A evidência reproduzível está em docs/evidence/ETAPA_6_GIZMO_GAP_CLOSURE_2026-08-23.md e no relatório Windows ampliado com 24 capturas. Este addendum não reescreve os snapshots de 2026-08-22; ele os supersede somente para o estado vivo atual. A etapa ainda não é formalmente concluída enquanto PR, CI, merge, pós-merge e revisão visual humana não forem realizados.
### Atualização viva da Etapa 6 — CI da PR #152

O primeiro run remoto da PR #152 (`32627926745`) falhou nos jobs Linux e Windows no gate de tipagem de `src/tools/polygon_edit_tool.py`, antes dos testes funcionais. A causa foi reproduzida e corrigida localmente; a suíte completa permanece `1621 passed, 2 skipped`. Um novo run remoto ainda é obrigatório antes de qualquer merge.
### Encerramento pós-merge da Etapa 6

A Etapa 6 foi merged na PR #152 em `ebdb889bc415eca4ea263a98e59551645130fbd5`. CI Linux/Windows e validação pós-merge local passaram; a etapa está encerrada no escopo aprovado, sem aprovação de release.
| 2026-08-23 | Retomada da Etapa 7 na branch `Ailton/stage7-side-panels-completion-20260823`: Objects, Layers, Groups e Collision receberam toolbars compactas preservando handles; seleção/inspector, estados, rolagem, tooltips e menus de contexto foram testados. Commit técnico `8334f87bd58ff2e33c5e7041217bf6354844bd2e`; suíte `1625 passed, 2 skipped`; auditor nativo Windows `12 capturas / 0 findings`; Pillow/OpenCV `12/12 PASS`. Revisão visual humana foi bloqueada por ACL e PR/CI/merge/pós-merge estão pendentes. | ETAPA 7 PASS_LOCAL_AUTOMATED / GATES PENDENTES |

### Addendum vivo — Etapa 7 — 2026-08-23

O snapshot de 2026-08-22 permanece histórico e limitado ao `GroupsPanel`. O estado vivo atual cobre os quatro painéis e está documentado em `docs/evidence/ETAPA_7_PAINEIS_LATERAIS_COMPLETA_2026-08-23.md`. A etapa não é formalmente aprovada: a árvore local contém artefatos históricos não rastreados, a revisão humana visual está bloqueada pelo ACL do visualizador e o ciclo remoto ainda não foi executado.
