# NeoEng-D-Trace — Decisão formal do sublote de otimização de performance

**Subordinação:** `P2D-05` — performance, limites, formatos e erros
**Sublote:** otimização de performance da fundação de composição 2D
**Status:** `ACCEPTED FOR IMPLEMENTATION — QUALIFICAÇÃO PENDENTE`
**Data de abertura:** 30/08/2026 (UTC-03)
**Branch de investigação:** `p2d-05-quality-hardening`
**HEAD de referência:** `fc59ff571e4e4d99ddd40a8ec318d50b8edd77f3`
**Rollback de produção:** `f55b07b85ef2cf65160f2c10ffac5e63b45732ac`
**Contrato pai:** `docs/DECISAO_P2D_05_PERFORMANCE_LIMITES_FORMATOS_ERROS_2026-08-30.md`

Este documento é o contrato específico autorizado para a investigação de
otimização aceita pelo proprietário. Ele não aprova implementação, não fecha
P2D-05, não altera o plano de gates P2D-06/P2D-07 e não autoriza commit,
build, merge, push, tag, release ou mudança remota.

## 1. Motivo e evidência de abertura

A investigação somente leitura foi registrada em:

`docs/EVIDENCIA_P2D_05_INVESTIGACAO_PERFORMANCE_2026-08-30.md`

Ela confirmou os seguintes sinais de escala:

| Objetos | Serialize p95 | Save/recovery p95 | Edit/history p95 | Preview p95 | Exportações p95 |
|---:|---:|---:|---:|---:|---:|
| 128 | 32,729 ms | 73,218 ms | 29,557 ms | 76,021 ms | 154–220 ms |
| 256 | 65,624 ms | 110,602 ms | 56,692 ms | 135,639 ms | aproximadamente 284 ms |
| 512 | 129,206 ms | 188,905 ms | 110,781 ms | 274,684 ms | 557–682 ms |

O profiling de funções confirmou:

- cópia profunda do documento inteiro como principal custo do histórico;
- reconstrução, pintura e verificações de visibilidade no preview;
- restauração e validação do estado-base durante cada evento de gesto;
- validação, hash e serialização repetidos na preparação da exportação.

Nenhum destes fatos autoriza modificar o produto sem este contrato e seu aceite
próprio.

## 2. Objetivo do sublote

Reduzir o custo mensurável dos caminhos de histórico/gesto, preview e
persistência/exportação da fundação profissional de composição 2D, mantendo
exatamente a mesma semântica de produto, os mesmos formatos válidos, os mesmos
limites, os mesmos resultados determinísticos e a mesma segurança de recuperação.

O sublote deve otimizar o custo real demonstrado. Não deve introduzir uma
arquitetura genérica de engine, GPU ou 3D sem evidência correspondente.

## 3. Escopo permitido

### 3.1 Metodologia de medição

- separar timing de CPU/GUI de medição de memória;
- repetir as cargas com pelo menos 50 amostras medidas, ou justificar
  documentalmente qualquer quantidade diferente;
- registrar p50, p95, p99, pior caso, erro e variação;
- medir memória Python separadamente de Working Set/Private Bytes do processo;
- usar fixtures determinísticas com 64, 128, 256 e 512 objetos;
- incluir assets compartilhados e únicos, tamanhos representativos, camadas,
  grupos, memberships e proporções de itens visíveis;
- medir o fluxo real de seleção, arraste, gizmo, preview, undo/redo, save e
  export;
- medir em hardware alvo identificado, sem publicar nome de host, usuário,
  caminhos locais ou credenciais;
- medir GPU somente se o profiler confirmar que o caminho de renderização atual
  possui custo GPU relevante.

### 3.2 Histórico e gesto

Investigar e, se confirmado pelo perfil final, reduzir:

- `model_copy(deep=True)` do documento inteiro em cada edição de alta
  frequência;
- restauração e validação integral do documento a cada evento de arraste/gizmo;
- alocações repetidas de estados que não foram alterados.

Qualquer alternativa por comando, delta, copy-on-write ou estrutura persistente
deverá cobrir todas as operações undoáveis incluídas no produto. Não será aceito
otimizar apenas `translate` e deixar `add`, `remove`, importação,
transformação, grupos, camadas, clipboard e demais operações com semântica
diferente sem uma matriz explícita de cobertura.

### 3.3 Preview e viewport

Investigar e, se confirmado pelo perfil final, reduzir:

- limpeza e reconstrução integral da cena em alterações não estruturais;
- atualização de itens que não foram alterados;
- recriação de gizmo e estados visuais sem necessidade;
- verificações repetidas de visibilidade, layer e membership.

A solução deve distinguir alteração estrutural de alteração incremental. O
preview deve continuar exibindo exatamente os mesmos objetos, ordem, transformações,
seleção, isolamento, zoom, parallax e estados normais.

Culling, spatial index e virtualização somente poderão ser adicionados se o
perfil demonstrar que são necessários. Não se deve confundir visibilidade lógica
com culling de viewport.

### 3.4 Persistência e exportação

Investigar e, se confirmado pelo perfil final, reduzir:

- validações repetidas do mesmo documento imutável;
- hashes e serializações repetidos dentro de uma mesma revisão;
- preparação de exportação duplicada entre generic, Godot e Unity.

O cache deverá ser:

- indexado por revisão/identidade válida do documento;
- invalidado em toda mutação relevante;
- incapaz de aceitar bytes de documento ou asset alterado;
- limitado em tamanho e acompanhado por evidência de memória;
- transparente para determinismo, SHA-256 e validação.

Atomicidade, `fsync`, recovery e preservação do destino válido não podem ser
removidos ou relaxados para obter redução de tempo.

### 3.5 Responsividade e paralelismo

Worker threads poderão ser investigadas apenas para leitura, validação,
serialização, exportação ou decodificação segura de dados. É proibido mover
mutação do modelo, `QGraphicsItem`, `QPixmap` ou controles Qt para fora da
thread apropriada.

Se a operação for assíncrona, o fluxo deve possuir:

- estado de progresso compreensível;
- cancelamento seguro;
- resultado descartado quando a revisão ficar obsoleta;
- erro acionável;
- preservação do documento ativo;
- teste de encerramento e concorrência.

Paralelismo não será usado para mascarar uma operação lenta nem para criar
corridas de estado.

## 4. Fora do escopo

Não fazem parte deste sublote:

- tilemap, autotiling, Rule Tiles, grid isométrico ou hexagonal;
- colisão própria do cenário, NavMesh, entidades, componentes ou prefabs;
- iluminação real, sombras, partículas, VFX, pós-processamento ou shaders;
- vectorização e processamento avançado de imagem;
- alteração de schema, formato, coordenadas, orientação ou adapters de engine;
- alteração de limites operacionais ou tolerâncias de auditor;
- redesign visual, geometria, QSS, widget tree, atalhos ou QAction;
- GPU renderer, instancing de malhas ou migração para 2.5D/3D;
- otimização de código sem hot spot demonstrado;
- limpeza de untracked, alteração de `.gitignore` ou publicação remota.

Qualquer necessidade fora desta lista interrompe o sublote e exige nova decisão
formal.

## 5. Invariantes obrigatórios

Toda implementação deverá preservar:

1. bytes canônicos e SHA-256 para documentos e exportações válidos;
2. determinismo de authoring e dos destinos generic, Godot e Unity;
3. schema V1/V2 e ausência de migração silenciosa;
4. limites atuais, inclusive rejeição antes de mutação ou escrita;
5. atomicidade, `fsync`, recovery e destino anterior válido;
6. undo/redo e histórico de todas as operações cobertas;
7. seleção, transformações, grupos, camadas, isolamento, parallax e preview;
8. thread affinity e integridade do modelo Qt;
9. mensagens seguras, sem caminhos locais, credenciais ou segredos;
10. G=0, V=0 e B=0 para semântica de produto, salvo nova decisão explícita;
11. compatibilidade com os testes, capturas e contratos já aceitos;
12. rollback sem apagar evidências, histórico ou untracked.

Se uma otimização alterar o resultado observável, a estabilidade dos bytes ou a
ordem das operações, ela não é uma otimização compatível e deve ser rejeitada ou
reclassificada.

## 6. Plano controlado de execução

### O-0 — calibração

- executar a matriz sem `tracemalloc` para timing;
- executar memória em processo separado;
- gerar workloads realistas;
- produzir baseline com hashes, ambiente e amostras;
- separar custo de preparação, validação, serialização, escrita e `fsync`.

### O-1 — histórico e gesto

- caracterizar todas as operações undoáveis;
- implementar somente a estratégia que mantenha cobertura completa;
- provar equivalência antes/depois;
- medir arraste, gizmo, undo, redo e cancelamento.

### O-2 — preview e viewport

- caracterizar alterações estruturais e incrementais;
- atualizar apenas itens necessários;
- provar seleção, ordem, visibilidade, isolamento e estados visuais;
- medir o fluxo real em todas as resoluções-alvo.

### O-3 — persistência e exportação

- eliminar trabalho redundante por revisão;
- medir generic, Godot e Unity separadamente;
- preservar hash, schema, atomicidade e recovery;
- testar documento e asset alterados durante a preparação.

### O-4 — fechamento técnico

- executar suíte completa, cobertura, qualidade estática e privacidade;
- executar benchmark calibrado e comparar com a baseline;
- executar captura e auditoria visual;
- revisar diff e fronteira;
- solicitar aceite PRECOMMIT próprio do sublote;
- somente depois seguir o ciclo de commit previsto por P2D-05.

Nenhum subestágio será apresentado como concluído se seus testes,
evidências ou equivalência estiverem incompletos.

## 7. Testes obrigatórios

A matriz mínima deverá conter:

- caracterização de bytes e SHA-256 antes/depois;
- equivalência de documentos e exportações;
- todas as operações undoáveis;
- arraste, gizmo, cancelamento, undo e redo;
- seleção, visibilidade, isolamento, layers, groups e sockets;
- preview em 720p, 768p e 1080p;
- save, recovery, reload e falha de `fsync`/destino;
- generic, Godot e Unity;
- documento grande, assets únicos/compartilhados e asset alterado;
- concorrência, cancelamento e revisão obsoleta, se houver worker;
- limites e rejeições sem mutação parcial;
- teste de memória Python e memória nativa do processo;
- full suite e cobertura conforme política;
- auditoria de privacidade e ausência de caminhos sensíveis.

## 8. Evidências obrigatórias

O pacote do sublote deverá conter:

- baseline e pós-otimização com ambiente e workloads hashados;
- profiling de função e, quando aplicável, profiling Qt/frame;
- tabela p50/p95/p99/pior caso e variação;
- memória Python e memória do processo separadas;
- matriz de equivalência funcional e de bytes;
- capturas reais do fluxo de usuário;
- auditoria visual e comparação;
- logs sem caminhos locais ou segredos;
- inventário de arquivos e mudanças;
- rollback verificado;
- decisão humana do sublote.

Perfis brutos que contenham caminhos locais ficam restritos à evidência local e
não entram em commit, review package ou seal sem sanitização independente.

## 9. Critérios de aceite do sublote

O sublote só poderá ser marcado `ACCEPTED / CLOSED` quando:

- os hot spots tiverem sido confirmados por profiling;
- cada hot spot incluído tiver correção completa ou decisão documentada de
  `NO_CHANGE`;
- todas as operações afetadas tiverem cobertura;
- não houver regressão funcional, visual, geométrica ou de bytes;
- as metas de performance forem propostas com metodologia calibrada e aceitas;
- a latência interativa e as operações bloqueantes estiverem separadas;
- memória Python e nativa não apresentarem crescimento não explicado;
- full suite, cobertura, qualidade estática e privacidade passarem;
- build, revisão humana e fluxo real do usuário forem concluídos;
- rollback for reproduzível;
- o diff final estiver dentro desta fronteira;
- P2D-05 registrar o resultado sem declarar capacidade não comprovada.

Um único item ausente mantém o sublote aberto e impede usar sua evidência para
fechar P2D-05.

## 10. Orçamentos de performance

Os valores medidos anteriormente para o workload de referência de 64 objetos
continuam provisórios. Este sublote não aceita automaticamente:

- `<=25 ms` para serialize;
- `<=15 ms` para load/validate;
- `<=60 ms` para save/recovery;
- `<=20 ms` para edit/history;
- `<=50 ms` para preview;
- `<=120 ms` para exportações.

Após a calibração O-0, os orçamentos deverão ser reapresentados com:

- workload;
- hardware;
- número de amostras;
- método de medição;
- p95/p99 e pior caso;
- margem operacional;
- comportamento esperado quando o limite for excedido.

Nenhum número será transformado em contrato por inferência.

## 11. Rollback e governança

O rollback técnico é `f55b07b85ef2cf65160f2c10ffac5e63b45732ac`, sujeito aos
commits efetivamente aprovados em P2D-05. Rollback não autoriza excluir
artefatos, limpar untracked, reescrever baselines ou alterar C3/G/V/B.

A decisão foi aceita pelo proprietário. O trabalho continua somente dentro da sequência O-0 → O-1 → O-2 → O-3 → O-4, com aceite formal entre contrato, precommit e fechamento.

## 12. Decisão registrada

O aceite explícito deste contrato foi registrado pelo proprietário com a frase:

`P2D-05-OTIMIZAÇÃO ACEITA — profiling, histórico, preview e exportação`

Esse aceite autoriza somente a execução controlada do sublote descrito aqui. Ele
não aceita o resultado de implementação, metas, build ou publicação. O status
vigente é:

`P2D-05-OTIMIZAÇÃO ACCEPTED FOR IMPLEMENTATION — qualificação pendente`
