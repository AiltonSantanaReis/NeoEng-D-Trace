# Inventário de localização — Etapa 0.6N1

Este documento impede que a existência de dois idiomas seja tratada como cobertura integral sem evidência.

## Cobertura confirmada

A janela principal propaga `en` e `pt` para:

- SidePanel;
- ToolPalette;
- GroupsPanel;
- CanvasView;
- ferramenta ativa quando ela implementa `update_language`.

A 0.6N1 adiciona contratos para a identidade NeoEng-D-Trace e para as ações principais da janela em ambos os idiomas.

## Lacunas existentes e não ocultadas

Os componentes abaixo ainda possuem textos fixos, predominantemente em inglês, e não expõem uma atualização de idioma completa:

- `src/ui/export_dialog.py`;
- `src/ui/export_preview.py`;
- `src/ui/mask_viewer.py`;
- `src/ui/collision_panel.py`;
- `src/ui/layers_panel.py`.

Há também mistura histórica de português e inglês em alguns rótulos iniciais de ferramentas. A 0.6N1 não declara que todo o aplicativo está traduzido.

## Decisão

A tradução integral será tratada em etapa própria, com inventário de todas as strings visíveis, chaves comuns, testes por componente e validação visual no Windows. Não deve ser misturada à migração de pacote, configuração ou formato de projeto.
