# Índice Documental Ativo Canônico — NeoEng-D-Trace

**Versão:** 2.3
**Data:** 2026-09-05
**ID:** DOC-INDEX-ACTIVE-CANONICAL-20260829
**Status:** ativo e prevalente

Este é o índice documental consolidado e prevalente. O índice `INDICE_DOCUMENTAL_ATIVO_2026-08-24.md` permanece **ATIVO** e integra o conjunto documental vigente. Em caso de divergência, este índice canônico prevalece e a execução deve ser bloqueada até a resolução formal do conflito.


## 1. Prevalência

1. decisões formais aprovadas;
2. [Governança de Integridade, Execução e Antialucinação](GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md);
3. [Plano Normativo Completo do Produto Profissional](PLANO_PRODUTO_PROFISSIONAL_NORMATIVO_COMPLETO_2026-08-24.md);
4. [Normativo do Editor de Composição 2D](NEOENG_EDITOR_COMPOSICAO_2D_NORMATIVO_2026-08-27.md);
5. [Adendo Normativo de Automação e IDs](ADENDO_NORMATIVO_AUTOMACAO_E_IDS_2026-08-24.md);
6. ADRs técnicos ativos;
7. especificação da etapa atual;
8. [Registro Canônico de IDs](REGISTRO_IDS_PRODUTO_PROFISSIONAL_CANONICO_2026-08-24.yaml);
9. testes, builds, baselines e evidências;
10. documentos históricos.

Conflito documental bloqueia execução. Nenhuma equipe poderá escolher informalmente o trecho mais conveniente.

## 2. Documentos normativos ativos

| Documento | Estado | Autoridade | Dependências |
|---|---|---|---|
| `GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md` | ATIVO / PREVALENTE | integridade, testes reais, no-bypass, sequência e baseline | decisões aprovadas |
| `PLANO_PRODUTO_PROFISSIONAL_NORMATIVO_COMPLETO_2026-08-24.md` | ATIVO | arquitetura, renderer, 2.5D, 3D e encerramento | governança |
| `REQUISITOS_EDITOR_CENARIOS_COMPLETO_2026-08-30.md` | ATIVO / PREVALENTE PARA ESCOPO FINAL | requisitos obrigatórios do editor de cenários completo, sem entrega parcial | governança, C3 e decisões aprovadas |
| `NEOENG_EDITOR_COMPOSICAO_2D_NORMATIVO_2026-08-27.md` | ATIVO / BASE DA FUNDAÇÃO P2D-COMP-01 | contrato, requisitos, ordem, gates e aceite da fundação de composição 2D | requisitos de escopo final, governança, C3 e decisões aprovadas |
| `EVIDENCIA_P2D_00_RECONCILIACAO_2026-08-29.md` | ATIVO / EVIDÊNCIA ACEITA | reconciliação do checkout, P2D-00 e abertura das linhas futuras | normativo do editor e baseline local |
| `DECISAO_P2D_01_ASSETS_ORIGINAIS_E_IMPORTACAO_2026-08-29.md` | ATIVO / DECISÃO APROVADA | política de assets originais, cópia controlada e provenance | normativo do editor e P2D-00 |
| DECISAO_P2D_01B_BIBLIOTECA_LIFECYCLE_2026-08-29.md | ATIVO / DECISÃO APROVADA | biblioteca, inspeção, relink, replace e missing assets | decisão P2D-01A e plano de evolução |
| EVIDENCIA_P2D_01B_BIBLIOTECA_LIFECYCLE_2026-08-29.md | ATIVO / EVIDÊNCIA ACEITA | implementação, lifecycle, captura, auditoria e aceite humano de P2D-01B | decisão P2D-01B e plano de evolução |
| `DECISAO_P2D_02A_ORDEM_CAMADAS_LOCKING_2026-08-29.md` | ATIVO / DECISÃO ACEITA | ordem visual, camadas, visibility e locking seguro do P2D-02A | normativo do editor e plano de evolução |
| `EVIDENCIA_P2D_02A_ORDEM_CAMADAS_LOCKING_2026-08-29.md` | ATIVO / EVIDÊNCIA ACEITA | fluxo Qt/Windows, reorder, visibility, lock, save/load e gates P2D-02A | decisão P2D-02A e plano de evolução |
| `DECISAO_P2D_02B_GRUPOS_HIERARQUIA_ISOLAMENTO_2026-08-29.md` | ATIVO / DECISÃO APROVADA | contrato, invariantes e aceite de grupos, hierarquia/membership e isolamento | normativo do editor e plano de evolução |
| `EVIDENCIA_P2D_02B_GRUPOS_HIERARQUIA_ISOLAMENTO_2026-08-29.md` | ATIVO / EVIDÊNCIA ACEITA | gates, fluxo Qt Windows/offscreen, persistência, herança, isolamento e revisão visual do P2D-02B | decisão P2D-02B e plano de evolução |
| `DECISAO_P2D_02_FECHAMENTO_2026-08-29.md` | ATIVO / DECISÃO DE FECHAMENTO | consolidação formal da macroetapa P2D-02 | decisões e evidências P2D-02A/P2D-02B |
| `EVIDENCIA_P2D_02_CONSOLIDACAO_2026-08-29.md` | ATIVO / EVIDÊNCIA ACEITA | aceite consolidado de ordem, camadas, grupos e isolamento | decisão de fechamento P2D-02 |
| `DECISAO_P2D_03_NAVEGACAO_SELECAO_PRODUTIVIDADE_2026-08-29.md` | ATIVO / DECISÃO ABERTA | contrato, invariantes, limites, testes e aceite de navegação, seleção e produtividade | normativo do editor, P2D-02 e auditoria P2D-03 |
| `EVIDENCIA_P2D_03_AUDITORIA_BASELINE_2026-08-29.md` | ATIVO / AUDITORIA BASELINE | inventário factual do editor profissional antes de P2D-03 | decisão P2D-03 e baseline `3c09f37` |
| `EVIDENCIA_P2D_03A_SELECAO_FOCO_2026-08-29.md` | ATIVO / EVIDÊNCIA ACEITA | implementação, testes, auditoria Qt/Windows e aceite de seleção/foco/marquee do P2D-03A | decisão P2D-03 e plano de evolução |
| `DECISAO_P2D_03B_OPERACOES_EDICAO_UNDO_CLIPBOARD_2026-08-29.md` | ATIVO / DECISÃO FECHADA | contrato, invariantes, limites e aceite de nudge, duplicate, delete, copy/paste e undo/redo | decisão P2D-03 e auditoria P2D-03B |
| `EVIDENCIA_P2D_03B_AUDITORIA_BASELINE_2026-08-29.md` | ATIVO / AUDITORIA BASELINE | auditoria factual da sessão, modelo, schema, viewport, inspector e atalhos antes do código P2D-03B | decisão P2D-03B e baseline `24a3178` |
| `EVIDENCIA_P2D_03B_IMPLEMENTACAO_2026-08-29.md` | ATIVO / EVIDÊNCIA ACEITA — P2D-03B CLOSED | implementação, requalificação pós-commit, build, gates, review package, aceite humano e seal do P2D-03B | decisão P2D-03B e plano de evolução |
| `DECISAO_P2D_03C_NAVEGACAO_CAMERA_ESTADOS_2026-08-30.md` | ATIVO / DECISÃO FECHADA — P2D-03C ACCEPTED / CLOSED | contrato aceito de navegação transitória, zoom, pan, fit e estados visuais | decisão P2D-03 e auditoria P2D-03C |
| `EVIDENCIA_P2D_03C_AUDITORIA_BASELINE_2026-08-30.md` | ATIVO / AUDITORIA BASELINE | constatações factuais e gaps do viewport profissional no checkpoint `78f7735` | decisão P2D-03C e checkpoint local |
| `EVIDENCIA_P2D_03C_IMPLEMENTACAO_PRECOMMIT_2026-08-30.md` | ATIVO / EVIDÊNCIA DE PRÉ-COMMIT | implementação autorizada, testes, gates, captura nativa e auditoria visual antes do commit | decisão P2D-03C e evidência baseline |
| `EVIDENCIA_P2D_03C_FECHAMENTO_2026-08-30.md` | ATIVO / EVIDÊNCIA ACEITA — P2D-03C CLOSED | requalificação pós-commit, build, captura, comparação, revisão humana e seal P2D-03C | decisão P2D-03C e evidência pré-commit |
| `EVIDENCIA_P2D_01A_ASSETS_IMPORTACAO_E_RENDERIZACAO_2026-08-29.md` | ATIVO / EVIDÊNCIA ACEITA | implementação e testes de P2D-01A | decisão P2D-01A e plano de evolução |
| `PLANO_EVOLUCAO_EDITOR_2D_2_5D_3D_E_LINHAS_INDEPENDENTES_2026-08-29.md` | ATIVO / PLANO DE EXTENSÕES | caminho 2D, extensão 2.5D/3D e separação dos workstreams futuros | normativo do editor e P2D-00 |
| `ADENDO_NORMATIVO_AUTOMACAO_E_IDS_2026-08-24.md` | ATIVO / ESPECIALIZADO | IDs e evidências antes da Fase 4 | governança e plano |
| `INDICE_DOCUMENTAL_ATIVO_2026-08-24.md` | ATIVO | índice normativo de referência mantido para continuidade documental | este índice prevalece em conflito |
| `REGISTRO_IDS_PRODUTO_PROFISSIONAL_2026-08-24.yaml` | ATIVO | registro de IDs já adotado, mantido para continuidade e auditoria | registro canônico prevalece para novos IDs |
| `REGISTRO_IDS_PRODUTO_PROFISSIONAL_CANONICO_2026-08-24.yaml` | ATIVO / FONTE CANÔNICA | declarações de IDs e rastreabilidade | adendo |
| `ADR_RUNTIME_CENARIOS_EFEITOS_2026-08-20.md` | ATIVO / ADR | limites técnicos de runtime e efeitos | governança |
| `PLANO_INTERFACE_MODERNA_PROFISSIONAL_2026-08-21.md` | ATIVO / SUPORTE | requisitos visuais e UX | plano normativo |
| `EVIDENCIA_AUDITORIA_PUBLICACAO_PRIVACIDADE_2026-08-30.md` | ATIVO / EVIDÊNCIA DE PUBLICAÇÃO | auditoria repository-wide, revisão dos commits locais e saneamento da linha publicada | governança e requisitos de escopo final |
| `evidence/DECISAO_CONTINUIDADE_POS_E13_2026-09-10.md` | ATIVO / DECISÃO APROVADA | continuidade pós-E13, lote ativo, escopo autorizado e decisões reservadas | governança, plano mestre e base pós-E13 |
| `evidence/DECISAO_REVISAO_HUMANA_FINAL_POS_E13_20260911.md` | ATIVO / DECISÃO APROVADA | revisão humana final deferida até os itens funcionais abertos passarem | governança, decisão de continuidade pós-E13 e evidência nativa profissional |
| `evidence/CHG_POS_E13_MATERIAL_DEFAULT_EDIT_20260910.md` | ATIVO / REGISTRO DE MUDANÇA EM IMPLEMENTAÇÃO | correção controlada dos defaults editáveis do Material V2 | decisão de continuidade pós-E13, governança e E08-C.4 |
| `evidence/CHG_POS_E13_PTBR_STATUS_20260910.md` | ATIVO / REGISTRO DE MUDANÇA EM IMPLEMENTAÇÃO | estados PT-BR do recarregamento e do Inspector | decisão de continuidade pós-E13, governança e P13-B |
| `evidence/CHG_POS_E13_TILEMAP_VECTOR_FLOW_20260910.md` | ATIVO / REGISTRO DE MUDANÇA EM IMPLEMENTAÇÃO | localização do Tilemap e seleção vetorial no fluxo nativo | decisão de continuidade pós-E13, governança, REQ-F03, REQ-F04, REQ-F10 e REQ-F02 |
| `evidence/CHG_POS_E13_AUDIO_NATIVE_FLOW_20260910.md` | ATIVO / REGISTRO DE MUDANÇA EM IMPLEMENTAÇÃO | prova nativa de escolha de áudio e criação de clip na timeline | decisão de continuidade pós-E13, governança, REQ-F09, REQ-F10 e REQ-F02 |
| `evidence/CHG_POS_E13_MASK_NATIVE_CAPTURE_20260910.md` | ATIVO / REGISTRO DE MUDANÇA EM IMPLEMENTAÇÃO | identificação fail-closed da janela nativa do Visualizador de Máscara | decisão de continuidade pós-E13, governança, REQ-F10 e REQ-F02 |
| `evidence/CHG_POS_E13_PROFESSIONAL_AUTHORING_UX_20260911.md` | ATIVO / REGISTRO DE MUDANÇA EM IMPLEMENTAÇÃO | câmera, guias de parallax, scrub contínuo, localização PT-BR e gizmo do editor profissional | decisão de continuidade pós-E13, governança, SCN-001, SCN-003, FX-001, FX-006, UX-001, UX-002, UX-003 e REQ-F09 |
| `evidence/CHG_POST_E13_DIRECIONAL_ORIENTAVEL_20260911.md` | ATIVO / REGISTRO DE MUDANÇA — CHECKPOINT TÉCNICO PASS | luz direcional, sockets orientáveis, gizmo, persistência e adapters sem quebrar defaults legados | decisão de revisão humana pós-E13, governança e FX-001/FX-005/FX-006 |
| `evidence/EVD_POST_E13_DIRECIONAL_ORIENTAVEL_NATIVE_20260911.md` | ATIVO / EVIDÊNCIA DE CHECKPOINT TÉCNICO | suíte 2186/2/1, build hashada, fluxo nativo real de luz/VFX, drag, salvar/recarregar e limites | CHG_POST_E13_DIRECIONAL_ORIENTAVEL_20260911.md, build `59a21a0` e decisão de revisão humana |
| `evidence/CHG_POST_E13_PARTICULAS_AUTORIA_RUNTIME_20260911.md` | ATIVO / REGISTRO DE MUDANÇA — CHECKPOINT TÉCNICO PASS | autoria de emissores, preview determinístico, persistência, correção do fluxo VFX e limites de runtime externo | decisão de revisão humana pós-E13, governança, REQ-F08, REQ-F09 e FX-002/FX-005/FX-006 |
| `evidence/EVD_POST_E13_PARTICULAS_AUTORIA_RUNTIME_NATIVE_20260911.md` | ATIVO / EVIDÊNCIA DE CHECKPOINT TÉCNICO | suíte 2193/2/1, build hashada, cliques nativos, partículas visíveis após 750 ms, salvar/recarregar e limitações | CHG_POST_E13_PARTICULAS_AUTORIA_RUNTIME_20260911.md, build `5fe5d77` e decisão de revisão humana |
| `evidence/CHG_POST_E13_PARTICLE_RUNTIME_NATIVE_20260911.md` | ATIVO / REGISTRO DE MUDANÇA — CHECKPOINT TÉCNICO PASS | consumo nativo do sidecar de partículas em Godot e Unity, guards de integridade e avanço determinístico | decisão de continuidade pós-E13, governança, REQ-F08, REQ-F09 e FX-002/FX-005/FX-006 |
| `evidence/EVD_POST_E13_PARTICLE_RUNTIME_NATIVE_20260911.md` | ATIVO / EVIDÊNCIA DE CHECKPOINT TÉCNICO | relatório v8, Godot com captura rasterizada, Unity nographics, equivalência de contagem e falhas controladas | CHG_POST_E13_PARTICLE_RUNTIME_NATIVE_20260911.md, commit `77b55df` e decisão de revisão humana |
| `evidence/CHG_POST_E13_PARTICLE_SCENE_EXPORT_NATIVE_20260911.md` | ATIVO / REGISTRO DE MUDANÇA — CHECKPOINT TÉCNICO PASS | ponte SceneAuthoringDocumentV2 para exportação Godot/Unity e materialização nativa de partículas | decisão de continuidade pós-E13, governança, REQ-F08, REQ-F09 e FX-002/FX-005/FX-006 |
| `evidence/EVD_POST_E13_PARTICLE_SCENE_EXPORT_NATIVE_20260911.md` | ATIVO / EVIDÊNCIA DE CHECKPOINT TÉCNICO | auditoria nativa v15, 17/17 checks, build, binário, fluxo Win32 real, captura e finding de workspace vazio | CHG_POST_E13_PARTICLE_SCENE_EXPORT_NATIVE_20260911.md, commit `73b7fcc` e decisão de revisão humana |
| `evidence/CHG_POST_E13_TILEMAP_PRO_AUTHORING_RUNTIME_20260912.md` | ATIVO / REGISTRO DE MUDANÇA — CHECKPOINT TÉCNICO PASS; REVISÃO HUMANA PENDENTE | autoria profissional de Tilemap/Tileset, payload seguro, materialização em runtime externo e composição hash-bound | decisão pós-E13, governança e decisão de revisão humana |
| `evidence/CHG_POST_E13_TILEMAP_TILESET_AUTHORING_20260911.md` | ATIVO / REGISTRO DE MUDANÇA — CHECKPOINT TÉCNICO PASS | atlas, miniaturas, paleta, camadas, três grades, PT-BR e persistência do subconjunto implementado | decisão pós-E13, governança, TMAP-001/002/003/005 e REQ-F03/REQ-F04/REQ-F10/REQ-F02 |
| `evidence/EVD_POST_E13_TILEMAP_TILESET_NATIVE_20260911.md` | ATIVO / EVIDÊNCIA DE CHECKPOINT TÉCNICO | suíte 2196/2/1, build hashada, cliques e arrastes reais, camadas, reabertura, hashes e limitações | CHG_POST_E13_TILEMAP_TILESET_AUTHORING_20260911.md, build `c1ea7bc` e decisão de revisão humana |
| `evidence/CHG_POST_E13_TILEMAP_ADVANCED_TOOLS_20260911.md` | ATIVO / REGISTRO DE MUDANÇA — CHECKPOINT TÉCNICO PASS | Retângulo, Balde, Conta-gotas, histórico atômico por gesto e layout responsivo sem remover o fluxo anterior | governança, decisão pós-E13, TMAP-003/005 e REQ-F02/REQ-F03/REQ-F04/REQ-F10 |
| `evidence/EVD_POST_E13_TILEMAP_ADVANCED_NATIVE_20260911.md` | ATIVO / EVIDÊNCIA DE CHECKPOINT TÉCNICO | suíte 2213/2/1, build `0689e72`, 26 ações nativas, 56 capturas, undo/redo real, persistência e limites | CHG_POST_E13_TILEMAP_ADVANCED_TOOLS_20260911.md, build responsiva e decisão de revisão humana |
| `evidence/EVD_POST_E13_TILEMAP_PRO_RESPONSIVE_NATIVE_20260911.md` | ATIVO / EVIDÊNCIA DE CHECKPOINT — PENDING_EVIDENCE | suíte 2216/2/1, build `b9341c9`, 41 ações/85 capturas nativas, seleção/cópia/colagem/variação/Rule Tiles, Tileset real e persistência; runtime externo pendente | CHG_POST_E13_TILEMAP_PRO_AUTHORING_RUNTIME_20260912.md, governança, decisão de continuidade e decisão de revisão humana |
| `evidence/EVD_POST_E13_TILEMAP_RUNTIME_ENGINES_20260912.md` | ATIVO / EVIDÊNCIA DE CHECKPOINT — PASS TÉCNICO | payload versionado, Godot/Unity reais, 27/27 células, drift de atlas rejeitado, build `c39a867`, integração hash-bound no exportador geral em `a7e22b3e` e fluxo Win32 do binário novo; build final da composição e lote pós-E13 continuam abertos | CHG_POST_E13_TILEMAP_PRO_AUTHORING_RUNTIME_20260912.md, governança, decisão de continuidade e decisão de revisão humana |
| `evidence/CHG_POST_E13_HYBRID_3D_AUTHORING_20260911.md` | ATIVO / REGISTRO DE MUDANÇA — RUNTIME EXTERNO PASS; LOTE GERAL PENDENTE | viewport híbrido 2D/2.5D/3D, cena vazia, câmera, meshes, luzes, gizmo, sidecar não destrutivo e adapters nativos Godot/Unity | decisão pós-E13, governança, REQ-F03/REQ-F04/REQ-F10/REQ-F02 e escopo 3D |
| `evidence/EVD_POST_E13_HYBRID_3D_NATIVE_20260911.md` | ATIVO / EVIDÊNCIA DE CHECKPOINT TÉCNICO | suíte 2201/2/1, build hashada, cliques/arrastes/orbita reais, modos 2.5D/3D, projeção, salvar/reabrir e limitações | CHG_POST_E13_HYBRID_3D_AUTHORING_20260911.md, build `b2d2df4` e decisão de revisão humana |
| `evidence/EVD_POST_E13_HYBRID_3D_RUNTIME_ENGINES_20260912.md` | ATIVO / EVIDÊNCIA DE GATE TÉCNICO PASS | adapters nativos Godot/Unity, capturas reais 640×360, animação observada, rejeição de drift por hash e findings preservados | CHG_POST_E13_HYBRID_3D_AUTHORING_20260911.md, commit `2226598`, decisão de revisão humana |
| `evidence/EVD_POST_E13_FINAL_BUILD_COMPOSITION_NATIVE_20260912.md` | ATIVO / EVIDÊNCIA DE CHECKPOINT TÉCNICO PASS — REVISÃO HUMANA PENDENTE | build v4 hashada, smoke 11/11, fluxo Win32 nativo, erro/recuperação, persistência e composição Tilemap/runtime revalidada | governança, decisões pós-E13, CHG de Tilemap e CHG híbrido; commit `dd344f4` |
| `evidence/AUDITORIA_FLUXO_USUARIO_POS_E13_FINAL_20260910.md` | ATIVO / AUDITORIA TÉCNICA ATUALIZADA — REVISÃO HUMANA PENDENTE | matriz nativa final10 preservada, adendo v4 de build/composição, capturas, persistência, limitações e decisões finais pós-E13 | governança, decisões pós-E13, registros CHG-P13 e evidência final v4 |
| `evidence/AUDITORIA_REFERENCIAS_UI_UX_INSPETOR_POS_E13_20260912.md` | ATIVO / AUDITORIA EM ANDAMENTO | análise do texto e das oito referências visuais, confronto com o editor canônico, achados, riscos e critérios de aceite | governança, auditoria de triagem pós-E13, decisão de continuidade pós-E13 e checkpoint pré-gizmo |
| `evidence/CHG_POST_E13_DOC_HYGIENE_20260912.md` | ATIVO / REGISTRO DE MUDANÇA EM IMPLEMENTAÇÃO | correção textual mínima da referência proibida encontrada pela suíte oficial, sem alterar código ou escopo | governança, auditoria de referências UI/UX e decisão de continuidade pós-E13 |
| `evidence/CHG_POST_E13_MATERIAL_BINARY_AUDIT_20260912.md` | ATIVO / EVIDÊNCIA DE CHECKPOINT TÉCNICO PASS — REFINAMENTO UX ABERTO | seleção, edição, aplicação e persistência de material no binário pós-E13 com captura Win32 real | governança, build final pós-E13, material V2 e auditoria UI/UX |
| `evidence/CHG_POST_E13_VECTOR_CONTOUR_BINARY_AUDIT_20260912.md` | ATIVO / EVIDÊNCIA DE CHECKPOINT TÉCNICO PASS — REFINAMENTO UX ABERTO | detecção, edição, criação e persistência de contorno vetorial no binário pós-E13 | governança, build final pós-E13, E09 vector scene e auditoria UI/UX |
| `evidence/CHG_POST_E13_MASK_VIEWER_BINARY_AUDIT_20260912.md` | ATIVO / EVIDÊNCIA DE CHECKPOINT TÉCNICO PASS | abertura, carregamento, erro controlado e modos visuais do Visualizador de Máscara no binário pós-E13 | governança, build final pós-E13, E09/E10 e auditoria UI/UX |
| `evidence/AUDITORIA_POST_E13_LOCALIZACAO_CONTEXTO_20260912.md` | ATIVO / AUDITORIA EM ANDAMENTO | menus, contexto do viewport, tooltip, round-trip PT-BR e correção controlada de status vetorial; build nova ainda pendente | governança, auditoria de referências UI/UX, checkpoint pré-gizmo e evidências nativas pós-E13 |
| `evidence/CHG_POST_E13_VECTOR_CONTOUR_BINARY_LOCALIZATION_FIX_20260912.md` | ATIVO / EVIDÊNCIA DE CHECKPOINT TÉCNICO PASS — ESCOPO RESTRITO | build nova e fluxo Win32 real comprovam status PT-BR de detecção, edição, criação e round-trip vetorial | governança, build `eea7b6c`, correção `c0989cd`, auditoria de localização/contexto e E09 vector scene |
| `evidence/STAGE5_SCOPE_AND_RECONCILIATION.md` | ATIVO / EVIDÊNCIA | prova da Etapa 5 | governança e etapa |
| `evidence/P2D05_SINCRONIZACAO_MAIN_2026-09-04.md` | ATIVO / EVIDÊNCIA DE SINCRONIZAÇÃO | registro v1, P2D-05, bases 35727d9/b9557e6; commit de inclusão é o merge que introduz este registro | política de qualidade, governança, contrato global P2D-05; informa README, plano mestre, matriz e acompanhamento vivo; não altera requisitos ou IDs |

Registro ativo adicional: [P2D05_LOTE_IDIOMA_STATUS_2026-09-04.md](P2D05_LOTE_IDIOMA_STATUS_2026-09-04.md),
ID P2D05-LANG-STATUS-20260904, versão 1, IN_PROGRESS; controle de mudança
aprovado para implementação sobre 4b873c3. Subordinado ao contrato global,
decisão P2D-05, política e governança; informa README, plano mestre, matriz,
acompanhamento e evidências. Não substitui snapshots ou requisitos.

Registro ativo adicional: LOTE_CANETA_ALCAS_QUANTIZACAO_2026-09-05.md,
ID PEN-HANDLES-20260905, versão 1, IN_PROGRESS / BLOCKED; commit qualificado
`fd4a67e0d2bf60f07b710c002c0be88eeee94424`; CI remoto `33990872253` passou em
Linux e Windows, sem auditoria nativa de cliques concluída. A autorização do
proprietário para corrigir alças explícitas e quantização não relaxa a
validação. Subordinado ao contrato global, decisão P2D-05, política e
governança; informa README, plano mestre, matriz, acompanhamento e evidências.
Não substitui snapshots, requisitos ou gates dos lotes anteriores.

Registro de evidência associado: evidence/PEN_HANDLES_QUANTIZACAO_PRECOMMIT_2026-09-05.md,
ID EVID-PEN-HANDLES-QUANTIZATION-20260905, estado ATIVO / SNAPSHOT PRÉ-COMMIT;
relatório histórico dos testes do candidato antes do commit, seus limites e a
decisão então vigente de não publicar.

Registro de evidência associado: evidence/PEN_HANDLES_QUANTIZACAO_POSTCOMMIT_2026-09-05.md,
ID EVID-PEN-HANDLES-QUANTIZATION-POSTCOMMIT-20260905, estado IN_PROGRESS /
BLOCKED; qualificação local do commit `1068166f3c046e008928d98e68fdb187838c87bc`,
recibos, hashes, falhas ambientais reproduzidas e limitações remotas/nativas.

Registro de evidência associado: evidence/PEN_HANDLES_MODAL_ISOLATION_CI_2026-09-05.md,
ID EVID-PEN-HANDLES-MODAL-ISOLATION-20260905, versão 1, IN_PROGRESS / BLOCKED;
qualificação do commit `fd4a67e0d2bf60f07b710c002c0be88eeee94424`, CI remoto verde,
recibos locais hashados e auditoria nativa de cliques ainda pendente. Subordinado
à governança, política de qualidade, lote PEN-HANDLES-20260905 e P2D-05; informa
README, plano mestre, acompanhamento vivo e índice de evidências. Documento novo
registrado nesta revisão; o commit de inclusão é o commit documental que o
incorporar.
| `evidence/PROPOSTA_PACOTES_ASSETS_PROPRIOS_20260910.md` | ATIVO / ESPECIFICAÇÃO EM IMPLEMENTAÇÃO | direção, limites e sequência dos pacotes de assets pós-E13 | governança, base pós-E13 e decisão P2D-01 |
| `evidence/PACK_01_03_PILOTO_FLORESTA_20260910.md` | ATIVO / EVIDÊNCIA PENDENTE | rastreabilidade do primeiro incremento do piloto Floresta e catálogo | proposta de pacotes e decisão P2D-01 |

## 3. Documentos superseded

| Documento | Estado | Substituto | Motivo |
|---|---|---|---|
| `PLANO_PRODUTO_PROFISSIONAL_NORMATIVO_2026-08-24.md` | DRAFT / SUPERSEDED | plano normativo completo | rascunho incompleto |

Documentos superseded permanecem preservados para auditoria e não podem governar implementação ou aprovação.

## 4. Cadeia obrigatória

```text
Decisão aprovada
  -> Governança
      -> Plano Normativo
          -> Adendo aplicável
              -> Registro canônico de IDs
                  -> Requisito
                      -> Feature/Componente
                          -> Teste
                              -> Evidência/Build/Baseline
```

Nenhum item da cadeia poderá ser omitido para declarar `PASS`.

## 5. Inclusão de novos documentos

Documento novo será `DRAFT` até ser registrado aqui com caminho, versão, autoridade, dependências, documentos afetados, IDs afetados e commit de inclusão.

Documento sem entrada neste índice não possui autoridade normativa.

O documento `REQUISITOS_EDITOR_CENARIOS_COMPLETO_2026-08-30.md` governa o escopo final do produto. Nenhum documento de fundação, etapa aceita ou plano de extensão pode reduzir seus requisitos sem uma decisão formal de mudança.

