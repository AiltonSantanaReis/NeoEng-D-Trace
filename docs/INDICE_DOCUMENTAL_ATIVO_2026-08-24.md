# Índice Documental Ativo — NeoEng-D-Trace

**Versão:** 1.0  
**Data:** 2026-08-24  
**Documento de controle:** `DOC-INDEX-ACTIVE-20260824`

Este índice define quais documentos estão ativos, quais são históricos e como eles se relacionam. Nenhum documento poderá ser usado como autoridade sem estar listado aqui.


## 1. Ordem de prevalência

1. Decisões formais de produto aprovadas.
2. [Índice Documental Ativo Canônico](INDICE_DOCUMENTAL_ATIVO_CANONICO_2026-08-24.md).
3. [Governança de Integridade, Execução e Antialucinação](GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md).
4. [Plano Normativo Completo do Produto Profissional](PLANO_PRODUTO_PROFISSIONAL_NORMATIVO_COMPLETO_2026-08-24.md).
5. [Adendo de Automação de Evidências e IDs](ADENDO_NORMATIVO_AUTOMACAO_E_IDS_2026-08-24.md).
6. ADRs técnicos ativos.
7. Especificações das etapas.
8. Registros de IDs ativos, com o registro canônico prevalente.
9. Evidências e relatórios de auditoria.
10. Documentos históricos.

Quando dois documentos ativos discordarem, a execução deverá ser bloqueada até que exista uma decisão formal de mudança. Não é permitido escolher informalmente o trecho mais conveniente.

## 2. Documentos ativos

| Documento | Status | Função | Depende de | Governa |
|---|---|---|---|---|
| LOTE_CANETA_ALCAS_QUANTIZACAO_2026-09-05.md | IN_PROGRESS / PRECOMMIT_PENDING | Alças explícitas, fechamento e proteção da validação Bézier | governança, política, decisão P2D-05 e plano mestre | Caneta, testes e evidências do lote |
| docs/evidence/PEN_HANDLES_QUANTIZACAO_PRECOMMIT_2026-09-05.md | IN_PROGRESS / PRECOMMIT_PENDING | Evidência do candidato não commitado, seus testes, limitações e decisão de não publicação | lote PEN-HANDLES-20260905 e governança | revisão PRECOMMIT e requalificação posterior |
| `INDICE_DOCUMENTAL_ATIVO_CANONICO_2026-08-24.md` | ATIVO / PREVALENTE | Índice consolidado e resolução formal de conflitos documentais | decisões aprovadas | cadeia documental |
| `GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md` | ATIVO / PREVALENTE | Integridade, anti-bypass, testes reais, avanço sequencial e baseline | decisões aprovadas | todos os documentos e etapas |
| `PLANO_PRODUTO_PROFISSIONAL_NORMATIVO_COMPLETO_2026-08-24.md` | ATIVO | Produto, arquitetura, renderer, 2.5D, 3D e encerramento | governança | execução do produto |
| `ADENDO_NORMATIVO_AUTOMACAO_E_IDS_2026-08-24.md` | ATIVO / ESPECIALIZADO | IDs e automação de evidências antes da Fase 4 | governança e plano | rastreabilidade e CI |
| `REGISTRO_IDS_PRODUTO_PROFISSIONAL_2026-08-24.yaml` | ATIVO / FONTE DE IDS | IDs canônicos e matriz inicial | adendo de IDs | código, testes, docs e artefatos |
| `REGISTRO_IDS_PRODUTO_PROFISSIONAL_CANONICO_2026-08-24.yaml` | ATIVO / FONTE CANÔNICA PREVALENTE | Declarações completas e rastreabilidade | adendo de IDs | IDs novos e validação |
| `ADR_RUNTIME_CENARIOS_EFEITOS_2026-08-20.md` | ATIVO / ADR | Limites técnicos de runtime e efeitos | governança | runtime e claims de capacidade |
| `PLANO_INTERFACE_MODERNA_PROFISSIONAL_2026-08-21.md` | ATIVO / SUPORTE | Requisitos e direção visual da interface | plano normativo | UI, inspector e shell |
| `evidence/STAGE5_SCOPE_AND_RECONCILIATION.md` | ATIVO / EVIDÊNCIA | Escopo e reconciliação da Etapa 5 | etapa e governança | prova da Etapa 5 |
| `docs/evidence/ETAPA_10_ACESSIBILIDADE_ANALISE_IMPACTO_2026-08-24.md` | ATIVO / EVIDÊNCIA | Análise de impacto e auditoria inicial da Etapa 10 | governança, plano de interface e registro de IDs | acessibilidade e usabilidade da Etapa 10 |

### 2.1 Evidência ativa da Etapa 10

| Documento | Status | Versão | Autoridade | Dependências | IDs | Commit de inclusão |
|---|---|---|---|---|---|---|
| `docs/evidence/ETAPA_10_ACESSIBILIDADE_ENCERRAMENTO_2026-08-24.md` | `PENDING_HUMAN_REVIEW` | `1.0` | Evidência técnica subordinada à governança ativa | Governança, índice, registro de IDs, adendo, plano de interface e análise de impacto da Etapa 10 | `REQ-F10-UI-ACCESSIBILITY`, `FEAT-UI-ACCESSIBILITY`, `EVID-F10-ACCESSIBILITY-AUDIT` | `6ba06acd75e401f03228f949c9bf4279830c63cb` |

## 3. Documentos históricos

Documentos históricos podem ser consultados para contexto e auditoria, mas não podem criar requisitos, alterar critérios ou autorizar avanço.

Todo documento histórico deverá ser identificado como `HISTORICAL` ou `SUPERSEDED` quando houver um substituto ativo.


## 4. Cadeia obrigatória de rastreabilidade

```text
Decisão aprovada
  └── Governança
       └── Plano normativo
            ├── Adendo normativo
            │    └── Registro de IDs
            ├── ADR técnico
            ├── Especificação da etapa
            ├── Testes
            └── Evidências / build / baseline
```

Uma evidência sem requisito não prova conclusão. Um requisito sem teste não pode ser encerrado. Um teste sem artefato não comprova comportamento visual. Um documento sem vínculo não possui autoridade de execução.

## 5. Atualização do índice

Qualquer novo plano, adendo, ADR, especificação de etapa, baseline ou relatório oficial deverá ser adicionado a este índice antes de ser usado.

A atualização deverá informar:

- nome e caminho;
- status;
- versão;
- autoridade;
- dependências;
- documentos afetados;
- IDs afetados;
- commit de inclusão.

Se o status não estiver definido, o documento será considerado `DRAFT` e não poderá governar implementação ou aprovação.

