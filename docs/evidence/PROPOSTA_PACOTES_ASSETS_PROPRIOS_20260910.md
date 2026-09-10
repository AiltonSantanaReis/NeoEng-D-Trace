# Pacotes próprios de assets — proposta pós-E13

Estado: IN_PROGRESS. Data: 2026-09-10.
Base inspecionada: 8c14aac8c4dfcc7b30d2c966dc401845090c9033.
Escopo deste documento: análise, especificação e acompanhamento do lote adicional pós-E13.
Autoridade: solicitação do usuário para analisar produção e disponibilização de pacotes próprios com miniaturas.

Dependências: [governança](../GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md),
[base pós-E13](BASE_ATIVA_POS_E13_2026-09-09.md),
[política de origem dos assets](../DECISAO_P2D_01_ASSETS_ORIGINAIS_E_IMPORTACAO_2026-08-29.md).
E13 permanece concluído conforme a decisão do usuário; o novo catálogo é um lote adicional.

## Diagnóstico confirmado em código

- `src/core/scene_asset_library.py`: importação externa com cópia controlada, hash, caminhos relativos, deduplicação de arquivo e diagnóstico de integridade. Reutilizar esse fluxo.
- `src/ui/scene_asset_panel.py`: lista de assets já importados, ícones reduzidos a 40 × 40, filtros Raster/Vetorial e busca por ID/caminho. O refresh calcula hashes e decodifica imagens de forma síncrona, com nova decodificação para o ícone; ampliar o catálogo sem mudar essa estratégia pode prejudicar a interação.
- O arraste usa `application/x-neoeng-scene-asset` com ID de um asset do documento. Um item do catálogo ainda não importado precisa primeiro virar asset do projeto; não pode ser tratado como ID já existente.
- `src/ui/tileset_authoring_panel.py`: um destino fixo `assets/tilesets/scenario`, listagem textual de tiles e rótulos como Tile width/Spacing em inglês. Pacotes múltiplos precisam de destinos próprios e mapeamento explícito para o tilemap.
- `packaging/NeoEng-D-Trace.spec`: a lista explícita de dados inclui o ícone de marca. A inclusão de pacotes e miniaturas na build precisa ser implementada e comprovada fora do checkout.
- Persistem mensagens em inglês na biblioteca. A localização completa do novo fluxo deverá incluir diálogos, estados, mensagens, tooltips e menus.

Essas constatações são de inspeção de código, não testes de execução nesta análise. A auditoria anterior não comprova o futuro catálogo.

## Direção de produto e produção

Produzir pequenas coleções coesas, cada uma capaz de montar uma cena utilizável. Priorizar uma identidade 2D estilizada, perspectiva lateral, escala e iluminação consistentes. Pixel art e isometria devem ser coleções separadas, com contratos próprios de escala e câmera.

| Coleção proposta | Conteúdo inicial alvo | Uso |
|---|---|---|
| Floresta | 6 planos de parallax, 20 elementos de vegetação/rochas, 24 peças de terreno, 1 cena exemplo | Plataforma, exploração, cenas naturais |
| Ruínas | 6 planos, 20 módulos/objetos arquitetônicos, 24 peças de terreno, 1 cena exemplo | Templos, vilas antigas, aventura |
| Cidade futurista | 6 planos, 20 módulos/objetos urbanos, 24 peças de terreno, 1 cena exemplo | Cidade, indústria, ficção científica |

Nomenclatura definida pelo usuário: usar nomes comuns e descritivos do conteúdo nos pacotes e assets. Aplicar essa regra às próximas coleções, às miniaturas e à busca.

Quantidades são metas de produção, não inventário entregue. Variações de cor não devem inflar a contagem de peças distintas. Começar com um piloto de Floresta: 3 planos, 6 objetos, 9 peças de terreno e uma composição real. Validar a direção visual e a montagem antes de multiplicar a produção.

Processo: guia visual por coleção → arquivos mestres editáveis → exportações individuais → validação técnica → composição de exemplo no editor → revisão visual → empacotamento versionado. Preservar mestres, histórico e identificação da origem de cada peça. Conteúdo assistido por IA deve registrar essa origem e passar por acabamento/revisão; não anunciar exclusividade jurídica apenas por ter sido gerado.

Os pacotes devem registrar autoria, ferramentas, versão, hash e termos de uso. A licença de distribuição ao usuário precisa esclarecer uso comercial nos jogos, modificações e redistribuição de arquivos avulsos; não pressupor termos aprovados nem incluir material de terceiros sem documentação.

## Critérios de qualidade

- Objetos: PNG RGBA com transparência limpa, escala consistente, pivô documentado e espaço de segurança para evitar cortes; manter mestres em resolução superior à exportação.
- Parallax: planos separados com dimensão, profundidade sugerida e indicação de repetição. Validar bordas repetidas em composição 3 × 3 e movimento da câmera; não derivar planos por recortes arbitrários de uma imagem achatada.
- Terreno: grade inicial de 64 px para a coleção estilizada, atlas com margem/extrusão compatíveis com o consumidor e encaixes testados em cantos, bordas e junções. Não afirmar autotiling sem contrato e teste do editor.
- Prévia fiel ao asset entregue: checkerboard para transparência, sem distorcer proporção. Cena demonstrativa identifica os elementos efetivamente incluídos.
- Presets de partículas/luz e áudio entram em lote posterior, vinculados às capacidades reais do editor. Áudio requer prévia acionada pelo usuário e origem registrada.
- Avaliar legibilidade a 100%, em miniatura e na cena em movimento; rejeitar halos, emendas, detalhes deformados, perspectiva incoerente e elementos que não se combinam.

## Catálogo e experiência proposta

Adicionar “Pacotes NeoEng” junto à biblioteca existente. Exibir capas das coleções e grade de miniaturas de 128–192 px, com tamanho ajustável, nome legível, categoria, busca por nome/tags e estado de instalação. Manter acesso à lista técnica atual.

Fluxo: abrir Biblioteca → Pacotes NeoEng → escolher coleção → selecionar miniatura → examinar prévia/dimensões/transparência → “Adicionar ao projeto” → arrastar para a moldura → ajustar → salvar → fechar e reabrir. Se o projeto não tiver pasta, solicitar salvamento no momento da importação; a navegação do catálogo permanece disponível.

Arraste direto do catálogo pode ser uma conveniência posterior: importar e inserir como uma operação transacional, respeitando molduras bloqueadas, cancelamento e desfazer/refazer. Oferecer também inserção por botão/teclado. Instalar pacote e importar conteúdo para uma cena são ações distintas.

## Distribuição e ciclo de vida

Incluir um pacote inicial compacto na build, utilizável offline. Distribuir expansões como arquivos de pacote versionados importáveis localmente; catálogo remoto e atualizações automáticas são evolução posterior, não pré-requisito.

Cada pacote possui manifest com `schema_version`, `pack_id`, `version`, nome/descrição localizados, compatibilidade mínima, licença, origem, dependências e entradas com ID estável, categoria, tags, dimensões, hash, caminho e miniatura. IDs de origem do pacote não substituem IDs locais de cena.

Instalar versões lado a lado em diretório de conteúdo do usuário; tratar o conteúdo embutido como somente leitura. Validar manifesto, caminhos, hashes e limites de expansão antes de promover uma instalação temporária. SHA-256 verifica integridade, não autenticidade do fornecedor.

Ao usar uma peça, copiar para o projeto pelo fluxo controlado existente e registrar a proveniência do pacote em extensão versionada ou registro auxiliar compatível. Atualizar/desinstalar pacote não deve modificar arquivos já importados. Conteúdo alterado localmente não pode ser substituído silenciosamente.

Miniaturas devem ser pré-geradas e carregadas sob demanda, com cache limitado identificado por hash/tamanho/versão do gerador. Hash completo e leitura do original pertencem à instalação/importação/verificação explícita, não a cada tecla da busca. Decodificação em background deve entregar imagens ao thread de UI para apresentação Qt.

## Impacto e sequência de implementação

| ID proposto | Entrega | Risco/aceite |
|---|---|---|
| PACK-01 | Piloto artístico + manifesto/proveniência | Peças individuais e cena exemplo revisadas; origem documentada |
| PACK-02 | Leitor/instalador local de pacotes | Rejeitar caminhos externos, pacote incompleto e hash inválido; instalação anterior preservada |
| PACK-03 | Grade de miniaturas integrada à biblioteca | Busca, seleção, prévia e teclado responsivos; biblioteca existente preservada |
| PACK-04 | Importação/inserção no projeto | Portabilidade, deduplicação, destino explícito, lock e undo/redo; zero dependência da instalação original |
| PACK-05 | Distribuição nativa | Build fora do checkout, piloto offline, capturas reais e regressão completa |
| PACK-06 | Expansão das três coleções | Qualidade do piloto aplicada, tamanho do pacote medido, cenas completas montadas |

IDs são propostos; conferir colisões no registro oficial antes de implementar. Módulos de maior impacto: biblioteca, sessão/documento, integração do editor, tileset/tilemap e empacotamento. Evitar reescrever schemas existentes; qualquer extensão exige registro de mudança e compatibilidade retroativa. Não inserir arquivos de pacote em destinos fixos que sobrescrevam tilesets do usuário.

## Evidência exigida para entrega

Capturar cliques reais no binário novo: descobrir coleção, pesquisar, pré-visualizar, importar, posicionar, desfazer/refazer, salvar, encerrar e reabrir. Confirmar render e exportação com conteúdo do projeto, sem resolver a origem externa. Testar pacote ausente/corrompido, conflito de versão, importação repetida e projeto existente.

Inspecionar miniaturas e transparência em 100%, 150% e 200% de DPI. Medir tempo de abertura/busca e memória num catálogo representativo de 1.000 entradas antes de fixar orçamento de desempenho. A aprovação exige resultado observado, artefatos, hashes, commit e limitações; a existência de imagens ou cartões não basta.

## Estado do lote iniciado em 2026-09-10

O primeiro incremento foi implementado de forma aditiva: leitor somente leitura do
manifesto, catálogo Qt integrado à Biblioteca, busca tolerante a acentos, prévia,
importação pelo fluxo existente e cópia de seis objetos do piloto Floresta. Os
arquivos estão em `assets/scene/packs/floresta/`, com hashes no manifesto e
proveniência em `PROVENIENCIA.md`. O catálogo não altera o registro de assets da
cena até o usuário acionar `Adicionar ao projeto`.

Estado de aceite deste incremento: `PENDING_EVIDENCE`.
A build limpa foi auditada e o fluxo nativo por cliques reais foi capturado para
catálogo, busca, prévia, importação, inserção por clique, salvamento, fechamento e
reabertura. O arraste direto ainda falha na execução observada e o menu contextual
do editor não foi comprovado em português; por isso não há `PASS` global. O piloto
completo (3 planos, 6 objetos, 9 peças de terreno e composição real) ainda não foi
entregue; os seis objetos são somente a primeira parte dessa meta. Ruínas e Cidade
futurista continuam `PLANNED`.
