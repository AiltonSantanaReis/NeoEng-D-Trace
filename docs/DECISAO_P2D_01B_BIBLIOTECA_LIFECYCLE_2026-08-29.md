# NeoEng-D-Trace — Decisão P2D-01B: biblioteca e lifecycle de assets

**Data:** 2026-08-29 (UTC-03)
**Linha:** P2D-COMP-01 / P2D-01B
**Estado:** APROVADA PARA IMPLEMENTAÇÃO LOCAL
**Autoridade:** solicitação explícita do proprietário do produto, subordinada ao normativo P2D-COMP-01, à decisão P2D-01A e aos imutáveis C3/G/V/B.

## 1. Objetivo obrigatório

P2D-01B deve transformar os registros de assets da cena em uma biblioteca utilizável dentro do editor profissional de composição 2D. O usuário deve conseguir identificar cada asset do documento, verificar seu estado, localizar referências ausentes ou alteradas e reparar ou substituir o conteúdo sem perder os objetos que o utilizam.

Esta subetapa complementa P2D-01A. Ela não reabre, altera ou reinterpreta o contrato de importação controlada, a renderização real, a persistência V1/V2 ou os artefatos já aceitos.

## 2. Definições operacionais

### 2.1 Relink

Relink é a reparação de uma referência quebrada ou alterada. O asset mantém o mesmo `id`; o usuário fornece um arquivo candidato; o arquivo é validado, copiado para `assets/scene/` quando necessário e o registro passa a apontar para o caminho relativo controlado e para o novo SHA-256.

O relink não altera `SceneObjectAuthoringRecord`, transforms, layers, groups, ordem, seleção ou qualquer vínculo de objeto. A origem local fornecida pelo usuário pode ser registrada apenas em `source_path` como provenance não resolvível.

### 2.2 Replace

Replace é a substituição intencional do conteúdo de um asset selecionado, válido ou não. O asset mantém o mesmo `id` para que todos os objetos que o utilizam continuem apontando para a mesma identidade lógica. Somente `path`, `sha256` e provenance aplicável são atualizados.

Replace preserva integralmente objetos, transforms, layers, groups, ordem, seleção e histórico transacional. Não haverá troca silenciosa do `asset_id` dos objetos nem remoção automática de registros ou arquivos.

## 3. Biblioteca e UX obrigatórias

1. A biblioteca existirá somente na janela do editor profissional de cenário; não será adicionada ao editor principal de imagem, ao visualizador de máscara ou a painéis legados.
2. A lista deve apresentar todos os assets do documento, inclusive os ausentes ou alterados.
3. Cada item deve indicar identidade legível, estado operacional, caminho relativo e quantidade de objetos que o utilizam.
4. Os estados mínimos são `READY`, `MISSING`, `MODIFIED` e `INVALID/UNAVAILABLE`, com diagnóstico acionável.
5. A biblioteca deve permitir selecionar um asset e executar `Relink` ou `Replace`; a ausência não pode ser ocultada por fallback visual silencioso.
6. A biblioteca deve oferecer atualização explícita do diagnóstico para detectar arquivo removido ou alterado depois da abertura da cena.
7. A UI deve distinguir uma operação sem alteração de uma operação aplicada e reportar a causa quando uma operação for rejeitada.
8. Os controles devem respeitar o modo preview somente leitura do editor profissional.

## 4. Contrato de dados e integridade

- `AssetReferenceRecord.id` é a identidade estável do asset dentro da cena.
- O vínculo operacional continua sendo somente `path` relativo POSIX e `sha256` do arquivo controlado.
- `source_path` continua sendo provenance opcional e não pode ser usado para resolver, exportar ou substituir automaticamente um arquivo.
- Relink e replace devem reutilizar a política content-addressed de P2D-01A, sem sobrescrever arquivo de hash diferente.
- A alteração do documento deve ser uma única transação da sessão, com Undo/Redo completo.
- Falha de validação, decodificação, cópia ou hash deve deixar documento e seleção exatamente como estavam antes da operação.
- Arquivos controlados não utilizados podem permanecer no projeto; limpeza automática não pertence a esta subetapa.
- Assets externos nunca podem continuar como dependência operacional fora do projeto.

## 5. Limites de escopo

P2D-01B inclui biblioteca, inspeção de estado, importação pela biblioteca, relink, replace, atualização de diagnóstico, preservação de vínculos e evidência visual/funcional no produto.

P2D-01B não inclui tilesets/tilemaps, pincéis, balde, borracha, autotiling, grids isométricos/hexagonais, colliders de cenário, NavMesh, entidades/componentes/prefabs, iluminação, sombras, VFX, 2.5D, 3D, alteração de exportadores, alteração de C3 ou alteração dos gates G/V/B. Essas linhas permanecem independentes e bloqueadas pelo plano vigente.

## 6. Evidência e aceite

O aceite exige, no mínimo:

1. teste de listagem de asset válido, ausente e alterado;
2. teste de relink de asset ausente com preservação de `id`, objeto e transform;
3. teste de replace de asset usado por múltiplos objetos com preservação de todos os vínculos;
4. teste negativo de formato/conteúdo inválido e falha sem mutação parcial;
5. teste de Undo/Redo das alterações de lifecycle;
6. captura Windows do painel e do viewport com asset válido e diagnóstico missing/modified;
7. revisão visual sem alteração fora do painel/asset esperado;
8. suíte completa, `git diff --check`, boundary revisado, commit local e requalificação pós-commit.

P2D-01B somente poderá ser declarado `ACCEPTED` quando código, testes, evidências, gates e revisão humana forem concluídos. Até lá, P2D-01 maior e P2D-COMP-01 permanecem `OPEN`.

## 7. Rollback e publicação

O rollback é o commit imediatamente anterior a P2D-01B. Nenhuma baseline C3, referência G/V/B ou evidência selada anterior será alterada. Push, tag, merge e qualquer publicação remota ficam proibidos até que o commit local, a build e o pacote de evidências sejam aceitos e o ciclo remoto seja explicitamente iniciado no ponto de release.
