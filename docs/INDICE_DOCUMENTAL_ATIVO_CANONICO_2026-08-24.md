# Índice Documental Ativo Canônico — NeoEng-D-Trace

**Versão:** 2.1
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
| `NEOENG_EDITOR_COMPOSICAO_2D_NORMATIVO_2026-08-27.md` | ATIVO / PREVALENTE PARA P2D-COMP-01 | contrato, requisitos, ordem, gates e aceite do editor de composição 2D | governança, C3 e decisões aprovadas |
| `EVIDENCIA_P2D_00_RECONCILIACAO_2026-08-29.md` | ATIVO / EVIDÊNCIA ACEITA | reconciliação do checkout, P2D-00 e abertura das linhas futuras | normativo do editor e baseline local |
| `DECISAO_P2D_01_ASSETS_ORIGINAIS_E_IMPORTACAO_2026-08-29.md` | ATIVO / DECISÃO APROVADA | política de assets originais, cópia controlada e provenance | normativo do editor e P2D-00 |
| `EVIDENCIA_P2D_01A_ASSETS_IMPORTACAO_E_RENDERIZACAO_2026-08-29.md` | ATIVO / EVIDÊNCIA ACEITA | implementação e testes de P2D-01A | decisão P2D-01A e plano de evolução |
| `PLANO_EVOLUCAO_EDITOR_2D_2_5D_3D_E_LINHAS_INDEPENDENTES_2026-08-29.md` | ATIVO / PLANO DE EXTENSÕES | caminho 2D, extensão 2.5D/3D e separação dos workstreams futuros | normativo do editor e P2D-00 |
| `ADENDO_NORMATIVO_AUTOMACAO_E_IDS_2026-08-24.md` | ATIVO / ESPECIALIZADO | IDs e evidências antes da Fase 4 | governança e plano |
| `INDICE_DOCUMENTAL_ATIVO_2026-08-24.md` | ATIVO | índice normativo de referência mantido para continuidade documental | este índice prevalece em conflito |
| `REGISTRO_IDS_PRODUTO_PROFISSIONAL_2026-08-24.yaml` | ATIVO | registro de IDs já adotado, mantido para continuidade e auditoria | registro canônico prevalece para novos IDs |
| `REGISTRO_IDS_PRODUTO_PROFISSIONAL_CANONICO_2026-08-24.yaml` | ATIVO / FONTE CANÔNICA | declarações de IDs e rastreabilidade | adendo |
| `ADR_RUNTIME_CENARIOS_EFEITOS_2026-08-20.md` | ATIVO / ADR | limites técnicos de runtime e efeitos | governança |
| `PLANO_INTERFACE_MODERNA_PROFISSIONAL_2026-08-21.md` | ATIVO / SUPORTE | requisitos visuais e UX | plano normativo |
| `evidence/STAGE5_SCOPE_AND_RECONCILIATION.md` | ATIVO / EVIDÊNCIA | prova da Etapa 5 | governança e etapa |

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

