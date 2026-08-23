# Plano Vivo e Fonte de Verdade — Interface Moderna e Profissional

**Projeto:** NeoEng-D-Trace
**Data de criação:** 2026-08-21
**Status do plano em 2026-08-23:** ETAPAS 0–7 APROVADAS SOMENTE NOS ESCOPOS COMPROVADOS / ETAPAS 8–14 PLANEJADAS E NÃO INICIADAS. Esta linha é o estado vivo canônico; registros anteriores que indiquem outro estado são snapshots históricos.
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

O histórico recente registra correções responsivas e auditorias de painéis. Isso não é tratado como validação automática deste plano. A Etapa 0 foi concluída somente como caracterização reproduzível da baseline. As Etapas 1–7 foram encerradas nos escopos comprovados nos respectivos snapshots pós-merge em docs/evidence/; isso não transforma requisitos fora desses escopos em implementados. As Etapas 8–14 permanecem planejadas e não podem iniciar sem o ciclo de autorização e baseline correspondente.

Na reconciliação de 2026-08-22, o `main` observado foi o merge `425f21df2bbf9a67c01a577b59ae6bbba25995b7`, que incorpora a documentação pós-merge da Etapa 5. A branch de trabalho do baseline da Etapa 6 parte desse mesmo conteúdo. Os diretórios locais de artefatos históricos não rastreados foram preservados e não são usados como evidência de árvore limpa, release ou aprovação.

Na leitura do estado local, foram encontrados diretórios de artefatos de auditoria não rastreados. Portanto, a árvore não foi considerada limpa; essa condição foi preservada e declarada. A validação pós-merge da Etapa 6 não dependeu de uma alegação de árvore limpa local.

As capturas, hashes e resultados de auditorias existentes continuam sendo evidências de seus respectivos commits e escopos. Não são evidência automática das etapas deste plano. A evidência local atual da Etapa 6 é válida apenas para a branch e o worktree identificados no relatório correspondente.

Reconciliação viva de 2026-08-23: a Etapa 7 está encerrada somente no escopo descrito em docs/evidence/ETAPA_7_PAINEIS_LATERAIS_ENCERRAMENTO_POS_MERGE_2026-08-23.md, após PR, CI, merge e validação pós-merge. O registro anterior limitado ao GroupsPanel é histórico e foi supersedido pelo addendum vivo posterior; não foi apagado. Diretórios locais não rastreados continuam preservados e não são evidência de árvore limpa.

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

**Estado vivo em 2026-08-23:** APROVADA NO ESCOPO COMPROVADO após PR, CI, merge, validação pós-merge e revisão visual humana registrados nos addenda e evidências da Etapa 6. O escopo aprovado não amplia automaticamente os comportamentos que o baseline marcou como fora do contrato.

### Etapa 7 — Painéis laterais

Corrigir tamanho mínimo, rolagem, hierarquia, estados disabled/enabled e separação entre inspector principal, camadas do projeto e cenário. Substituir grades de botões por barras de ferramentas compactas quando não houver perda de descoberta; manter menus de contexto e tooltips. Nada pode ficar esmagado ou inacessível.

**Gate:** geometrias Qt reais, ações clicáveis, seleção de itens, propriedades editáveis, painéis visíveis em DPI/resoluções alvo e ausência de falsos positivos do auditor.

**Estado vivo em 2026-08-23:** APROVADA NO ESCOPO COMPROVADO nos quatro painéis e no inspector, conforme docs/evidence/ETAPA_7_PAINEIS_LATERAIS_ENCERRAMENTO_POS_MERGE_2026-08-23.md. A aprovação não declara concluídas as Etapas 8–14 nem requisitos de editor de cenário que pertençam a essas etapas.

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

| 2026-08-23 | Revisão visual humana das 12 capturas reais concluída: 0 clipping irreversível, 0 sobreposição estrutural, 0 artefatos visuais bloqueantes e tema escuro consistente. A rolagem compacta foi distinguida de clipping. Menus abertos permanecem cobertos pelos testes Qt, não por captura. | ETAPA 7 PASS_LOCAL_AUTOMATED + HUMAN_VISUAL_PASS / CICLO REMOTO FINAL PENDENTE |

### Addendum vivo — revisão visual humana da Etapa 7 — 2026-08-23

A revisão humana está registrada em `docs/evidence/ETAPA_7_REVISAO_VISUAL_HUMANA_2026-08-23.md`. Ela não reescreve o relatório anterior nem aprova release. A Etapa 7 ainda requer promoção da PR, decisão de merge e validação pós-merge.

| 2026-08-23 | Encerramento pós-merge da Etapa 7: PR #154, CI `32634474078` Linux/Windows aprovado, merge `bf6da772afb659e0801b869f2ce5a0740918d94e`, main sincronizado, evidência `110 manifests`, baseline `2618 files` e suíte pós-merge `1625 passed, 2 skipped`. | ETAPA 7 APROVADA NO ESCOPO DEFINIDO / ETAPAS 8–14 PLANEJADAS |

### Encerramento pós-merge — Etapa 7 — 2026-08-23

O encerramento está documentado em `docs/evidence/ETAPA_7_PAINEIS_LATERAIS_ENCERRAMENTO_POS_MERGE_2026-08-23.md`. A aprovação é limitada ao escopo dos painéis laterais e não é aprovação de release.

## 11. Especificação consolidada obrigatória — 2026-08-23

Esta seção consolida os requisitos operacionais do plano e é a referência de execução para as Etapas 0–14. Ela não substitui políticas globais, contratos, workflows ou ADRs. Em conflito, a governança global prevalece e a divergência deve ser registrada antes de qualquer alteração.

### 11.1 Referência visual e limites
A imagem de referência orienta hierarquia visual, distribuição de espaço, densidade, agrupamento, proporção entre viewport e painéis, cores e leitura do estado ativo. Não exige copiar a cena, assets ou conteúdo ilustrativo. Toda comparação separa fatos mensuráveis (geometria, clipping, overlap, dimensões, cores e widgets), julgamento humano (legibilidade, equilíbrio, hierarquia e aspecto profissional) e limitações de resolução, backend ou DPI. Semelhança subjetiva, captura antiga, build antiga ou CI verde isolado não aprovam etapa.

### 11.2 Máquina de estados e bloqueio
Estados permitidos: PLANEJADA / NÃO INICIADA, EM IMPLEMENTAÇÃO, PASS_LOCAL, HUMAN_VISUAL_PASS, CI_PASS, MERGED, PÓS_MERGE_PASS, APROVADA NO ESCOPO COMPROVADO, PARCIAL, NÃO TESTADA, BLOQUEADA e REPROVADA. PASS_LOCAL, revisão humana ou CI isoladamente não encerram etapa. APROVADA exige implementação completa, testes positivos/negativos, artefatos reais, hashes, auditoria visual, revisão humana necessária, documentação, CI no SHA exato, merge autorizado e validação pós-merge independente. Qualquer falha, divergência, artefato ausente, não determinismo, regressão ou impedimento interrompe a etapa; corrige-se a causa, nunca o gate.

### 11.3 Etapa 0 — Baseline, governança e inventário
Somente caracterização; nenhum código, contrato, regra ou layout de produção pode ser alterado. Ler políticas, plano mestre, riscos, template, workflows, contratos e documentos vivos; confirmar branch, SHA-base, remote, worktree e untracked sem apagar dados do proprietário; inventariar MainWindow, ToolPalette, tool manager/buttons, abas, painéis, X-Ray, gizmo, navegação, cenário separado, inspetores, menus, atalhos, status bar e exportadores; identificar sinais, nomes públicos e contratos; reproduzir problemas; capturar sem projeto, projeto, painéis, gizmo, validação, cenário e máscara/X-Ray em 1920x1080, 1366x768 e 1280x720; registrar dimensões, transparência, hashes, geometria Qt, clipping, overlap, paleta, contraste e acessibilidade; gerar e validar manifesto via Git blob. Saída: baseline reproduzível, findings e limitações.

### 11.4 Etapa 1 — Tokens e tema
Centralizar QSS/funções sem cores arbitrárias. Tokens mínimos: canvas #11161b, panel #1d2329, surface #252c33, elevated #2d363e; primary #e8edf2, secondary #a8b2bd, disabled #66717c; accent #59d8e8, active #3f93ad, selection #365f78, focus #7ce9f5; success #75d99b, warning #e4bb6a, error #e77b86. Manter hover, pressed, checked, disabled e focus; remover bordas laranja sem função; garantir contraste; evitar sombras/gradientes excessivos e temas não controlados. Testar paleta, contraste, estados, cores não autorizadas e capturas.

### 11.5 Etapa 2 — Ícones
Biblioteca vetorial versionada, própria/licenciada/nativa, sem caminho local e sem emoji funcional. Catálogo: seleção, laço, laço poligonal, laço magnético, caneta, retângulo, elipse, edição de polígono, pincel de colisão, mover, zoom, fit, foco, abrir, salvar, exportar, desfazer, refazer, limpar, visibilidade, bloqueio, adicionar, remover, subir, descer, X-Ray, iluminação, gizmo, snap, grade, cenário e validação. Cada ícone deve suportar 16/20/24 px ou escala vetorial, DPI 100/125/150/200, padding, tooltip, accessibleName/Description, fallback textual, contraste e estados. Testar catálogo, build Windows, fallback, tooltip, atalhos, clipping e DPI.

### 11.6 Etapa 3 — Rail esquerda
Rail de aproximadamente 56–72 px, botões quadrados, ícone, tooltip, atalho, foco e indicador ativo. Grupos: seleção (seleção, retângulo, elipse); contorno (laços, caneta, edição); colisão (pincel, colisor, validação); navegação (mover, zoom, fit, foco). Preservar tool_manager, tool_buttons, nomes, sinais, seleção exclusiva, atalhos e compatibilidade. Testar mouse/teclado, checked/disabled, tooltips, exclusividade, compacto e clipping.

### 11.7 Etapa 4 — Barra superior
Agrupar com separadores nativos: Arquivo (abrir projeto/imagem, salvar, exportar); Visualização (fit, 1:1, foco, grade, snap); Renderização/máscara (Lit, X-Ray 1/2/3, máscara); Edição (undo, redo, limpar, configurações); Comandos (Ctrl+K, recentes e buscas). Uniformizar ícone/texto; compacto IconOnly com tooltip e acessibilidade; amplo TextBesideIcon; remover espaços artificiais e órfãos; preservar menus/atalhos/sinais; preview de cenário abre editor separado. Testar ações, overflow e não invasão do canvas.

### 11.8 Etapa 5 — Viewport e HUD
Viewport amplo, sem ocultar objeto, vértice, colisor ou gizmo. HUD/status informa Lit/X-Ray, zoom, snap, cursor, grade, gizmo, seleção e transformação sem overlap. Persistente na QStatusBar; temporário expira. Testar zoom, X-Ray no Mask Viewer, coordenadas, fit, clipping, overlap e gizmo nas três resoluções.

### 11.9 Etapa 6 — Gizmo
A imagem orienta composição e não substitui a lógica. Melhorias: escala proporcional ao zoom, linhas finas, X/Y/Z consistentes, anéis discretos, alças, eixo ativo, caixa suave e feedback numérico sem ocultar texto. Preservar translação, rotação, escala, seleção, vértices, undo/redo, bloqueio, snap, pivô, coordenadas, colisor, exportação e transações. Cada gesto é uma transação; cancelamento restaura snapshot; undo/redo determinístico. Testar hit-test, limites, multi-seleção, vértice, DPI, resize e capturas anotadas.

### 11.10 Etapa 7 — Painéis
Não misturar editor principal e cenário; manter rolagem e mínimo de conteúdo. Objects: lista, busca, seleção, visibilidade, bloqueio, grupos e ações. Layers: hierarquia, profundidade, visibilidade, bloqueio, ordenação e toolbar. Groups: criar/remover, adicionar/remover seleção, ordenar, visibilidade e bloqueio. Collision: validação, shapes, vértices, convexidade, topologia, exportação e geração. Inspector recolhível: Transform, Pivot, Scale, Rotation, Snap, Parallax, Sockets, Collision e Metadata. Divisores sutis, sem QGroupBox excessivo; ações primárias visíveis e secundárias em contexto. Testar geometria, seleção, edição, estados, rolagem, tooltips, menus, clipping e DPI.

### 11.11 Etapa 8 — Editor de cenário separado
Janela própria com viewport, layer stack, inspector, camera preview, parallax, sockets, overlays, undo/redo, salvamento e exportação. Testar abrir/fechar, carregar, selecionar, mover, transformar, adicionar layer, salvar/recarregar, exportar, cancelar sem perda e isolamento. Preview não é autoria. Iluminação, partículas, shaders, pós-processamento, triggers e streaming só entram em etapas/contratos próprios; ausência não pode ser mascarada.

### 11.12 Etapa 9 — Responsividade e DPI
Matriz: 1280x720 compacto, 1366x768 compacto, 1920x1080 desktop; escalas 100/125/150/200%; maximizar/restaurar, fonte maior e troca de monitor quando disponível. Verificar dimensões lógicas/físicas, transparência, clipping, overlap, paleta, hashes, geometrias Qt, widgets críticos, rolagem e menus dentro da tela. Não reduzir fonte abaixo do limite nem esconder controle sem rota comprovada.

### 11.13 Etapa 10 — Acessibilidade
Adicionar accessibleName/Description, tooltips, Tab, foco, atalhos, teclado, contraste, estados que não dependam só de cor, nomes claros e erros acionáveis. Botão sem texto possui tooltip e nome. Testar mouse e teclado separadamente, conflitos, foco, paleta e texto alternativo.

### 11.14 Etapa 11 — Auditoria visual
Ler PNGs com Pillow/OpenCV; validar dimensões, alpha, SHA-256, clipping, overlap canvas/toolbars/painéis, geometrias Qt, paleta/contraste, widgets críticos e áreas anotadas. Relatório determinístico PASS/FAIL/NOT_CONFIRMED. Estados: sem projeto, projeto, painéis, gizmo, validação, cenário e máscara/X-Ray. PASS automático não substitui revisão humana; NOT_CONFIRMED não vira PASS. Fixtures negativos devem falhar para clipping, hash, dimensão, transparência e overlap. É proibido remover widgets, alterar thresholds, mascarar paths, omitir worktree ou trocar falha por warning sem justificativa. Revisão humana registra captura, resolução/DPI e observações concretas; não substitui automação.

### 11.15 Etapa 12 — Performance
Medir contra baseline: abertura; troca de resolução; alternância/resize de painéis; seleção; zoom; captura; abertura do cenário; memória lógica; widgets; renderização. Método determinístico. Hardware pode ser informativo quando a política não o torna gate; orçamento lógico, tick e contagem são reproduzíveis. Não sacrificar legibilidade, adicionar dependência pesada sem justificativa, reconstruir painéis em cada resize ou atualizar continuamente; usar incremental/debounce.

### 11.16 Etapa 13 — Compatibilidade e pacote
Validar Python, build oficial, portátil, GUI, CLI, Godot, Unity, JSON, GLB, perfis, estado e dependências. Recurso não suportado por engine recebe NÃO SUPORTADO ou fallback observável. Build em worktree limpo registra commit, manifesto, hashes, logs, smoke e warnings; sem dados pessoais, caminhos ou credenciais. Testar rollback de empacotamento.

### 11.17 Etapa 14 — Checkpoint obrigatório
Sem abreviação: ler governança; confirmar ponto/autorização; baseline; implementação completa; testes focados; testes negativos; suíte/gates estáticos; auditoria visual/capturas; análise de artefatos/geometria/paleta/clipping/overlap/desempenho; hashes e Git blob; regressões/limitações; documentação viva sem reescrever snapshots; diff/higiene/segredos/worktree; commit somente com comprovação; revalidar SHA; push normal sem force quando autorizado; PR com base/head/evidências; revisar CI no SHA; autorização explícita; merge normal; validação independente pós-merge no main; evidência pós-merge; só então APROVADA. Ordem: 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14. Etapa 0 não implementa; concluir uma não conclui a seguinte.

### 11.18 Critério final único
Encerramento somente quando cada etapa tiver decisão individual; funções existentes operarem; três resoluções e quatro escalas forem validadas; painéis acessíveis; auditoria sem achados reais; capturas/relatórios hashados; revisão humana registrada; build limpa aprovada; Godot/Unity documentados; documentos reconciliados; CI verde no SHA correto; push/PR/merge autorizado; e pós-merge aprovado. Isso não aprova release; release tem gates próprios.