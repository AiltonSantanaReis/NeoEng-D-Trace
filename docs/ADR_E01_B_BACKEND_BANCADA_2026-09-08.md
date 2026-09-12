# ADR E01-B — bancada isolada de backend

**Estado:** `ACCEPTED_LOCAL_QUALIFICATION`  
**Escopo:** somente bancada técnica E01-B; nenhuma migração do renderer do produto.  
**Data:** 2026-09-08

## Decisão

Qualificar `QOpenGLWidget` como candidato de backend para a futura fronteira de
viewport de cenário híbrido, mantendo o renderer e os fluxos atuais do produto
inalterados durante E01. O caminho raster Qt permanece o fallback portátil e a
referência determinística para testes de contrato.

Esta decisão não afirma que o produto já usa OpenGL, nem satisfaz os requisitos
de efeitos de E08. Ela apenas libera a próxima implementação isolada a usar um
viewport experimental atrás de uma fronteira explícita, com rollback para o
fallback raster.

## Critérios observáveis

A mesma fixture contém:

- câmera ortográfica e coordenadas `top_left/pixel`;
- textura RGBA com alfa;
- quatro camadas de profundidade declaradas;
- 48 partículas com seed 17;
- luz radial que altera pixels;
- captura de frame, resize e recuperação do contexto.

O candidato OpenGL habilitou `GL_DEPTH_TEST`/`GL_LEQUAL`, capturou a fixture
através de `QOpenGLWidget`, redimensionou o framebuffer físico de `1280×720`
para `1600×900` e recuperou um frame válido após `makeCurrent/doneCurrent`.

## Resultado local

Artefato: `artifacts/e01-independent-scene-20260908/backend-bench-r11/`.

| Candidato | Estado | p50 | p95 | p99 | pior amostra |
|---|---|---:|---:|---:|---:|
| Qt raster | `PASS_LOCAL` | 1.124 ms | 1.280 ms | 1.302 ms | 1.310 ms |
| Qt OpenGL Widget | `PASS_LOCAL` | 16.146 ms | 16.739 ms | 16.775 ms | 16.780 ms |

Hashes de frame:

- raster: `4360e6c219407ab78567f4efb4f53aa71a3ba7299ab8351505fc037f0ddedeaf`;
- OpenGL: `4bc4c41c6db085c4defc1d4791b4e08ec21c4023a1b2c55e5a5e86fede3a7aa6`.

## Veto, alternativas e rollback

- Vetar OpenGL se o candidato não criar contexto, não produzir frame, não
  sobreviver a resize/recuperação, exigir dependência não empacotável ou
  exceder os budgets que serão definidos antes da integração.
- Não escolher QRhi nesta rodada: a disponibilidade da API não foi suficiente
  para provar a matriz de drivers e packaging exigida pelo plano.
- Não escolher uma engine externa: isso violaria a preservação do produto e
  mudaria o escopo da etapa.
- Rollback: desabilitar o viewport experimental e manter a implementação
  raster; nenhum documento `.ndtscene` depende desta bancada.

## Limitações

O resultado é uma observação local no Windows disponível e não uma promessa
universal de desempenho. O fornecedor/driver detalhado não foi inferido a
partir de uma API que apresentou instabilidade de binding; o manifesto registra
SO, arquitetura, Qt, backend, contexto válido, depth test, hashes e métricas.
Uma qualificação de hardware/driver mais ampla continua necessária antes de
qualquer integração produtiva de E08.
