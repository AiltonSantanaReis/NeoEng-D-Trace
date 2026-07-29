# Etapa 0.6N1A — Correções de responsividade, localização e layout

Data: 27 de julho de 2026.

## Origem da correção

A validação visual da Etapa 0.6N1 revelou três defeitos reais:

1. o Laço Magnético podia bloquear ou tornar a interface lenta durante o cálculo;
2. o diálogo de exportação, a pré-visualização de exportação e o Visualizador de Máscara permaneciam em inglês após selecionar português;
3. textos da paleta de ferramentas podiam ultrapassar ou ser cortados pela caixa, especialmente com escala de tela e fontes maiores.

A Etapa 0.6N1 não deve ser considerada visualmente validada enquanto esta correção não passar pelos testes automáticos e pela validação manual no Windows.

## Alterações funcionais controladas

### Laço Magnético

- preparação de Sobel/Canny e do mapa de bordas movida para worker quando o canvas é um widget Qt real;
- pré-visualização calculada por um A* reduzido e limitado, destinado somente ao movimento do cursor;
- segmento confirmado continua usando o algoritmo direcional preciso anterior;
- solicitações de movimento são condensadas: somente a posição mais recente fica pendente;
- resultados antigos são descartados por revisão, identidade da imagem e assinatura das configurações;
- o pool de trabalho é serializado para não saturar a CPU;
- o cursor indica processamento durante um segmento confirmado;
- modo Legado e comportamento síncrono de adaptadores/mock permanecem disponíveis.

A correção não declara que todo cálculo será instantâneo. Segmentos precisos grandes ainda podem levar tempo, mas não devem executar o A* no thread da interface.

### Idiomas

Foram adicionados catálogos inglês/português e identificadores internos estáveis para:

- diálogo principal de exportação;
- mensagens e seletores de exportação;
- pré-visualização de exportação;
- Visualizador de Máscara;
- presets, camadas, parâmetros, status e mensagens do Visualizador de Máscara.

A tradução não altera identificadores de perfil (`generic`, `godot`, `unity`, `phaser`) nem de preset (`Basic`, `Perfect`, `Enhanced`).

### Paleta de ferramentas

- largura calculada pela fonte e pelo idioma ativos;
- margem, borda e padding considerados no cálculo;
- altura calculada por quantidade de linhas;
- limite superior defensivo de 260 pixels;
- recálculo após alternar entre português e inglês.

## Correções adicionais encontradas durante a revisão

- a troca de idioma do Visualizador de Máscara não reinicia mais zoom e deslocamento;
- o helper headless de pré-visualização deixou de referenciar `self` fora de uma classe;
- valores ausentes de pivô não são mais formatados como número de ponto flutuante;
- o Visualizador de Máscara mantém IDs de preset separados dos textos traduzidos;
- o ciclo do worker de detecção encerra thread e referências de forma explícita.

## Preservação e limites

Não foram alterados:

- formato de projeto;
- formatos dos exportadores;
- contratos dos perfis de engine;
- modelo de dados da cena;
- histórico Git;
- remote, commit ou tag;
- nome do pacote Python;
- algoritmo direcional usado para o segmento preciso confirmado.

## Validação obrigatória no Windows

- compilação de todos os arquivos Python;
- testes novos da 0.6N1A;
- testes da identidade 0.6N1;
- checkpoint 0.5.2F3;
- suíte oficial completa;
- teste visual nos dois idiomas;
- teste do Laço Magnético com imagem real pequena, média e grande;
- confirmação de que a janela continua respondendo durante pré-visualização e confirmação de segmento;
- o resultado somente será declarado corrigido após a validação automática e visual no Windows.
