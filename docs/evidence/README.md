- ADENDO_INTEGRIDADE_ARTEFATOS_2026-08-16.md — correção da cadeia de bytes, bloqueio de manifests e limites históricos declarados; não é aprovação de merge.
- ETAPA_7_SINCRONIZACAO_OVERRIDES_2026-08-16.md — snapshot histórico da sincronização real; não deve ser lido como aprovação do estado atual sem o gate de integridade e o HEAD correspondente.
# Evidências de validação

Estado vivo após o merge da PR `#107`: a Etapa 4 do editor profissional está integrada no `main` pelo merge `19f3cfd`; o CI `32314410332` foi aprovado em Linux e Windows. A Etapa 5 do plano profissional foi iniciada para persistência versionada, importação/exportação e adaptadores explícitos. Isso não constitui aprovação automática de release.

- `ETAPA_4_CAMERA_PARALLAX_MODELO_2026-08-18.md` — modelo matemático puro de câmera ortográfica/parallax, com testes negativos e hashes; evidência da implementação integrada.
- `ETAPA_4B1_SCHEMA_LATERAL_2026-08-18.md` — schema lateral versionado, hash-bound, limites, round-trip, parsing negativo, escrita atômica e rollback; evidência da implementação integrada.
- `ETAPA_4B2_PREVIEW_OVERLAYS_2026-08-18.md` — preview somente leitura, overlays e isolamento da edição normal; evidência da implementação integrada.
- `ETAPA_4B3_AUTORIA_CENARIO_2026-08-18.md` — autoria lateral, Undo/Redo isolado, persistência e auditoria Qt/Pillow/NumPy; evidência da implementação integrada.
- `ETAPA_4B4_EXPORTACAO_ENGINES_2026-08-18.md` — snapshot histórico da primeira execução da exportação; consulte a correção atual dos validadores.
- `ETAPA_4B4_CORRECAO_VALIDADORES_2026-08-18.md` — correção do contrato LF/blob, validadores Godot/Unity fortalecidos, cinco casos negativos por engine e execução real reproduzível; evidência da implementação integrada.
- `ETAPA_4B5_FECHAMENTO_QUALIDADE_2026-08-18.md` — determinismo, benchmark e fechamento de qualidade; evidência da implementação integrada.
- `ETAPA_4B_ENCERRAMENTO_POS_MERGE_2026-08-18.md` — confirmação do merge `a129cd2` e do CI pós-merge `32184900502` em Linux e Windows.

- `ETAPA_3_PALETA_COMANDOS_2026-08-18.md` — implementação da paleta visual, busca, teclado, Escape, localização e acessibilidade, com capturas reais en/pt, geometrias Qt, hashes Pillow/OpenCV e validação do manifest.
- `ETAPA_3_ENCERRAMENTO_POS_MERGE.md` — fechamento pós-merge da PR `#97`, CI `32125768535` aprovado em Linux/Windows e sincronização do `main` ao merge `5d4c0829`.

- `RECONCILIACAO_DOCUMENTAL_2026-08-18.md` — reconciliação dos documentos vivos com o merge da PR `#92`, registro do novo plano e classificação explícita de paleta/parallax como planejados e não iniciados.
- `ETAPA_4_TRANSACAO_GLOBAL_MANIFESTOS_2026-08-17.md` — transação única e rollback global de múltiplos manifestos, com testes Python, execução real Godot/Unity, hashes e falhas intermediárias preservadas.

- PRIVACIDADE_ARTEFATOS_RECONCILIACAO_2026-08-17.md — correção fail-closed dos identificadores de host/processo nos artefatos e regeneração independente dos manifests.
- `APP_ICON_INTEGRATION_2026-08-17.md` — integração do ativo autorizado no runtime Qt, PyInstaller, executável GUI e atalho WiX, com hashes e validação real.
- `RECONCILIACAO_GATES_RELEASE_2026-08-17.md` — decisão vigente que remove
  assinatura, formalização jurídica e CI dinâmico das engines como gates
  obrigatórios, aprova o R-016 e registra a verificação atual da baseline com
  1268 arquivos. Snapshots históricos permanecem inalterados.
- ETAPA_AUDITOR_VISUAL_REPRODUTIVEL_2026-08-16.md — contrato fail-closed para PNGs Pillow/OpenCV, hashes, alfa, geometrias Qt reais, clipping, sobreposição, paleta QSS e anotações reproduzíveis.

- `ETAPA_3_PLUGIN_GODOT_SOURCE_ONLY_2026-08-16.md` — addon Godot somente com GDScript, diagnóstico somente leitura, ZIP determinístico e execução headless real; não cobre a importação de Sprite2D/colisão da etapa 4.

- `VALIDACAO_REAL_ENGINES_HARNESS_2026-08-16.md` — execução real do harness de exportadores no Godot 4.7 e Unity 6000.5.7f1; aprova apenas o escopo JSON/PNG/GLB existente, não os plugins nativos planejados.
- `ETAPA_6_REPRODUCAO_FALHAS_UNITY_2026-08-16.md` — reprodução real no Unity dos dois estados de falha históricos da Etapa 6; os logs originais continuam declarados como indisponíveis.

- `ETAPA_1_2_CONTRATO_INTEGRACAO_PLUGINS_2026-08-16.md` — contrato comum e manifesto determinístico dos adaptadores nativos; inclui hashes reais, escrita atômica, testes negativos e artefatos reproduzíveis. Engines Godot/Unity permanecem NÃO TESTADAS nesta etapa.

- `ETAPA_DETECCAO_QUALIDADE_PRE_MERGE_2026-08-16.md` — corpus adversarial real do pipeline OpenCV, métricas de máscara/borda, comparação dos modos, reprodução do limite de 2.000 pontos, benchmark, artefatos hashados e riscos residuais pré-merge.
- ETAPA_UI_RESPONSIVA_AUDITORIA_2026-08-16.md — auditoria funcional e visual da MainWindow em três resoluções, com artefatos PNG, hashes, mensagem real de validação, gates locais e limitações tipográficas explícitas.

- `ETAPA_ROI_GRABCUT_COLISAO_PRE_MERGE_2026-08-15.md` — pipeline funcional ROI/GrabCut, visualização raio-X, colisão composta, artefatos reais, hashes, gates locais e reconciliação legada; aprovação local pré-merge, sem CI remoto.


- `ETAPA_14_BUILD_RELEASE_PRE_MERGE.md` — build portátil/MSI, duas execuções reproduzíveis, instalação/desinstalação, engines reais, gate completo, falhas intermediárias e bloqueios explícitos de release.
- `ETAPA_14_RELEASE_VALIDATION_MANIFEST.json` — manifesto estruturado do commit-fonte, hashes, métricas, fixtures e decisões.
- `ETAPA_14_GODOT_RELEASE_VALIDATION.json` — relatório real do Godot `4.7` sobre fixtures produzidos pelo candidato.
- `ETAPA_14_UNITY_RELEASE_VALIDATION.json` — relatório real do Unity `6000.5.7f1` com glTFast `6.19.0`.
- `ETAPA_14_ENCERRAMENTO_POS_MERGE.md` — auditoria dos logs, proveniência, cobertura, legado e artefatos do CI pós-merge.
- `ETAPA_14_ENCERRAMENTO_POS_MERGE.json` — manifesto estruturado do fechamento técnico pós-merge.
- `RELEASE_V0.2.0_PUBLICACAO.md` — commit, tag, hashes, validações reais e limitações da release oficial publicada.
- `CHECKLIST_RELEASE_PUBLICA.md` — gates necessários para transformar uma build técnica em release pública.
- `RELEASE_INICIAL_VALIDACAO.md` — decisão e controles da primeira release oficial sem assinatura, com hashes e transparência.
- `NOTICE.md` — aviso de propriedade, identidade visual autorizada pelo proprietário e atribuições futuras.
- `POLITICA_PUBLICACAO_E_DADOS.md` — decisão de publicação e dados, com formalizações futuras documentadas.
- `IDENTIDADE_VISUAL_E_ATRIBUICOES.md` — ativo visual autorizado pelo proprietário, hash e trâmites futuros.
- `PLANO_MIGRACAO_BUILDER_MSI_R016.md` — plano técnico e critérios de aceite para substituir `msilib`.

- `AUDITORIA_INTEGRIDADE_PRE_ETAPA_14_2026-08-13.md` — auditoria de fabricação,
  alteração de testes, gates, cadeia de custódia, workflows remotos e
  reproduções locais antes da Etapa 14.
- `PRE_ETAPA_14_ENGINE_VALIDATION_MANIFEST_2026-08-13.json` — vínculo verificável
  entre commit-fonte, versões, contratos, relatórios reais de Godot/Unity e hashes canônicos.
- `PRE_ETAPA_14_GODOT_VALIDATION_2026-08-13.json` — saída normalizada da
  importação real no Godot.
- `PRE_ETAPA_14_UNITY_VALIDATION_2026-08-13.json` — saída normalizada da
  importação real no Unity com glTFast.
- `PRE_ETAPA_14_RECRIACAO_EVIDENCIAS_2026-08-13.md` — limites honestos e método
  para produzir provas substitutivas atuais dos pacotes frágeis.

Cada etapa deve criar um arquivo `ETAPA_<numero>_<nome>.md` baseado no modelo abaixo.

## Modelo obrigatório

```markdown
# Evidência — Etapa N

## Identificação
- Commit:
- Branch:
- Data/hora:
- Responsável:

## Ambiente
- Sistema operacional:
- Python:
- Dependências/lockfile:

## Objetivo e escopo

## Entradas
- Arquivo:
- SHA-256:

## Comandos executados

## Resultados
- Aprovados:
- Reprovados:
- Ignorados:
- Bloqueados:
- Cobertura:

## Artefatos

## Falhas e causa raiz

## Limitações e riscos residuais

## Decisão
APROVADO | REPROVADO | BLOQUEADO | PARCIAL | NÃO TESTADO
```

Uma captura isolada, relato verbal ou resultado sem commit identificado não é evidência suficiente.

- ETAPA_1_CENARIOS_PROFISSIONAIS_2026-08-19.md — baseline e contratos da extensão profissional de autoria visual de cenários; permanece pendente até o fechamento do baseline e dos gates.
- `ETAPA_3_EDITOR_PROFISSIONAL_CENARIO_2026-08-19.md` — snapshot histórico da implementação do editor profissional; a integração atual foi encerrada pelo merge `f477b6d` e CI `32306687719`. Não reescrever este snapshot para representar a Etapa 4.
- `ETAPA_4_EDITOR_PROFISSIONAL_PREVIEW_2026-08-19.md` — snapshot histórico pré-merge da Etapa 4; preservado sem reescrita retroativa.

## Evidências registradas

- `SANITIZACAO_PACOTES_HISTORICOS_2026-08-11.md` — autorização, transformação,
  hashes anteriores/novos e validação recursiva dos ZIPs históricos.

- `ETAPA_10_EXPORTADORES_ENGINES.md` — contratos Godot/Unity, rollback do atlas,
  harness reproduzível, validação real em ambas as engines e decisão local
  pré-merge; não representa integração nem aprovação de release.
- `ETAPA_10_CORRECAO_COBERTURA_POS_MERGE.md` — merge da PR `#42`, CI pós-merge
  verde rejeitado, causa-raiz, correção determinística, PR `#43` e validações aceitas.
- `ETAPA_10_ENCERRAMENTO_POS_MERGE.md` — CI corretivo `31464786333`, merge
  `f8caec3e7156d308f03046f81d2c89996f959466`, pós-merge `31469610508`,
  artefatos auditados e encerramento formal sem aprovação de release.

- `ETAPA_1_AMBIENTE_REPRODUZIVEL_CI_WINDOWS_LINUX.md` — validações da Etapa 1
  anteriores ao merge.
- `ETAPA_1_ENCERRAMENTO_POS_MERGE.md` — validação da `main` e encerramento
  formal da Etapa 1 depois do merge.

- `ETAPA_2_INVENTARIO_FUNCIONAL_CARACTERIZACAO.md` — inventário, caracterização e riscos da Etapa 2 antes do merge.
- `ETAPA_2_ENCERRAMENTO_POS_MERGE.md` — validação da `main` e registro de encerramento da Etapa 2 depois do merge.


- `ETAPA_3_PACOTE_1_PERSISTENCIA_VERSIONADA.md` — implementação, auditoria e
  validação do formato de projeto v1.
- `ETAPA_3_PACOTE_1_ENCERRAMENTO_POS_MERGE.md` — validação da `main` e registro
  de encerramento do Pacote 1 da Etapa 3 depois do merge funcional.

- `ETAPA_4_ENCERRAMENTO_POS_MERGE.md` — validação da `main` e encerramento
  formal da Etapa 4 depois do merge.
- `ETAPA_4_EVIDENCE_MANIFEST.json` — manifesto estruturado da Etapa 4.

- `ETAPA_5_PACOTE_1_COMMAND_MANAGER_CONTRACT.md` — implementação e validação
  funcional do contrato, pilhas, transação e estado da UI.
- `ETAPA_5_PACOTE_1_ENCERRAMENTO_POS_MERGE.md` — validação da `main` e
  encerramento formal do Pacote 1 da Etapa 5.
- `ETAPA_5_PACOTE_1_EVIDENCE_MANIFEST.json` — manifesto estruturado do
  encerramento do Pacote 1 da Etapa 5.

- `ETAPA_5_PACOTE_2A_OBJECT_RELATIONS.md` — integridade transacional de
  identidade, relações, colisão, forma e limpeza no núcleo da cena.
- `ETAPA_5_PACOTE_2B_UI_COMMAND_PATHS.md` — remoção dos fallbacks manuais nos
  caminhos de interface cobertos pelos comandos do Pacote 2A.
- `ETAPA_5_PACOTE_3A_GIZMO_GESTURE.md` — prévia contínua e consolidação do
  movimento pelo gizmo em uma única operação reversível.
- `ETAPA_5_PACOTE_3B_VERTEX_EDITING.md` — movimento, inclusão e
  exclusão de vértices por transações reversíveis.
- `ETAPA_5_PACOTE_4A_OBJECT_DELETION.md` — exclusão simples e múltipla por comandos reversíveis.
- `ETAPA_5_PACOTE_4B_COLLISION_TRANSFORM.md` — movimento e escala por gestos transacionais.
- `ETAPA_5_PACOTE_4C_LAYER_GROUP_UI_FALLBACKS.md` — painéis de camadas e grupos bloqueiam alterações sem histórico e usam comandos reversíveis exatos.
- `ETAPA_5_PACOTE_5A_CREATION_COMMAND_PATHS.md` — identidade estável de criação e remoção dos fallbacks diretos das ferramentas ativas.
- `ETAPA_5_PACOTE_5B_BATCH_COLLISION_COMMANDS.md` — lotes de máscara e auto-detect atômicos, com auto-geração reversível de colisões.
- `ETAPA_5_PACOTE_5C_BEZIER_RESIDUAL_COMMANDS.md` — criação e edição Bézier reversíveis e cobertura nominal dos comandos residuais.
- `ETAPA_5_PACOTE_5C_VALIDACAO_PRE_MERGE.md` — commit funcional, validação visual, CI Linux/Windows, artefatos e gates independentes anteriores ao merge.
- `ETAPA_5_ENCERRAMENTO_POS_MERGE.md` — merge da PR `#27`, auditoria corretiva, PR `#28` integrada e CI pós-merge final aprovado.
- `AUDITORIA_RIGOROSA_2026-08-10.md` — bloqueios descobertos, reconciliação legada e novos gates de segurança, tipagem e branches.
- `ETAPA_6_EXPORTACAO_COLISOES.md` — snapshot pré-merge do schema versionado e unificado de colisões.
- `ETAPA_6_ENCERRAMENTO_POS_MERGE.md` — PR `#33`, merge, CI pós-merge, artefatos e encerramento formal de `R-005`/Etapa 6.
- `COBERTURA_MODULOS_CRITICOS_2026-08-10.md` — snapshot pré-merge dos testes comportamentais dos módulos abaixo de 30%; integrado posteriormente pela PR `#35`; `R-003` permanece aberto.
- `ETAPA_7_CLI_PRE_MERGE.md` — matriz local de argumentos, saídas, códigos de processo e subprocessos reais; `R-006` permanece aberto até merge e CI pós-merge.
- `ETAPA_7_ENCERRAMENTO_POS_MERGE.md` — PR `#36`, merge, CI pós-merge, artefatos e encerramento formal de `R-006`/Etapa 7.
- `ETAPA_8_BEZIER_GEOMETRIA_PRE_MERGE.md` — validação matemática local de Bézier, triangulação e degenerados; `R-007` permanece aberto até merge e CI pós-merge.
- `ETAPA_8_ENCERRAMENTO_POS_MERGE.md` — PR `#38`, merge, CI pós-merge, artefatos e encerramento formal de `R-007`/Etapa 8.
- `ETAPA_9_DRY_RUN_SEGURANCA_ROLLBACK_PRE_MERGE_2026-08-17.md` — gates pré-merge da Etapa 9 dos adaptadores nativos, com falhas intermediárias e limitações declaradas.
- `ETAPA_9_ENCERRAMENTO_POS_MERGE_2026-08-17.md` — PR `#81`, merge, CI pós-merge, testes reais locais de Godot/Unity e inventário dos artefatos.
- `ETAPA_9_COLISAO_ARQUITETURA_PRE_MERGE.md` — falhas reproduzidas, API estática única, compatibilidade e validação pré-merge.
- `ETAPA_9_ENCERRAMENTO_POS_MERGE.md` — PR `#40`, merge, CI pós-merge, artefatos e encerramento formal de `R-008`/Etapa 9.
- `ETAPA_11_COBERTURA_UI_PACOTE_1.md` — primeiro pacote local da Etapa 11; 742 testes, métricas exatas por módulo, zero módulos abaixo de 30% e `R-003` ainda aberto.
- `ETAPA_11_COBERTURA_UI_PACOTE_2.md` — segundo pacote pré-merge da Etapa 11; lasso magnético, máscara, pincel de colisão e edição poligonal, com métricas exatas de linhas e ramos e CI auditado; `R-003` permanece aberto.
- `ETAPA_11_COBERTURA_UI_PACOTE_3.md` — terceiro pacote pré-merge da Etapa 11; canvas e diálogo de exportação acima de 90% de linhas, métricas exatas e CI `31479113082` auditado; `R-003` permanece aberto.
- `ETAPA_11_COBERTURA_NUMERICA_PACOTE_4.md` — quarto pacote pré-merge da Etapa 11; detecção, processamento visual, ferramenta base e máscaras, com dois ramos mortos removidos e CI `31481664506` auditado; `R-003` permanece aberto.
- `ETAPA_11_COMANDOS_PAINEIS_PACOTE_5.md` — quinto pacote pré-merge da Etapa 11; contratos transacionais de comandos e painéis Qt entre 98% e 100% de linhas, com CI `31483687046` auditado; `R-003` permanece aberto.
- `ETAPA_11_METAS_FINAIS_PACOTE_6.md` — sexto pacote pré-merge da Etapa 11; metas globais 90%/85% atingidas, CI `31488173784` auditado e `R-003` preservado aberto até integração e CI pós-merge.
- `ETAPA_11_ENCERRAMENTO_POS_MERGE.md` — PR funcional `#45` integrada em `2a38b89e542390b3b4396a88d9a416f3695caadc`; fechamento `#46` integrado em `a22a90088220e586c3382c3ed5dc1075a3ff7e6b`; CI pós-merge final `31495971632` auditado; `R-003` encerrado e Etapa 11 concluída no escopo aprovado.
- `ETAPA_12_SEGURANCA_LIMITES_PRE_MERGE.md` — falhas reproduzidas, limites centrais, corpus malformado, benchmarks Windows, `928` testes e riscos residuais; commit técnico `da7611b543bb0ceb4eb8e67a7900aadcb8f04a5f` e CI pré-merge `31684136128` do HEAD fonte `a42b54b07d8e9e10feb8d283adc664b52f9d25d3` auditados; `R-012` aberto.
- `ETAPA_12_ENCERRAMENTO_POS_MERGE.md` — PR funcional `#49`, merge `872bf079d228d13d0203d22b844052b1f920e99b` e CI `31686321925` com `928` testes; fechamento `#50`, merge final `fc81c2ea10e751c15a39627d462ddfff390eeb04` e CI final `31688307089`; `R-012` encerrado e Etapa 12 concluída no escopo aprovado.
- `ETAPA_13_REFATORACAO_QT_AUTOSAVE_PRE_MERGE.md` — refatoração Qt, autosave protegido, CI `31693639653` rejeitado, correção portátil e CI corretivo `31695151223` aceito após auditoria.
- `ETAPA_13_ENCERRAMENTO_POS_MERGE.md` — PR funcional `#51`; fechamento `#52`, merge `b4d9390dbd1274c283a3e3985d6d79be47de45d6`, CI pós-merge final `31705652046`, artefatos auditados e encerramento de `R-011`/Etapa 13 sem aprovação de release.

## Estado operacional da evidência atual

Etapa 10 dos adaptadores nativos integrada pela PR #84 no merge `bca43f399928d69cb81e133e40991b7c011a0c10` em 17 de agosto de 2026:

- `ETAPA_10_ADAPTADORES_NATIVOS_ENCERRAMENTO_2026-08-17.md` registra o escopo, os gates e as limitações sem reescrever snapshots históricos;
- `artifacts/native-stage10-2026-08-17/` contém o relatório, índice SHA-256, fixtures, PNGs, manifests, logs reais de Godot/Unity, suíte completa e o resumo das falhas intermediárias;
- o harness real produziu `NATIVE_STAGE10=SUCCESS`, com Godot `4.7.stable`, Unity `6000.5.7f1`, determinismo e regressões das Etapas 4/6 aprovados;
- a suíte completa local registrou `1173 passed, 2 skipped, 10 warnings`; os skips são os testes de symlink condicionados à permissão do Windows e não foram alterados;
- hashes, integridade de evidências e privacidade passaram; a release continua explicitamente NÃO APROVADA;
- a CI atual não inicializa dinamicamente as engines; portanto a prova real de Godot/Unity é local, reproduzível e separada da cobertura dinâmica de CI;
- a etapa está integrada e auditada; CI pós-merge passou nos jobs Linux e Windows. Release permanece NÃO APROVADA.

Etapa 9 dos adaptadores nativos integrada no escopo técnico pós-merge em 17 de agosto de 2026:

- PR `#81`, merge `e1620571ab2f638ba671baa33ac508858e229313`; checks pré-merge `32011747754` e CI pós-merge `32012110722`, ambos com Linux e Windows em `success`;
- `1167` testes locais, `2` skips condicionados à permissão de symlink no Windows local, cobertura total de `90,72%`, política de cobertura aprovada, mypy sem erros e integridade de baseline/evidências aprovada;
- Godot `4.7.stable` e Unity `6000.5.7f1` executados localmente pelo harness real; dry-run, aplicação, repetição, drift de hash e rollback foram registrados nos artefatos versionados;
- o diretório `artifacts/native-stage9-2026-08-17/` contém `13` arquivos, sendo `12` payloads no índice e o próprio índice; a varredura de privacidade passou;
- a CI valida os gates Python, tipagem, cobertura e integridade, mas não inicializa dinamicamente Godot/Unity; por isso a execução real das engines permanece evidência local reproduzível, não cobertura dinâmica de CI;
- `pip-audit` continua limitado pelo pacote local não publicado e há dez ocorrências históricas B110 fora do escopo da Etapa 9; nenhuma foi promovida artificialmente a PASS;
- STAGE9_STATUS=INTEGRATED; STAGE9_RELEASE_APPROVED=NO; STAGE10_STATUS=NOT_STARTED.
- suplemento administrativo local: os dois testes de symlink passaram com 2 passed, 0 skipped; a proveniência da transcrição e o SHA-256 estão no fechamento e no artefato normalizado.
Etapa 14 encerrada no escopo técnico pós-merge em 15 de agosto de 2026:

- commit-fonte do build MSI `828cf626b7ce382c360723b1be10c4ce718c4187`; merge documental/técnico atual `f15193a55d1a5de0c7031f5bab656107302eee1b`;
- `982` testes por sistema, cobertura `92,80%` de linhas e `85,02%` de branches, política aprovada e legado `27/27` reconciliado;
- WiX 4.0.6 fixado, builds MSI reproduzíveis, instalação, desinstalação, upgrade e repair reais validados;
- Microsoft Defender sem ameaças detectadas e zero referências proibidas no bundle;
- PR `#58`, merge `f15193a55d1a5de0c7031f5bab656107302eee1b` e CI pós-merge `31905237922` foram auditados em logs e artefatos;
- cobertura idêntica em 80 módulos, árvore limpa e zero violações nos pacotes auditados;
- assinatura, jurídico e identidade visual permanecem abertos; a migração do builder MSI foi validada tecnicamente;
- `STAGE14_TECHNICAL_CANDIDATE=PASS`; `STAGE14_COMPLETED=YES`; `RELEASE_APPROVED=NO`.

O relatório permanente do fechamento é `ETAPA_14_ENCERRAMENTO_POS_MERGE.md`.

Etapa 13 integrada e concluída no escopo aprovado em 13 de agosto de 2026:

- PR `#51`, HEAD final `0b5d3c4e3831ad5efe52ae03a41107c6dafbf535` e merge `e7eb4a4c81fa2b46e8b9d5db40562e4ce7021108`;
- CI pós-merge `31698961646`: `953` testes em Linux/Windows, cobertura exata idêntica e zero módulos abaixo de 30%;
- pacote documental local de encerramento: `955` testes aprovados e baseline de `338` arquivos, sem alteração das métricas de código integradas;
- auditoria retrospectiva: scanner anterior não detectava separadores JSON duplicados; `60` payloads/`852` ocorrências locais foram removidos de quatro ZIPs autorizados; correção integrada pela PR `#52` no merge `b4d9390dbd1274c283a3e3985d6d79be47de45d6`;
- CI pós-merge final `31705652046`: `955` testes por sistema, legado `196` com reconciliação `27/27`, `57/57` documentos idênticos e `1.416` payloads sem violações;
- `R-011` encerrado e Etapa 13 concluída; naquele snapshot, Etapa 14 não iniciada; release não aprovada.

Etapa 12 integrada e concluída no escopo aprovado em 13 de agosto de 2026:

- PR funcional `#49` e fechamento `#50`, merge final `fc81c2ea10e751c15a39627d462ddfff390eeb04`;
- CI pós-merge final `31688307089` auditado em Linux/Windows com `929` testes;
- cobertura exata `11.174/12.040` linhas e `3.309/3.892` branches; `90,91%` combinada;
- mypy em `73` arquivos, pip-audit sem vulnerabilidades conhecidas, Bandit limpo e legado `27/27` conciliado;
- artefatos Linux `9176359924` e Windows `9176393106` com digests publicados e `1.420` payloads sem violações;
- baseline local do fechamento: `326` arquivos;
- `R-012` encerrado e Etapa 12 concluída no escopo aprovado; release não aprovada.

Etapa 11 integrada e concluída no escopo aprovado em 11 de agosto de 2026:

- PR `#45` integrada em `2a38b89e542390b3b4396a88d9a416f3695caadc`;
- `145` testes focais e `877` testes oficiais aprovados no Windows/Python 3.11.9;
- cobertura exata `10.787/11.628` linhas e `3.147/3.700` branches; `90,91%` combinada;
- zero módulos abaixo de 30% em linhas ou branches mensuráveis;
- CIs pós-merge funcional `31491221322` e final `31495971632` aceitos após auditoria; o último teve logs, hashes e 1.418 payloads conferidos; `R-003` encerrado e Etapa 11 concluída no escopo aprovado; Etapa 12 iniciada com `R-012` aberto e release não aprovada.

Snapshot do encerramento formal da Etapa 10 em 11 de agosto de 2026:

- PR `#42` integrada em `9b22bdc54b13992658172d4748bfab44f3127c8e`;
- validação local real em Godot `4.7` e Unity `6000.5.7f1`;
- CIs remotos `31450335289`, `31451363518` e `31452032479` rejeitados após inspeções progressivas dos artefatos;
- run `31457937902` aceito após validar schema v4, ancestralidade, `729` testes por sistema, cobertura exata, `44` arquivos publicados e varredura recursiva sem violações;
- CI pós-merge `31463873481` rejeitado após detectar `8.581/2.145` cobertos no Linux contra `8.582/2.146` no Windows;
- CI corretivo `31464786333` aceito; PR `#43` integrada em `f8caec3e7156d308f03046f81d2c89996f959466`; pós-merge `31469610508` aceito após auditoria de `51` arquivos e `1.410` payloads;
- Etapa 10: CONCLUÍDA; Etapa 11: NÃO INICIADA; release: NÃO APROVADA.

### Snapshot integrado anterior — Etapa 9

Encerramento formal da Etapa 9 em 10 de agosto de 2026:

- commit técnico `28273dfb7cb0e0aeab1f8f9f3a99c07df3b08a76`;
- validação local: 39 testes da etapa, 702 oficiais, 196 históricos e 27/27 divergências exatas;
- cobertura: 73.65% de linhas, 57.65% de branches e 69.79% combinada;
- PR `#40`, merge `76dd6b7ca3e7da08fab653d66ae29a33a839baf3`; CI pós-merge `31445518755` aprovado em Linux e Windows;
- `R-008`: ENCERRADO NO ESCOPO APROVADO;
- Etapa 9: CONCLUÍDA; Etapa 10: NÃO INICIADA; release: NÃO APROVADA.

Os arquivos `ETAPA_9_COLISAO_ARQUITETURA_PRE_MERGE.md` e `ETAPA_9_ENCERRAMENTO_POS_MERGE.md` preservam os gates local, remoto e pós-merge.

## Snapshot histórico anterior — encerramento da Etapa 8

Snapshot de encerramento formal da Etapa 8 em 10 de agosto de 2026:

- commits técnico/corretivo: `d11cd3dc0bd0063e325a53dd30fc439feda9dd24` e `23d467f37b39e97251e589b544b84f29bcb18fee`;
- PR `#38`, merge `fc869250e5067fb7b06b70c7d2dd3c0e1e1ee94e`;
- CI da PR `31440755594` e pós-merge `31441024001`: Linux e Windows em `success`, zero anotações;
- artefatos pós-merge: Linux `9082863959` e Windows `9082897744`, com digests no relatório de encerramento;
- validação local: 125 testes focais, 661 totais no pacote pré-merge, 662 no fechamento e 27/27 divergências legadas exatas;
- `R-007`: ENCERRADO NO ESCOPO APROVADO; Etapa 8: CONCLUÍDA;
- Etapa 9: não iniciada; release: NÃO APROVADA.

O arquivo `ETAPA_8_ENCERRAMENTO_POS_MERGE.md` é a evidência permanente deste gate.

## Snapshot histórico anterior — encerramento da Etapa 7

Snapshot de encerramento formal da Etapa 7 em 10 de agosto de 2026, condicionado à verificação do HEAD e do GitHub:

- commits técnico/documental: `a940ef13018aabc430126db3fd705b521fc1be06` e `51e55a37021c506471111ef1f4e7bc9abe67c65d`;
- PR `#36`, merge `99326f2d7ccf7046e401d90830feb8a5d33e9f9a`;
- CI da PR `31436763095` e CI pós-merge `31437000772`: Linux e Windows em `success`, zero anotações;
- artefatos pós-merge: Linux `9081388807` e Windows `9081419753`, com digests no relatório de encerramento;
- validação local: 47 testes focais, 620 no commit técnico, 621 no pacote pré-merge e 622 no fechamento, cobertura combinada 68.53% e launcher em 85%;
- `R-006`: ENCERRADO NO ESCOPO APROVADO;
- Etapa 7: CONCLUÍDA;
- naquele snapshot, Etapa 8: não iniciada; release: NÃO APROVADA.

O arquivo `ETAPA_7_ENCERRAMENTO_POS_MERGE.md` é a evidência permanente deste gate.

## Snapshot histórico anterior — encerramento da Etapa 6

Snapshot de encerramento formal da Etapa 6 em 10 de agosto de 2026, condicionado à verificação do HEAD e do GitHub:

- commits técnico/documental: `3c80bb7f0f72a26f5f4972c5aeb483b8d16e2e98` e `321ccf3a692c7c1916eeeb61e7a041ee8bcef035`;
- PR `#33`, merge `73a128ec44cde17867bbac6a7854ce86a43aba5a`;
- CI da PR `31431473940` e CI pós-merge `31431739320`: Linux e Windows em `success`, zero anotações;
- artefatos pós-merge: Linux `9079413130` e Windows `9079450269`, com digests no relatório de encerramento;
- validação local: 32 testes focais da implementação, 543 totais no fechamento, cobertura combinada 62.45% e mypy sem erros em 66 arquivos;
- `R-005`: ENCERRADO NO ESCOPO APROVADO;
- Etapa 6: CONCLUÍDA;
- Etapa 7: não iniciada; release: NÃO APROVADA.

O arquivo `ETAPA_6_ENCERRAMENTO_POS_MERGE.md` é a evidência permanente deste gate.

## Snapshot histórico anterior — encerramento da Etapa 5

Snapshot de fechamento formal de 10 de agosto de 2026, condicionado à verificação do HEAD e do GitHub:

- âncora técnica integrada e auditada: `574be9bd0268e70c384903f93f16cf6e73aa57a2`;
- PR `#27`: fechada e mesclada;
- HEAD funcional v4.1: `9bf83af0d58b5984ccfefc59a543428379b02632`;
- HEAD documental final da PR: `8ce44c238aaea79dafa64b8e1bba3ba5a8a7157e`;
- Pacote 5C: integrado;
- gate funcional Windows/Python 3.11.9: 95 focais, 16 documentais, 517 totais, 66% de cobertura e baseline 263;
- validação visual manual: aprovada; validação automática: 17/17 estados;
- CI final pré-merge `#83` (`31135700216`): Linux e Windows em `success`;
- CI pós-merge `#84` (`31136893143`): Linux e Windows em `success`;
- artefato Linux pós-merge: ID `8978309717`, digest `25ee252a77fb43796a6c5b1cbbf10c5987791187a6e860a11c17e9980d45b091`;
- artefato Windows pós-merge: ID `8978326062`, digest `0432e2e7ccc11d21d8769f160268f820ccf62af7edb5fd6f5a2070bcca4c912f`;
- branch funcional: preservada no remoto;
- auditoria corretiva: commit `236eefd41ee51c7085e21d52fc80074eede0a793`, HEAD final `ab71e148c0b7441bd36f489472856d0b4adfaa1e`;
- PR `#28`: mesclada em `56533b65f81d21fd9c762aa10c0d3e6747d742ca`;
- pacote técnico final: PR `#29`, HEAD `956db473a88641bfdcfbd49ed122479f3fa2c51d`, merge `574be9bd0268e70c384903f93f16cf6e73aa57a2`;
- CI pós-merge técnico `31425585259`: Linux e Windows em `success`, zero anotações;
- artefatos técnicos finais: Linux `9077091136` (`sha256:0ce0ad1f77b348f1d4061c7783a3467633a3089f19b18327627979f51befce51`) e Windows `9077113199` (`sha256:ab18e3e260f3f2b1e64b41e834363460f721112131411f350ac83e779fa9dae8`);
- `R-004`: ENCERRADO NO ESCOPO APROVADO;
- Etapa 5: CONCLUÍDA;
- gate atual: candidato técnico da Etapa 6 em validação; release permanece bloqueada;
- Etapa 6: aprovada localmente, ainda não integrada.

O arquivo `ETAPA_5_ENCERRAMENTO_POS_MERGE.md` é a evidência permanente
deste gate. Commit, push, PR, merge, CI da PR e CI pós-merge foram executados;
a integração da Etapa 6 e a aprovação de release permanecem decisões independentes.

## Histórico dos correctors do Pacote 5C

- corrector v1: bloqueado no dry-run pelo contrato de tipo de `SceneObject.beziers`, sem mutação;
- corrector v2: código e testes locais aprovados, mas procedimento bloqueado por duas linhas em branco excedentes no EOF, deixando oito arquivos modificados, sem commit e sem push;
- corrector v3: bloqueado no dry-run por trailing whitespace no payload documental, sem escrita no repositório;
- corrector v3.1: gate integral Windows aprovado para revisão de diff, com 19 arquivos locais, sem commit e sem push;
- revisão pós-v3.1: bloqueou o commit porque o `repository.diff` não continha o novo teste untracked e porque a Caneta não recarregava os nós do mesmo objeto após Undo/Redo global;
- corrector v3.2: bloqueado no dry-run pelo mypy ao acessar o objeto selecionado sem narrowing explícito; nenhum arquivo foi escrito;
- corrector v3.3: gate integral Windows aprovado com 50 testes focais, 9 documentais, 465 totais e 65% de cobertura; evidência autossuficiente dos 19 arquivos produzida, sem commit ou push;
- revisão pós-v3.3: bloqueou o commit porque o gesto ativo da Caneta não consumia primeiro Undo, Redo ou Escape, uma divergência externa podia conflitar com a soltura e o relatório permanente registrava 48/6/460 em vez dos resultados v3.3;
- corrector v3.4: gate integral Windows aprovado com 59 testes focais, 10 documentais, 475 totais e 65% de cobertura; evidência completa e métricas dinâmicas produzidas, sem commit ou push;
- revisão pós-v3.4: bloqueou o commit porque a criação atômica rejeitava curvas no sentido oposto e a edição de handle podia instalar polígono degenerado ou auto-intersectante;
- corrector v3.5: gate integral Windows aprovado com 67 testes focais, 11 documentais, 484 totais e 65% de cobertura; evidência completa dos 19 arquivos produzida, sem commit ou push;
- revisão pós-v3.5: bloqueou o commit porque o fallback determinístico usado sem Shapely aceitava certos contatos de extremidade e cruzamentos colineares entre arestas não adjacentes;
- corrector v3.6: gate integral Windows aprovado com 71 testes focais, 12 documentais, 489 totais e 65% de cobertura; evidência completa dos 19 arquivos produzida, sem commit ou push;
- revisão pós-v3.6: bloqueou o commit porque Shapely opcional ainda podia alterar a decisão de validade e coordenadas não representáveis podiam escapar como `OverflowError`;
- corrector v3.7: bloqueado no dry-run antes de escrever arquivos porque o teste de independência tentou substituir um símbolo `Polygon` intencionalmente ausente sem `raising=False`; o código funcional não foi aplicado ao worktree;
- corrector v3.8: gate integral Windows aprovado com 77 testes focais, 13 documentais, 496 totais e 66% de cobertura; evidência completa dos 19 arquivos produzida, sem commit ou push;
- revisão pós-v3.8: bloqueou o commit porque a conversão baixa de controles não representáveis ainda expunha `OverflowError` por `Scene.sample_beziers_to_polygon()` e pela exportação de sprite;
- corrector v3.9: gate integral Windows aprovado com 80 testes focais, 14 documentais, 500 totais e 66% de cobertura; evidência completa dos 20 arquivos produzida, sem commit ou push;
- revisão pós-v3.9: bloqueou o commit porque a avaliação cúbica ainda podia gerar infinito intermediário com controles finitos extremos e o reparo heurístico era acionado mesmo com `auto_repair` desativado;
- corrector v4.0: gate Windows aprovado com 89 testes focais, 15 documentais, 510 totais e 66% de cobertura; a revisão pós-gate bloqueou commit pelo contrato não estrito do índice de handle;
- corrector v4.1: exige `handle_index` inteiro não booleano no núcleo e em `HandleMoveCommand`, rejeita booleanos, floats e valores não hashable sem mutação ou histórico e mantém o escopo final em 20 arquivos;
- gate vigente naquele snapshot pré-commit: uma evidência v4.1 com `APPROVED_FOR_DIFF_REVIEW_ONLY` era pré-condição para iniciar a revisão do diff; commit, push e novo CI ainda eram gates separados.

O formato de projeto v1 já persiste segmentos Bézier. Qualquer documento ou metadado da PR que afirme ausência dessa persistência deve ser corrigido antes de Ready for review.
- `ETAPA_2_MODELO_CENARIO_PROFISSIONAL_2026-08-19.md` — contrato e modelo editável profissional; estado pré-merge da PR.
