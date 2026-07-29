# Checkpoint funcional — Etapa 0.5.2E

Data de congelamento: 27 de julho de 2026.

A Etapa 0.5.2F foi desenvolvida sobre a instalação transacional 0.5.2E validada no Windows pelo usuário. Para os arquivos que a 0.5.2F altera, o instalador verifica os bytes da 0.5.2E por SHA-256 antes de copiar qualquer conteúdo.

Arquivos funcionais congelados:

- `src/tools/base_tool.py`;
- `src/tools/magnetic_lasso.py`;
- `src/ui/canvas_view.py`;
- `src/ui/main_window.py`;
- `src/ui/tool_palette.py`.

A implementação original de `dijkstra_pathfinding()` continua presente no modo **Legado**. O rollback transacional devolve exatamente esses cinco arquivos à versão 0.5.2E e remove somente os arquivos exclusivos da 0.5.2F.

Nenhum arquivo de projeto do usuário, imagem importada, cena salva ou formato persistente é migrado pela 0.5.2F.
