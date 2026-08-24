# Etapa 1 — escopo normativo e reconciliação documental

Este documento fixa o que será considerado evidência da Etapa 1 no alvo
`FINAL_TARGET`. A Etapa 1 cobre exclusivamente o sistema visual do chrome da
aplicação: tokens semânticos, QSS centralizado, contraste, foco de teclado,
estados interativos e ausência de estilos inline não autorizados.

## Critérios verificáveis

- Os tokens `window`, `canvas`, superfícies, bordas, textos, destaque,
  seleção, foco, alerta, erro e sucesso existem em schema imutável.
- Todas as cores dos tokens são hexadecimais válidas, únicas e derivam o QSS.
- O contraste atende `4.5:1` para texto primário/secundário e `3:1` para foco.
- O QSS contém evidência para `hover`, `pressed`, `checked`, `disabled` e
  `focus`, incluindo o papel de ferramenta.
- Não existem `setStyleSheet` ou `setPalette` inline nos módulos de chrome.
- Cores literais de canvas, gizmo, cenário e dados de sockets permanecem
  classificadas como semântica de conteúdo; elas não são reclassificadas como
  chrome e pertencem aos contratos das etapas correspondentes.
- Uma fixture Qt isolada gera 18 PNGs: seis estados em cada uma das três
  resoluções lógicas obrigatórias, incluindo amostras de pixels e `hasFocus`.

## Reconciliação do comparador histórico

O comparador visual legado é mantido intacto como evidência diagnóstica. Seu
resultado observado foi `FAIL`, com 192 diferenças geométricas contra uma
referência anterior. Esse resultado permanece explícito e é classificado como
`HISTORICAL_ONLY`; não é convertido em aprovação nem usado para mascarar uma
regressão atual.

O veredito atual da Etapa 1 vem do contrato de tokens/QSS e das capturas de
estados. Se esse contrato falhar, a decisão fica bloqueada independentemente do
resultado histórico. Se passar, a decisão automatizada é
`PASS_WITH_HISTORICAL_EVOLUTION`, permanecendo sujeita à revisão humana e ao
CI no commit exato.

## Limites

As cores de desenho do viewport, gizmo e editor de cenário não são tokens de
chrome. Elas permanecem em seus contratos funcionais posteriores e não podem
ser removidas ou substituídas nesta etapa apenas para satisfazer o auditor.
