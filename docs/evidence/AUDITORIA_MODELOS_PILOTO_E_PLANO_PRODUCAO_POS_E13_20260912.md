# Auditoria do piloto de modelos e plano de produção pós-E13

**ID:** `AUDIT-POS-E13-MODEL-CATALOG-20260912`
**Status:** `IN_PROGRESS`
**Data:** 2026-09-12
**Escopo:** catálogo proprietário, miniaturas e modelos para o Editor de Cenário
**Pacote auditado:** `assets/scene/packs/floresta` versão `0.1.0-piloto`

## Resultado executivo

O catálogo atual é um piloto de seis sprites PNG para floresta 2D. Ele é útil
para exercitar a biblioteca, miniaturas, importação e composição, mas ainda não
é um pacote profissional de distribuição. Não há modelo 3D, GLB, FBX, tileset
modular, prop arquitetônico ou variação de um mesmo asset no pacote.

O piloto será preservado sem alteração. A próxima frente deve produzir masters
novos e complementares, revisar as máscaras existentes e só depois publicar uma
versão de pacote com licença, proveniência e validação de runtime declaradas.

## Inventário observado

| ID | Categoria | Dimensão | Observação objetiva |
|---|---|---:|---|
| `pedra` | Rochas | 1254×1254 | conteúdo toca o limite esquerdo do canvas |
| `arbusto` | Vegetação | 1254×1254 | silhueta ampla, sem variante de escala |
| `tronco` | Madeira | 1536×1024 | `alpha_max=254`, nenhum pixel totalmente opaco |
| `samambaia` | Vegetação | 1254×1254 | conteúdo toca o limite inferior do canvas |
| `cogumelos` | Vegetação | 1254×1254 | cluster único, sem variações |
| `pinheiro` | Árvores | 1254×1254 | raízes tocam o limite inferior do canvas |

Os seis arquivos possuem canal alpha e os hashes do manifesto conferem com os
arquivos auditados. O fundo preto observado em uma visualização é a cor de
composição do visualizador para transparência, não uma conclusão de que exista
fundo preto no PNG. A inspeção de bordas continua necessária porque não há
masters editáveis disponíveis no repositório.

O próprio manifesto marca o pacote como piloto, acabamento em revisão e licença
de distribuição pendente. Portanto o estado de publicação é `PENDING_EVIDENCE`.

## Lacunas para um pacote profissional

1. **Composição:** não existe kit de chão, parede, borda, canto, plataforma ou
   tileset com regras de encaixe.
2. **Leitura de cena:** faltam foreground, midground e background compatíveis,
   com escala relativa e pivôs de base consistentes.
3. **Modularidade:** faltam variantes pequenas/médias/grandes, versões espelhadas
   aprovadas, estados quebrado/aceso/fechado e objetos repetíveis.
4. **Autoria:** faltam props que permitam criar uma cena do zero sem depender de
   uma única imagem principal.
5. **Profundidade:** faltam assets desenhados para os três planos de parallax e
   modelos 2.5D/3D com material, escala e orientação documentados.
6. **Distribuição:** a licença, a origem dos masters e a política de conteúdo
   assistido por IA ainda não estão aprovadas para uso público.

## Linha de produção recomendada

### Pacote 1 — kit modular de floresta 2D

Produzir primeiro, porque é o conjunto com maior retorno imediato no editor:

- terreno: topo de grama, terra, pedra, lama, água e transições;
- peças de tile: centro, bordas, quatro cantos, rampas e plataformas;
- composição: cerca, ponte, escada, placa, caixa, toco e ruína pequena;
- vegetação: três tamanhos de árvore, três arbustos, capim, flores e folhas de
  foreground;
- atmosfera: névoa, vaga-lumes, folhas e partículas de ambiente separadas dos
  sprites estáticos.

Cada família deve ter uma miniatura de catálogo, pivô e baseline definidos,
escala relativa documentada e uma variante suficiente para evitar repetição
visual evidente.

### Pacote 2 — kit 2.5D híbrido

Depois do kit 2D passar pelo fluxo real, produzir modelos leves para testar
profundidade e orientação:

- rocha modular, tronco, ponte, casa pequena e ruína;
- versões GLB com materiais simples, normal opcional e origem consistente;
- thumbnail frontal, vista 3/4 e indicação de eixo/pivô;
- LOD ou limite de complexidade documentado;
- compatibilidade marcada como `VERTICAL_SLICE_ONLY` até haver runtime real.

### Pacote 3 — biblioteca de variações

Somente após os dois primeiros pacotes: estados, variantes de iluminação,
danos, sazonalidade e combinações que possam ser sincronizadas com timeline,
partículas e luzes sem duplicar indevidamente o manifesto.

## Contrato de cada novo asset

Nenhum asset novo entra no catálogo apenas por existir um arquivo. O registro
deverá conter:

- ID estável, nome comum, categoria, tags e descrição em português;
- formato, dimensão, escala, pivô, baseline e uso recomendado por camada;
- hash SHA-256, origem do master, ferramenta de criação e licença;
- thumbnail gerada pelo próprio catálogo e preview em fundo quadriculado;
- validação de alpha, bordas, dimensões, decodificação e integridade;
- teste de importação, arraste para moldura, transformação, salvar/reabrir,
  undo/redo e exportação quando a capacidade existir;
- capability de destino: `NATIVE`, `ADAPTED`, `METADATA_ONLY`, `FALLBACK` ou
  `UNSUPPORTED`, conforme a matriz de engines.

## Gates antes da distribuição

1. revisão artística de silhueta, escala, iluminação e repetição;
2. validação técnica de alpha, borda, tamanho, nome, hash e manifesto;
3. miniatura e busca em português no catálogo nativo;
4. fluxo real de usuário: abrir pacote, selecionar, visualizar, importar,
   arrastar, posicionar em parallax, salvar e reabrir;
5. exportação/runtime conforme a capability declarada;
6. teste de falha para asset ausente, hash adulterado, licença ausente e
   pipeline incompatível;
7. captura nativa, relatório, commit e aprovação humana.

Até esses gates passarem, o catálogo permanece interno e o piloto não será
reclassificado como produto final.

## Evidências usadas

- `assets/scene/packs/floresta/manifest.json`
- `assets/scene/packs/floresta/PROVENIENCIA.md`
- seis PNGs do diretório do pacote, inspecionados visualmente;
- análise real de dimensões, bounding box alpha, alpha mínimo/máximo e contagem
  de pixels;
- `tests/test_asset_packs.py`, que cobre descoberta, hash, dimensões, alpha,
  catálogo, importação, persistência, repetição, erro e ausência de projeto;
  execução Windows/Python 3.11.9 em 2026-09-12: `11 passed in 3.84s`.

## Dependências

- [Governança de integridade](../GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md)
- [Matriz de limites Godot/Unity](MATRIZ_LIMITES_ENGINES_GODOT_UNITY_POS_E13_20260912.md)
- [ADR do editor independente](../ADR_POS_E13_DEPRECACAO_EDITOR_INDEPENDENTE_20260912.md)
