# NeoEng-D-Trace — Evidência P2D-00

## Reconciliação documental, baseline local e abertura de linhas futuras

**Data:** 2026-08-29 (horário local, UTC-03)
**Etapa:** P2D-00 — Adoção, reconciliação e baseline local
**Decisão:** ACCEPTED
**Escopo da etapa:** governança e documentação; nenhum código de produto foi alterado nesta etapa.

## 1. Objetivo e autoridade

Esta evidência registra a conferência do repositório antes do início da consolidação do editor profissional de composição 2D baseado em objetos. Ela não substitui o documento normativo. O documento normativo continua sendo a autoridade operacional da linha P2D-COMP-01.

A ordem de autoridade permanece:

1. decisão explícita do proprietário do produto;
2. documento normativo vigente;
3. contratos e pacote C3 imutáveis;
4. código e testes reproduzíveis;
5. evidências de captura e auditoria;
6. documentação histórica.

Nenhuma funcionalidade foi marcada como existente somente porque está planejada.

## 2. Prova compacta do estado local

| Verificação | Resultado comprovado |
|---|---|
| Diretório | <workspace-root> (caminho local omitido pelo gate de higiene) |
| Branch | modernization/multiaxis-ui |
| HEAD | 4824e7bf7b4a82dbf664485aed6b509c96d59851 |
| Último commit | feat(mask-viewer): add isolated polygon editing tools |
| Tracked tree | limpo; git status --short --untracked-files=no retornou 0 caminhos |
| git diff --check | exit code 0 |
| Python de qualificação | .venv\Scripts\python.exe, Python 3.11.9 |
| Qualificação anterior registrada | suíte completa: 1762 passed / 2 skipped / 0 failed |
| Qualificação focal anterior | cenário/exportação: 154 passed |

O volume de untracked legítimo não foi inspecionado como alteração de produto, não foi removido e não foi normalizado.

## 3. Divergência documental corrigida

O documento normativo emitido em 2026-08-27 ainda identificava 7df73f2 como HEAD e informava 1758 passed / 2 skipped. Esses valores eram históricos e não correspondiam ao checkout atual. A norma foi atualizada para refletir exclusivamente o estado comprovado acima.

Também foram atualizadas as referências de continuidade para reconhecer o commit atual e o registro desta reconciliação. Nenhum commit histórico, pacote C3, tolerância, baseline ou auditor foi reescrito.

## 4. Resultado da reconciliação P2D-COMP-01

P2D-COMP-01 permanece OPEN. A aceitação de P2D-00 não é aceitação do produto final.

Os bloqueadores já comprovados permanecem visíveis:

- viewport ainda precisa renderizar os assets reais, e não somente polígonos abstratos;
- ciclo de vida de assets, biblioteca, relink/replace e missing diagnostics ainda é parcial;
- ordem visual efetiva, camadas e hierarquia profissional ainda precisam de consolidação;
- produtividade de teclado/mouse, comandos e fit selection ainda precisa de prova completa;
- persistência, recovery, preview, exportação e orientação GLB para Godot exigem requalificação dedicada;
- gates, captura Windows, auditoria visual, build e revisão humana só ocorrerão após os lotes de implementação.

Não existe autorização para contornar esses bloqueadores com mudança de texto, tolerância ou classificação cosmética.

## 5. Decisão de arquitetura para 2D, 2.5D e 3D

O produto será evoluído em camadas, preservando o núcleo de composição e evitando que uma futura capacidade 2.5D ou 3D seja simulada por campos ambíguos no contrato 2D.

### 5.1 Núcleo compartilhado permitido

O núcleo comum deve preservar, com identificadores estáveis e contratos versionados:

- identidade de documento, asset e objeto;
- referência de asset com hash e diagnóstico de disponibilidade;
- transformações, pivô, seleção, visibilidade, lock e undo/redo;
- camadas, grupos e relações explícitas;
- câmera, coordenadas e adapters de exportação com capacidades declaradas;
- persistência determinística, recovery e evidências reproduzíveis.

### 5.2 Limites atuais

- P2D-COMP-01 continua sendo um produto 2D baseado em objetos.
- O z existente em estruturas de transformação não é, por si só, prova de profundidade visual, ordenação 2.5D ou cena 3D.
- O exportador GLTF/GLB atual não transforma o NeoEng-D-Trace em editor 3D e possui contrato limitado; a orientação para Godot é uma pendência específica de exportação, não deve ser corrigida silenciosamente dentro de um lote não relacionado.
- 2.5D exigirá contrato próprio para profundidade, câmera, ordenação, conversão de coordenadas e validação em engine.
- 3D exigirá contrato próprio para cena, malha, materiais, câmera, iluminação, importação/exportação e viewport; não será tratado como extensão implícita do editor 2D.

### 5.3 Regra de compatibilidade

Qualquer evolução 2.5D/3D deverá adicionar schema versionado, adapter explícito, fixtures assimétricos, testes negativos, evidência de round-trip e validação real no destino. Nenhuma etapa futura pode rebaixar os contratos V1/V2 existentes ou alterar a semântica 2D sem decisão formal de baseline.

## 6. Ordem aprovada de execução

As etapas são sequenciais. Uma linha posterior não pode mascarar uma lacuna da linha anterior.

| Ordem | Linha | Estado após P2D-00 | Critério de avanço |
|---|---|---|---|
| 1 | P2D-01 — assets e renderização real | READY | contrato de assets aprovado; implementação e testes iniciados |
| 2 | P2D-02 — ordem, camadas e hierarquia | BLOCKED BY P2D-01 | P2D-01 ACCEPTED |
| 3 | P2D-03 — navegação e produtividade | BLOCKED BY P2D-02 | P2D-02 ACCEPTED |
| 4 | P2D-04 — persistência, recovery, preview e exportação | BLOCKED BY P2D-03 | P2D-03 ACCEPTED |
| 5 | P2D-05/P2D-06 — qualidade, performance, gates, build e revisão humana | BLOCKED BY P2D-04 | P2D-04 ACCEPTED |
| 6 | P2D-07 — fechamento formal | BLOCKED BY P2D-05/P2D-06 | todos os gates e aceite humano presentes |

P2D-01 é a próxima linha de implementação. Antes de alterar código, deve ser fechado o contrato de política para asset externo: copiar para o projeto, manter referência externa com relink explícito, ou rejeitar. Essa escolha altera persistência, portabilidade e exportação e, portanto, não será presumida.

## 7. Linhas independentes posteriores

As linhas abaixo foram abertas documentalmente como workstreams independentes. Elas não foram implementadas, não estão liberadas para desenvolvimento paralelo neste checkpoint e não são branches Git criadas por este registro.

Cada linha deverá possuir contrato, schema, adapters, testes, evidências, baseline, plano de rollback, revisão humana e aceite próprios. O núcleo compartilhado só pode ser alterado por contrato versionado e com análise de impacto G/V/B/H/X.

| ID | Linha | Entrega futura | Dependência mínima |
|---|---|---|---|
| EXT-TMAP-01 | Tilemap | tilesets, mapas por células, pincel, balde, borracha, seleção, múltiplas camadas, snapping, autotiling/rule tiles e exportação declarada | P2D-COMP-01 ACCEPTED; contrato de grid aprovado |
| EXT-COLL-01 | Colisão de cenário | camadas de colisão próprias, shapes editáveis, triggers, validação geométrica e exportação por engine | P2D-COMP-01 ACCEPTED; contrato de colisão aprovado |
| EXT-NAV-01 | NavMesh | regiões navegáveis, obstáculos, conexões, validação e exportação/integração de navegação | EXT-COLL-01 ACCEPTED ou contrato explícito de dependência |
| EXT-ENT-01 | Entidades/componentes/prefabs | entidades, componentes, instâncias, overrides, referências e ciclo de vida | P2D-COMP-01 ACCEPTED; modelo de composição versionado |
| EXT-FX-01 | Iluminação e VFX | luzes reais, sombras, efeitos, preview determinístico e integração de runtime | sockets V2 podem ser migrados, mas não são aceitação; contrato de runtime aprovado |

As cinco linhas não devem ser implementadas como “pequenos acréscimos” no editor 2D sem contrato. Isso criaria acoplamento, dificultaria rollback e faria parecer que marcadores de dados são recursos funcionais.

## 8. Gate de P2D-00

| Gate | Resultado |
|---|---|
| HEAD/branch/tracked boundary conferidos antes da mutação | PASS |
| Divergências documentais identificadas e classificadas | PASS |
| C3 e demais imutáveis preservados | PASS |
| Estado atual separado de intenção futura | PASS |
| P2D-COMP-01 mantido como OPEN | PASS |
| Ordem P2D-01 a P2D-07 registrada | PASS |
| Cinco linhas futuras registradas como independentes e não implementadas | PASS |
| Push/tag/merge/limpeza de untracked | não executados |

## 9. Próximo checkpoint obrigatório

O próximo passo é P2D-01. O responsável deve reler o documento normativo vigente, confirmar o checkpoint novamente e apresentar/registrar a decisão de política de asset externo antes da implementação. Nenhum requisito de tilemap, colisão de cenário, NavMesh, entidades/componentes/prefabs ou iluminação/VFX deve ser misturado a P2D-01.

**Decisão de fechamento:** P2D-00 ACCEPTED; P2D-COMP-01 OPEN; EXT-TMAP-01, EXT-COLL-01, EXT-NAV-01, EXT-ENT-01 e EXT-FX-01 PLANNED/BLOCKED BY P2D-COMP-01.
