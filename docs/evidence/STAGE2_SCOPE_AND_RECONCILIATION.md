# Etapa 2 — escopo normativo e reconciliação documental

A Etapa 2 cobre a biblioteca própria de ícones vetoriais do projeto. O
catálogo normativo deve conter os glyphs de seleção, contorno, colisão,
navegação, arquivo, edição, visibilidade, raio-X, iluminação, gizmo, encaixe,
grade, cenário e validação previstos no plano, incluindo `undo`, `redo` e
`snap`.

## Critérios verificáveis

- Cada ícone normativo possui `IconSpec`, SVG embutido no código versionado e
  nome acessível.
- Cada ícone renderiza em 16, 20 e 24 px; o tamanho 32 px pode existir como
  extensão sem substituir os tamanhos obrigatórios.
- A biblioteca não depende de fontes, caminhos locais, download, pacote de
  terceiros ou emojis funcionais.
- Ações e widgets reais possuem ícone não nulo, texto preservado, tooltip,
  nome acessível e fallback textual observável.
- `undo`, `redo` e `snap` pertencem ao catálogo central. Implementações
  posteriores específicas, como máscara e overlay de colisão, permanecem
  extensões posteriores e não são usadas para inflar o resultado da Etapa 2.
- A matriz Qt executa a MainWindow e a galeria em 100%, 125%, 150% e 200%,
  com hashes, auditoria visual e detecção de clipping.

## Achado corrigido antes do snapshot

Os testes históricos passavam, mas não verificavam a completude da lista
normativa: `undo`, `redo` e `snap` estavam ausentes do catálogo central, e
`undo`/`redo` eram duplicados no toolbar. A correção centralizou esses ícones,
preservou os contratos públicos e adicionou testes e auditoria específicos.

## Reconciliação histórica

As evidências anteriores da matriz DPI permanecem como referência diagnóstica.
O resultado atual é calculado separadamente no commit filho da Etapa 1; uma
diferença histórica não pode substituir nem mascarar o contrato atual.
