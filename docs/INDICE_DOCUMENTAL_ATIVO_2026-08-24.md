# Índice Documental Ativo — NeoEng-D-Trace

**Versão:** 1.0  
**Data:** 2026-08-24  
**Documento de controle:** `DOC-INDEX-ACTIVE-20260824`

Este índice define quais documentos estão ativos, quais são históricos e como eles se relacionam. Nenhum documento poderá ser usado como autoridade sem estar listado aqui.

## 1. Ordem de prevalência

1. Decisões formais de produto aprovadas.
2. [Governança de Integridade, Execução e Antialucinação](C:/Users/atnco/Pictures/NeoEng-D-Trace/docs/GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md).
3. [Plano Normativo Completo do Produto Profissional](C:/Users/atnco/Pictures/NeoEng-D-Trace/docs/PLANO_PRODUTO_PROFISSIONAL_NORMATIVO_COMPLETO_2026-08-24.md).
4. [Adendo de Automação de Evidências e IDs](C:/Users/atnco/Pictures/NeoEng-D-Trace/docs/ADENDO_NORMATIVO_AUTOMACAO_E_IDS_2026-08-24.md).
5. ADRs técnicos ativos.
6. Especificações das etapas.
7. Registro canônico de IDs.
8. Evidências e relatórios de auditoria.
9. Documentos históricos.

Quando dois documentos ativos discordarem, a execução deverá ser bloqueada até que exista uma decisão formal de mudança. Não é permitido escolher informalmente o trecho mais conveniente.

## 2. Documentos ativos

| Documento | Status | Função | Depende de | Governa |
|---|---|---|---|---|
| `GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md` | ATIVO / PREVALENTE | Integridade, anti-bypass, testes reais, avanço sequencial e baseline | decisões aprovadas | todos os documentos e etapas |
| `PLANO_PRODUTO_PROFISSIONAL_NORMATIVO_COMPLETO_2026-08-24.md` | ATIVO | Produto, arquitetura, renderer, 2.5D, 3D e encerramento | governança | execução do produto |
| `ADENDO_NORMATIVO_AUTOMACAO_E_IDS_2026-08-24.md` | ATIVO / ESPECIALIZADO | IDs e automação de evidências antes da Fase 4 | governança e plano | rastreabilidade e CI |
| `REGISTRO_IDS_PRODUTO_PROFISSIONAL_2026-08-24.yaml` | ATIVO / FONTE DE IDS | IDs canônicos e matriz inicial | adendo de IDs | código, testes, docs e artefatos |
| `ADR_RUNTIME_CENARIOS_EFEITOS_2026-08-20.md` | ATIVO / ADR | Limites técnicos de runtime e efeitos | governança | runtime e claims de capacidade |
| `PLANO_INTERFACE_MODERNA_PROFISSIONAL_2026-08-21.md` | ATIVO / SUPORTE | Requisitos e direção visual da interface | plano normativo | UI, inspector e shell |
| `evidence/STAGE5_SCOPE_AND_RECONCILIATION.md` | ATIVO / EVIDÊNCIA | Escopo e reconciliação da Etapa 5 | etapa e governança | prova da Etapa 5 |

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
