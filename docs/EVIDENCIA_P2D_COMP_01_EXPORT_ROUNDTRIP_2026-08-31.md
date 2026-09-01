# Evidência P2D-COMP-01 — exportação e round-trip

**Data:** 31/08/2026 (UTC-03)

**Estado:** QUALIFICATION PASS — publicação commit/push/merge pendente

## 1. Escopo

Esta evidência fecha o bloqueador de qualificação da fundação atual de
composição 2D: exportar a cena declarada, importar em Godot e Unity, verificar
a layer e o objeto materializados, e rejeitar um artefato cujo hash não
corresponde ao contrato. Ela não transforma a fundação em aceite do produto
integral descrito em
docs/REQUISITOS_EDITOR_CENARIOS_COMPLETO_2026-08-30.md.

## 2. Causa e correção

O harness contava os filhos diretos do root como layers. A cena real também
contém SceneCamera, portanto o harness rejeitava uma cena válida com duas
crianças técnicas. A contagem foi tornada semântica:

- Godot localiza a única Node2D com o metadado neoeng_layer_id e exige a
  presença de SceneCamera;
- Unity conta componentes
  NeoEngProfessionalLayerMetadata em toda a hierarquia importada;
- os casos negativos continuam exigindo falha para hash incorreto.

Arquivos de implementação e contrato alterados:

- tools/godot_professional_scene_stage5_validator.gd;
- integrations/unity/package/com.neoeng.dtrace/Editor/ProfessionalSceneImportGenerator.cs;
- tests/test_p2d_04_persistence_recovery_export.py.

Os seis artefatos de evidência Stage 5 foram regenerados pelos auditores após a
correção, preservando logs positivos, negativos e hashes sanitizados.

## 3. Gates executados

| Gate | Resultado |
| --- | --- |
| Suíte completa | 1871 passed, 2 skipped, 1 warning, 47,50 s |
| Teste focado P2D-04/persistência/exportação | 9 passed, 2,18 s |
| Auditoria real Godot | PASS; 4.7.stable.official.5b4e0cb0f; 1 layer; 1 objeto |
| Auditoria real Unity | PASS; 6000.5.7f1; 1 layer; 1 objeto |
| Hash incorreto em Godot | PASS negativo; rejeição observada |
| Hash incorreto em Unity | PASS negativo; rejeição observada |
| git diff --check | PASS |

A auditoria Unity reportou apenas avisos ambientais do licenciamento local
(access token indisponível e Curl error 42); a importação funcional retornou
sucesso e o caso negativo retornou falha como esperado.

## 4. Resultado técnico

Os caminhos reais de Godot e Unity materializam a cena em um objeto dentro de
uma layer reconhecida, sem tratar a câmera como layer. Os relatórios positivos
registram exatamente 1 layer e 1 objeto; os relatórios negativos registram
falha e rejeição do hash. A validação continua baseada no artefato exportado e
na importação real, não em marcador isolado ou metadado sem objeto.

## 5. Decisão e limites

A fundação de P2D-COMP-01 fica qualificada para o contrato atual de composição
2D e exportação/round-trip dos objetos suportados, após a publicação e a
requalificação pós-merge. Nenhuma linha EXT é aceita por esta evidência.

Permanecem explicitamente fora deste fechamento: autoria completa a partir de
cena vazia, pacote proprietário de assets, tilemap completo, colisão e
navegação de cenário, entidades/componentes/prefabs, iluminação/sombras,
partículas, pós-processamento, shaders editáveis, efeitos em tempo real e
aceite visual integral do produto. Conforme a emenda vigente, o produto final
permanece OPEN / INCOMPLETE até esses requisitos terem implementação, testes,
evidência e aceite próprios.

## 6. Publicação

Os hashes do commit técnico, do commit documental, do push, do merge e da
requalificação pós-merge serão adicionados no fechamento da publicação.
