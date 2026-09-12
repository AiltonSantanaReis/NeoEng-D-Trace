# Gate de produção — Kit Modular de Floresta 2D

**ID:** `STAGE-POS-E13-MODELS-FOREST-2D-20260912`
**Status:** `IN_PROGRESS`
**Data de início:** 2026-09-12
**Baseline protegida:** `checkpoint/canonical-post-e13-pre-gizmo-20260912`
**Gizmo:** `DEFERRED`
**Editor canônico:** protegido, sem alteração nesta etapa

## Objetivo

Produzir o primeiro lote de modelos proprietários realmente útil para criar
cenários 2D do zero, sem remover ou substituir o piloto atual. O lote deverá
ser modular, pesquisável por miniaturas e preparado para uso em fundo, meio e
frente do parallax.

## Direção visual inicial

O lote parte da linguagem observada no piloto `Floresta`: ilustração pintada à
mão, silhueta clara, iluminação quente superior esquerda, recorte transparente
e leitura em vista lateral. Essa escolha mantém continuidade visual, mas não
aprova automaticamente os seis assets existentes para distribuição.

## Lote de produção proposto

### Terreno e tileset

- topo de grama, terra, pedra e lama;
- centro repetível, bordas, quatro cantos, rampas e plataformas;
- variações de transição entre grama, terra e água;
- regras de encaixe, escala e baseline documentadas.

### Props de composição

- ponte modular, cerca, placa, caixa, escada, toco e lanterna;
- versões de frente e de fundo quando a profundidade exigir;
- pivô de base consistente e indicação de colisão sugerida.

### Vegetação e foreground

- árvores pequenas, médias e grandes;
- arbustos alternativos, capim, flores e folhas de primeiro plano;
- pelo menos duas silhuetas úteis por família para evitar repetição evidente.

## Contrato de entrada

Cada master deverá chegar acompanhado de:

- formato e dimensões declarados;
- canal alpha verificável e bordas sem halo não intencional;
- nome comum, ID estável, categoria, tags e descrição em português;
- pivô, baseline, escala relativa e papel de parallax;
- proveniência, licença, ferramenta de criação e referência de estilo;
- thumbnail para o catálogo e preview em fundo quadriculado;
- hash SHA-256 antes de entrar no manifesto.

## Gates obrigatórios

1. **Master artístico:** silhueta, proporção, iluminação e coerência com o
   piloto aprovadas por inspeção humana.
2. **Higiene técnica:** alpha, bounding box, dimensões, borda, decodificação e
   ausência de arquivo auxiliar acidental.
3. **Manifesto:** IDs, categorias, tags, descrição, proveniência, licença e
   hash vinculados sem sobrescrever o piloto.
4. **Catálogo:** thumbnail, busca em português, preview e descrição legíveis.
5. **Fluxo nativo:** abrir pacote, selecionar, visualizar, importar, arrastar
   para moldura, transformar, salvar e reabrir.
6. **Composição:** usar pelo menos um asset em cada moldura de parallax e
   confirmar que o resultado não altera o contrato do editor canônico.
7. **Export/runtime:** declarar capability por engine; só marcar suporte após
   evidência da versão e pipeline exatos.
8. **Falha:** asset ausente, hash adulterado, licença ausente e formato
   incompatível devem falhar de forma explícita e recuperável.

## Estado atual do gate

- definição do lote: `PASS`;
- baseline de proteção: `PASS`;
- gizmo fora do escopo: `PASS`;
- masters novos: `PENDING_EVIDENCE`;
- thumbnails novas: `PENDING_EVIDENCE`;
- manifesto de distribuição: `PENDING_EVIDENCE`;
- fluxo nativo do lote novo: `PENDING_EVIDENCE`;
- runtime externo: `PENDING_EVIDENCE`;
- aprovação humana do pacote: `PENDING_EVIDENCE`.

Nenhum arquivo de modelo novo é promovido pelo simples fato de existir. Até os
gates passarem, o catálogo atual permanece intacto e o pacote continua interno.

## Dependências

- [Checkpoint canônico pré-gizmo](CHECKPOINT_CANONICAL_PRE_GIZMO_20260912.md)
- [Auditoria do catálogo piloto](AUDITORIA_MODELOS_PILOTO_E_PLANO_PRODUCAO_POS_E13_20260912.md)
- [Matriz de limites Godot/Unity](MATRIZ_LIMITES_ENGINES_GODOT_UNITY_POS_E13_20260912.md)
- [Governança de integridade](../GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md)

