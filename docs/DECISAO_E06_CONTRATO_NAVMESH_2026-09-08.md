# Decisão E06 — NavMesh 2D utilizável

**Data:** 2026-09-08  
**Estado:** `ACTIVE_TECHNICAL_CONTRACT`  
**Dependência:** checkpoint técnico E05 em `0e93ec1`.

## Contrato autorizado

E06 começa por navegação de superfície 2D, separando geometria fonte do bake
derivado. A fonte possui regiões caminháveis retangulares, obstáculos,
margem de agente e links explícitos. O bake é determinístico, versionado e
carrega hash da fonte; qualquer edição posterior torna o resultado obsoleto.

O consumidor deve distinguir caminho encontrado de caminho inexistente. Não há
inferência de gravidade, salto, plataforma ou NavMesh 3D neste lote.

## Aceite e negativos

O fluxo técnico é região → obstáculo → agente → bake → origem/destino → caminho
→ persistência. São rejeitados agente inválido, região degenerada, obstáculo
fora da região quando configurado como inválido, origem/destino fora da área,
corredor menor que a margem e fonte modificada após bake.

Symlink e revisão humana permanecem reservados à auditoria final do plano.
