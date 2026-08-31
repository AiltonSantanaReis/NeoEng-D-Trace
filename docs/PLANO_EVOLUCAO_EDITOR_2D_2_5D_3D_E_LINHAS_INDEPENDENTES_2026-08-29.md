# NeoEng-D-Trace — Plano de evolução do editor

## Composição 2D, caminho 2.5D/3D e linhas independentes

**Status:** plano aprovado para execução local
**Data:** 2026-08-29 (UTC-03)
**Documento normativo principal:** docs/NEOENG_EDITOR_COMPOSICAO_2D_NORMATIVO_2026-08-27.md
**Registro de adoção:** docs/EVIDENCIA_P2D_00_RECONCILIACAO_2026-08-29.md
**Decisão P2D-01A:** docs/DECISAO_P2D_01_ASSETS_ORIGINAIS_E_IMPORTACAO_2026-08-29.md
**Evidência P2D-01A:** docs/EVIDENCIA_P2D_01A_ASSETS_IMPORTACAO_E_RENDERIZACAO_2026-08-29.md
**Evidência P2D-01B:** docs/EVIDENCIA_P2D_01B_BIBLIOTECA_LIFECYCLE_2026-08-29.md
**Decisão P2D-02A:** docs/DECISAO_P2D_02A_ORDEM_CAMADAS_LOCKING_2026-08-29.md
**Evidência P2D-02A:** docs/EVIDENCIA_P2D_02A_ORDEM_CAMADAS_LOCKING_2026-08-29.md
**Decisão P2D-02B:** docs/DECISAO_P2D_02B_GRUPOS_HIERARQUIA_ISOLAMENTO_2026-08-29.md
**Evidência P2D-02B:** docs/EVIDENCIA_P2D_02B_GRUPOS_HIERARQUIA_ISOLAMENTO_2026-08-29.md
**Decisão P2D-02 (fechamento):** docs/DECISAO_P2D_02_FECHAMENTO_2026-08-29.md
**Evidência P2D-02 (consolidação):** docs/EVIDENCIA_P2D_02_CONSOLIDACAO_2026-08-29.md
**Decisão P2D-03:** docs/DECISAO_P2D_03_NAVEGACAO_SELECAO_PRODUTIVIDADE_2026-08-29.md
**Auditoria P2D-03:** docs/EVIDENCIA_P2D_03_AUDITORIA_BASELINE_2026-08-29.md
**Fechamento P2D-03C:** docs/EVIDENCIA_P2D_03C_FECHAMENTO_2026-08-30.md
**Decisão P2D-04:** docs/DECISAO_P2D_04_PERSISTENCIA_RECOVERY_PREVIEW_EXPORT_COORDENADAS_2026-08-30.md
**Evidência P2D-04:** docs/EVIDENCIA_P2D_04_POSTCOMMIT_2026-08-30.md
**Publicação P2D-04:** docs/EVIDENCIA_P2D_04_PUBLICACAO_2026-08-30.md
**Decisão P2D-05:** docs/DECISAO_P2D_05_PERFORMANCE_LIMITES_FORMATOS_ERROS_2026-08-30.md

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
| P2D-02 | ordem visual, camadas, grupos e isolamento | ordem observável, persistente e editável; ACCEPTED / CLOSED |
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

### 3.4 Abertura P2D-02A

P2D-02A foi aberto após auditoria do fluxo de usuária e cobre ordem visual efetiva, visibilidade e bloqueio seguro no editor profissional. A subetapa foi aceita e fechada no commit `2118266df6daeafee8eafa82e80c953abc866b00`, com requalificação pós-commit e auditoria nativa Windows documentadas na evidência P2D-02A. Grupos, hierarquia/membership e isolamento permanecem reservados à subetapa P2D-02B e não são considerados implementados.

### 3.5 Abertura P2D-02B

P2D-02B foi aberta a partir do checkpoint limpo d152b214b1bccb717911001396936c1f93b23714 e fechada no commit af02f3ef513487bd176c939085fea0ca56a7da6b. A decisão técnica foi implementada exclusivamente no editor profissional, preservando o modelo legado, o schema V1 e os baselines imutáveis. A requalificação pós-commit, as auditorias Qt Windows/offscreen e a evidência aceita estão registradas em EVIDENCIA_P2D_02B_GRUPOS_HIERARQUIA_ISOLAMENTO_2026-08-29.md.
### 3.6 Abertura formal P2D-03

P2D-03 foi aberta após a auditoria somente de leitura do checkpoint `3c09f37c140f8a807b8b9006aa095db37729129b`, com branch e remoto alinhados e tracked tree limpo antes da documentação. A auditoria confirmou que o editor profissional já possui seleção básica, multisseleção por Ctrl, transformação por mouse/gizmo, bloqueios, grupos/camadas e undo/redo. Também confirmou que nudge por teclado, duplicate, copy/paste, marquee/select-all e navegação explícita de zoom/pan/fit ainda não estão fechados no viewport profissional; recursos equivalentes do `CanvasView` pertencem ao legado e não contam para P2D-03.

A decisão formal e a evidência da auditoria definem invariantes de identidade/seleção, transações, bloqueios, clipboard, nudge, navegação, foco, limites, testes, evidências e decisões de UX que exigem aceite antes do código. O status de P2D-03 é `OPEN — decisão/contrato`; nenhuma alteração de produto foi feita nesta abertura.

### 3.7 Fechamento P2D-03A

P2D-03A foi implementada exclusivamente no fluxo profissional e fechada como
`ACCEPTED / CLOSED` após a revisão humana do proprietário. O commit de código é
`17c3cbcdb244419fc6b69b907652983dac36432a`, a documentação pós-commit é
`13c8b6a0b39d7411d5f2ee00dc901aca3a3982d3` e a evidência consolidada está em
`EVIDENCIA_P2D_03A_SELECAO_FOCO_2026-08-29.md`. A entrega cobre foco inicial,
seleção por clique/Ctrl/Shift, clique vazio, marquee, Ctrl+A, elegibilidade por visibilidade e preservação do drag existente. P2D-03 permanece aberta para o fechamento de P2D-03C; P2D-03B está ACCEPTED / CLOSED e P2D-03C foi aberta posteriormente em ciclo próprio de contrato e qualificação.

### 3.8 Abertura formal P2D-03B

P2D-03B foi aberta no checkpoint limpo
`24a3178d52f1096e55c73b40daf196bccfe0d8cc`, após auditoria somente de leitura
das APIs de sessão, modelo, schema, viewport, inspector e janela profissional.
O sublote cobre nudge, duplicate, delete por seleção, copy/paste versionado e
undo/redo contextual. A decisão registrada propõe offset `(16, 16)` em unidades
de mundo, allocator de IDs novos, bloqueio atômico, preservação explícita de
referências e clipboard sem bytes/caminhos externos.

O proprietário aceitou explicitamente o contrato de P2D-03B com `P2D-03B ACEITO — contrato de operações, histórico e clipboard` e posteriormente registrou o aceite humano final da build com `aceito` em 30/08/2026. A implementação ficou limitada ao sublote, foi requalificada e está registrada como `ACCEPTED / CLOSED` em `EVIDENCIA_P2D_03B_IMPLEMENTACAO_2026-08-29.md`. P2D-03A, C3, G/V/B e o editor legado permanecem intactos; P2D-03C será conduzida pelo ciclo documental próprio abaixo.

### 3.9 Fechamento formal P2D-03C

P2D-03C foi aberta a partir do checkpoint limpo `78f773583b0277fa9b970d1f849538b4fa3fdcc6`, após auditoria somente de leitura do viewport, da janela profissional, da sessão, do modelo, da projeção e dos controles do inspector. O proprietário aceitou o contrato com `P2D-03C ACEITO — contrato de navegação, fit e estados visuais` e, após a revisão final, registrou `P2D-03C ACEITO — entrega final` em 30/08/2026. A implementação foi concluída no commit técnico `58674dde87ba94082e84f066ebda21d144da65cd`, com requalificação pós-commit, captura, auditoria visual, comparação, build portátil, seal e verificação independente documentados em `EVIDENCIA_P2D_03C_FECHAMENTO_2026-08-30.md`. O reteste humano da transição Fit/Focus não reproduziu a lentidão relatada. O estado é `ACCEPTED / CLOSED`. C3, G/V/B, schema, legado e os sublotes P2D-03A/B permanecem fora da mutação.

### 3.10 Fechamento P2D-04 e abertura P2D-05

P2D-04 foi tecnicamente qualificada no commit b9e9043f98c58752e8e322a7627b4d17e145d6d3, recebeu correções de governança e cobertura nos commits posteriores da mesma linha, e foi publicada pela PR #163. O merge commit efetivo em main é f55b07b85ef2cf65160f2c10ffac5e63b45732ac; os checks protegidos Linux/Windows passaram e a sincronização pós-merge foi reproduzida localmente. O snapshot técnico e o adendo de publicação são mantidos separados para preservar a cronologia.

P2D-05 foi aberta formalmente neste checkpoint, exclusivamente para performance, limites, formatos e erros da fundação já existente. A decisão está em DECISAO_P2D_05_PERFORMANCE_LIMITES_FORMATOS_ERROS_2026-08-30.md e foi aceita pelo proprietário em 30/08/2026. O status atual é ACCEPTED FOR IMPLEMENTATION — qualificação pendente; a implementação controlada está isolada na branch local `p2d-05-quality-hardening`, sem commit técnico nem publicação remota autorizados. Nenhum workstream de tilemap, colisão, NavMesh, entidades/prefabs ou FX pode ser iniciado por esta abertura.

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

O trabalho começou formalmente em P2D-01 após P2D-00 ACCEPTED. P2D-01A está ACCEPTED e fechada conforme sua decisão, evidência e commit próprios; P2D-01B está ACCEPTED e fechada conforme sua decisão, evidência, gates automatizados e aceite humano; P2D-02 está ACCEPTED e fechada conforme suas decisões, evidências, gates e commits; P2D-03C está ACCEPTED / CLOSED; P2D-04 está ACCEPTED / CLOSED no merge f55b07b8; P2D-05 está ACCEPTED FOR IMPLEMENTATION — qualificação pendente. As cinco linhas avançadas continuam documentadas como PLANNED/BLOCKED BY P2D-COMP-01:

- EXT-TMAP-01 — Tilemap;
- EXT-COLL-01 — colisão de cenário;
- EXT-NAV-01 — NavMesh;
- EXT-ENT-01 — entidades/componentes/prefabs;
- EXT-FX-01 — iluminação e VFX.

Nenhuma delas deve ser apresentada ao usuário como disponível antes de sua própria aceitação formal.

## 9. Emenda obrigatória de escopo do produto — 2026-08-30

A solicitação explícita do proprietário do produto registrada em 30/08/2026
define que o resultado final não é apenas uma fundação de composição 2D nem um
fluxo de importação. O documento
docs/REQUISITOS_EDITOR_CENARIOS_COMPLETO_2026-08-30.md passa a ser a fonte
prevalente para o escopo final.

O rótulo P2D-COMP-01 permanece preservado como identificação histórica e
operacional da fundação de composição 2D já trabalhada. Seus sublotes aceitos
não constituem, isoladamente, o aceite do produto final. A conclusão do produto
exige todas as capacidades obrigatórias do documento prevalente, incluindo
autoria a partir de cena vazia, pacote proprietário de assets disponível por
padrão, tilemaps completos, colisão e navegação de cenário, entidades e
prefabs, iluminação, sombras, partículas, pós-processamento, shaders editáveis,
efeitos em tempo real, preview equivalente ao runtime e round-trip visual
comprovado com as engines de destino.

As linhas EXT-TMAP-01, EXT-COLL-01, EXT-NAV-01, EXT-ENT-01 e
EXT-FX-01 deixam de ser interpretáveis como melhorias cosméticas ou
facultativas: são workstreams obrigatórios para o produto final. Cada uma
deve ter contrato próprio, implementação funcional, testes unitários e de
integração, fluxo de usuário, evidência visual e aceite formal. Metadados,
marcadores, sockets, sidecars ou importação estrutural não substituem a
capacidade funcional correspondente.

Até o aceite integral, o produto permanece OPEN / INCOMPLETE e nenhuma build
ou release poderá ser apresentada como editor profissional completo de
cenários.
