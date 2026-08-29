# NeoEng-D-Trace — Decisão P2D-01: assets originais e importação controlada

**Data:** 2026-08-29 (UTC-03)
**Linha:** P2D-COMP-01 / P2D-01A — contrato de assets, lifecycle e renderização real
**Estado:** APROVADA PARA IMPLEMENTAÇÃO LOCAL
**Autoridade:** decisão explícita do proprietário do produto, subordinada ao documento normativo P2D e aos imutáveis C3/G/V/B.

## 1. Decisão

O editor usará somente assets cuja origem e conteúdo possam ser identificados.

- Assets internos do produto serão originais do NeoEng-D-Trace ou gerados proceduralmente pela equipe. Eles ficarão em `assets/scene/` e serão tratados como conteúdo próprio do produto.
- Um asset externo arrastado para o editor será validado e copiado para `assets/scene/` dentro da raiz do projeto antes de ser adicionado à cena.
- O arquivo de cena referenciará apenas o caminho relativo controlado pelo projeto e o SHA-256 do arquivo copiado.
- O caminho original do sistema operacional será preservado no registro como provenance, exclusivamente para diagnóstico e auditoria. Ele nunca será usado como dependência de carregamento ou exportação.
- A cópia será content-addressed: o nome conterá o stem sanitizado e os primeiros 16 caracteres do SHA-256. Um arquivo existente só será reutilizado se o hash coincidir; nunca será sobrescrito silenciosamente.
- Assets já localizados dentro da raiz do projeto não serão duplicados. Sua referência relativa existente será preservada e o conteúdo será verificado pelo hash.
- Nenhuma biblioteca, textura, ícone ou imagem de terceiros será incluída no produto sem licença e provenance registrados. Quando não houver comprovação, o asset não entra no conjunto distribuível.

## 2. Formatos da primeira entrega

P2D-01A aceita os formatos raster já suportados (`PNG`, `JPG`, `JPEG`, `WEBP`, `BMP`, `GIF`) e `SVG` original/procedural. O formato não é aceito apenas pela extensão: o conteúdo precisa ser decodificável pelo Qt, possuir dimensões positivas e passar pelo hash do arquivo efetivamente persistido.

O primeiro lote não implementa tileset, tilemap, autotiling, colisão de cenário, NavMesh, entidades, prefabs, iluminação ou VFX. Essas capacidades continuam nas linhas independentes já documentadas.

## 3. Segurança e integridade

- Caminhos persistidos continuam relativos, POSIX e incapazes de escapar da pasta da cena.
- O provenance local pode ser absoluto e não é resolvido durante o carregamento.
- A resolução verifica existência, arquivo regular e SHA-256 antes de renderizar ou exportar.
- A ausência, corrupção ou divergência de hash produz diagnóstico explícito; não haverá fallback silencioso para um asset diferente.
- A importação usa escrita temporária e substituição atômica no diretório controlado. Falha de cópia não altera o documento nem deixa uma referência apontando para arquivo parcial.
- Undo/redo desfaz e refaz o registro da cena; o arquivo copiado pode permanecer como conteúdo não utilizado, pois limpeza automática de assets não faz parte deste lote e seria destrutiva.

## 4. Compatibilidade

Os campos existentes `path`, `path_kind` e `sha256` continuam obrigatórios e preservam seu significado. `source_path` é opcional para manter leitura de cenas V1/V2 existentes; cenas antigas sem provenance continuam válidas. A canonicalização exclui campos opcionais nulos, portanto nenhum documento legado é reescrito apenas por ser carregado.

## 5. Critérios de aceite P2D-01A

1. Asset externo é copiado para área controlada e renderizado no viewport.
2. Asset interno é referenciado sem cópia duplicada e renderizado quando válido.
3. O documento registra caminho relativo, hash e provenance externo quando aplicável.
4. Conteúdo alterado, formato inválido, caminho inseguro e falha de cópia são rejeitados com diagnóstico.
5. O viewport informa assets ausentes/corrompidos e não os substitui silenciosamente.
6. SVG e raster têm dimensões reais e não são desenhados somente como polígonos abstratos.
7. Testes existentes permanecem verdes, sem alteração de semântica fora do fluxo de assets.

## 6. Rollback

O rollback desta subetapa é o commit anterior a P2D-01A. Nenhuma baseline C3, referência G/V/B ou artefato selado será alterado. O conteúdo copiado em `assets/scene/` não será removido automaticamente.

## 7. Aprovação

**Decisão do proprietário:** aprovada — seguir a política de assets originais/procedurais e importação externa controlada.
**Limite:** esta aprovação autoriza somente P2D-01A e seus testes/evidências; não autoriza as linhas EXT-TMAP-01, EXT-COLL-01, EXT-NAV-01, EXT-ENT-01 ou EXT-FX-01.
