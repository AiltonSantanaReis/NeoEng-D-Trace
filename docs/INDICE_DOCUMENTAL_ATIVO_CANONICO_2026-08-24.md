# Índice Documental Ativo Canônico — NeoEng-D-Trace

**Versão:** 2.0  
**Data:** 2026-08-24  
**ID:** DOC-INDEX-ACTIVE-CANONICAL-20260824  
**Status:** ativo e prevalente

Este é o índice documental vigente. O índice anterior `INDICE_DOCUMENTAL_ATIVO_2026-08-24.md` fica marcado como `SUPERSEDED` por não apontar para o registro canônico completo de IDs.

## 1. Prevalência

1. decisões formais aprovadas;
2. [Governança de Integridade, Execução e Antialucinação](GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md);
3. [Plano Normativo Completo do Produto Profissional](PLANO_PRODUTO_PROFISSIONAL_NORMATIVO_COMPLETO_2026-08-24.md);
4. [Adendo Normativo de Automação e IDs](ADENDO_NORMATIVO_AUTOMACAO_E_IDS_2026-08-24.md);
5. ADRs técnicos ativos;
6. especificação da etapa atual;
7. [Registro Canônico de IDs](REGISTRO_IDS_PRODUTO_PROFISSIONAL_CANONICO_2026-08-24.yaml);
8. testes, builds, baselines e evidências;
9. documentos históricos.

Conflito documental bloqueia execução. Nenhuma equipe poderá escolher informalmente o trecho mais conveniente.

## 2. Documentos normativos ativos

| Documento | Estado | Autoridade | Dependências |
|---|---|---|---|
| `GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md` | ATIVO / PREVALENTE | integridade, testes reais, no-bypass, sequência e baseline | decisões aprovadas |
| `PLANO_PRODUTO_PROFISSIONAL_NORMATIVO_COMPLETO_2026-08-24.md` | ATIVO | arquitetura, renderer, 2.5D, 3D e encerramento | governança |
| `ADENDO_NORMATIVO_AUTOMACAO_E_IDS_2026-08-24.md` | ATIVO / ESPECIALIZADO | IDs e evidências antes da Fase 4 | governança e plano |
| `REGISTRO_IDS_PRODUTO_PROFISSIONAL_CANONICO_2026-08-24.yaml` | ATIVO / FONTE CANÔNICA | declarações de IDs e rastreabilidade | adendo |
| `ADR_RUNTIME_CENARIOS_EFEITOS_2026-08-20.md` | ATIVO / ADR | limites técnicos de runtime e efeitos | governança |
| `PLANO_INTERFACE_MODERNA_PROFISSIONAL_2026-08-21.md` | ATIVO / SUPORTE | requisitos visuais e UX | plano normativo |
| `evidence/STAGE5_SCOPE_AND_RECONCILIATION.md` | ATIVO / EVIDÊNCIA | prova da Etapa 5 | governança e etapa |

## 3. Documentos superseded

| Documento | Estado | Substituto | Motivo |
|---|---|---|---|
| `INDICE_DOCUMENTAL_ATIVO_2026-08-24.md` | SUPERSEDED | este índice | não apontava para o registro canônico completo |
| `REGISTRO_IDS_PRODUTO_PROFISSIONAL_2026-08-24.yaml` | SUPERSEDED | registro canônico v2 | possuía referências sem declaração própria |
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

