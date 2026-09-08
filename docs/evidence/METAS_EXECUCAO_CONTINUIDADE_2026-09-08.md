# Metas de execução até o encerramento do Plano Mestre

**Meta ativa:** concluir integralmente o Plano Mestre do NeoEng-D-Trace.  
**Regra de parada:** não encerrar uma rodada por uma pendência intermediária;
parar somente após a conclusão de todas as metas abaixo ou quando uma decisão
do proprietário for indispensável.

## Controle central de status

| ID | Meta | Status atual | Critério de conclusão |
|---|---|---|---|
| M00 | Governança e continuidade | CONCLUÍDA PARA O CHECKPOINT TÉCNICO | Registro único atualizado, worktree E01 identificado, proveniência conferida e nenhuma decisão material implícita |
| M01 | Checkpoint técnico de E00 | CONCLUÍDO — auditoria final pendente | Base restaurável, rastreabilidade/decisões E00 reconciliadas, suite/estática/build/runtime/capturas documentados; symlink e revisão humana ficam para auditoria final |
| M02 | Corrigir findings reproduzíveis | CONTÍNUA — E03 r13 selado no checkpoint técnico | Cada finding recebe causa, correção, teste focado, suíte proporcional, build oficial, captura real e commit rastreável |
| M03 | Validar experiência visual e usabilidade | CHECKPOINT TÉCNICO PASS — revisão final pendente | Fluxos reais do binário testados; layout, tradução, scroll, abas, toolbar, acessibilidade e erros sem finding aberto |
| M04 | Symlinks | ADIADA CONTROLADAMENTE | Executar somente na auditoria final do plano; 31 casos, relatório completo e skips locais mantidos separados |
| M05 | Revisão humana final | ADIADA CONTROLADAMENTE | Proprietário revisar o SHA/build final, roteiro, capturas e findings; todas as observações resolvidas ou formalmente aceitas |
| M06 | Fechar E00 | PENDENTE — auditoria final | Symlink, revisão humana, findings finais e demais critérios de fechamento; não é pré-requisito para o checkpoint técnico |
| M07 | E01 — contratos e cena vazia independente | CHECKPOINT TÉCNICO PASS — aceite final pendente | Sublotes E01-A/B/C têm implementação, testes, build r5 e evidências; aceite formal continua pendente até auditoria final |
| M08 | E02–E13 | E08 em execução — E08-A selado tecnicamente e E08-B ativo | Executar em lotes pequenos, na ordem do Plano Mestre, sem pular dependências |
| M09 | Auditoria final do plano | PENDENTE | Suítes, estática, segurança, portabilidade, engines aplicáveis, capturas e documentação finais aprovadas |
| M10 | Encerramento/publicação | PENDENTE | Auditoria humana concluída, critérios finais satisfeitos e autorização explícita para qualquer push, merge, tag ou release |

## Regras operacionais

1. Usar somente o worktree, commit e binário declarados no registro de
   continuidade.
2. Ler governança, Plano Mestre e decisões vigentes antes de cada lote.
3. Não iniciar E02 enquanto E01 não estiver formalmente aceita; E01 só foi aberta após checkpoint técnico autorizado de E00.
4. Aplicar correções autorizadas somente quando reproduzíveis e dentro do
   escopo da etapa; reconstruir build e evidências após correção.
5. Nunca converter `SKIP`, ausência de relatório ou captura automatizada em
   `PASS`.
6. Preservar evidências históricas e artefatos não relacionados; não limpar
   worktrees nem reescrever snapshots.
7. Atualizar este checklist, o registro JSON e a evidência do lote a cada
   transição de status.

## Estado no momento da criação

- E00: `TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING`.
- Correção da toolbar: validada no binário oficial `5a6275f8`.
- Symlinks: `PENDING_EVIDENCE / DEFERRED_UNTIL_FINAL_AUDIT`.
- Revisão humana: `PENDING_EVIDENCE`, deferida até a auditoria final por
  autorização do proprietário.
- E01: checkpoint técnico concluído; aceite final pendente.
- E02: checkpoint técnico aprovado, com aceite final pendente.
- E03: `TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING`, build r13 e captura real registrados; branch `Ailton/e03-assets-20260908`.
- E04: checkpoint técnico concluído; aceite final permanece pendente até a auditoria final; branch `Ailton/e04-tilemaps-20260908`, build r14 e captura real registrados.
- E05: `TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING`; branch `Ailton/e05-colliders-20260908`, build r15 e captura real registrados.
- E06: `TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING`; branch `Ailton/e06-navmesh-20260908`, build r22 e captura real final registrados.
- E07: `TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING`; branch `Ailton/e07-entities-20260908`, build r24 e captura real final registrados; E08 pode ser aberto após atualização do registro central.
- E08: `IN_PROGRESS`; E08-A checkpoint técnico selado em build r28; E08-B checkpoint técnico selado em build r35; E08-C ativo para materiais, normal maps, luzes e sombras; E09–E13 ainda não iniciadas.

## Metas executáveis do lote E01

| Sub-lote | Estado | Evidência principal | Próxima verificação |
|---|---|---|---|
| E01-A contrato e fluxo | `TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING` | `docs/evidence/E01_A_CENA_INDEPENDENTE_EVIDENCIA_2026-09-08.md` | preservar contrato e revalidar no pacote final |
| E01-B bancada de backend | `PASS_LOCAL` | `docs/evidence/E01_B_BACKEND_BANCADA_EVIDENCIA_2026-09-08.md` | repetir somente se houver mudança de renderer/backend |
| E01-C implementação independente | `TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING` | `docs/evidence/E01_C_FLUXO_INDEPENDENTE_EVIDENCIA_2026-09-08.md` | manter E01 aberto até auditoria final |
| E02-A contrato/modelo | `TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING` | `docs/evidence/E02_A_CONTRATO_PRIMITIVAS_EVIDENCIA_2026-09-08.md` | preservar evidência; aceite final permanece na auditoria do plano |
| E02-B operações de autoria | `TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING` | `docs/evidence/E02_B_OPERACOES_AUTORIA_EVIDENCIA_2026-09-08.md` | edição/seleção/transformação e save/reopen observável |
| E02-C edição de pontos e gestos | `TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING` | `docs/evidence/E02_C_EDICAO_PONTOS_GESTOS_EVIDENCIA_2026-09-08.md` | edição livre, estados de gesto, negativos, captura real e save/reopen |
| E03-A pacote/proveniência | `TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING` | `docs/evidence/E03_ASSET_LIBRARY_EVIDENCIA_2026-09-08.md` | categorias, estados, hashes, licença/proveniência |
| E03-B biblioteca/UX | `TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING` | `docs/evidence/E03_ASSET_LIBRARY_EVIDENCIA_2026-09-08.md` | pesquisa, miniaturas, filtros, drag/drop e tradução |
| E03-C lifecycle/negativos | `TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING` | `docs/evidence/E03_ASSET_LIBRARY_EVIDENCIA_2026-09-08.md` | import, relink, replace, Undo/Redo, missing/tamper/invalid |
| E04-A TileSet/células/camadas | `TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING` | `docs/evidence/E04_TILEMAP_GRID_EVIDENCIA_2026-09-08.md` | contrato, limites, chunks e benchmark |
| E04-B ferramentas transacionais | `TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING` | `docs/evidence/E04_TILEMAP_GRID_EVIDENCIA_2026-09-08.md` | paleta, pincel, balde limitado, borracha, retângulo e clipboard |
| E04-C três grids | `TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING` | `docs/evidence/E04_TILEMAP_GRID_EVIDENCIA_2026-09-08.md` | ortogonal, isométrico, hexagonal, picking e vizinhança |
| E04-D Rule Tiles | `TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING` | `docs/evidence/E04_TILEMAP_GRID_EVIDENCIA_2026-09-08.md` | regras determinísticas, fallback e invalidação incremental |
| E04-E persistência/destino | `TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING` | `docs/evidence/E04_TILEMAP_GRID_EVIDENCIA_2026-09-08.md` | save/reopen, validação, desempenho e import/export representativo |
| E05-A modelo/validação | `TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING` | `docs/evidence/E05_COLLIDERS_EVIDENCIA_2026-09-08.md` | coleção física versionada e negativos canônicos |
| E05-B comandos transacionais | `TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING` | `docs/evidence/E05_COLLIDERS_EVIDENCIA_2026-09-08.md` | criar, editar, mover, duplicar, remover e Undo/Redo |
| E05-C formas e triggers | `TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING` | `docs/evidence/E05_COLLIDERS_EVIDENCIA_2026-09-08.md` | caixa, círculo, polígono, cadeia, categorias/máscaras |
| E05-D persistência/destino | `TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING` | `docs/evidence/E05_COLLIDERS_EVIDENCIA_2026-09-08.md` | save/reopen e consumidor mínimo real |
| E05-E UI/capturas | `TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING` | `docs/evidence/E05_COLLIDERS_EVIDENCIA_2026-09-08.md` | overlay, fluxo visual, negativos e build |
| E06-A fonte/bake | `TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING` | `docs/evidence/E06_NAVMESH_EVIDENCIA_2026-09-08.md` | regiões, obstáculos, margem, hash e bake determinístico |
| E06-B caminho/negativos | `TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING` | `docs/evidence/E06_NAVMESH_EVIDENCIA_2026-09-08.md` | origem/destino, conectividade, corredor estreito e bake obsoleto |
| E06-C persistência | `TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING` | `docs/evidence/E06_NAVMESH_EVIDENCIA_2026-09-08.md` | save/reopen versionado e fonte preservada |
| E06-D UI/consumo | `TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING` | `docs/evidence/E06_NAVMESH_EVIDENCIA_2026-09-08.md` | painel, bake, caminho e estado obsoleto observáveis |
| E06-E build/capturas | `TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING` | `docs/evidence/E06_R22_CAPTURAS_MANIFESTO.json` | binário r22, smoke, captura real e manifesto |
| E07-A/B/C | `TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING` | `docs/evidence/E07_ENTIDADES_PREFABS_EVIDENCIA_2026-09-08.md` e `docs/evidence/E07_R24_CAPTURAS_MANIFESTO.json` | entidades/componentes, hierarquia, ciclo de prefab, build r24, smoke e captura real |
| E08-A | `TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING` | `docs/evidence/E08_RENDERER_FX_EVIDENCIA_2026-09-08.md` e `docs/evidence/E08_A_R28_CAPTURAS_MANIFESTO.json` | plano 2.5D, ordenação, fallback raster, cache, build r28, smoke e captura real |
| E08-B.1 contrato/schema | `TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING` | `docs/evidence/E08_RENDERER_FX_EVIDENCIA_2026-09-08.md` | scroll X/Y, offset, repeat/mirror, defaults e limites |
| E08-B.2 runtime/preview | `TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING` | `docs/evidence/E08_RENDERER_FX_EVIDENCIA_2026-09-08.md` | projeção, round-trip, variantes determinísticas, sem dupla aplicação |
| E08-B.3 UI transacional | `TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING` | `docs/evidence/E08_RENDERER_FX_EVIDENCIA_2026-09-08.md` | inspetor, Undo/Redo, fluxo do usuário e tradução |
| E08-B.4 build/capturas | `TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING` | `docs/evidence/E08_B_R35_CAPTURAS_MANIFESTO.json` | build limpa, smoke, captura real e manifesto hashado |

## Fila operacional única — não parar antes do fechamento

Esta é a fila de execução central. Cada linha só muda para `PASS` depois de
teste proporcional, regressão, artefato, hash, documentação e commit. A única
decisão ainda reservada ao proprietário é a revisão humana da auditoria final;
ela não interrompe a execução técnica autorizada.

| Ordem | Meta | Status | Saída obrigatória |
|---:|---|---|---|
| 1 | E08-B câmera/paralaxe | `TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING` | contrato, testes, build e captura real |
| 2 | E08-C materiais/normal maps/luzes/sombras | `IN_PROGRESS` | pixels observáveis, negativos e fallback |
| 3 | E08-D partículas/shaders/pós | `PLANNED` | seed/lifecycle, erro recuperável e cadeia |
| 4 | E08-E determinismo/destinos | `PLANNED` | timestep, tolerâncias e matriz de capacidades |
| 5 | E09 autoria/exportação vetorial | `PLANNED` | fluxo editável, persistente e exportável |
| 6 | E10 integração com engines | `PLANNED` | importação/execução real por destino aplicável |
| 7 | E11 composição/runtime | `PLANNED` | cena executada fora do editor |
| 8 | E12 recursos avançados/híbrido 3D | `PLANNED` | contrato, implementação e destinos |
| 9 | E13 fechamento/portabilidade | `PLANNED` | instaladores, documentação e baseline final |
| 10 | Auditoria final | `PLANNED` | symlinks, revisão humana, findings e decisão formal |

### Sublotes ativos de E08-C

| Sublote | Status | Critério de saída |
|---|---|---|
| E08-C.1 passe raster determinístico | `TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING` | ambiente, luz, material, normal perturbada, emissão e oclusão alteram pixels no binário |
| E08-C.2 integração V2 e autoria | `IN_PROGRESS` | fixture V2 real, estado persistido, controles autorais e fallback explícito |
| E08-C.3 build/captura/requalificação | `PENDING_EVIDENCE` | build após C.2, captura V2, negativos e manifesto hashado |

Regra de parada: continuar automaticamente entre essas metas; parar somente
quando todas estiverem concluídas ou quando uma decisão do proprietário for
indispensável. O gate de symlinks permanece exclusivamente na linha 10.

## Ordem fixa de execução

1. Confirmar branch, SHA, registry e worktree antes de cada lote.
2. Implementar somente o lote ativo ou um artefato explicitamente marcado como `PREPARATORY_ONLY`.
3. Executar testes focados, suíte oficial, estática, build oficial e captura real do binário quando houver alteração executável; E03 r13 cumpriu todos esses gates.
4. Registrar causa, correção, teste, hash, limitação e rollback no mesmo pacote de evidências.
5. Não executar novamente symlinks durante E01/E02 preparatório; o gate fica reservado à auditoria final.
6. Não converter captura automatizada em revisão humana; a revisão final permanece pendente.
7. Só promover E01/E02 após todos os critérios obrigatórios e decisão formal correspondente.

## Mapa mestre de etapas e metas

| Etapa | Meta | Estado central | Saída obrigatória |
|---|---|---|---|
| E00 | preservar, reconciliar e qualificar a base | `TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING` | auditoria final, symlink, revisão humana e decisão formal |
| E01 | contrato, backend e cena independente | `IN_PROGRESS` — checkpoint técnico dos sub-lotes A/B/C | aceite formal com fluxo, negativos, build, captura e rollback |
| E02 | primitivas, edição, persistência e histórico | `IN_PROGRESS` — E02-C | três primitivas, edição, Undo/Redo, save/reopen e negativos |
| E03 | biblioteca própria e lifecycle de assets | `TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING` | assets rastreáveis, offline, relink/replace e licença |
| E04 | tilemaps, grids e regras de terreno | `TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING` — r14 validado no binário | três grids, chunks, regras e persistência |
| E05 | colisão própria de cenário | `TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING` | tipos físicos, triggers, persistência e validação de contato |
| E06 | NavMesh 2D e consumo real | `TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING` | navegação de superfície, bake, caminho e persistência |
| E07 | componentes e instâncias | `TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING` | relações, parent/grupos, ciclo completo de prefab, build r24 e captura real |
| E08 | materiais, paralaxe, efeitos e determinismo | `IN_PROGRESS` — E08-A/E08-B checkpoints técnicos, E08-C ativo | renderer/FX qualificados com budgets e tolerâncias |
| E09 | autoria e exportação vetorial | `PLANNED` | objetos editáveis, persistentes e exportáveis |
| E10 | capacidades e integração com engines | `PLANNED` | importação/execução real nas engines aplicáveis |
| E11 | composição e runtime completo | `PLANNED` | cena executada no binário, não apenas estrutura descritiva |
| E12 | recursos avançados, animação e híbrido 3D | `PLANNED` | contrato aprovado e fluxo completo de recursos |
| E13 | fechamento, portabilidade e publicação | `PLANNED` | auditoria final, instaladores, documentação e autorização |
