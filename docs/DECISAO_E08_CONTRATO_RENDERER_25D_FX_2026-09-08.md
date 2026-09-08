# Decisão E08 — Composição 2.5D, iluminação, sombras e FX reais

**Data:** 2026-09-08  
**Estado:** `ACTIVE_TECHNICAL_CONTRACT`  
**Dependência:** checkpoint técnico E07 em `d35bc84`  
**Plano normativo:** seção 15 do Plano Mestre; requisitos FX-001/002/003/004/005/006 e EXT-FX-01.

## Decisão de arquitetura

E08 será implementada atrás de uma fronteira de composição determinística,
com o raster Qt como referência portátil e o candidato `QOpenGLWidget` como
backend acelerado opcional. A cena autoral não dependerá de um widget nem de
um backend específico. Quando o backend acelerado estiver indisponível, o
estado será explicitamente `degraded` e o fallback raster permanecerá
observável; nenhum efeito será anunciado como suportado somente por existir um
controle ou um sidecar.

A ordenação será definida por uma lista de planos estáveis: camada autoral,
profundidade/paralaxe, geometria visual, sombra/occluder, iluminação/material,
partículas e overlays. `position.z` continua distinto de profundidade de
paralaxe. A câmera de edição e a câmera autoral permanecem estados separados.

## Lotes e critérios obrigatórios

- **E08-A:** plano de renderização, backend raster de referência, ordenação,
  cache/invalidação, resize, cleanup e diagnóstico de backend.
- **E08-B:** câmera/paralaxe com scroll X/Y, offset, repetição/espelhamento,
  preview transitório e persistência transacional sem dupla aplicação.
- **E08-C:** materiais, normal map, luzes e sombras com alteração observável de
  pixels, receptores/emissores explícitos e intensidade zero verificável.
- **E08-D:** partículas com seed, lifecycle e limites; shaders com erro
  preservando o último estado válido; pós-processamento com cadeia e ordem.
- **E08-E:** timestep/seed reproduzíveis, comparação temporal com tolerância
  registrada e matriz de capacidades por backend/destino.

Cada lote exige teste unitário/contrato, integração, negativo, persistência
quando houver dados, regressão oficial, build limpa e captura real do binário.
E08 só poderá receber checkpoint técnico quando os cinco lotes tiverem
evidência própria; este primeiro commit abre apenas o contrato e E08-A.

## Negativos e rollback

Shader inválido, textura incompatível, backend ausente, contexto perdido,
limite de recursos, efeito sem suporte e alteração durante compilação devem
produzir diagnóstico acionável, preservar o último estado válido e nunca
emitir sucesso silencioso. Rollback desativa o backend experimental e mantém
o raster; documentos com FX novos não podem ser sobrescritos de forma
destrutiva em modo limitado.

Symlink e revisão humana continuam reservados à auditoria final do Plano
Mestre, conforme autorização já registrada.
