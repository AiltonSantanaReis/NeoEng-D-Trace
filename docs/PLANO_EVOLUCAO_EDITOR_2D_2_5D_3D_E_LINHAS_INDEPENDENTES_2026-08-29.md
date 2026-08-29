# NeoEng-D-Trace — Plano de evolução do editor

## Composição 2D, caminho 2.5D/3D e linhas independentes

**Status:** plano aprovado para execução local
**Data:** 2026-08-29 (UTC-03)
**Documento normativo principal:** docs/NEOENG_EDITOR_COMPOSICAO_2D_NORMATIVO_2026-08-27.md
**Registro de adoção:** docs/EVIDENCIA_P2D_00_RECONCILIACAO_2026-08-29.md
**Decisão P2D-01A:** docs/DECISAO_P2D_01_ASSETS_ORIGINAIS_E_IMPORTACAO_2026-08-29.md
**Evidência P2D-01A:** docs/EVIDENCIA_P2D_01A_ASSETS_IMPORTACAO_E_RENDERIZACAO_2026-08-29.md

## 1. Finalidade

Este plano transforma a decisão de engenharia em uma carteira rastreável. Ele separa:

- a consolidação imediata do editor profissional de composição 2D baseado em objetos;
- os pontos de extensão necessários para permitir 2.5D e 3D no futuro;
- as capacidades avançadas que devem permanecer em linhas independentes.

O plano não declara nenhuma capacidade ausente como pronta.

## 2. Princípios de execução

1. O editor 2D será concluído primeiro como produto coerente e verificável.
2. Cada etapa terá contrato, código, testes, evidências, gate e decisão formal.
3. O código só será alterado dentro da etapa autorizada.
4. O estado atual será separado de intenção futura em código, documentação, UI e exportação.
5. C3, baselines aprovadas, tolerâncias, auditores e artefatos selados permanecem imutáveis.
6. Falhas legacy continuarão visíveis; nenhum auditor será relaxado para produzir PASS.
7. Nenhuma linha futura será introduzida por acoplamento informal ao schema V2.
8. Push, tag, merge e publicação continuam fora do escopo sem autorização explícita.

## 3. Produto primeiro: P2D-COMP-01

### 3.1 Resultado de negócio

O usuário deve conseguir criar ou abrir uma composição, adicionar assets suportados, vê-los de fato no viewport, selecionar e transformar objetos, organizar camadas e grupos, persistir o trabalho, recuperar erros e exportar somente capacidades declaradas.

### 3.2 Ordem obrigatória

| Etapa | Objetivo | Saída de aceite |
|---|---|---|
| P2D-00 | adoção, reconciliação e baseline local | registro de checkpoint e divergências; ACCEPTED |
| P2D-01 | assets, biblioteca, lifecycle, diagnósticos e renderização real | asset real visível, portable e testado |
| P2D-02 | ordem visual, camadas, grupos e isolamento | ordem observável, persistente e editável |
| P2D-03 | seleção, teclado, mouse, nudge, duplicate, copy/paste, marquee e fit | produtividade comprovada por testes e captura |
| P2D-04 | save atômico, recovery, preview, export e orientação de coordenadas | round-trip e adapters aceitos |
| P2D-05 | performance, limites, formatos e erros | testes positivos/negativos e limites documentados |
| P2D-06 | gates G/V/B, captura Windows, auditoria e revisão humana | evidência completa e decisão ACCEPT/REJECT |
| P2D-07 | aceite formal e seal | produto fechado ou bloqueado explicitamente |

Nenhuma etapa posterior pode ser aceita enquanto a anterior estiver aberta, bloqueada ou rejeitada.

### 3.3 Decisão aprovada de P2D-01

A política de assets foi aprovada e está registrada no documento de decisão P2D-01A. Ela afeta portabilidade e persistência e, portanto, passa a ser requisito obrigatório do código e dos testes:

- copiar asset externo para a área controlada assets/scene/;
- preservar source_path somente como provenance não resolvível;
- manter apenas caminho relativo e SHA-256 no vínculo operacional da cena;
- preservar referências já internas ao projeto sem duplicação;
- rejeitar formato não suportado, conteúdo não decodificável, tamper e destino inseguro com diagnóstico explícito;
- não incluir conteúdo de terceiros sem licença/provenance comprováveis.

P2D-01 será executado em subetapas fecháveis:

- **P2D-01A:** contrato, importação controlada, hash, diagnostics e renderização real raster/SVG;
- **P2D-01B:** biblioteca/UX de assets, lifecycle de relink/replace/missing e evidência de uso no produto.

Nenhuma subetapa pode declarar P2D-01 completo antes de seu próprio código, testes, evidências, gates e revisão humana.

## 4. Arquitetura de extensão 2.5D/3D

### 4.1 Núcleo estável

O núcleo de composição deve permanecer agnóstico quanto ao destino quando isso não mudar a semântica:

- IDs estáveis e referências verificáveis;
- assets com caminho relativo, hash e estado de disponibilidade;
- objetos, camadas, grupos e relações;
- transformações com valores numéricos finitos;
- câmera, seleção, undo/redo e persistência determinística;
- adapters com capacidades declaradas e rejeição explícita do que não suportam.

### 4.2 Extensão 2.5D

2.5D só será aceito quando houver contrato próprio para:

- profundidade e ordem de desenho observáveis;
- câmera ortográfica/perspectiva conforme o destino;
- parallax e escala dependentes de profundidade;
- conversão de coordenadas e orientação validada com fixture assimétrica;
- materiais, recorte e alpha se fizerem parte do adapter;
- round-trip e importação real na engine-alvo.

O campo z já presente em registros não deve ser tratado como implementação de 2.5D enquanto não houver semântica de renderização e evidência.

### 4.3 Extensão 3D

3D será uma linha de produto própria, com:

- modelo de cena e hierarquia 3D;
- viewport 3D e ferramentas de câmera;
- malhas, materiais, UVs, normais, iluminação e animação conforme o escopo;
- importadores/exportadores com contratos separados;
- validação em engine real e testes de orientação, escala, winding e unidades.

O contrato GLTF/GLB existente permanece limitado e não pode ser interpretado como editor 3D.

## 5. Linhas independentes posteriores

As linhas a seguir não entram na implementação do primeiro produto. Cada uma terá uma branch/commit line de trabalho somente quando for autorizada e iniciada formalmente; este documento apenas estabelece a separação de escopo.

### EXT-TMAP-01 — Tilemap

**Objetivo:** autoria de tilesets e mapas por células.

**Escopo mínimo:** grid ortogonal inicial, múltiplas camadas, seleção de tiles, pincel, balde, borracha, preenchimento determinístico, undo/redo e exportação. Isométrico, hexagonal, autotiling e Rule Tiles serão extensões declaradas, não presumidas.

**Riscos:** crescimento de memória, semântica de ordenação, importação de tileset, regras de borda e divergência entre preview e engine.

**Gates indispensáveis:** teste de células e bordas, round-trip, performance em mapas grandes, captura visual e validação no destino.

### EXT-COLL-01 — Colisão de cenário

**Objetivo:** autoria de colisores próprios do cenário, separados dos contornos de máscara e dos shapes herdados do projeto.

**Escopo mínimo:** camada de colisão, retângulo, círculo, polígono, cadeia/trigger conforme contrato, seleção e edição, validação de winding/interseção/degeneração, diagnóstico acionável e exportação por engine.

**Riscos:** polígonos inválidos, sistemas de coordenadas, regras diferentes entre engines e aplicação parcial.

**Gates indispensáveis:** nenhum export inválido, bloqueio transacional, teste negativo por shape e reprodução do erro com identificação do objeto/ponto responsável.

### EXT-NAV-01 — NavMesh 2D

**Objetivo:** autoria de regiões navegáveis e obstáculos para IA.

**Escopo mínimo:** regiões, obstáculos, conexões e validação; comportamento de caminhada/pulo só entra se houver contrato de navegação correspondente.

**Dependências:** contrato de colisão ou definição formal de como obstáculos serão representados.

**Gates indispensáveis:** conectividade, regiões isoladas, obstáculos sobrepostos, determinismo e validação no runtime alvo.

### EXT-ENT-01 — Entidades, componentes e prefabs

**Objetivo:** permitir instâncias editáveis de entidades com composição de componentes e prefabs.

**Escopo mínimo:** identidade da entidade, componentes versionados, instância, overrides, vínculo com asset e ciclo de vida.

**Riscos:** acoplamento ao runtime, herança ambígua, overrides não determinísticos e perda de dados no round-trip.

**Gates indispensáveis:** criação, instanciação, override, atualização do prefab, break-link explícito, save/reopen e validação no destino.

### EXT-FX-01 — Iluminação e VFX

**Objetivo:** converter sockets declarativos em recursos editoriais e runtime reais apenas quando o contrato estiver definido.

**Escopo mínimo:** luzes, sombras, efeitos, parâmetros, preview determinístico e exportação/integração declarada.

**Limite:** sockets atuais são dados/markers; eles não constituem iluminação, sombra ou VFX funcionais.

**Gates indispensáveis:** estados ligados/desligados, ordem de composição, performance, reprodutibilidade, fallback e validação no runtime alvo.

## 6. Regras de independência

Uma linha futura pode reutilizar o núcleo compartilhado, mas não pode:

- alterar silenciosamente o significado dos campos 2D existentes;
- adicionar dados sem schema versionado e migração explícita;
- usar sockets, polígonos ou marcadores como substitutos de um sistema funcional;
- mudar baselines G/V/B sem decisão formal;
- acoplar a UI principal antes de testes de contrato e rollback;
- declarar suporte a Unity, Godot ou outra engine sem validação real do adapter.

Uma linha futura deve poder ser revertida sem remover ou corromper documentos P2D-COMP-01 válidos.

## 7. Critérios de priorização

A prioridade de implementação futura será decidida por valor de produto, risco e dependência, nesta ordem:

1. completar P2D-COMP-01;
2. corrigir bloqueadores de exportação e round-trip já identificados;
3. escolher uma linha vertical com valor demonstrável e contrato de destino claro;
4. implementar a linha inteira com validação, não apenas controles visuais;
5. somente depois abrir a próxima linha.

## 8. Decisão vigente

O trabalho começou formalmente em P2D-01 após P2D-00 ACCEPTED. P2D-01A está ACCEPTED e fechada conforme sua decisão, evidência e commit próprios; P2D-01B permanece pendente. As cinco linhas avançadas estão documentadas como PLANNED/BLOCKED BY P2D-COMP-01:

- EXT-TMAP-01 — Tilemap;
- EXT-COLL-01 — colisão de cenário;
- EXT-NAV-01 — NavMesh;
- EXT-ENT-01 — entidades/componentes/prefabs;
- EXT-FX-01 — iluminação e VFX.

Nenhuma delas deve ser apresentada ao usuário como disponível antes de sua própria aceitação formal.
