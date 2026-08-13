# Changelog

## [Unreleased] — programa de estabilização, Etapas 1 a 13

Registro documental contínuo, atualizado em 13 de agosto de 2026. O estado real da branch, da PR e do CI deve ser verificado antes de qualquer transição.

### Etapa 13 — aprovada localmente, ainda não integrada

- reduz `main_window.py` de `1.306` para `1.175` linhas físicas e separa sessão de documento, caminhos de estado, conversão de imagem, traduções e coordenação do autosave;
- adiciona autosave local versionado, atômico e limitado, com quarentena de snapshot inválido, fingerprint do projeto-fonte e recuperação explícita;
- preserva snapshots quando a recuperação é adiada, exige `Salvar como` após conflito da origem e limpa o snapshot somente após salvamento explícito bem-sucedido;
- aprova `951` testes no commit limpo `58ef2ac5091683ac81a9ee93a6ca6db2e617dd63`, com `11.578/12.469` linhas, `3.370/3.964` branches e `90,96%` combinada;
- mantém zero módulos abaixo de 30%, baseline de `334` arquivos, mypy em `80` arquivos, gates Black/isort/Bandit aprovados e nenhuma vulnerabilidade conhecida nas dependências auditáveis;
- reconcilia `196` testes legados com `27/27` falhas históricas previstas e zero inesperadas;
- valida fora do pytest um `QTimer` real e a recuperação entre processos distintos sem alterar o projeto-fonte;
- registra e corrige falhas intermediárias, inclusive uma suíte `939 passed, 1 failed`, risco de exclusão no fluxo adiado e branches inicialmente abaixo de 85%;
- mantém `R-011` aberto, Etapa 13 não concluída, Etapa 14 não iniciada e release não aprovada até merge autorizado e CI pós-merge auditado.

### Etapa 12 — integrada e concluída, segurança e limites operacionais

- vincula a validação local ao commit técnico `da7611b543bb0ceb4eb8e67a7900aadcb8f04a5f` com worktree limpa;

- adota a ordem normativa do plano mestre; o plano de desenvolvimento antigo permanece classificado como roadmap histórico superado;
- centraliza tetos de configuração, imagens, projeto, geometria, detecção, broadphase, atlas, GLTF e logs;
- rejeita JSON desconhecido/duplicado/não finito, imagens incompatíveis ou multiframe, geometria excessiva/inválida e alocações patológicas antes da mutação final;
- corrige a regressão descoberta na suíte integral sem remover a validação: estado inválido usa assinatura determinística para a janela, mas continua impossível de salvar/exportar;
- aprova localmente `928` testes, `11.174/12.040` linhas, `3.309/3.892` branches, mypy em `73` arquivos, Bandit e pip-audit sem vulnerabilidades conhecidas;
- reconcilia `196` testes legados com `27/27` divergências históricas e zero inesperadas;
- audita o CI pré-merge `31684136128` no HEAD fonte `a42b54b07d8e9e10feb8d283adc664b52f9d25d3`: Linux e Windows aprovam `928` testes e as métricas exatas; dois artefatos têm digest confirmado e a varredura recursiva cobre `1.419` payloads sem violações;
- integra a PR `#49` em `872bf079d228d13d0203d22b844052b1f920e99b` e aceita o CI pós-merge `31686321925` após auditoria de Linux/Windows, logs, digests, cobertura, legado e `1.419` payloads sem violações;
- aprova localmente `929` testes e baseline de `326` arquivos no pacote documental de encerramento, sem alteração nas métricas de cobertura do código-fonte;
- integra o fechamento pela PR `#50` em `fc81c2ea10e751c15a39627d462ddfff390eeb04` e aceita o CI final `31688307089`, com `929` testes em Linux/Windows e artefatos auditados;
- encerra `R-012` e conclui a Etapa 12 no escopo aprovado; `R-011`, Etapas 13–14 e release permanecem pendentes.

### Etapa 11 — integrada e concluída no escopo aprovado

- adiciona 145 testes comportamentais para UI, ferramentas, comandos, detecção, máscaras, processamento visual e exportação;
- aprova 877 testes no Windows/Python 3.11.9;
- eleva a cobertura de 69,93% para 90,91% combinada, com 92,77% de linhas e 85,05% de branches;
- elimina todos os módulos abaixo de 30% e leva cena, janela principal, laço magnético, caneta, painel de colisões e exportador de sprites a 92–100%;
- remove três ramos comprovadamente inalcançáveis: um da paleta e dois da detecção automática;
- integra a PR `#45` em `2a38b89e542390b3b4396a88d9a416f3695caadc` e aceita seu CI pós-merge `31491221322`; integra o fechamento formal pela PR `#46` em `a22a90088220e586c3382c3ed5dc1075a3ff7e6b`; aceita o CI pós-merge final `31495971632` somente após auditoria de logs, hashes e 1.418 payloads; encerra `R-003` e conclui a Etapa 11 no escopo aprovado, sem aprovar release.

### Etapa 10 — concluída no escopo aprovado

- corrige offsets Godot, pivôs Unity e divergência entre exportação de cena e objeto;
- versiona schemas específicos e centraliza validação de retângulos e pivôs;
- protege PNG/JSON do atlas com rollback após falha no segundo commit;
- adiciona harness reproduzível para Godot e Unity, com nomes e caminhos Unicode;
- fixa o importador oficial Unity glTFast `6.19.0` e valida GLB real nas duas engines;
- aprova `17` testes da etapa, `730` oficiais, `196` históricos com reconciliação `27/27`, mypy em `70` arquivos e cobertura combinada `69,93%`;
- registra falhas de licença, bootstrap, `ApiUpdater` e ausência de importador GLB nativo sem convertê-las em sucesso;
- abre a PR `#42`; rejeita o primeiro CI remoto `31450335289` apesar dos gates verdes, porque a inspeção dos artefatos revelou upload documental obsoleto e proveniência ambígua do resumo legado;
- generaliza o upload de evidências; rejeita também o segundo CI `31451363518`, que publicou os arquivos corretos, mas ainda exigia metadado externo para ligar o merge sintético ao HEAD da PR;
- eleva o resumo para schema v4, separando merge testado, HEAD fonte, estado da worktree e origem histórica, com prova de ancestralidade;
- rejeita o terceiro CI `31452032479` após o scanner profundo encontrar referências proibidas em ZIPs históricos aninhados; sanitiza quatro pacotes mediante autorização explícita e recalcula checksums e hashes dependentes;
- aceita o CI pré-merge `31457937902` somente após validar os dois jobs, `729` testes por sistema, proveniência v4, cobertura exata e `44` arquivos de evidência com varredura recursiva sem violações;
- integra a PR `#42` no merge `9b22bdc54b13992658172d4748bfab44f3127c8e`;
- rejeita o CI pós-merge `31463873481` apesar dos jobs verdes: Linux cobriu uma linha e um branch a menos que Windows;
- adiciona teste que força a ordem inversa da broadphase e elimina a cobertura dependente da ordem de conjunto;
- aceita o CI pré-merge corretivo `31464786333` após auditoria dos artefatos e integra a PR `#43` em `f8caec3e7156d308f03046f81d2c89996f959466`;
- aceita o CI pós-merge `31469610508` após confirmar `730` testes nos dois sistemas, cobertura detalhada idêntica, `45` evidências e zero violações recursivas;
- conclui a Etapa 10; mantém a Etapa 11 não iniciada e a release não aprovada.

### Etapa 9 — integrada e encerrada no escopo aprovado

- consolida `src.collision` como API pública única de colisão estática e transforma `src.physics` em compatibilidade sem implementações concorrentes;
- corrige IDs heterogêneos, validação geométrica, falso positivo côncavo e direção do MTV;
- remove promessas inertes de gravidade, backend, passo fixo e callbacks, alinhando código e UI ao escopo estático da versão 1.0;
- adiciona 39 casos da etapa; aprova 702 testes oficiais e 27/27 divergências históricas exatas;
- alcança 73.65% de linhas, 57.65% de branches e 69.79% combinada; módulos canônicos de colisão entre 89% e 95%;
- commit técnico `28273dfb7cb0e0aeab1f8f9f3a99c07df3b08a76`; `R-008` permanece aberto até merge e CI pós-merge; release não aprovada.
- registra que o primeiro CI da PR (`31444322950`) falhou em Linux e Windows por manifesto de baseline desatualizado; o pacote corretivo regenera e verifica o manifesto antes de repetir o CI.
- registra que o segundo CI (`31444483410`) expôs comparação não determinística de `baseline_date` após a virada UTC; a data passa a ser informativa, validada como ISO e coberta por regressão.
- CI corrigido `31444774539` aprova Linux e Windows sem anotações no HEAD `eed101ee03e74298e36c15cf271e378fd51be5dc`.
- CI final da PR `31445205968` aprova o HEAD documental `86cfb6b0cf43613417b12b3366f423216bd1e036`; PR `#40` mesclada em `76dd6b7ca3e7da08fab653d66ae29a33a839baf3`; CI pós-merge `31445518755` aprovado nos dois sistemas, sem anotações; `R-008` encerrado; release não aprovada.

### Etapa 8 — integrada e encerrada no escopo aprovado

- corrige o fallback de triangulação dependente da orientação e exige convexidade de cada orelha;
- valida coordenadas, repetição de vértices, área, quantidade de triângulos, preservação de área e índices do backend opcional;
- adiciona 38 casos Bézier/geométricos e substitui uma asserção antes inócua por rejeição explícita de fixture autossobreposto;
- aprova 125 testes focais, 660 totais no commit técnico, 661 no pacote pré-merge, 662 no fechamento e 27/27 divergências legadas estritamente reconciliadas;
- alcança 95.59% de linhas e 93.29% de branches no núcleo geométrico;
- PR `#38` mesclada em `fc869250e5067fb7b06b70c7d2dd3c0e1e1ee94e`; CI da PR `31440755594` e pós-merge `31441024001` aprovaram Linux e Windows sem anotações; `R-007` encerrado; Etapa 9 e release não iniciadas.

### Etapa 7 — integrada e encerrada no escopo aprovado

- define a matriz integral de argumentos, modos, saídas e códigos `0`, `1` e `2`;
- elimina argumentos de operação silenciosamente ignorados e rejeita combinações incompletas;
- propaga códigos reais por `app.py` e execução direta do módulo;
- valida subprocessos, entradas reais, JSON/projeto reabertos e GLBs com magic `glTF`;
- alcança 85% no launcher e 68.53% de cobertura combinada, com 620 testes no commit técnico e 622 no fechamento;
- PR `#36` mesclada em `99326f2d7ccf7046e401d90830feb8a5d33e9f9a`; CI da PR `31436763095` e pós-merge `31437000772` aprovaram Linux e Windows sem anotações; `R-006` encerrado; release não aprovada.

### Cobertura de módulos críticos — integrada

- adiciona 46 testes comportamentais, negativos e Qt offscreen;
- eleva a cobertura combinada de 62.45% para 67.51%, com 589 testes aprovados;
- leva os módulos priorizados de 8–29% para 60–100%, exceto `launcher.py`, reservado à Etapa 7;
- rejeita escalas/pesos de borda inválidos, dimensões Qt não suportadas e zoom zero no overlay;
- PR `#35` mesclada em `511c0ba47f29971bfa218349fff2119ebe69dc3c`; CI pós-merge `31435181903` aprovou Linux e Windows;
- mantém `R-003` aberto, metas finais pendentes e release não aprovada.

### Etapa 6 — integrada e encerrada no escopo aprovado

- unifica toolbar, painel e metadados genéricos no schema de colisões `neoeng-d-trace-collisions` v1;
- valida referências, pontos finitos, quantidade mínima e área antes da exportação;
- torna o TXT uma visão derivada com substituição atômica e preservação do destino em falha;
- adiciona testes negativos, round-trip e integração UI; PR `#33` mesclada em `73a128ec44cde17867bbac6a7854ce86a43aba5a`; CI pós-merge `31431739320` aprovou Linux e Windows; `R-005` encerrado; release não aprovada.

### Auditoria corretiva local — 2026-08-10

- atualiza Pillow para 12.3.0 e adiciona gates reproduzíveis com `pip-audit` e Bandit;
- corrige falso sucesso da CLI, limites/rotação do atlas e exportação real do painel de colisões;
- executa 196 testes legados e reconcilia estritamente 26 divergências conhecidas, sem ocultar as falhas brutas;
- integra `LayersPanel`, consolida o alias de lasso e cobre a API SAT compatível;
- habilita mypy em corpos não anotados e cobertura de branches com piso incremental de 62%;
- adiciona política de segurança, matriz funcional viva e evidência auditada;
- migra metadados para PEP 621, exige `poetry check --strict` e promove Flake8 integral a gate com zero achados;
- remove código morto duplicado do exportador GLTF e centraliza o bootstrap Qt dos testes;
- publica o commit `236eefd41ee51c7085e21d52fc80074eede0a793`; a PR `#28` foi mesclada em `56533b65f81d21fd9c762aa10c0d3e6747d742ca`; CI pós-merge `31423386971` aprovou Linux e Windows; release permanece não aprovada.

- ambiente reproduzível consolidado em Python 3.11, Poetry 2.4.1 e CI Linux/Windows;
- formato de projeto `.ndtproj` com schema v1 estrito, migração legada, escrita atômica e round-trip de colisões e segmentos Bézier;
- ciclo Abrir/Salvar integrado e validado no Windows;
- Etapa 5 funcionalmente integrada até o Pacote 5C no merge commit `6c4bcb3d945405a4615a4d6551247d1b01ce79f1`;
- Pacote 5C foi mesclado pela PR `#27`; o HEAD final da PR é `8ce44c238aaea79dafa64b8e1bba3ba5a8a7157e`;
- revisão do Pacote 5C identificou e corrige atomicidade observável, sincronização da Caneta com a seleção e rejeição de no-op obsoleto;
- a validação local v3.1 passou no Windows, mas a revisão posterior bloqueou o commit por evidência incompleta do arquivo untracked e por sincronização ausente após Undo/Redo global no mesmo objeto Bézier;
- o corrector v3.2 preservou essas correções, mas o dry-run foi bloqueado pelo mypy antes de qualquer escrita porque o acesso ao objeto selecionado não possuía narrowing explícito de nulidade;
- o corrector v3.3 passou no Windows com 50 testes focais, 9 documentais, 465 totais e cobertura global de 65%, produzindo evidência autossuficiente dos 19 arquivos;
- a revisão pós-v3.3 bloqueou o commit porque Undo, Redo e Escape durante um arraste de handle não cancelavam primeiro a prévia ativa, uma mudança externa podia conflitar com a soltura do mouse e o relatório permanente ainda exibia as métricas antigas 48/6/460;
- o corrector v3.4 passou no Windows com 59 testes focais, 10 documentais, 475 totais e cobertura global de 65%, produzindo evidência completa dos 19 arquivos com métricas dinâmicas;
- a revisão pós-v3.4 bloqueou o commit porque a criação Bézier atômica rejeitava a orientação oposta em vez de normalizá-la e `HandleMoveCommand` podia aceitar um polígono amostrado degenerado, invertido ou auto-intersectante;
- a correção incremental v3.5 centraliza a preparação geométrica Bézier, normaliza o polígono para sentido anti-horário, rejeita amostras inválidas antes de mutar o modelo ou o histórico e mantém prévias inválidas apenas no estado visual da Caneta;
- o corrector v3.5 passou no Windows com 67 testes focais, 11 documentais, 484 totais e cobertura global de 65%, com evidência completa dos 19 arquivos;
- a revisão pós-v3.5 bloqueou o commit porque o fallback geométrico determinístico, efetivamente usado no ambiente bloqueado sem Shapely, não detectava todos os contatos de extremidade e cruzamentos colineares entre arestas não adjacentes;
- a correção incremental v3.6 implementa interseção inclusiva de segmentos, validação finita e remoção do vértice terminal duplicado em curvas fechadas válidas;
- o corrector v3.6 passou no Windows com 71 testes focais, 12 documentais, 489 totais e cobertura global de 65%, com evidência completa dos 19 arquivos;
- a revisão pós-v3.6 bloqueou o commit porque o bloco opcional de Shapely ainda participava da decisão de validade e conversões de coordenadas Bézier não representáveis podiam produzir `OverflowError` fora do contrato de rejeição;
- a correção incremental v3.7 torna o validador determinístico a única autoridade de validade, rejeita aritmética de área não finita e traduz overflow de coordenadas em `ValueError` ou `CommandStatus.REJECTED` sem mutação;
- o corrector v3.7 foi bloqueado no dry-run antes de escrever arquivos porque o teste de independência tentava substituir `scene_module.Polygon` sem permitir a ausência intencional desse símbolo;
- a correção incremental v3.8 ajustou somente o harness desse teste com `raising=False`, preservou o estado inicial exato do v3.6 e manteve inalterado o código funcional da linha v3.7;
- o corrector v3.8 passou no Windows com 77 testes focais, 13 documentais, 496 totais e cobertura global de 66%, com evidência completa dos 19 arquivos;
- a revisão pós-v3.8 bloqueou o commit porque `canonical_point()` ainda deixava `OverflowError` escapar pela amostragem direta de `Scene.sample_beziers_to_polygon()` e pela exportação de sprite de um Bézier carregado;
- a correção incremental v3.9 centraliza a conversão numérica representável em `src/core/bezier_geometry.py`, transforma overflow em `ValueError` controlado para todos os chamadores e amplia o escopo final para 20 arquivos;
- o corrector v3.9 passou no Windows com 80 testes focais, 14 documentais, 500 totais e cobertura global de 66%, com evidência completa dos 20 arquivos;
- a revisão pós-v3.9 bloqueou o commit porque a fórmula Bernstein ainda podia gerar `inf` intermediário a partir de controles finitos extremos e `Scene.add_object()` executava o reparo heurístico antes de conferir se `auto_repair` estava habilitado;
- a correção incremental v4.0 preserva exatamente a avaliação Bernstein no domínio ordinário e usa De Casteljau numericamente estável para controles extremos, aplica o invariante canônico na amostragem pública e na sincronização da Caneta, e torna o reparo de polígonos estritamente opt-in com rejeição controlada;
- o corrector v4.0 passou no Windows com 89 testes focais, 15 documentais, 510 totais e cobertura global de 66%, com evidência completa dos 20 arquivos;
- a revisão pós-v4.0 bloqueou o commit porque o índice de handle não tinha contrato de tipo estrito: booleanos e `1.0` eram aceitos como índice 1, enquanto listas ou dicionários podiam expor `TypeError` bruto;
- a correção incremental v4.1 exige `handle_index` inteiro não booleano no núcleo e no comando, rejeita entradas inválidas de forma controlada e garante ausência de mutação e de histórico;
- o gate oficial v4.1 passou no Windows/Python 3.11.9 com 95 testes focais, 16 documentais, 517 totais, baseline funcional 263 e cobertura global de 66%;
- a validação manual foi aprovada e a integração visual automática aprovou 17/17 estados, com ZIP SHA-256 `2981a29d85f8df329bddd0711e16b54665a75d8522447405c476359d6bd2d189`;
- o commit funcional `9bf83af0d58b5984ccfefc59a543428379b02632` foi publicado por fast-forward sem força;
- o commit documental pré-merge `8ce44c238aaea79dafa64b8e1bba3ba5a8a7157e` elevou a baseline para 264 arquivos;
- o CI final pré-merge `#83` (`31135700216`) aprovou Linux e Windows no HEAD documental exato;
- a PR `#27` foi mesclada por merge commit em `6c4bcb3d945405a4615a4d6551247d1b01ce79f1`, preservando a branch funcional;
- o CI pós-merge `#84` (`31136893143`) aprovou Linux e Windows no merge commit;
- os artefatos pós-merge são Linux `8978309717` (`25ee252a77fb43796a6c5b1cbbf10c5987791187a6e860a11c17e9980d45b091`) e Windows `8978326062` (`0432e2e7ccc11d21d8769f160268f820ccf62af7edb5fd6f5a2070bcca4c912f`);
- o pacote documental pós-merge foi integrado pela PR `#28`; `R-004` está encerrado no escopo aprovado e a Etapa 5 está concluída;
- o CI final da PR `#28` (`31422901244`) e o CI pós-merge `31423386971` aprovaram Linux e Windows;
- a PR técnica final `#29` foi mesclada em `574be9bd0268e70c384903f93f16cf6e73aa57a2`; o CI pós-merge `31425585259` aprovou Linux e Windows sem anotações;
- naquele snapshot da Etapa 5, a Etapa 6 ainda não havia sido iniciada; a branch foi preservada e a release permaneceu não aprovada;
- atualiza `checkout`, `setup-python` e `upload-artifact` para as releases oficiais `v7`/Node.js 24, eliminando a causa do aviso;
- consolida a configuração efetiva do mypy em `mypy.ini`, remove a duplicação inócua no `pyproject.toml` e confirma corpos não tipados sem notas de exclusão.

## 0.6O2 — observabilidade confiável e persistência segura

- no modo `--validation-log`, as cinco exportações manuais usam uma pasta exclusiva da sessão e não dependem de seletores nativos;
- o resumo da sessão passa a distinguir `SUCCESS`, `INCOMPLETE` e `FAILURE` sem declarar sucesso quando faltam ações;
- tokens de objetos passam a usar HMAC com chave aleatória não registrada, reduzindo a possibilidade de recuperação por dicionário;
- exceções registradas fora de um bloco `except` passam a conter o traceback real da exceção;
- erros que já possuem evento estruturado deixam de ser recapturados como `python.log`, evitando contagem duplicada;
- substituições de JSON, sprite, atlas e GLB deixam de apagar o destino antes da gravação e usam `os.replace` no mesmo sistema de arquivos;
- os bytes e contratos dos formatos exportados permanecem inalterados nos testes de regressão;
- `CLI-LAZY-001` e `LOG-DUP-001` são encerrados; as demais limitações conhecidas permanecem documentadas.

## 0.6O1 — observabilidade da validação manual

- adiciona modo opcional `--validation-log` com eventos JSONL sanitizados;
- registra abertura, idioma, imagem, criação/seleção de polígono e exportações;
- valida pós-condições reais de JSON, PNG, atlas e GLB;
- captura avisos, erros, tracebacks e exceções não tratadas;
- corrige a duplicação do logger sem alterar os fluxos funcionais;
- mantém uma única árvore `src/`, sem aliases ou migração estrutural.

## 0.6C1 — consolidação da renomeação em árvore única

### Decisão

- encerrada a migração física para `neoeng_d_trace/`;
- restaurada uma única fonte de verdade em `src/`;
- removidos aliases, wrappers e a entrada `python -m neoeng_d_trace`;
- distribuição e marca permanecem `neoeng-d-trace` / NeoEng-D-Trace;
- `app.py` e o console `src.launcher:main` são as entradas oficiais.

### Preservado

- todas as melhorias funcionais do checkpoint 0.5.2F3 e da identidade 0.6N1;
- correções JSON e GLTF/GLB, incluindo `save_binary()`, generator, atomicidade e padding;
- interface bilíngue, ferramentas, física, UI e formatos existentes;
- configuração `config.json` na raiz.

### Removido explicitamente

- segunda árvore `neoeng_d_trace/`;
- testes e documentos exclusivos da migração física.

> As entradas 0.6N2 e 0.6N3 abaixo permanecem somente como histórico de uma abordagem cancelada. Elas não descrevem a arquitetura atual.



## 0.6N3E-R3 — contrato real de metadados vazios no GLB

- Corrige somente o contrato de teste da serialização real GLB.
- Registra que `pygltflib 1.16.5` remove listas vazias durante a serialização JSON.
- Mantém `groups` presente em memória antes da gravação e considera sua ausência após reabertura equivalente a nenhuma associação.
- Não altera o exportador, a geometria, os buffers, a interface ou qualquer arquivo de runtime.

## [0.6N3-E-R2] - 2026-07-27

### Correção de serialização GLB real
- O exportador passa a chamar `GLTF2.save_binary()` diretamente quando disponível.
- Isso evita que `GLTF2.save()` do `pygltflib` 1.16.5 substitua o `asset.generator` definido pelo NeoEng-D-Trace.
- Backends alternativos e doubles de teste sem `save_binary()` continuam usando o fallback `save()`.
- Retorno explícito `False` do backend de persistência passa a ser tratado como falha.

### Contrato GLB
- O teste de objeto individual passa a distinguir dados úteis de padding do chunk BIN.
- O tamanho JSON do buffer e o blob reaberto são validados com alinhamento de quatro bytes.
- Os dois bytes finais de padding são exigidos como zero sem alterar `bufferView.byteLength`.
- Geometria, índices, accessors, metadados e aliases `src.*` permanecem inalterados.

## [0.6N3-E] - 2026-07-27

### Migração estrutural
- Migração física de `exporters.gltf_exporter` para `neoeng_d_trace.exporters`.
- Preservação de `src.exporters.gltf_exporter` como alias do mesmo módulo.
- Atualização dos imports internos para identidade, logger, cena e triangulação canônicos.

### Garantias
- AST funcional preservado sem alteração intencional de algoritmo.
- Cena, cena sem metadados e objeto individual comparados byte a byte com backend determinístico.
- Estrutura GLTF, buffer binário, accessors, offsets, metadados e atomicidade protegidos por testes.
- A validação Windows exige `pygltflib` real e reabre os arquivos GLB produzidos.
- 2.5D, UI, idiomas e formato de projeto permanecem fora do escopo.
- `LOG-DUP-001`, `PERF-MAGNETIC-001`, `UI-RESIZE-PT-001` e `CLI-LAZY-001` permanecem abertos.

## [0.6N3-D] - 2026-07-27

### Migração estrutural
- Migração física de `exporters.json_exporter` para `neoeng_d_trace.exporters`.
- Preservação de `src.exporters.json_exporter` como alias do mesmo módulo.
- Atualização dos imports internos para modelo, logger e perfis canônicos.

### Garantias
- Schemas, ordem de campos, indentação, perfis e mensagens de erro não foram alterados.
- Sete saídas determinísticas e a persistência em arquivo foram congeladas por hashes de contrato.
- GLTF, interface, idiomas e formato de projeto permanecem fora do escopo.
- `LOG-DUP-001`, `PERF-MAGNETIC-001`, `UI-RESIZE-PT-001` e `CLI-LAZY-001` permanecem abertos.

## [0.6N3-C] - 2026-07-27

### Migração estrutural
- Migração física de `sprite_exporter`, `atlas_exporter` e quatro perfis de metadados para `neoeng_d_trace.exporters`.
- Preservação dos caminhos históricos `src.exporters.*` como aliases do mesmo objeto de módulo.
- Atualização do import do `Packer` para o namespace canônico, sem alteração do algoritmo.

### Garantias
- Formatos de sprite, atlas e metadados não foram alterados.
- Interface, idiomas, GLTF, JSON de cena e comportamento do Laço Magnético permanecem fora do escopo.
- `LOG-DUP-001`, `PERF-MAGNETIC-001`, `UI-RESIZE-PT-001` e `CLI-LAZY-001` permanecem abertos.

# NeoEng-D-Trace — Registro de mudanças

> NeoEng-D-Trace é a identidade ativa. O pacote de distribuição é `neoeng-d-trace`; módulos são migrados fisicamente em lotes, mantendo `src.*` como compatibilidade controlada.

## [2026-07-27] — Etapa 0.6N3-B: geometria, colisão e utilitários fundamentais

### Alterado

- transferida a fonte de verdade de broadphase, SAT, decomposição convexa, wrapper de colisão, packing e máscaras de seleção para `neoeng_d_trace`;
- os seis caminhos históricos correspondentes em `src.*` foram reduzidos a aliases dos mesmos objetos de módulo;
- referências internas do wrapper de colisão passaram a resolver o SAT pelo namespace canônico;
- adicionados testes de ordem de importação, identidade, localização física e contratos comportamentais dos seis módulos.

### Preservado

- algoritmos e resultados numéricos não foram intencionalmente alterados;
- imports antigos continuam válidos;
- schemas de cena, física, colisão, atlas e máscaras permanecem inalterados;
- interface, idiomas, Laço Magnético, exportadores e arquivos do usuário não foram modificados.

### Limites conhecidos

- `physics.physics_manager`, exportadores, ferramentas e UI ainda dependem parcialmente de `src.*`;
- `PERF-MAGNETIC-001`, `UI-RESIZE-PT-001` e `CLI-LAZY-001` permanecem abertas;
- validação completa no Windows/Python 3.11 continua obrigatória.

## [2026-07-27] — Etapa 0.6N3-A: primeiro lote da migração física

### Alterado

- transferida a fonte de verdade de `app_identity`, `logger`, `config`, `commands` e `models.scene` para `neoeng_d_trace`;
- imports internos desses módulos passaram a usar exclusivamente o namespace canônico;
- os cinco caminhos históricos em `src.*` foram reduzidos a aliases de compatibilidade para os mesmos objetos de módulo;
- classes como `Scene`, `CommandManager` e `ConfigManager` passam a declarar `__module__` no namespace canônico;
- adicionados testes de ordem de importação, identidade de classes, estado compartilhado, round-trip de configuração e contratos da cena.

### Preservado

- imports históricos `src.*` continuam válidos;
- módulos canônicos e históricos permanecem o mesmo objeto em memória;
- schemas de configuração, cena e exportação não foram alterados;
- algoritmos, interface, traduções, Laço Magnético, formato de projeto e arquivos do usuário não foram modificados.

### Limites conhecidos

- os demais módulos continuam fisicamente em `src/` e serão migrados em lotes posteriores;
- desempenho adicional do Laço Magnético, redimensionamento do painel em português e imports tardios da CLI permanecem pendências não bloqueantes;
- a suíte Qt e a validação visual no Windows continuam obrigatórias antes da aprovação da etapa.

## [2026-07-27] — Etapa 0.6N2: namespace canônico do pacote

### Alterado

- criado o namespace importável `neoeng_d_trace` com aliases para os mesmos objetos de módulo existentes em `src.*`;
- movida a lógica do launcher para `neoeng_d_trace.launcher`, mantendo `app.py` como entrada compatível;
- adicionada execução por `python -m neoeng_d_trace`;
- nome da distribuição alterado de `polygontool` para `neoeng-d-trace`;
- adicionada a entrada de console `neoeng-d-trace` no metadado Poetry;
- declarados explicitamente os pacotes `neoeng_d_trace` e `src` durante a fase de compatibilidade.

### Preservado

- os módulos funcionais continuam fisicamente em `src/` nesta subfase;
- imports antigos `src.*` permanecem válidos;
- aliases canônicos resolvem para os mesmos objetos de módulo, evitando classes e singletons duplicados;
- algoritmos, interface, idiomas, exportadores, configuração e formato de projeto não foram alterados.

### Limite conhecido

- `__module__` de classes existentes continua apontando para `src.*` até a migração física R3B;
- dependências ainda não estão travadas; isso pertence à etapa de ambiente reproduzível;
- desempenho adicional do Laço Magnético permanece dívida técnica registrada.

## [2026-07-27] — Etapa 0.6N1: identidade central e runtime bilíngue

### Alterado

- criado `src/core/app_identity.py` como fonte única da identidade visual e técnica aprovada;
- títulos da janela principal migrados para NeoEng-D-Trace em inglês e português;
- título com arquivo carregado preserva a nova marca ao alternar idioma;
- CLI, logger, GLTF generator, benchmarks e executor de testes legados passaram a consumir a nova identidade;
- ações de colisão, modos Lit/Raio-X e diálogo de abertura da janela principal receberam atualização bilíngue;
- funções duplicadas e inalcançáveis de exportação de colisão foram removidas sem alterar o formato exportado;
- adicionados testes de identidade não gráficos e contratos Qt para os dois idiomas.

### Preservado

- algoritmos de detecção, laços, polígonos, colisões, física e exportação geométrica não foram modificados;
- formato JSON e TXT das colisões não foi alterado;
- `PROJECT_FORMAT_ID` continua indefinido até ADR própria, evitando atrelar o formato à marca;
- pacote de distribuição `polygontool` permanece temporariamente até a Fase R3;
- configuração na raiz e histórico Git permanecem inalterados.

### Limites conhecidos

- ExportDialog, ExportPreview, MaskViewer, CollisionPanel e LayersPanel ainda não possuem cobertura bilíngue completa;
- CLI e logs continuam em inglês;
- migração de pacote, AppData, formato de projeto, executável e instalador permanece pendente;
- validação visual e suíte Qt completa continuam obrigatórias no Windows/Python 3.11.

## [2026-07-27] — Etapa 0.6R: realinhamento documental e privacidade

### Alterado

- definição do produto consolidada a partir das decisões aprovadas;
- identidade NeoEng-D-Trace formalizada sem alterar o código funcional;
- README corrigido para refletir os resultados reais da 0.5.2F3 e da auditoria 0.6A1;
- metadado de autoria substituído por identidade técnica e e-mail `noreply`;
- caminho pessoal do Windows removido da documentação;
- envio para serviço externo de cobertura removido;
- CI alinhada ao Python 3.11 e configurada para execução Qt offscreen;
- estratégia do novo repositório revisada para um baseline limpo, sem os 15 commits históricos locais.

### Preservado

- nenhum arquivo funcional em `app.py` ou `src/` foi alterado;
- hashes críticos do checkpoint 0.5.2F3 permanecem obrigatórios;
- histórico local continua preservado e não será enviado ao novo repositório;
- nenhuma configuração de remote, commit, tag, stage ou push faz parte desta etapa.

### Limites

- a renomeação interna ainda não foi executada;
- disponibilidade jurídica/comercial do nome ainda deve ser confirmada antes de lançamento público;
- o texto jurídico da licença proprietária ainda está pendente;
- lacunas de formato de projeto, 2.5D, build e exportação permanecem abertas.

## Nota de confiabilidade do histórico legado

As entradas abaixo são preservadas como registro histórico. Afirmações amplas como “todas as funcionalidades testadas”, “compatível” ou “sem regressões” devem ser interpretadas conforme as evidências disponíveis na época e não substituem os relatórios de validação atuais.

## Histórico legado — PolygonTool

Este arquivo registra o status das funcionalidades adicionadas e alterações no projeto, para rastrear quando o projeto quebrou.

## [2025-11-30] - CI Pipeline, CLI Headless e Benchmarks: Infraestrutura externa e configurações de sistema

### Adicionado
- **CI Pipeline**: GitHub Actions workflow (`.github/workflows/ci.yml`) com testes automatizados, linting, type checking e cobertura
- **CLI Headless**: Suporte a modo headless em `app.py` com argparse para processamento automatizado
  - Carregamento de imagens e projetos
  - Export para GLTF (cena e objetos individuais)
  - Export para JSON metadata
  - Salvamento de projetos
- **Benchmarks**: Suite completa de benchmarks em `bench/` para medir performance
  - `benchmark_triangulation.py`: Performance de triangulação de polígonos
  - `benchmark_convex_decomp.py`: Performance de decomposição convexa
  - `benchmark_gltf_export.py`: Performance de export GLTF
  - `run_benchmarks.py`: Executor principal para todos os benchmarks

### Status
- CI Pipeline configurado para múltiplas versões Python (3.9-3.11)
- CLI Headless funcional com operações de export automatizadas
- Benchmarks abrangentes com medição de tempo, memória e estatísticas
- Todas as funcionalidades testadas e integradas sem regressões

## [2025-11-30] - Export GLTF: Geração de mesh.glb com triangulação e metadados

### Adicionado
- Novo módulo `gltf_exporter.py` para exportação GLTF (.glb)
- Triangulação automática de polígonos usando Mapbox Earcut
- Geração de meshes GLTF com posições, índices e primitivas
- Inclusão de metadados como object_id, layer, polygon, groups
- Suporte a exportação de cena completa ou objeto individual
- Integração com UI de exportação (botões "Export Scene to GLTF" e "Export Object to GLTF")
- Salvamento atômico para evitar corrupções

### Status
- GLTF export funcional com triangulação robusta
- Metadados preservados como extras no formato GLTF
- Compatível com engines 3D que suportam GLTF

## [2025-11-30] - Convex Decomposition com Limites Box2D

### Adicionado
- Implementação de merge de triângulos em convex_decomp.py para produzir polígonos convexos com <=8 vértices.
- Algoritmo greedy para combinar triângulos adjacentes compartilhando arestas.
- Compatibilidade com Box2D que limita fixtures a 8 vértices.

### Status
- Decomposição convexa agora produz polígonos otimizados para Box2D.
- Testes atualizados para validar polígonos com <=8 vértices.

## [2025-11-30] - Performance Gating com Progress e Cancel

### Adicionado
- Sinais de progresso em XrayWorker (progress 0-100).
- Método cancel() em XrayWorker para operações pesadas off-UI.
- Suporte a cancelamento de tarefas assíncronas.

### Status
- Operações pesadas agora têm feedback de progresso e podem ser canceladas.
- Xray generation off-UI mantido.

## [2025-11-30] - Comportamento Transacional em CommandStack

### Adicionado
- CompositeCommand para executar múltiplos comandos como transação.
- Se um comando falha, os executados anteriormente são desfeitos automaticamente.
- Suporte a undo em lote para operações compostas.

### Status
- CommandStack agora suporta transações para composite operations.
- Tests existentes passam, sem regressões.

## [2025-11-30] - Melhorias na Validação de Polígonos (Self-Intersections)

### Adicionado
- Checagem de self-intersections em _validate_polygon usando algoritmo de interseção de segmentos de linha.
- Polígonos com arestas que se cruzam são rejeitados.
- Funções auxiliares: _has_self_intersections e _lines_intersect.

### Status
- Validação completa: winding + self-intersections.
- Testes passam, sem regressões.

## [2025-11-30] - Melhorias na Validação de Polígonos

### Adicionado
- Validação de winding (counter-clockwise) em _validate_polygon usando fórmula shoelace.
- Polígonos devem ter área positiva para serem válidos.

### Status
- Validação aprimorada sem quebrar funcionalidade existente.
- Testes de cena passam.

## [2025-11-30] - Correção de Validação de Configuração

### Corrigido
- Erro de validação Pydantic para window_geometry: alterado de Dict para str para corresponder ao formato de armazenamento (base64).
- Aplicação agora inicia sem erros de configuração.

### Status
- Configuração carrega corretamente, geometria da janela restaurada via base64.
- Sem quebras em outras funcionalidades.

## [2025-11-30] - Unificação da Implementação SAT (Separating Axis Theorem)

### Adicionado
- Implementação canônica de SAT em src/physics/sat2d.py com epsilon para tolerância numérica, validação de entrada e MTV correto.
- Unificação das implementações: src/collision/sat2d.py agora importa da física e fornece wrapper numpy para compatibilidade.
- Função sat_polygon_vs_polygon com assinatura consistente, retornando tipos simples (bool, Optional[Tuple[float, float]]).
- Testes mantidos passando para ambas as interfaces.

### Status
- SAT unificado com implementação robusta em physics, wrapper em collision para compatibilidade.
- Todas as funções têm validação, epsilon e testes.
- Sem duplicação de código, API consistente.

### Próximas Melhorias
- Integrar SAT no PhysicsManager para checagem de colisão centralizada.

## [2025-11-30] - Melhorias no Módulo Convex Decomposition

### Adicionado
- Integração de mapbox_earcut para triangulação eficiente em src/physics/convex_decomp.py.
- Fallback para ear clipping algorithm quando mapbox_earcut não disponível.
- Função triangulate_to_convex usando numpy arrays para earcut.
- Testes unitários em tests/test_convex_decomp.py para triangulação de triângulos e polígonos côncavos (L-shape).

### Status
- Convex decomposition funcional com library otimizada e fallback robusto.
- Todas as funções testadas, integração mantida.
- Dependências opcionais: mapbox_earcut, numpy.

### Próximas Melhorias
- Implementar merging de triângulos para polígonos convexos maiores.

## [2025-11-30] - Melhorias no Módulo Broadphase

### Adicionado
- Nova implementação BroadPhaseSAP (Sweep and Prune) em src/physics/broadphase.py para eficiência em cenários axis-aligned.
- Testes unitários em tests/test_broadphase_sap.py para insert/update/remove e potential pairs.

### Status
- Duas implementações de broadphase: UniformGrid e SAP.
- SAP é determinístico e eficiente para muitos cenários.
- Todas as funções testadas.

### Próximas Melhorias
- Comparação de performance entre UniformGrid e SAP.

## [2025-11-30] - Melhorias no Módulo Physics

### Adicionado
- Melhorias em src/physics/physics_manager.py: fixed timestep com accumulator, scale handling (pixels_per_meter), gravity, backend placeholder, collision callbacks.
- Novos métodos: add_body, remove_body, step, register_collision_callback.
- Metadata support em PhysicsObject.
- Testes unitários em tests/test_physics_manager.py para add/remove body, step accumulator, callbacks.

### Status
- Physics manager com API clara e fixed timestep para determinismo.
- Integração mantida com broadphase e SAT.
- Todas as funções têm validação e testes.

### Próximas Melhorias
- Backend integration com Box2D ou fallback.

## [2025-11-30] - Melhorias no Módulo Collision

### Adicionado
- Melhorias em src/collision/sat2d.py: type hints, docstrings, epsilon para tolerância numérica, validação de entrada (mínimo 3 vértices).
- Atualização de src/collision/__init__.py para expor funções de SAT.
- Testes unitários em tests/test_collision_sat2d.py para casos de colisão, não-colisão e contato.

### Status
- SAT implementation profissional com validação e testes.
- Todas as funções têm docstrings e tipagem.
- Integração mantida, sem quebras.

### Próximas Melhorias
- Unificar com src/physics/sat2d.py se necessário.

## [2025-11-30] - Melhorias no Core Module

### Adicionado
- Exception handling em CommandManager.execute/undo/redo com logging de erros.
- Docstrings e typing consistente em commands.py.
- Testes unitários para CommandManager: exec/undo/redo/exception-case.
- Worker integration para ViewProcessor.xray generation usando QThreadPool em canvas_view.py.
- XrayWorker e XrayWorkerSignals para processamento assíncrono de xray.

### Status
- Todos os testes passando (7/7 novos em test_commands + existentes).
- Aplicação roda sem erros, comandos com exception handling, xray generation assíncrona.
- ViewProcessor mantém métodos puros e testáveis.

### Próximas Melhorias
- Implementar padrões avançados: comando transacional.
- Adicionar mais testes para fluxos de falha.

## [2025-11-28] - Integração de Exportadores (Fase 7)

### Adicionado
- Sistema completo de exportadores modulares para sprites, atlas e metadados JSON.
- `sprite_exporter.py`: Extração de sprites mascarados com antialiasing ('none', 'fast', 'high'), padding, trim, suporte a BGR/BGRA e RGB/RGBA.
- `json_exporter.py`: Exportação de metadados JSON com campos obrigatórios (rect, rect_trimmed, pivot normalizado, polygon_in_image/sprite, layer, group).
- `atlas_exporter.py`: Empacotamento determinístico em atlas múltiplos, com sorting por área/area/width/name, verificação de não-overlap.
- Perfis `unity.py` e `godot.py`: Ajustes específicos para engines (pivot normalizado).
- `export_preview.py`: Widget UI para preview de exportações.
- `test_exporters.py`: Testes unitários abrangentes (alpha mask, trim/padding, profiles, no-overlap, multi-atlas, save atomic).
- `docs/phase-7-exporters.md`: Documentação com APIs, extensibilidade e edge cases.

### Status
- Todos os testes passando (6/6 novos + existentes).
- Aplicação roda sem erros, exportadores funcionais.
- APIs testáveis headless, separação UI/core mantida.
- Dependências: Pillow (manipulação imagens), NumPy (arrays), OpenCV (antialias).

### Próximas Melhorias
- Integrar preview no diálogo de exportação.
- Adicionar mais perfis (ex: custom).
- Otimizar packing para rotação.

## [2025-11-28] - Integração de Groups Feature

### Adicionado
- Suporte completo a groups: criação, remoção, adição/remoção de objetos, visibilidade, bloqueio, ordenação.
- Classe Group no scene.py com atributos id, name, visible, locked, members.
- Métodos no Scene para gerenciar groups: create_group, remove_group, add_object_to_group, etc.
- Comandos undo/redo para groups: CreateGroupCommand, RemoveGroupCommand, AddToGroupCommand, RemoveFromGroupCommand, MoveGroupCommand.
- UI GroupsPanel para gerenciar groups via botões (New, Delete, Add Selected, Remove Selected, Up, Down, Toggle Vis, Toggle Lock).
- Persistência de groups em save_project/load_project.
- Testes para groups: test_groups.py.
- Integração do GroupsPanel no MainWindow com splitter de três painéis (Canvas, SidePanel, GroupsPanel).
- Método load_image adicionado ao Scene para carregar imagens.

### Status
- Todos os testes passando (9/9 incluindo test_groups).
- Aplicação inicia sem erros, carrega imagens, UI com três painéis.
- Funcionalidades de layers, Bézier e groups operacionais.
- Logs de erro em operações de persistência.

### Próximas Melhorias
- Adicionar logs detalhados para erros em todas as operações.
- Melhorar UI para edição de Bézier e groups.
- Implementar exportação de sprites com layers e groups.

## [2025-11-28] - Integração de Melhorias Iniciais

### Adicionado
- Suporte completo a layers (visibilidade, bloqueio, ordenação).
- Comandos undo/redo para layers: CreateLayerCommand, RemoveLayerCommand, MoveLayerCommand, ToggleLayerVisibilityCommand, ToggleLayerLockCommand.
- Comandos para edição de polígonos: ExpandContractCommand, HandleMoveCommand.
- Suporte a curvas Bézier: conversão Catmull-Rom, amostragem para polígonos.
- Testes adicionais: test_expand_contract_command.py, test_handle_command.py.
- Correção de sintaxe em magnetic_lasso.py.
- Sistema de logging para erros em operações críticas.
- Pasta backups/ para organização de backups de arquivos.

### Status
- Todos os testes passando (8/8).
- Aplicação inicia e carrega imagens corretamente.
- Funcionalidades de layers e Bézier operacionais.
- Logs de erro adicionados em operações de persistência (save/load project).

### Próximas Melhorias
- Adicionar logs detalhados para erros em todas as operações.
- Melhorar UI para edição de Bézier.
- Implementar exportação de sprites com layers.
