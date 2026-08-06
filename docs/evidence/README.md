# Evidências de validação

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

## Evidências registradas

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

## Estado operacional da evidência atual

Snapshot de 5 de agosto de 2026:

- `main`: `ee38a2f1dc85093e34140ddd087312629b4ecb43`;
- Etapa 5 e `R-004`: abertos;
- Pacote 5C: PR `#27`, draft e não integrado;
- CI `#81`: aprovado somente para o HEAD remoto anterior `4802e24d6dd91a20dda4b56ae526ba33e5544322`;
- revisão inicial do diff: três achados corretivos;
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
- gate vigente: somente uma evidência v4.1 com `APPROVED_FOR_DIFF_REVIEW_ONLY` permite iniciar nova revisão do diff; commit, push e novo CI continuam gates separados.

O formato de projeto v1 já persiste segmentos Bézier. Qualquer documento ou metadado da PR que afirme ausência dessa persistência deve ser corrigido antes de Ready for review.
