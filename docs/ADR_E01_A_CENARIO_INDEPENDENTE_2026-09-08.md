# ADR E01-A — contrato de cenário independente

**Estado:** IMPLEMENTADO LOCALMENTE — lote E01-A em validação
**Data:** 2026-09-08
**Escopo:** F01, contrato e identidade de uma cena nova sem projeto de imagem

## Decisão

O cenário independente usa o formato `neoeng-d-trace-independent-scene`,
versão de schema `1`, extensão `.ndtscene` e o modelo
`IndependentSceneDocumentV1`. O documento não possui `project`,
`ProjectReferenceRecord`, hash de projeto ou qualquer caminho fictício para
satisfazer um contrato legado.

O documento inicial contém somente a identidade da cena, resolução autoral,
sistema de coordenadas, raiz de assets, promessa explícita de compatibilidade,
câmera ortográfica e uma raiz de autoria vazia. Objetos, transformações,
grupos e primitivas serão introduzidos nos lotes posteriores do plano; não são
simulados neste contrato.

## Identidade e persistência

- `format_id`: `neoeng-d-trace-independent-scene`.
- `schema_version`: `1`.
- `metadata.name`: nome do documento, não derivado de projeto externo.
- `assets_root`: `assets`, relativo ao diretório do documento quando assets
  forem introduzidos.
- bytes UTF-8, JSON canônico, ordenação estável, sem BOM e sem chaves
  duplicadas.
- gravação atômica; falha de validação, staging ou replace preserva o arquivo
  anterior.

## Coordenadas, resolução e câmera

- resolução autoral limitada a `1..32768` em largura e altura;
- origem no canto superior esquerdo;
- eixo X cresce para a direita, eixo Y cresce para baixo;
- unidade autoral: pixel;
- viewport físico é estado de runtime e não é persistido;
- câmera é ortográfica, com posição finita e zoom positivo;
- câmera inicial: posição `(0, 0)` e zoom `1.0`.

## Evolução e compatibilidade

V1 é o contrato inicial. Uma V2 futura somente será aceita após adicionar um
migrador executável, fixtures positivas e negativas, comparação de estado e
regressão de leitura V1. O leitor rejeita versão desconhecida; ele não converte
silenciosamente campos ausentes, projeto legado ou referência de imagem.

O sidecar `.ndtscenario.json` dependente de `.ndtproj` e o contrato
`neoeng-d-trace-scene-authoring` existente permanecem intactos e não são
reinterpretados como cenas independentes.

## Critérios do lote

O lote só poderá ser aceito após teste de contrato, I/O atômico, lifecycle
`Novo → editar resolução/câmera → Salvar → Salvar como → fechar/reabrir`, testes
negativos e evidência da build real. Este ADR registra a decisão técnica; não
constitui aceite humano nem fechamento de E01.
