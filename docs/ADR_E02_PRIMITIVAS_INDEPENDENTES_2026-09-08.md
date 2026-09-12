# ADR E02-A — primitivas autorais em cena independente

**Data:** 2026-09-08  
**Estado:** `ACCEPTED_TECHNICAL_CHECKPOINT_PENDING_FINAL_AUDIT`  
**Etapa:** E02-A  
**Base:** E01 técnico em `dd65102e184565dfa7e8873faafd723ae8ed25c3`

## Contexto

E02 precisa permitir autoria sem asset artificial, preservando o contrato
independente criado em E01 e sem introduzir `ProjectReferenceRecord`. O schema
V1 descreve uma cena vazia; formas autorais exigem um sucessor explícito para
que documentos V1 continuem legíveis e a migração seja reversível em memória.

## Decisão

1. O schema V2 mantém `format_id`, coordenadas, resolução, câmera, raiz e
   `assets_root` de V1, adicionando `objects` e compatibilidade
   `reader_min_schema_version=1 / writer_schema_version=2`.
2. Cada objeto possui identidade estável, nome, geometria, transformação,
   visibilidade e bloqueio.
3. A geometria aceita `rectangle`, `ellipse`, `polygon` e `path`:
   retângulo/elipse usam dois pontos de bounding box; polígono exige forma
   fechada com pelo menos três pontos; path pode ser aberto e não preenchido.
4. Pontos repetidos, escala não positiva, pivô fora de `[0,1]`, preenchimento
   de path aberto, valores não finitos e auto-interseção de polígono são
   rejeitados antes da alteração do documento.
5. Undo/Redo é histórico de edição em memória, baseado em snapshots V2; não é
   persistido como estado operacional. O documento salvo contém apenas o
   resultado autoral determinístico.
6. A primeira superfície UI usa comandos explícitos de retângulo, elipse e
   polígono, além de Undo/Redo. O desenho livre e a edição de pontos serão
   sub-lotes posteriores de E02, não são declarados concluídos aqui.

## Alternativas rejeitadas

- reutilizar `SceneAuthoringDocument` com projeto obrigatório: rejeitado por
  reintroduzir dependência de projeto e contrariar SCN-001;
- guardar formas somente como JSON auxiliar: rejeitado porque o requisito exige
  documento autoral persistente e comparável;
- alterar V1 em lugar: rejeitado por quebrar leitura determinística do fluxo E01.

## Rollback

Documentos V1 permanecem intactos. O leitor V2 pode ser desativado e o fluxo de
E01 continua abrindo/salvando cenas vazias V1. A implementação nova só deve ser
promovida após build e evidência do SHA correspondente.
