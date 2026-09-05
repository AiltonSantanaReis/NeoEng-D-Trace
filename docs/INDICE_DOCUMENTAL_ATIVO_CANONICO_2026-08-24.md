# Índice Documental Ativo Canônico — NeoEng-D-Trace

**Versão:** 2.2
**Data:** 2026-08-29
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
| `evidence/STAGE5_SCOPE_AND_RECONCILIATION.md` | ATIVO / EVIDÊNCIA | prova da Etapa 5 | governança e etapa |
| `evidence/P2D05_SINCRONIZACAO_MAIN_2026-09-04.md` | ATIVO / EVIDÊNCIA DE SINCRONIZAÇÃO | registro v1, P2D-05, bases 35727d9/b9557e6; commit de inclusão é o merge que introduz este registro | política de qualidade, governança, contrato global P2D-05; informa README, plano mestre, matriz e acompanhamento vivo; não altera requisitos ou IDs |

Registro ativo adicional: [P2D05_LOTE_IDIOMA_STATUS_2026-09-04.md](P2D05_LOTE_IDIOMA_STATUS_2026-09-04.md),
ID P2D05-LANG-STATUS-20260904, versão 1, IN_PROGRESS; controle de mudança
aprovado para implementação sobre 4b873c3. Subordinado ao contrato global,
decisão P2D-05, política e governança; informa README, plano mestre, matriz,
acompanhamento e evidências. Não substitui snapshots ou requisitos.

Registro ativo adicional: LOTE_CANETA_ALCAS_QUANTIZACAO_2026-09-05.md,
ID PEN-HANDLES-20260905, versão 1, IN_PROGRESS / PRECOMMIT_PENDING; autorização
do proprietário para corrigir alças explícitas e quantização sem relaxar a
validação. Subordinado ao contrato global, decisão P2D-05, política e
governança; informa README, plano mestre, matriz, acompanhamento e evidências.
Não substitui snapshots, requisitos ou gates dos lotes anteriores.

Registro de evidência associado: evidence/PEN_HANDLES_QUANTIZACAO_PRECOMMIT_2026-09-05.md,
ID EVID-PEN-HANDLES-QUANTIZATION-20260905, estado IN_PROGRESS /
PRECOMMIT_PENDING; relatório dos testes do candidato não commitado, seus
limites e a decisão de não publicar antes do aceite do patch exato.

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

