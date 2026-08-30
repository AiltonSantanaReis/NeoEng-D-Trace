# NeoEng-D-Trace — Requisitos obrigatórios do editor de cenários completo

**ID:** PRODUCT-SCENE-FULL-01
**Status:** ESCOPO OBRIGATÓRIO / IMPLEMENTAÇÃO ABERTA
**Data:** 30/08/2026 (UTC-03)
**Autoridade:** solicitação explícita do proprietário do produto registrada nesta consolidação
**Documento prevalente:** este documento governa o escopo final do produto

## 1. Finalidade e precedência

Este documento transforma em requisito obrigatório de produto as capacidades
solicitadas para que o NeoEng-D-Trace seja uma ferramenta profissional de
desenvolvimento de cenários para usuários comuns, artistas e desenvolvedores.

Ele não é uma evidência de implementação e não declara nenhuma capacidade como
entregue. Uma capacidade só poderá ser marcada como ACCEPTED quando estiver
funcional no fluxo de usuário, testada, evidenciada e validada nos destinos
de exportação aplicáveis.

O rótulo P2D-COMP-01 e seus sublotes aceitos são preservados como histórico
da fundação de composição 2D. Eles não constituem, isoladamente, a definição
do produto final. Este documento prevalece sobre qualquer redação que possa
interpretar tilemaps, autoria do zero, conteúdo proprietário, efeitos ou
round-trip visual como opcionais ou fora do objetivo final.

## 2. Regra de completude

Não será aceita implementação parcial, simulada ou apenas declarativa como
cumprimento de um requisito. Em particular, não são equivalentes à capacidade
final:

- botão sem fluxo funcional;
- marcador visual sem sistema executável;
- socket ou metadado sem renderização e comportamento;
- sidecar sem objeto funcional no destino;
- teste estrutural sem teste visual no runtime da engine;
- importação sem autoria, edição e persistência;
- exportação de dados sem exportação do objeto, malha, material, colisão ou
  efeito correspondente;
- fallback que oculte uma ausência de capacidade;
- aceite baseado apenas em código sem fluxo realizado pelo usuário.

Requisito não concluído permanece OPEN, BLOCKED ou NOT ACCEPTED. A ausência de
uma implementação não pode ser convertida em PASS por ajuste de tolerância,
alteração de auditor, redução de escopo informal ou linguagem ambígua.

## 3. Capacidades obrigatórias do produto final

### 3.1 Autoria de cenários e objetos

SCN-001 — O usuário deve conseguir criar um cenário novo e vazio
independentemente de importar um modelo, uma cena ou um projeto pré-existente.
O editor deve fornecer o fluxo de criação inicial, configuração de resolução,
coordenadas, câmera e salvamento.

SCN-002 — O usuário deve conseguir criar um objeto do zero dentro do editor,
incluindo primitivas e formas editáveis, sem depender de uma imagem previamente
importada.

SCN-003 — Objetos devem possuir transformação, pivot, escala, rotação,
camadas, grupos, hierarquia, visibilidade, bloqueio, seleção, duplicação,
remoção, histórico e persistência.

SCN-004 — O fluxo deve permitir composição real de um cenário, e não apenas
visualização ou organização de referências importadas.

### 3.2 Pacote proprietário de assets

ASSET-001 — O produto deve entregar um pacote de assets próprio, original ou
procedural, com qualidade suficiente para uso real pelo usuário.

ASSET-002 — O pacote deve conter, no mínimo, tiles, árvores, rochas,
construções, props, personagens, objetos interativos, materiais e ambientes
demonstrativos.

ASSET-003 — O pacote deve estar disponível por padrão no produto ou no
projeto inicial, sem depender de download ou importação manual para o primeiro
fluxo funcional.

ASSET-004 — Cada asset deve possuir manifesto de proveniência e licença,
incluindo identidade, origem, autor ou processo de geração, versão, hash,
permissão de redistribuição e restrições de uso.

ASSET-005 — Nenhum conteúdo de terceiros poderá ser incluído sem licença
compatível, registro de proveniência e verificação documental.

### 3.3 Tilemaps

TMAP-001 — Suporte a tilemaps com múltiplas camadas claramente separadas
para background, midground, foreground e camadas adicionais.

TMAP-002 — Grid configurável com snapping e resolução ajustável, incluindo
filosofias ortogonal, isométrica e hexagonal.

TMAP-003 — Paleta e seleção de tiles com pincel, balde de preenchimento,
borracha, seleção, retângulo, variação aleatória e operações determinísticas.

TMAP-004 — Autotiling e Rule Tiles devem posicionar bordas, quinas e
transições de terreno conforme as regras configuradas pelo usuário.

TMAP-005 — Todas as operações devem possuir undo/redo, persistência,
validação e exportação reproduzível.

### 3.4 Colisão e navegação

COLL-001 — Camada de colisão própria do cenário, separada dos objetos
visuais, com edição direta no viewport.

COLL-002 — Ferramentas para caixas, círculos, polígonos, segmentos/cadeias e
áreas de trigger, com seleção, criação, edição, duplicação e remoção.

COLL-003 — Validação obrigatória de degeneração, winding, auto-interseção,
vértices inválidos e compatibilidade com o formato de destino. O cenário só
poderá ser aplicado ou exportado quando os bloqueios forem resolvidos.

NAV-001 — Editor de NavMesh 2D com regiões caminháveis, obstáculos,
conexões, áreas especiais e validação visual.

NAV-002 — O resultado deve ser exportado e consumido pela engine de destino,
com evidência de navegação real, não apenas de dados armazenados.

### 3.5 Entidades, componentes e prefabs

ENT-001 — O usuário deve conseguir criar entidades e instâncias com
identidade, transform, componentes e propriedades editáveis.

ENT-002 — O editor deve oferecer agrupamento, hierarquia, tags, filtros,
isolamento, visibilidade e organização adequados para cenários complexos.

ENT-003 — Prefabs devem permitir criação, instanciação, atualização,
overrides controlados, aplicação, desvinculação e validação de referências.

ENT-004 — O modelo persistido deve ser versionado, migrável e exportável sem
perder entidades, componentes ou overrides.

### 3.6 Iluminação, partículas e efeitos

FX-001 — Iluminação real com luzes posicionáveis, parâmetros editáveis,
iluminação global, sombras e composição correta no viewport.

FX-002 — Partículas renderizadas, com emissão, forma, velocidade, vida,
cor, textura, variação, simulação e controle editável.

FX-003 — Pós-processamento configurável e visível no preview, com parâmetros
persistidos e resultado reproduzível.

FX-004 — Shaders editáveis ou configuráveis dentro do contrato do produto,
com compilação, diagnóstico e resultado visível.

FX-005 — Efeitos em tempo real, incluindo atualização de parâmetros,
animação/simulação e visualização equivalente ao runtime.

FX-006 — O preview do editor deve representar o resultado que será entregue
à engine, respeitando câmera, escala, ordenação, materiais, luzes, sombras,
partículas e pós-processamento.

Sockets, marcadores, sidecars e registros declarativos podem existir como
parte da implementação, mas não satisfazem estes requisitos sozinhos.

### 3.7 Imagem, vetorização e objeto exportável

VEC-001 — O usuário deve conseguir importar uma imagem e produzir contorno,
vértices e polígonos com detecção controlada.

VEC-002 — O usuário deve conseguir corrigir manualmente os resultados,
incluindo vértices, segmentos, formas, orientação, simplificação e validação.

VEC-003 — O fluxo deve permitir gerar colisões válidas a partir do contorno,
identificar precisamente problemas e impedir a aplicação de geometria inválida.

VEC-004 — O resultado deve tornar-se um objeto de cenário persistente,
editável e exportável, sem depender do arquivo original permanecer em um
caminho externo.

VEC-005 — A funcionalidade de contorno não substitui um sistema completo de
autoria vetorial; caso o produto ofereça formas livres, elas também devem ter
edição, validação, persistência e exportação completas.

### 3.8 Exportação e round-trip real

EXP-001 — Exportadores devem produzir os objetos efetivos da cena, incluindo
hierarquia, sprites ou malhas, materiais, transforms, pivots, colisões,
entidades, luzes, partículas, efeitos e demais recursos suportados.

EXP-002 — Exportar somente JSON, metadados ou sidecars não caracteriza a
exportação do cenário.

EXP-003 — Godot e Unity devem ser validados com projetos reais, executando o
fluxo de importação e renderização do objeto ou cenário exportado.

EXP-004 — A validação deve comprovar orientação, escala, pivot, textura,
material, hierarquia, colisão, iluminação, efeitos e aparência no runtime.

EXP-005 — Cada destino deve possuir testes positivos e negativos, captura
visual, logs, versão da engine, manifesto de artefatos e instruções de
reprodução sem caminhos pessoais.

### 3.9 Experiência para usuários comuns, artistas e desenvolvedores

UX-001 — Os fluxos principais devem ser descobríveis, coerentes e operáveis
por mouse e teclado.

UX-002 — Erros devem indicar o que ocorreu, qual objeto ou recurso foi
afetado e como corrigir, sem mensagens técnicas bloqueantes e vagas.

UX-003 — Todas as operações relevantes devem possuir undo/redo, estado
visual compreensível, confirmação adequada e recuperação segura.

## 4. Arquitetura para 2.5D e 3D

O núcleo 2D deve preservar extensibilidade para profundidade, ordenação,
câmera, parallax, escala por profundidade, materiais e coordenadas compatíveis
com 2.5D.

Uma futura linha 3D deve possuir viewport, hierarquia, mesh, material, UV,
normais, câmera, luz, animação e exportação próprios. O exportador GLB atual,
por si só, não transforma o produto em editor 3D e não pode ser usado como
substituto dessa linha.

## 5. Ordem obrigatória de execução

As implementações podem ser divididas em lotes, mas a ordem de aceite é:

1. contrato de escopo, governança, modelo de autoria e cena vazia;
2. objetos criados do zero, persistência, undo/redo e fluxo de usuário;
3. pacote proprietário de assets, disponibilidade padrão e manifesto de
   licença/proveniência;
4. tilemaps completos;
5. colisão própria do cenário;
6. NavMesh 2D;
7. entidades, componentes, grupos, hierarquia e prefabs;
8. iluminação, sombras, partículas, pós-processamento, shaders e VFX reais;
9. pipeline de imagem, vetorização, correção, colisão e objeto exportável;
10. exportação efetiva e round-trip visual em Godot e Unity;
11. aceitação final integral do produto.

As linhas existentes EXT-TMAP-01, EXT-COLL-01, EXT-NAV-01,
EXT-ENT-01 e EXT-FX-01 são workstreams obrigatórios relacionados a essa
ordem. Nenhuma delas poderá ser encerrada com controles visuais, metadata-only
ou uma implementação parcial.

## 6. Gates obrigatórios para cada etapa

Cada etapa deve conter:

- contrato de entrada, saída, invariantes e fronteira protegida;
- implementação funcional completa dentro do escopo da etapa;
- testes unitários, negativos, integração e regressão;
- fluxo real realizado como o usuário executaria;
- captura Windows/offscreen quando aplicável;
- auditoria visual e revisão humana;
- teste de persistência, recuperação e erro;
- exportação e round-trip nos destinos aplicáveis;
- manifesto, hashes, logs e instruções reproduzíveis;
- verificação de privacidade e ausência de caminhos pessoais, segredos e
  credenciais;
- commit identificado e requalificação pós-commit.

Se qualquer item estiver ausente, a etapa não é concluída e a próxima não
deve ser iniciada.

## 7. Estado factual na data deste documento

P2D-01A, P2D-01B, P2D-02 e P2D-03A/B/C possuem aceites de subetapa
registrados. Eles comprovam uma fundação de composição por objetos, biblioteca
de assets, organização, seleção, edição e navegação.

Esses aceites não comprovam ainda:

- editor independente de cena vazia;
- criação livre de objetos sem asset importado;
- pacote proprietário de conteúdo disponível por padrão;
- tilemap completo;
- colisão própria de cenário;
- NavMesh;
- entidades/componentes/prefabs completos;
- iluminação, sombras, partículas, pós-processamento, shaders editáveis ou
  VFX em tempo real;
- round-trip visual efetivo em Godot e Unity;
- aceite integral do editor profissional de cenários.

O estado correto do produto é OPEN / INCOMPLETE até que todos os requisitos
deste documento sejam aceitos individualmente e no conjunto.

## 8. Imutáveis e proibições

C3, baselines aprovadas, contratos históricos, evidências aceitas, tolerâncias
e auditores permanecem imutáveis. Mudança de requisito, redução de escopo,
alteração de baseline ou remoção de evidência exige decisão formal.

É proibido:

- apresentar uma fundação como produto completo;
- chamar dados exportados de objeto renderizado sem prova no destino;
- chamar sockets ou marcadores de iluminação/VFX funcionais;
- declarar asset proprietário sem licença e proveniência;
- aprovar etapa com funcionalidade parcial;
- publicar caminhos pessoais, segredos ou credenciais;
- avançar enquanto houver gate, teste, evidência ou fluxo de usuário ausente.

## 9. Regra final de aceite

O produto só poderá ser apresentado como editor profissional completo de
cenários quando o fluxo integral — criar cena vazia, criar ou inserir assets,
compor, editar, organizar, iluminar, simular efeitos, validar colisões,
salvar, recuperar, exportar e abrir/renderizar nas engines de destino — for
executado com sucesso e comprovado por testes, evidências e revisão humana.

Até lá, qualquer descrição pública deve declarar explicitamente as capacidades
aceitas, as capacidades abertas e as limitações restantes.
