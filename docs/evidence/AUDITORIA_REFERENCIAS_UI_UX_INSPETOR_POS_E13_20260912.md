# Auditoria das referências de UI/UX do inspetor — pós-E13

**ID:** `AUD-POST-E13-REF-UIUX-20260912`
**Versão:** 1.0
**Data:** 2026-09-12
**Estado:** `IN_PROGRESS`
**Commit auditado:** `ca6b4d2c11dbe34956212fbdf04ad204ba0a5df0`
**Checkpoint protegido:** `ec94530fcba39be3bbce0439fc56aa48957442c0`
**Escopo:** análise do texto colado pelo usuário, oito imagens de referência e confronto com o Editor de Cenário canônico pós-E13.

Este documento registra uma auditoria de produto e engenharia. O texto e as
imagens anexados são material de referência, não instruções normativas nem
prova de comportamento do projeto. A governança, as decisões aprovadas e os
contratos do produto continuam prevalentes.

## 1. Governança e fronteira protegida

Antes desta etapa foi lida integralmente a
[governança de integridade](../GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md).

Aplicações desta etapa:

1. E13 permanece fechado e o trabalho continua no lote pós-E13.
2. O checkpoint pré-gizmo permanece a referência de restauração.
3. Nenhum código do editor canônico, gizmo ou asset de produção foi alterado.
4. A falha oficial encontrada na suíte foi preservada; não houve filtro,
   `skip`, `xfail`, alteração de threshold ou remoção de evidência.
5. Os mockups não foram promovidos a requisito visual nem a captura nativa.

## 2. Referências recebidas

As oito imagens abaixo foram inspecionadas visualmente e identificadas por
nome e SHA-256. Elas possuem marca d’água de geração e são referências
conceituais, não capturas do executável.

| Arquivo | Tamanho | SHA-256 |
|---|---:|---|
| `Copilot_20260912_203500.png` | 1.620.943 bytes | `2670E786D23680B4C94C7A17D14A9FF4427D4767E57B93742440E93CB0D3B9E6` |
| `Copilot_20260912_203505.png` | 1.628.091 bytes | `1885B93B6350F59F7FA116A3BE243083C7C30C55F4F09BFA48D1DC183850A022` |
| `Copilot_20260912_203511.png` | 1.337.665 bytes | `2E632EFB00A6DDAE89BCE62298C568CB8FCA02E01341424B9F05B004C70DC8E2` |
| `Copilot_20260912_203649.png` | 1.780.199 bytes | `54D1DDF4A1DE75216FE063164A4A9078CED370390495F57175EF03D8F0AE8931` |
| `Copilot_20260912_204435.png` | 1.710.321 bytes | `150292DD5A9D9E97B1F94F654A5B28A8A9C88A2D07A18CF041DF67172B578054` |
| `Copilot_20260912_204440.png` | 1.852.846 bytes | `F5EBB2AF4E582DEA947049E2833AEEA0EED1024B751D58FD1F17E5CF30C75D89` |
| `Copilot_20260912_204448.png` | 1.913.978 bytes | `1E543D0DFA3F2E6CA11CDC7831B0BC6E2EB5F7D11CA22F8CB6CA2FE5935B340B` |
| `Copilot_20260912_205321.png` | 1.880.081 bytes | `7C568D1AD88ABFB6F47CA29EE9F73D2D1FE2FA02600A587A938263F2405B05B0` |

## 3. Evidência de execução do checkout

A suíte oficial foi executada sem seleção de testes e terminou com:

```text
2619 passed, 1 failed, 2 skipped, 5 warnings
```

O resultado atual é `FAIL`, não `PASS`. A falha está em
`tests/test_repository_reference_hygiene.py:97` e aponta
`docs/evidence/PROMPTS_PRODUCAO_KIT_FLORESTA_20260912.md:184`, que contém uma
referência textual proibida pela política de higiene do repositório. O
documento não foi removido nem editado nesta etapa.

Os dois `skipped` pertencem aos testes de criação de symlink em
`tests/test_integration_sync.py:92` e `tests/test_integration_sync.py:123`;
o ambiente não permite a operação. Os cinco warnings incluem uso de
construtor de `QMouseEvent` marcado como obsoleto pelo Qt. Essas ocorrências
continuam registradas.

A árvore permaneceu limpa após a execução. Não houve alteração em `src/`,
`tests/`, schemas, baseline ou artefatos de runtime. A auditoria técnica
anterior e a matriz de engines permanecem como evidência histórica vinculada:
[triagem do Editor de Cenário](AUDITORIA_EDITOR_CENARIO_TRIAGE_POS_E13_20260912.md)
e [matriz de limites de engines](MATRIZ_LIMITES_ENGINES_GODOT_UNITY_POS_E13_20260912.md).

## 4. Análise do texto de referência

### 4.1 Direções que devem ser aproveitadas

- Inspetor contextual por seleção, com apenas os módulos pertinentes ao tipo
  de objeto.
- Precisão sob demanda, usando valor numérico editável sem abrir um modal para
  cada alteração.
- Feedback visual imediato e reversível, com undo/redo preservado.
- Hierarquia de camadas com visibilidade, bloqueio, isolamento e miniaturas.
- Catálogo de objetos e assets com arrastar e soltar, busca e filtros.
- Separação entre composição global, propriedades do objeto e pós-processo.
- Controles visuais compactos para parâmetros intuitivos, sem eliminar o
  campo numérico preciso.

### 4.2 Direções que não devem ser copiadas literalmente

- Dials grandes em todas as propriedades: ocupam espaço vertical e exigem
  rolagem excessiva em resolução comum.
- Abas que misturam cena, composição, material, câmera e luz no mesmo nível.
- Modal com botão `OK` para cada número: aumenta atrito e quebra o fluxo de
  experimentação.
- FOV, abertura e transparência exibidos sem distinguir câmera 2D,
  perspectiva 2.5D/3D e material.
- Efeitos visuais exibidos como disponíveis sem capability comprovada no
  runtime de destino.
- Texto gerado sem validação humana. Os erros visíveis nos mockups comprovam
  que a localização precisa de catálogo de strings, testes e revisão, não de
  uma imagem conceitual.

## 5. Auditoria individual das imagens

| Referência | O que é útil | Problema observado | Decisão para o produto |
|---|---|---|---|
| `205321` — composição | Cards de camadas, blend e intensidade | Mistura composição global com controles de material; há texto corrompido e ações duplicadas | Usar como inspiração de composição, mantendo semântica separada |
| `204448` — efeitos | Cards modulares, ativação e precisão sob demanda | Não informa capability, custo ou impacto no runtime; layout é alto | Adotar cards compactos e capability-aware |
| `204440` — camadas | Outliner com hierarquia, visibilidade, lock e isolamento | Ícones sem estados suficientemente explicados e texto truncado | Consolidar com `SceneAuthoringLayerStack` e `SceneAuthoringGroupStack` |
| `204435` — objetos | Miniaturas grandes e arrastar para criar | As miniaturas não são assets reais nem provam criação funcional | Integrar à biblioteca real, com preview, origem e estado de licença |
| `203649`/`203505` — câmera | FOV e foco visíveis, leitura rápida | São quase duplicadas; transparência está no contexto errado; FOV não representa a câmera 2D ortográfica | Separar câmera 2D, câmera 2.5D e câmera 3D |
| `203511` — transformações | Eixos coloridos e precisão numérica | Eixos duplicados/errados, dial grande e modal intrusivo | Manter gizmo fora desta etapa; definir contrato de unidades antes |
| `203500` — materiais | Cor, rugosidade, metalness e transparência com affordance visual | Não deixa claro quando há material aplicável; controle não é adequado a câmera/luz | Mostrar apenas para geometria com slot de material |

## 6. Confronto com a arquitetura atual

O código atual mostra uma topologia que deve ser preservada, mas melhor
apresentada:

1. `ScenarioEditorWindow` é o contêiner canônico. Ele instancia o viewport
   profissional, inspetor, hierarquia, grupos, biblioteca, tilemap, tileset,
   colisão, navegação, entidades e sequência.
2. `SceneAuthoringViewport` é a superfície canônica de autoria. A
   `SceneCameraGuide` já existe para mover e rotacionar a câmera; as guias de
   parallax também existem no viewport.
3. `SceneAuthoringInspector` possui páginas de objeto, câmera, camada,
   material e efeitos. A implementação atual usa principalmente
   `QDoubleSpinBox`, botões explícitos e campos técnicos; ainda não é o
   inspetor contextual e visual proposto nas referências.
4. `ScenarioPanel` é um painel legado de camadas/inspeção dentro da janela
   canônica. `CanvasView` é uma superfície de compatibilidade/preview. Eles
   não devem ser apagados por limpeza nominal.
5. `IndependentSceneWindow` é uma ferramenta independente de formas 2D. Ela
   não é equivalente ao estúdio profissional de parallax e não deve ser
   apresentada como segundo editor completo.

## 7. Achados controlados

| ID | Achado | Classificação | Estado |
|---|---|---|---|
| `REF-UI-01` | A arquitetura visual ainda precisa separar workspace global e inspetor contextual | UX/arquitetura | `IN_PROGRESS` |
| `REF-UI-02` | O gizmo visual precisa de revisão, mas sua alteração foi explicitamente adiada | UX visual | `PLANNED` |
| `REF-UI-03` | A câmera precisa de contrato distinto para ortográfica 2D e perspectiva 2.5D/3D; a completude da experiência necessita nova captura nativa | produto/evidência | `PENDING_EVIDENCE` |
| `REF-UI-04` | Luz, VFX e partículas têm contratos existentes, mas a descoberta, orientação, capability e equivalência por runtime ainda precisam ser verificadas visualmente | produto/runtime | `PENDING_EVIDENCE` |
| `REF-UI-05` | As guias de parallax existem, porém precisam de níveis de visualização, bounds, safe area e leitura menos dominante | UX/viewport | `IN_PROGRESS` |
| `REF-UI-06` | Biblioteca e catálogo têm base de miniaturas; o custo de inspeção/decodificação e a escala de uso ainda não têm baseline de desempenho | desempenho | `PENDING_EVIDENCE` |
| `REF-UI-07` | Há traduções PT-BR implementadas, mas falta matriz nativa completa de menus, tooltips, erros e estados vazios | localização | `PENDING_EVIDENCE` |
| `REF-UI-08` | A suíte oficial está bloqueada por uma referência documental proibida | qualidade de repositório | `FAIL` |
| `REF-UI-09` | Produção de modelos proprietários continua fora do escopo atual | assets | `PLANNED` |

## 8. Arquitetura de experiência recomendada

### Workspace global

Deve conter apenas ações de cena: salvar, exportar, desfazer/refazer, modo de
visualização, camadas/grupos, assets, timeline, render e capability do destino.

### Inspetor contextual

Deve seguir o tipo da seleção:

- objeto: transformação, pivot, material e colisão quando aplicável;
- câmera 2D: posição, zoom, rotação, limites, smoothing e enquadramento;
- câmera 2.5D/3D: projeção, FOV, foco e clipping, somente quando suportado;
- luz: tipo, direção, intensidade, cor, sombras e máscara;
- VFX: emissor, seed, ciclo, orientação, escala e preview;
- camada/parallax: profundidade, fator de rolagem, repetição, bounds e offset.

Se uma propriedade não for válida para a seleção, o painel deve ficar oculto
ou desabilitado com explicação acionável, nunca aparecer como controle sem
efeito.

### Interação e desempenho

O valor numérico deve aceitar teclado, incremento fino, colagem e validação de
locale. O scrubber contínuo pode ser implementado depois de definir unidades,
undo por gesto e acessibilidade. Miniaturas devem ser carregadas sob demanda,
com cache e medição de tempo de frame, tempo de refresh e memória.

## 9. Sequência de execução e critérios de aceite

1. Fechar o `FAIL` de higiene documental preservando o artefato anterior.
2. Reexecutar a suíte oficial sem filtros e registrar o novo resultado.
3. Executar fluxo nativo do zero: cena vazia, objeto, camada, parallax,
   câmera, luz, VFX, material, tilemap, tileset, timeline, salvar, reabrir,
   exportar e recuperação de erro.
4. Capturar cada estado real do binário, com manifestos e hashes.
5. Medir viewport e biblioteca em escalas de objetos/assets previamente
   definidas.
6. Auditar PT-BR, menus contextuais, tooltips, foco, teclado e estados de
   erro.
7. Implementar somente o lote aprovado, com análise de impacto, testes,
   checkpoint e requalificação.

O lote só poderá ser `PASS` quando tiver entrada controlada, operação real,
saída observável, persistência, runtime aplicável, erro recuperável, captura
real, hash, suíte oficial sem falha e revisão humana.

## 10. Decisões reservadas para o encerramento

As decisões humanas ficam concentradas no final da revisão:

1. aprovar a separação definitiva entre workspace global e inspetor contextual;
2. definir quais recursos de câmera/luz/VFX serão de primeira classe em 2D,
   2.5D e 3D;
3. decidir o posicionamento final da ferramenta de cena 2D independente;
4. aprovar o sistema visual do gizmo quando ele voltar ao escopo;
5. aprovar os limites de desempenho e os perfis de engine anunciados.

Até essas decisões e as novas capturas nativas, o estado correto da auditoria
permanece `IN_PROGRESS`. Nenhuma conclusão de aceite visual foi emitida.
