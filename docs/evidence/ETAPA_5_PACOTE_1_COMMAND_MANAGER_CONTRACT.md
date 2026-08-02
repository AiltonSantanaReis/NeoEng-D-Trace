# Etapa 5 - Pacote 1: contrato do gerenciador de comandos

## Estado

- Etapa: `5 - Undo/Redo completo`;
- risco: `R-004`;
- pacote: `1 - contrato, pilhas, transacao e estado da UI`;
- base: `635f4cc11246fe1dc519ba039ee474f43b5ac891`;
- branch: `feat/etapa-5-pacote-1-command-manager-contract`;
- `R-004`: permanece aberto;
- Etapa 5: permanece em desenvolvimento.

## Inventario de entrada

- ZIP externo: `NeoEng-D-Trace_Etapa5_Inventario_20260802_181805.zip`;
- SHA-256:
  `47aa328c713c1e372d684f3b67d22a2cfd95ee3677ff9b9b717b9256839a4fba`;
- classes de comando: `20`;
- chamadas ao gerenciador: `75`;
- mutacoes candidatas fora do servico: `117`;
- testes atuais relacionados: `17`;
- testes historicos relacionados: `41`;
- achados P1: `10`.

## Escopo deste pacote

- `CommandStatus` e `CommandResult`;
- checkpoint dos atributos editaveis da cena;
- rollback em falha de execute, undo e redo;
- nenhuma entrada de historico para operacao sem mudanca;
- pilhas preservadas em falha;
- redo invalidado somente por edicao aplicada;
- limite e estado observavel do historico;
- `CompositeCommand` repetivel;
- acoes Undo/Redo sincronizadas;
- logs sem mensagem bruta da excecao;
- testes positivos, negativos e Qt offscreen.

## Limites

Continuam pendentes:

- classificar e migrar as `117` mutacoes candidatas;
- comandos ausentes de movimento e propriedades;
- matriz execute/undo/redo por operacao;
- restauracao integral das relacoes de objetos;
- multiplos objetos e ancoras temporarias;
- sessao manual Windows;
- cobertura alvo;
- encerramento de `R-004`.

Este pacote nao conclui a Etapa 5 e nao autoriza a Etapa 6.
