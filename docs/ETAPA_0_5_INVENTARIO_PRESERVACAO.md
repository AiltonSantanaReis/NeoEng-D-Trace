# Etapa 0.5 — Inventário de preservação funcional

## 1. Regra de interpretação

“Presente” significa que foi encontrada implementação no código atual. Não
significa que o recurso esteja completo, conectado à interface ou validado.

Nenhum item desta lista pode ser removido apenas por estar incompleto, duplicado
ou sem teste.

## 2. Núcleo de projeto e dados

| Capacidade | Implementação identificada | Estado inicial | Regra de preservação |
|---|---|---|---|
| Cena e objetos | `src/models/scene.py` | Presente, complexa | Proteger com round-trip e migração antes de alterar |
| Camadas | `Scene`, `LayersPanel`, comandos | Presente | Preservar ordem, visibilidade, bloqueio e associação |
| Grupos | `Scene`, `GroupsPanel`, comandos | Presente | Preservar associação, ordem e transformações |
| Colisão por objeto | `Scene.set_object_collision()` | Presente | Não perder IDs nem geometrias ao salvar |
| Eventos da cena | `subscribe()` e `_notify()` | Presente | Mapear assinantes antes de trocar o mecanismo |
| Salvamento/carregamento | `Scene.save_project()` e carregamento | Parcial | Criar schema versionado e testes antes de mudar |

## 3. Comandos, undo e redo

O arquivo `src/core/commands.py` contém comandos para:

- camadas;
- visibilidade e bloqueio;
- alças;
- expansão e contração;
- grupos;
- criação e remoção de polígonos;
- criação e exclusão de objetos;
- movimentação de grupos;
- colisões;
- limpeza da cena.

Estado: presente, mas a cobertura atual não demonstra todos os ciclos
`execute → undo → redo`.

Regra: nenhuma ação de edição poderá migrar para uma nova arquitetura sem teste
de equivalência e rollback.

## 4. Ferramentas 2D identificadas

| Ferramenta | Arquivo | Estado inicial | Risco |
|---|---|---|---|
| Caneta/Bézier | `src/tools/pen_tool.py` | Presente | Alto |
| Laço livre A | `src/tools/lasso.py` | Presente | Alto |
| Laço livre B | `src/tools/lasso_tool.py` | Presente e duplicado nominalmente | Alto |
| Laço poligonal | `src/tools/polygonal_lasso.py` | Presente | Alto |
| Laço magnético | `src/tools/magnetic_lasso.py` | Presente | Alto |
| Seleção retangular | `src/tools/rect_selection.py` | Presente | Médio |
| Seleção elíptica | `src/tools/ellipse_selection.py` | Presente | Médio |
| Seleção de objetos | `src/tools/selection_tool.py` | Presente, métodos vazios | Alto |
| Edição de polígonos | `src/tools/polygon_edit_tool.py` | Presente, parcial | Alto |
| Pincel de colisão | `src/tools/collision_brush_tool.py` | Presente | Alto |
| Suavização | `src/tools/smoothing.py` | Presente | Médio |
| Utilitários de máscara | `src/tools/mask_utils.py` | Presente | Alto |
| Detecção de bordas | `src/tools/edge_utils.py` | Presente | Médio |

As duas classes `LassoTool` devem permanecer até existir um contrato único,
testes de comportamento e uma decisão de migração.

## 5. Detecção automática e visualização

Implementações encontradas:

- detecção básica;
- detecção aprimorada;
- detecção “perfect”;
- presets;
- integração com cena;
- retorno compatível por `DetectResult`;
- `MaskViewer`;
- processamento em worker;
- seleção de polígonos detectados;
- modos de visualização/X-Ray;
- processamento CPU e tentativa de aceleração GPU.

Estado: presente, mas não integralmente validado em imagens reais e limites de
memória.

Regra: criar corpus de teste e métricas antes de alterar algoritmos ou presets.

## 6. Colisão e física

Implementações encontradas:

- SAT em `src/physics/sat2d.py`;
- wrapper de compatibilidade em `src/collision/sat2d.py`;
- sweep-and-prune;
- broadphase por grade;
- triangulação;
- decomposição convexa;
- `PhysicsManager`;
- overlay de colisões;
- painel de colisões;
- teste em lote;
- geração automática;
- exportação textual/JSON parcial.

Estado: presente, com incompatibilidades entre APIs históricas e atuais.

Regra: não remover aliases históricos nem simplificar o modelo até que os testes
SAT, broadphase e decomposição tenham sido reconciliados.

## 7. Exportação

Implementações encontradas:

- sprite recortado;
- atlas;
- JSON genérico;
- perfis Godot;
- perfis Unity;
- perfis Phaser;
- GLTF/GLB;
- preview;
- exportação individual e em lote;
- gravação atômica em partes do pipeline.

Estado: presente, mas os testes históricos revelaram divergência nos metadados
específicos de Godot, Unity e Phaser.

Regra: cada perfil deve possuir schema documentado, golden file e teste na engine
antes de ser considerado estável.

## 8. Interface

Componentes identificados:

- janela principal;
- canvas;
- paleta de ferramentas;
- painel lateral;
- camadas;
- grupos;
- máscara;
- exportação;
- preview;
- colisões;
- gizmo;
- temas;
- atalhos e menus;
- idiomas.

Estado: presente, mas a auditoria sem PySide6 não validou os fluxos gráficos.

Regra: alterações visuais devem preservar ações, atalhos, foco, seleção, menus de
contexto e acessibilidade funcional.

## 9. Arquivos excluídos que exigem decisão

Não são candidatos a remoção automática:

- `src/tools/rect_tool.py`;
- `src/tools/magnetic_lasso_backup.py`;
- `src/ui/canvas_view_backup_2025-11-28.py`;
- `integration_test.py`;
- `physics_demo.py`;
- testes históricos em `tests/`;
- benchmarks antigos;
- scripts de demonstração e correção.

Os backups podem sair do código ativo, mas somente depois de comparação e
arquivamento rastreável.

## 10. Arquivos novos não rastreados relevantes

Entre os arquivos atuais que ainda não estavam no HEAD encontram-se:

- `src/core/view_processor.py`;
- `src/exporters/gltf_exporter.py`;
- `src/tools/collision_brush_tool.py`;
- `src/tools/polygon_edit_tool.py`;
- `src/tools/selection_tool.py`;
- `src/ui/gizmo.py`;
- novos testes;
- novos benchmarks;
- workflow de CI;
- documentos da auditoria.

Esses arquivos fazem parte do estado funcional recebido e devem ser preservados
no baseline depois da validação mínima.

## 11. Critério de conclusão do inventário

O inventário será considerado completo somente quando cada capacidade possuir:

- proprietário lógico;
- entrada e saída;
- ponto de acesso na interface;
- dependências;
- teste atual;
- teste histórico relacionado;
- estado no Windows;
- decisão de versão 1.0;
- risco de regressão;
- plano de rollback.
