# NeoEng-D-Trace — Documento Normativo de Consolidação do Editor Profissional de Composição 2D Baseado em Objetos

**Versão do documento:** 1.0 — referência operacional para esta linha de produto
**Data de emissão:** 27/08/2026 — horário local do usuário, UTC-03
**Repositório:** REPO_ROOT
**Branch de referência:** modernization/multiaxis-ui
**HEAD de referência:** 7df73f21f5a609196e6cadac85065c89a989ecb4 — fix(ui): consolidate menu and toolbar integration
**Natureza:** documento normativo, plano de execução, contrato de evidência e checklist de aceite
**Preset editorial do DOCX:** compact_reference_guide
**Padrão de abertura:** memo_masthead

**Símbolos de caminho:** REPO_ROOT significa a raiz local do checkout do repositório; DOWNLOAD_ROOT significa o diretório local destinado a artefatos baixados ou gerados fora do repositório. Os símbolos são deliberadamente usados para evitar vazamento de caminhos de usuário em artefatos versionados.

> **REGRA DE AUTORIDADE:** este documento deve ser lido integralmente antes de qualquer nova etapa de implementação, alteração de escopo, execução de gate, commit, build, release ou encerramento. A leitura não é uma recomendação. É uma pré-condição operacional. Nenhuma etapa pode ser marcada como concluída sem que a equipe registre que este documento foi consultado e que todos os itens obrigatórios da etapa foram atendidos.

> **REGRA DE COMPLETUDE:** “parcial”, “quase pronto”, “funciona no caso feliz”, “validado manualmente” ou “sem falhas conhecidas” não são estados de aceite. Uma etapa só pode ser ACEITA quando todos os critérios obrigatórios, evidências e revisões humanas definidos neste documento estiverem presentes, rastreáveis e sem divergências não classificadas.

> **REGRA DE HONESTIDADE:** este documento não transforma lacunas atuais em funcionalidades existentes. Ele define o que deve ser implementado, como comprovar cada item e quais condições bloqueiam a declaração de conclusão.

---

## 0. Finalidade, autoridade e modo de uso

### 0.1 Finalidade

O objetivo deste documento é consolidar, em uma única referência auditável, o caminho para transformar o NeoEng-D-Trace em um editor profissional de composição 2D baseado em objetos, preservando as bases congeladas, evitando regressões de geometria, visual e comportamento e impedindo que entregas incompletas sejam confundidas com conclusão.

O documento contém, em sequência única:

- a definição inequívoca do produto-alvo;
- o estado factual atual, separado de intenção futura;
- os contratos e artefatos imutáveis;
- as restrições que continuam válidas mesmo quando outra etapa estiver em execução;
- os requisitos funcionais e não funcionais;
- as etapas obrigatórias, na ordem obrigatória;
- a definição de pronto para cada etapa;
- os gates técnicos, visuais, comportamentais e documentais;
- o pacote mínimo de evidências;
- a regra para divergência, dúvida, falha, mudança de baseline e conflito entre fontes;
- o formulário de aceite humano e o protocolo de encerramento.

### 0.2 Autoridade deste documento

Este documento é a referência operacional da linha de consolidação do editor de composição 2D. Ele não substitui o código, os testes, os contratos canônicos ou a aprovação humana. Ele organiza como esses elementos devem ser usados.

Quando houver conflito entre informações, a equipe não pode escolher silenciosamente uma interpretação. Deve registrar a divergência, interromper a etapa afetada e aplicar a ordem de precedência abaixo:

1. decisão explícita mais recente do usuário ou proprietário do produto, registrada na conversa ou em decisão assinada;
2. este documento, na versão formalmente adotada para a etapa;
3. contratos e pacote C3 imutáveis;
4. comportamento comprovado pelo código atual e pelos testes reproduzíveis;
5. evidências de captura e auditoria;
6. documentos históricos, notas de trabalho e descrições antigas.

Se uma fonte de nível inferior contradisser uma fonte de nível superior, a fonte inferior é tratada como divergente até ser corrigida. Ela não pode redefinir o produto.

### 0.3 Leitura obrigatória em cada etapa

Antes de iniciar cada etapa, o responsável deve:

1. abrir este documento na versão vigente;
2. ler as seções 1, 2, 3, 4 e a seção específica da etapa;
3. conferir o estado real do repositório;
4. registrar identificador do documento, versão, commit lido e resultado da conferência;
5. declarar qualquer divergência antes de editar código;
6. somente então iniciar a atividade da etapa.

Ao finalizar cada etapa, o responsável deve conferir as seções 5, 6, 7, 8 e 9, executar todos os gates aplicáveis e preencher o registro de aceite. O trabalho não pode avançar para a etapa seguinte com um gate obrigatório ausente.

### 0.4 Termos normativos

Neste documento, as palavras abaixo têm significado obrigatório:

- **DEVE / OBRIGATÓRIO:** requisito que precisa ser cumprido; ausência bloqueia o aceite.
- **NÃO DEVE / PROIBIDO:** ação que não pode ser realizada dentro desta linha.
- **SOMENTE:** condição que limita uma ação a um caso explicitamente definido.
- **PODE:** opção permitida, desde que não viole itens obrigatórios e seja registrada quando alterar evidência, comportamento ou escopo.
- **ACEITA:** etapa concluída com todos os gates obrigatórios PASS, evidências preservadas e revisão humana registrada.
- **REJEITADA:** etapa que possui falha, evidência insuficiente ou divergência não resolvida.
- **BLOQUEADA:** etapa que não pode avançar por dependência identificada; não significa concluída.
- **ADIADA:** requisito explicitamente fora do escopo da entrega atual, sem ser apresentado como implementado.
- **NO_CHANGE:** decisão formal de não alterar um item após revisão; exige registro do finding inexistente e não equivale a implementação.

---

## 1. Identidade da linha de produto e estado de referência

### 1.1 Produto-alvo

O produto-alvo desta linha é um editor profissional de composição 2D por objetos, integrado ao NeoEng-D-Trace, no qual o usuário consegue montar, revisar, organizar, persistir e exportar uma composição visual formada por assets e objetos editáveis.

O produto-alvo não é, nesta primeira consolidação, um editor de pixels, um modelador 3D, um runtime completo de jogo ou uma suíte de efeitos avançados. Esses itens somente entram por decisão explícita de produto e por uma nova etapa com escopo, contratos e gates próprios.

### 1.2 Estado factual do repositório no momento da emissão

O estado de referência informado para este documento é:

| Item | Valor obrigatório de referência |
|---|---|
| Diretório | REPO_ROOT |
| Branch | modernization/multiaxis-ui |
| HEAD | 7df73f2 |
| Último commit | fix(ui): consolidate menu and toolbar integration |
| Commit anterior relevante | bb0fc0d — feat(scenario): bind professional document to main preview |
| Tracked tree | limpo após os commits consolidados |
| Untracked | existem artefatos históricos legítimos; não devem ser apagados nem tratados isoladamente como dirty tracked tree |
| Python de qualificação | REPO_ROOT/.venv/Scripts/python.exe |
| Python esperado | 3.11.9 |
| PySide6 esperado | 6.10.1 |
| pytest esperado | 9.1.1 |
| Suíte completa mais recente no worktree consolidado | 1758 passed / 2 skipped / 0 failed |

Se qualquer linha acima não corresponder ao repositório real, o responsável deve parar e classificar a divergência antes de qualquer mutação. Não é permitido corrigir o documento por suposição.

### 1.3 O que já está consolidado

As seguintes decisões e integrações já existem no histórico de trabalho e devem ser preservadas:

- a janela profissional de cenário é separada da janela principal;
- o formato V2 .ndtscene.json é o documento canônico do editor profissional;
- o formato V1 .ndtscenario.json permanece legível para compatibilidade explícita;
- migração V1 para V2 só ocorre em ação explícita de save;
- o preview principal utiliza as camadas, visibilidade, parallax e câmera ativas e persistidas em V2;
- existe modelo de objetos, camadas, grupos, snapping, câmera, parallax e sockets;
- existem seleção, multisseleção, movimentação, transformação, flip, inspector numérico, camadas, sockets, undo/redo, save/load/reset/export;
- existem adapters de exportação genérica, Godot e Unity com declaração explícita das capacidades que não são suportadas;
- os commits anteriores de modernização de UI e integração documental foram realizados localmente;
- não houve autorização para push, tag, merge remoto ou publicação remota.

Esses fatos não significam que todos os requisitos do editor profissional já estejam cumpridos. O estado atual e as lacunas estão definidos na seção 4.

---

## 2. Imutáveis e restrições permanentes

Esta seção é superior a qualquer etapa futura. Um requisito de implementação que contradiga um item desta seção está incorreto até que exista uma decisão formal de mudança de baseline.

### 2.1 Baseline C3 imutável

O pacote C3 é a referência criptograficamente congelada da conformance multiaxial e não pode ser reescrito, reinterpretado, relaxado ou substituído retroativamente.

| Propriedade | Valor imutável |
|---|---|
| Commit C3 | 9b3ab0f9edfd338c44da6118fa6b7a9c3906a8b4 |
| Pacote | DOWNLOAD_ROOT/neoeng-conformance-c3-freeze-9b3ab0f.zip |
| Manifest SHA-256 | 0f876447f365ba0f0205a3229597e86e70f7b527e2f3b85476fcd5795189e969 |
| ZIP SHA-256 | f96b19af50aad18a00cd140abc5b0a0e055f1c1952548e9cc470365532d01598 |
| Tamanho do ZIP | 8.293.076 bytes |
| Evidências | 238 artefatos + manifest + hash do manifest |
| Cobertura canônica | G60/60 + V12/12 + B21/21 = 93/93 PASS |
| Suíte congelada | 1756 passed / 2 skipped / 0 failed |

Formulação obrigatória: “C3 canonical first-coverage gate PASS 93/93” ou “C3 baseline freeze accepted/closed”. É proibido chamar o C3 de “conformance exaustiva do produto”, pois essa não é a afirmação comprovada pelo pacote.

### 2.2 Eixos e interpretação de gates

Somente G, V e B são eixos bloqueantes da conformance multiaxial do editor:

| Eixo | Significado | Resultado canônico de referência |
|---|---|---|
| G | geometria e referência física | 60 checks; PASS quando 60/60 |
| V | sistema visual | 12 checks; PASS quando 12/12 |
| B | comportamento e interação | 21 checks; PASS quando 21/21 |
| H | histórico e governança | suporte não bloqueante, preserva evidência |
| X | CI, release e escopos externos | gates próprios, fora do aggregate multiaxial |

O aggregate canônico possui 93 checks. Produtores legacy G/B podem continuar retornando FAIL por visual_geometry mixed legacy enquanto os adapters canônicos de ownership permanecem PASS. Isso deve ser registrado, não mascarado.

### 2.3 Contratos de produto que não podem ser alterados silenciosamente

Sem um lote explicitamente classificado e aprovado, permanecem imutáveis:

- keys dos glyphs existentes e seus mappings semânticos;
- accessible names e nomes visíveis quando a etapa não for explicitamente de acessibilidade ou texto;
- QAction, shortcuts, command routing e semântica de comandos existentes;
- widget tree e geometria da UI em etapas V-only ou de iconografia;
- dimensões, width, height, min, max, padding, margin, spacing, métricas de fonte e setIconSize em lotes V-only;
- renderer existente e comportamento de seleção/transição fora do escopo declarado;
- significado de SceneObject.position.z nos contratos já existentes até haver decisão de composição/order semantics;
- formato V1 .ndtscenario.json, sua leitura e sua compatibilidade;
- formato .ndtproj e seus contratos existentes;
- baseline, tolerância e auditor dos gates; não podem ser alterados para fabricar PASS;
- condições históricas H, que devem continuar visíveis e não podem ser apagadas;
- glyphs classificados como KEEP ou NO_CHANGE sem novo finding real;
- collider_edit e scenario como runtime not-seen enquanto não houver cobertura dirigida que os materialize;
- o estado atual do rail de 84 px observado nos probes atuais; o antigo rail de 61 px permanece histórico H;
- qualquer pacote de evidência já selado, incluindo os seals de M2.1, M2.2, M2.3A-r1 e M2.3B1-r1.

### 2.4 Proibições operacionais permanentes

- Não usar o Python global 3.13 para qualificação.
- Não fazer push, tag, merge ou qualquer mutação remota sem autorização explícita.
- Não apagar, mover, limpar ou normalizar o volume de untracked legítimo.
- Não alterar .gitignore para ocultar artefatos ou reduzir artificialmente o escopo de inspeção.
- Não fazer commit antes de todos os gates obrigatórios da etapa.
- Não reportar PASS com base somente em uma captura ou em audit_ui_capture.py.
- Não tratar “não observado” como dead code.
- Não mudar a baseline aprovada sem APPROVED_BASELINE_CHANGE, justificativa, evidência e aprovação explícita.
- Não reabrir itens KEEP/NO_CHANGE sem finding novo reproduzível.
- Não implementar funcionalidades fora da etapa atual apenas para aumentar a aparência de completude.

### 2.5 Mudança formal de um imutável

Se uma decisão de produto exigir alterar um item desta seção, a equipe deve criar antes da implementação um registro de mudança contendo:

1. identificador único da mudança;
2. item imutável afetado;
3. motivo e benefício esperado;
4. impacto em G, V, B, H e X;
5. baseline anterior e baseline proposta;
6. testes e evidências adicionais;
7. risco de compatibilidade e plano de reversão;
8. aprovação explícita do proprietário do produto;
9. data, responsável e commit de referência.

Sem esse registro, o imutável continua vigente e o código não pode ser alterado naquele ponto.

---

## 3. Definição inequívoca do produto a consolidar primeiro

### 3.1 Nome da primeira consolidação

O primeiro produto a ser concluído sob este documento chama-se P2D-COMP-01 — Editor Profissional de Composição 2D Baseado em Objetos.

### 3.2 Resultado que P2D-COMP-01 deve entregar

Ao final de P2D-COMP-01, um usuário deve conseguir, dentro do editor profissional:

1. criar uma composição vazia ou abrir uma composição existente;
2. adicionar assets suportados ao projeto por uma operação previsível;
3. visualizar os assets reais no viewport, e não apenas representações geométricas abstratas;
4. selecionar um objeto, selecionar vários objetos e identificar claramente a seleção;
5. mover, duplicar, remover, girar e redimensionar objetos com precisão;
6. editar transformações pelo viewport e por valores numéricos;
7. controlar ordem visual, camada, visibilidade, bloqueio, agrupamento e isolamento;
8. navegar pelo viewport com zoom, pan e ajuste de enquadramento previsíveis;
9. usar teclado e mouse para as operações principais, com foco e estados visuais claros;
10. desfazer e refazer operações sem corromper o documento;
11. salvar, reabrir e recuperar uma composição sem perda silenciosa de dados;
12. exportar uma representação estruturada compatível com os adapters declarados;
13. visualizar a composição no preview principal quando o documento estiver integrado;
14. receber diagnóstico explícito para asset ausente, formato inválido, caminho externo, documento inválido ou exportação não suportada.

Se qualquer item acima não estiver implementado, testado e aceito, P2D-COMP-01 permanece aberto. Não existe “P2D-COMP-01 concluído com o item 3 pendente”. O item pendente deve ser classificado como bloqueio, adiamento formal ou mudança de escopo aprovada.

### 3.3 Escopo incluído

P2D-COMP-01 inclui:

- composição 2D baseada em objetos visuais;
- assets raster e vetoriais nos formatos explicitamente suportados;
- transformações 2D e edição numérica;
- seleção simples e múltipla;
- camadas, ordem visual, visibilidade e bloqueio;
- grupos e organização hierárquica compatível com o modelo;
- snapping configurável, quando declarado no contrato;
- navegação e enquadramento do viewport;
- histórico transacional undo/redo;
- persistência V2 canônica e leitura compatível V1;
- integração com preview principal;
- exportação estruturada e adapters que declararem suporte real;
- testes automatizados, captura Windows, auditoria visual e revisão humana.

### 3.4 Escopo explicitamente fora de P2D-COMP-01

Os itens abaixo não fazem parte da primeira consolidação e não podem ser apresentados como existentes dentro dela:

- editor de pixels ou pintura raster;
- tilemap completo com autotiling/rule tiles;
- filosofia isométrica ou hexagonal, salvo se criada em etapa futura específica;
- NavMesh 2D ou sistema completo de navegação de IA;
- iluminação 2D em tempo real e sombras físicas;
- partículas, shaders, pós-processamento ou simulação de efeitos;
- runtime completo de jogo;
- modelagem 3D;
- colaboração remota em tempo real;
- streaming de assets ou projeto;
- importadores universais sem contrato de formato;
- exportação que prometa recursos não suportados pelo adapter.

Um item fora do escopo pode ser planejado depois. Ele não pode ser usado como justificativa para declarar P2D-COMP-01 parcialmente pronto.

---

## 4. Verdade atual da implementação: existente, parcial e ausente

Esta seção é um inventário técnico. Ela deve ser atualizada somente quando uma alteração comprovada mudar o estado real.

| Área | Estado real de referência | Evidência ou consequência |
|---|---|---|
| Schema V2 | existente | src/persistence/scene_authoring_schema.py; contém metadata, project, assets, layers, objects, groups, snap, camera, parallax_layers e sockets |
| Modelo de autoria | existente | src/core/scene_authoring_model.py; possui objetos, layers, grupos, transforms e sockets |
| Sessão undo/redo | existente | src/core/scene_authoring_session.py; mutações transacionais e histórico |
| Janela profissional separada | existente | src/ui/scenario_editor_window.py |
| Seleção e multisseleção | existente | seleção simples e Ctrl multisseleção no viewport |
| Gizmo e inspector | existente | translate, rotate, scale uniforme, flip e edição numérica |
| Layers | existente, porém limitada | adicionar, remover, renomear, reordenar, visível e locked; UI atual não é uma árvore profissional |
| Sockets | existente como dado | não equivale a luz, VFX ou trigger funcional |
| Camera/parallax | existente como dados e preview | deve ser preservado e testado como composição, sem prometer simulação completa |
| Save/load/reset/export | existente | deve ser requalificado para o contrato final e para recuperação de erro |
| Integração no preview principal | existente | commit bb0fc0d; deve ser coberta por testes e captura |
| Visualização real de assets | ausente no estado auditado | SceneObjectGraphicsItem.paint() desenha apenas polígono colorido; não há renderização QPixmap/QImage dos assets |
| Geometria inicial de drop | parcial | assets dropped recebem retângulo padrão; dimensões reais não são a fonte visual final |
| Asset lifecycle | parcial | drop aceita apenas o primeiro path e exige caminho sob project_root; faltam cópia interna, biblioteca, relink, replace, thumbnails e diagnóstico completo |
| Ordem visual por z | ausente como comportamento completo | itens gráficos recebem setZValue(10.0); position.z não controla de forma efetiva a ordem visual |
| Hierarquia profissional | parcial | grupos existem no modelo, mas falta UI de árvore, pastas, tags e isolamento profissional |
| Navegação por teclado | ausente ou incompleta | não há conjunto completo comprovado de key handling, atalhos, nudge, duplicate, copy/paste, marquee e select-all no editor profissional |
| Fit Selection | incompleto | inspector expõe request_fit, mas a ligação ao comportamento do viewport precisa ser comprovada |
| Colisão no documento V2 | ausente | ferramentas de colisão existentes não são, por si, autoria de colisão integrada ao P2D-COMP-01 |
| NavMesh 2D | ausente | fora do primeiro escopo |
| Luzes e VFX reais | ausente | sockets e marcadores não são preview de luz, sombra ou efeito |
| Exportação | existente com limites | adapters devem declarar capacidades reais e rejeitar silenciosamente nenhum recurso não suportado |
| Documentação do plano | precisa de consolidação | plano histórico anterior não refletia os commits bb0fc0d e 7df73f2; este documento passa a ser a referência operacional |

### 4.1 Regra de interpretação do inventário

“Existente” significa que há implementação identificável, não necessariamente que o item já passou pelos gates finais de P2D-COMP-01. “Parcial” significa que há fundamento, mas o requisito completo ainda não pode ser aceito. “Ausente” significa que o requisito deve ser implementado ou formalmente excluído ou adiado por decisão registrada.

### 4.2 Bloqueadores técnicos atuais para declarar o produto concluído

Com base no inventário acima, os seguintes pontos bloqueiam a conclusão imediata de P2D-COMP-01:

1. renderização real de assets no viewport;
2. ciclo de vida de assets e diagnóstico de missing/external asset;
3. ordem visual efetiva e sua relação com camadas e objetos;
4. hierarquia de composição utilizável no editor;
5. navegação e produtividade por teclado e mouse;
6. ligação efetiva do fit de seleção e demais comandos expostos;
7. persistência e recovery comprovados para todos os novos estados;
8. requalificação final, build portátil e revisão humana completa.

Esses bloqueadores não devem ser resolvidos por mudança cosmética, ajuste de tolerância ou declaração textual de suporte.

---

## 5. Requisitos normativos de P2D-COMP-01

Cada requisito abaixo deve ter implementação, teste, evidência e status. O identificador não pode ser removido quando o requisito for concluído; ele deve continuar rastreável.

### 5.1 Documento, projeto e assets

| ID | Requisito obrigatório | Critério verificável |
|---|---|---|
| P2D-001 | criar composição vazia | novo documento abre com schema V2 válido e estado inicial determinístico |
| P2D-002 | abrir V2 | documento válido abre preservando todos os campos suportados |
| P2D-003 | ler V1 | documento V1 compatível abre sem mutação automática |
| P2D-004 | migrar V1 explicitamente | somente ação de save cria V2; migração registra origem e resultado |
| P2D-005 | adicionar asset | operação cria referência estável e objeto visual correspondente |
| P2D-006 | asset externo | sistema copia, relinka ou rejeita de maneira explícita; não cria referência quebrada silenciosa |
| P2D-007 | asset ausente | UI mostra diagnóstico acionável e preserva dados não afetados |
| P2D-008 | formatos suportados | cada formato tem lista declarada, teste positivo e teste negativo |
| P2D-009 | replace/relink | usuário pode reparar ou substituir referência sem corromper transformações |
| P2D-010 | biblioteca/inspeção | usuário consegue identificar assets do projeto e seu estado |

### 5.2 Composição e visualização

| ID | Requisito obrigatório | Critério verificável |
|---|---|---|
| P2D-011 | renderização real | objeto visual usa o asset real, respeitando alpha e dimensão declarada |
| P2D-012 | transformações | move, rotate, scale uniforme, flip e valores numéricos são consistentes |
| P2D-013 | seleção | estado selecionado é inequívoco e não altera o asset armazenado |
| P2D-014 | multisseleção | transformação de seleção múltipla é determinística e reversível |
| P2D-015 | ordem visual | z/layer/order produz ordem observável e persistente |
| P2D-016 | camadas | camada suporta visibilidade, lock, nome e ordem com feedback visual |
| P2D-017 | grupos | agrupar/desagrupar preserva objetos e permite edição coerente |
| P2D-018 | isolamento | ocultar/isolar não apaga nem altera o documento |
| P2D-019 | snapping | estado desligado, ligado e configuração são perceptíveis e persistentes |
| P2D-020 | zoom/pan/fit | navegação e fit funcionam pelo viewport e pelos comandos expostos |

### 5.3 Produtividade e interação

| ID | Requisito obrigatório | Critério verificável |
|---|---|---|
| P2D-021 | teclado | foco, tab order e shortcuts principais são testados no Windows |
| P2D-022 | nudge | setas deslocam com passo definido; modificadores alteram passo somente se documentado |
| P2D-023 | duplicate/delete | comandos são reversíveis e não perdem referência de asset |
| P2D-024 | copy/paste | estado copiado é válido e não cria alias indevido de identidade |
| P2D-025 | marquee/select-all | seleção por área e seleção total têm resultado determinístico |
| P2D-026 | mouse states | hover, pressed, checked, focus e disabled têm aparência e comportamento coerentes |
| P2D-027 | undo/redo | cada transação relevante retorna ao estado anterior sem drift |
| P2D-028 | erros | erro operacional não deixa transação parcial silenciosa |

### 5.4 Persistência, integração e exportação

| ID | Requisito obrigatório | Critério verificável |
|---|---|---|
| P2D-029 | save atômico | falha de escrita não destrói o último documento válido |
| P2D-030 | round-trip | save → close → open preserva visual, transforms, layers, groups e metadata suportados |
| P2D-031 | determinismo | mesma entrada gera documento e export equivalente, salvo campos explicitamente não determinísticos |
| P2D-032 | preview principal | documento ativo e estado salvo aparecem corretamente no preview integrado |
| P2D-033 | exportação genérica | estrutura exportada é validada e documentada |
| P2D-034 | adapters | Godot e Unity só declaram e exportam capacidades realmente suportadas |
| P2D-035 | compatibilidade | V1 continua legível e não é reescrito sem ação explícita |
| P2D-036 | recovery | arquivo inválido, asset ausente e versão incompatível produzem mensagem e não crash silencioso |

### 5.5 Qualidade, desempenho e governança

| ID | Requisito obrigatório | Critério verificável |
|---|---|---|
| P2D-037 | testes unitários | regras de modelo, schema, transforms e persistência têm cobertura direta |
| P2D-038 | testes de UI | ações críticas são exercitadas por teste automatizado ou probe determinístico |
| P2D-039 | conformance | G/V/B e adapters aplicáveis passam sem mascarar legacy |
| P2D-040 | captura nativa | Windows real é usado para capturas de referência |
| P2D-041 | auditoria visual | deltas são classificados e revisados por humano |
| P2D-042 | resolução/DPI | resoluções-alvo e escala relevante são verificadas |
| P2D-043 | desempenho | documento de teste, limite e resultado são registrados |
| P2D-044 | documentação | contratos, limitações, fluxo e troubleshooting estão atualizados |
| P2D-045 | commit | somente arquivos autorizados entram no commit da etapa |
| P2D-046 | seal | pacote de evidências é hasheado, extraído e revalidado independentemente |

---

## 6. Ordem obrigatória de execução

As etapas abaixo são sequenciais. Uma etapa posterior não pode ser aceita se uma etapa anterior estiver IN_PROGRESS, BLOCKED ou REJECTED.

### Etapa P2D-00 — Adoção, reconciliação e baseline local

**Objetivo:** garantir que a equipe trabalha sobre o repositório correto, o documento correto e os imutáveis corretos.

**Ações obrigatórias:**

1. provar branch, HEAD e tracked tree;
2. confirmar que untracked será preservado;
3. verificar o acesso ao pacote C3 e aos seals históricos;
4. ler este documento e registrar versão;
5. comparar o plano histórico com o estado atual e marcar divergências;
6. registrar os requisitos P2D-001 a P2D-046 no backlog rastreável;
7. confirmar que nenhuma mutação remota será feita.

**Saída obrigatória:** registro de baseline local, matriz de divergências e decisão READY ou BLOCKED.

**Não pode avançar se:** HEAD, branch ou tracked boundary forem inesperados, C3 não puder ser identificado ou existir conflito não classificado.

### Etapa P2D-01 — Contrato de assets e renderização real

**Objetivo:** transformar objetos abstratos em composição visual real baseada em assets.

**Ações obrigatórias:**

- definir formatos suportados e política de alpha;
- implementar renderização QPixmap, QImage ou equivalente no item visual;
- preservar seleção, transforms, DPI e proporção;
- definir tamanho inicial do asset sem depender de retângulo arbitrário;
- tratar caminho interno, externo, cópia, relink, replace e asset ausente;
- criar testes de asset válido, inválido, ausente, externo e duplicado;
- registrar qualquer alteração visual esperada.

**Critério de aceite:** o usuário consegue colocar um asset e vê exatamente o asset no viewport, com diagnóstico completo para casos inválidos.

**Bloqueador absoluto:** um polígono colorido representando o objeto não satisfaz P2D-011.

### Etapa P2D-02 — Ordem visual, camadas e hierarquia

**Objetivo:** tornar a organização visual determinística e editável.

**Ações obrigatórias:**

- definir a relação entre layer, group, order e position.z;
- implementar ordem visual observável e persistente;
- criar UI de layer stack compatível com uso profissional;
- garantir visibilidade, lock, reorder, rename e isolamento;
- implementar ou concluir grupos sem alterar identidade dos objetos;
- testar ciclos de reordenação e round-trip.

**Critério de aceite:** dois objetos sobrepostos podem ser reordenados de maneira previsível, o resultado aparece imediatamente, salva e reabre sem drift.

**Proibição:** alterar o significado histórico de position.z sem change record aprovado.

### Etapa P2D-03 — Navegação, seleção e produtividade

**Objetivo:** permitir uso diário eficiente e acessível.

**Ações obrigatórias:**

- conectar e comprovar fit selection, fit all, zoom e pan;
- definir foco inicial, tab order e retorno de foco;
- testar shortcuts, nudge, duplicate, delete, copy/paste e select-all;
- implementar marquee se o produto o exigir no contrato P2D-025;
- verificar mouse press/release, hover, checked, focus e disabled;
- testar múltiplas resoluções e escala DPI no Windows;
- garantir que atalhos não sejam sequestrados pelo menu principal.

**Critério de aceite:** um usuário consegue executar o fluxo de composição sem depender exclusivamente do mouse ou de controles sem foco.

### Etapa P2D-04 — Persistência, recuperação e preview integrado

**Objetivo:** assegurar que a composição sobreviva ao ciclo de uso real.

**Ações obrigatórias:**

- definir save atômico e recuperação de falha;
- validar V2, compatibilidade V1 e migração explícita;
- executar round-trip de cada campo suportado;
- testar documento inválido, versão incompatível e asset ausente;
- confirmar que o preview principal usa documento ativo e salvo correto;
- garantir que reset e cancel não destruam dados sem confirmação;
- verificar exportação e limites dos adapters.

**Critério de aceite:** fechar e reabrir o projeto produz a mesma composição lógica e visual, dentro das exceções documentadas.

### Etapa P2D-05 — Hardening de qualidade e desempenho

**Objetivo:** transformar a implementação funcional em produto confiável.

**Ações obrigatórias:**

- criar testes de regressão para cada bug corrigido;
- medir tempo de abertura, adição de asset, seleção e save em cenário mínimo e representativo;
- definir limite de falha e registrar ambiente;
- verificar memory/resource cleanup;
- executar suíte completa e gates G/V/B;
- validar que nenhuma mudança de composição reabre legacy sem classificação;
- revisar mensagens, logs e diagnóstico para operação real.

**Critério de aceite:** todos os requisitos incluídos possuem prova positiva e as falhas esperadas possuem prova negativa.

### Etapa P2D-06 — Evidência visual, build e revisão humana

**Objetivo:** provar que o produto funciona na build que será utilizada.

**Ações obrigatórias:**

- captura nativa Windows;
- auditoria visual dos artefatos;
- comparação com a baseline aprovada apropriada;
- revisão de teclado, foco, hover, checked, disabled e resolução/DPI;
- build portátil a partir do commit final;
- smoke test da build limpa;
- revisão humana de composição, asset, ordering, layers, recovery e export;
- pacote de evidências com manifest, hashes e revalidação independente.

**Critério de aceite:** revisão humana aprovada sem finding aberto que contradiga o escopo ou a qualidade esperada.

### Etapa P2D-07 — Encerramento formal

**Objetivo:** fechar o produto somente depois de todos os gates e registros.

**Ações obrigatórias:**

1. conferir a matriz P2D-001 a P2D-046;
2. conferir commit final e tracked cleanliness;
3. conferir evidências e hashes;
4. conferir documentação e changelog;
5. registrar itens fora do escopo como ADIADOS, nunca como implementados;
6. obter revisão humana e decisão do proprietário do produto;
7. gerar o registro de fechamento;
8. somente após autorização separada avaliar push, tag ou merge.

**Saída:** ACCEPTED, REJECTED ou BLOCKED. Nenhum quarto estado informal é permitido.

---

## 7. Gates obrigatórios e critérios de aceite

### 7.1 Gate de repositório

Obrigatório antes e depois de toda etapa mutável:

- branch esperada confirmada;
- HEAD registrado;
- git status --short --untracked-files=no usado para tracked cleanliness;
- exatamente os arquivos autorizados na mudança;
- git diff --check PASS;
- nenhuma limpeza de untracked;
- nenhum push, tag ou merge não autorizado.

### 7.2 Gate semântico e estrutural

Obrigatório para mudanças de editor:

- schema e contratos válidos;
- mappings e accessible names preservados quando não forem escopo;
- protected regions sem delta indevido;
- geometry-sensitive declarations sem delta indevido em lote não-G;
- comandos e shortcuts verificados;
- migração e compatibilidade verificadas;
- nenhum campo desconhecido descartado silenciosamente.

### 7.3 Gate de testes

O responsável deve executar o conjunto proporcional à mudança e registrar comando, ambiente, saída e exit code. Para o fechamento de P2D-COMP-01, a suíte completa é obrigatória.

O resultado esperado do último estado conhecido é 1758 passed / 2 skipped / 0 failed, mas esse número é uma referência histórica, não autorização para ignorar testes novos. Se novos testes forem adicionados, o resultado deve ser atualizado e explicado.

### 7.4 Gate G/V/B

Para o aggregate canônico do produto:

- G: 60/60;
- V: 12/12;
- B: 21/21;
- total: 93/93;
- blocking: false.

Qualquer FAIL legacy mixed deve permanecer visível com produtor, motivo, ownership e decisão. Um adapter canônico PASS não apaga o FAIL legacy.

### 7.5 Gate visual e captura

Captura é obrigatória em Windows nativo para o fechamento final. A auditoria deve verificar:

- clipping;
- posicionamento e alinhamento;
- proporção e alpha dos assets;
- seleção e handles;
- layer e ordering visíveis;
- foco e keyboard cues;
- hover, checked e disabled;
- mensagens de erro;
- DPI e resoluções-alvo;
- ausência de delta visual fora do escopo.

Deltas por cursor, status ao vivo ou estado transitório não podem ser mascarados. Devem ser localizados, classificados e registrados.

### 7.6 Gate de build

A build portátil deve ser gerada a partir do commit final aceito, não de um worktree com alterações não commitadas. O teste deve usar um diretório separado e, quando possível, um ambiente limpo.

O pacote da build deve conter versão e commit identificáveis, instrução de execução, dependências empacotadas e registro de smoke test. A build não pode ser chamada de release se qualquer gate anterior estiver aberto.

### 7.7 Gate de revisão humana

A revisão humana é obrigatória mesmo que todos os testes automatizados passem. O revisor deve executar o fluxo real:

1. abrir ou criar composição;
2. adicionar asset;
3. selecionar e multisselecionar;
4. mover, transformar, duplicar e remover;
5. reordenar e organizar camadas e grupos;
6. navegar por teclado e mouse;
7. verificar foco, hover, checked e disabled;
8. salvar, fechar e reabrir;
9. testar asset ausente e erro;
10. visualizar no preview principal;
11. exportar e inspecionar o resultado;
12. repetir nas resoluções-alvo.

Cada finding deve conter reprodução, impacto, evidência, classificação e decisão. “Pareceu bom” não é registro de revisão.

---

## 8. Evidência, rastreabilidade e pacote de entrega

### 8.1 Regra de evidência

Cada requisito aceito deve apontar para pelo menos uma evidência adequada. Um screenshot sem teste não comprova persistência. Um teste unitário sem captura não comprova aparência. Um log de build sem revisão humana não comprova usabilidade.

### 8.2 Estrutura mínima do pacote

O pacote final deve possuir, no mínimo:

- 00-baseline — HEAD, branch, tracked status, ambiente e imutáveis;
- 01-tests — suíte, testes focais, testes negativos e logs;
- 02-conformance — G, V, B, aggregate e condições legacy;
- 03-capture — capturas Windows nativas e metadados;
- 04-visual-audit — relatório visual e classificação dos deltas;
- 05-human-review — checklist preenchido, findings e decisão;
- 06-build — pacote portátil, hash e smoke test;
- 07-docs — documento normativo, changelog, ADRs e matriz de requisitos;
- manifest.json — hashes, tamanhos, tipos, origem e relação com requisitos;
- manifest.sha256 — hash do manifest;
- seal.zip — pacote final;
- seal.zip.sha256 — hash do pacote.

O nome dos diretórios pode variar somente se a mudança for registrada. O conteúdo e a rastreabilidade não podem ser reduzidos.

### 8.3 Manifest obrigatório

O manifest deve declarar:

- produto e versão;
- branch e commit;
- documento normativo e versão;
- baseline C3 e seus hashes;
- eixo primário e eixos impactados;
- classificação da mudança;
- requisitos atendidos;
- requisitos adiados e justificativa;
- arquivos modificados;
- resultados G/V/B;
- suíte completa;
- captura, auditoria e revisão humana;
- condições legacy;
- hash de cada artefato;
- timestamp e ambiente;
- responsável pela geração e pela revisão.

É proibido declarar byte-identical se houver qualquer exceção de estado. A exceção deve aparecer com bbox, origem, classificação e decisão.

### 8.4 Revalidação independente

Antes do seal, o pacote deve ser extraído em diretório separado e revalidado:

1. recalcular hash de todos os artefatos;
2. comparar com o manifest;
3. recalcular hash do manifest;
4. recalcular hash do ZIP;
5. confirmar que todos os caminhos esperados existem;
6. confirmar que nenhum arquivo foi omitido;
7. confirmar tracked cleanliness do repositório;
8. registrar sucesso ou falha.

---

## 9. Regra de entrega não parcial

### 9.1 Estados permitidos

Cada requisito e cada etapa deve estar em exatamente um dos estados:

| Estado | Significado |
|---|---|
| NOT_STARTED | não iniciado; nenhuma alegação de implementação |
| IN_PROGRESS | trabalho em andamento; não pode ser apresentado como disponível |
| BLOCKED | dependência ou falha impede avanço; exige descrição |
| ACCEPTED | todos os gates e evidências obrigatórios passaram |
| REJECTED | revisão encontrou falha ou evidência insuficiente |
| SUPERSEDED | substituído por mudança formal, com histórico preservado |
| DEFERRED | fora do escopo atual por decisão explícita; não é implementado |

Não usar “done with limitations” como estado. Limitações podem existir somente se forem compatíveis com o escopo aceito e estiverem registradas como comportamento suportado ou DEFERRED.

### 9.2 Critério para declarar uma etapa completa

Uma etapa é ACCEPTED somente quando:

- todos os requisitos da etapa têm status definido;
- nenhum requisito obrigatório está IN_PROGRESS, BLOCKED ou REJECTED;
- todos os gates da etapa têm resultado;
- todas as divergências têm classificação;
- o commit foi feito após a verificação;
- a requalificação pós-commit passou;
- os artefatos estão preservados;
- a revisão humana foi feita quando exigida;
- o registro de aceite foi assinado pelo responsável e pelo proprietário do produto.

### 9.3 Falha em qualquer ponto

Se um gate falhar:

1. a etapa permanece aberta;
2. o resultado é registrado exatamente como ocorreu;
3. a causa é investigada;
4. a correção é implementada em escopo controlado;
5. os gates afetados são repetidos;
6. as evidências antigas são preservadas e marcadas como superseded quando necessário;
7. somente após nova aceitação a etapa pode avançar.

Não se pode corrigir um FAIL apagando o log, mudando tolerância, trocando referência ou removendo o teste sem decisão formal de mudança.

---

## 10. Protocolo obrigatório para dúvidas e divergências

Como o produto deve evitar suposições e alucinações, qualquer incerteza deve seguir este protocolo:

1. declarar a dúvida em linguagem concreta;
2. indicar qual requisito, contrato, arquivo ou evidência está envolvido;
3. fazer apenas verificações read-only para reduzir a incerteza;
4. não editar código com base em hipótese não confirmada;
5. se a dúvida permanecer material, perguntar ao proprietário do produto;
6. registrar a resposta como decisão, incluindo data e impacto;
7. atualizar a matriz de requisitos se a resposta alterar escopo;
8. somente então implementar.

O agente de desenvolvimento pode escolher detalhes internos que não alterem produto, contrato, baseline, API, UX, persistência ou evidência. Quando o detalhe tiver qualquer um desses impactos, a decisão deve ser explicitamente confirmada.

### 10.1 Dúvidas que bloqueiam sem resposta

- significado de uma propriedade que pode alterar compatibilidade;
- mudança de comportamento de shortcut;
- formato novo de persistência;
- alteração de baseline visual ou geométrica;
- inclusão de tilemap, navmesh, luz ou runtime fora do escopo P2D-COMP-01;
- escolha entre copiar asset ou manter referência externa quando isso muda o contrato do projeto;
- qualquer alteração remota ou publicação.

### 10.2 Decisões técnicas internas permitidas

- nome de uma classe privada;
- decomposição interna de um método;
- organização de testes que preserve a mesma observabilidade;
- escolha de uma estrutura de cache sem alteração do contrato;
- refatoração sem mudança de comportamento, desde que os gates provem equivalência.

---

## 11. Matriz de rastreabilidade e modelo de registro

### 11.1 Campos obrigatórios por requisito

Cada linha de rastreabilidade deve conter:

| Campo | Obrigatório |
|---|---|
| ID do requisito | sim |
| descrição literal | sim |
| etapa | sim |
| arquivos e símbolos | sim |
| teste positivo | sim |
| teste negativo | quando aplicável; obrigatório para erro e recovery |
| evidência | sim |
| status | sim |
| owner | sim |
| revisão humana | quando visual ou interativa |
| observações | sim quando houver exceção |

### 11.2 Registro de etapa

O registro de cada etapa deve seguir este formato:

ETAPA: P2D-XX
DOCUMENTO LIDO: NEOENG_EDITOR_COMPOSICAO_2D_NORMATIVO_2026-08-27.md
VERSÃO DO DOCUMENTO: 1.0
DATA/HORA LOCAL:
BRANCH:
HEAD ANTES:
TRACKED BOUNDARY ANTES:
ESCOPO AUTORIZADO:
REQUISITOS COBERTOS:
ARQUIVOS AUTORIZADOS:
TESTES EXECUTADOS:
G/V/B:
CAPTURA/AUDITORIA:
REVISÃO HUMANA:
FINDINGS:
DIVERGÊNCIAS:
COMMIT:
HEAD DEPOIS:
TRACKED BOUNDARY DEPOIS:
DECISÃO: ACCEPTED | REJECTED | BLOCKED | DEFERRED
RESPONSÁVEL:
APROVAÇÃO DO PROPRIETÁRIO:

Campos vazios significam evidência ausente e bloqueiam o aceite; não podem ser preenchidos com N/A sem justificativa objetiva.

### 11.3 Registro de finding

FINDING ID:
REQUISITO AFETADO:
COMO REPRODUZIR:
RESULTADO OBSERVADO:
RESULTADO ESPERADO:
IMPACTO: G | V | B | H | X
SEVERIDADE:
EVIDÊNCIA:
CAUSA:
CORREÇÃO OU DECISÃO:
STATUS: OPEN | FIXED | ACCEPTED_EXCEPTION | DEFERRED
RETESTE:
REVISOR:

---

## 12. Comandos e ambiente de qualificação

Os comandos abaixo são referências operacionais. Antes de executar, confirmar que os caminhos e scripts ainda existem. Se um comando estiver desatualizado, registrar a divergência e atualizar a referência por mudança documental controlada.

Diretório de trabalho: REPO_ROOT
Python de qualificação: REPO_ROOT/.venv/Scripts/python.exe

Comandos mínimos:

- git rev-parse HEAD
- git branch --show-current
- git status --short --untracked-files=no
- git diff --check
- .venv/Scripts/python.exe -m pytest -q

Para Qt nativo Windows, usar QT_QPA_PLATFORM=windows.
Para produtores Stage9 offscreen, usar QT_QPA_PLATFORM=offscreen.
Em ambos os casos, usar PYTHONPATH apontando para a raiz do repositório e restaurar o ambiente depois da execução.

Os logs devem informar plataforma, Python, PySide6, pytest, commit e timestamp.

---

## 13. Responsabilidades e aprovações

### 13.1 Responsável de implementação

Deve ler este documento, executar a etapa autorizada, preservar imutáveis, produzir testes e evidências, relatar dúvidas e não declarar aceite por conta própria quando a revisão humana for obrigatória.

### 13.2 Revisor técnico

Deve conferir diff, testes, contratos, gates, manifest, hashes e coerência entre código e documentação. Deve rejeitar qualquer afirmação que não seja suportada por evidência.

### 13.3 Revisor humano de produto

Deve usar a build real, executar os fluxos definidos, registrar findings e decidir se a experiência atende ao produto. Não deve substituir o gate automatizado nem ser substituído por ele.

### 13.4 Proprietário do produto

Decide escopo, mudanças de baseline, adiamentos, exceções e aceite final. Autorizações remotas devem ser separadas do aceite local.

---

## 14. Checklist final de P2D-COMP-01

O produto só pode ser declarado concluído quando todas as caixas abaixo tiverem evidência associada:

- [ ] este documento foi lido na versão vigente antes da etapa final;
- [ ] branch, HEAD e tracked boundary foram registrados;
- [ ] C3 continua íntegro e imutável;
- [ ] P2D-001 a P2D-046 possuem status final;
- [ ] nenhum requisito obrigatório está aberto, bloqueado ou rejeitado;
- [ ] assets reais aparecem no viewport;
- [ ] asset lifecycle e missing asset estão cobertos;
- [ ] ordem visual, layers e groups funcionam e persistem;
- [ ] seleção, multisseleção, transforms e inspector funcionam;
- [ ] zoom, pan, fit, foco, atalhos e keyboard navigation funcionam;
- [ ] hover, checked, focus e disabled foram revisados em Windows;
- [ ] undo/redo, duplicate, delete e copy/paste foram testados;
- [ ] save/load/round-trip/recovery passaram;
- [ ] preview principal está integrado e correto;
- [ ] exportação e limites dos adapters estão documentados;
- [ ] suíte completa passou;
- [ ] G60/60, V12/12 e B21/21 passaram;
- [ ] legacy FAILs permanecem visíveis e classificados;
- [ ] capturas Windows foram produzidas;
- [ ] auditoria visual foi concluída;
- [ ] revisão humana foi concluída nas resoluções-alvo;
- [ ] build portátil foi gerada a partir do commit final;
- [ ] smoke test da build passou em diretório separado;
- [ ] manifest, hashes, extração e rehash passaram;
- [ ] documentação, changelog e matriz foram atualizados;
- [ ] commit final contém somente arquivos autorizados;
- [ ] não houve push, tag ou merge sem autorização;
- [ ] proprietário do produto registrou decisão final.

Se uma caixa não puder ser marcada, a decisão correta é manter o produto aberto ou adiar formalmente o requisito. Não é correto entregar como concluído.

---

## 15. Formulário de aceite formal

PRODUTO: P2D-COMP-01 — Editor Profissional de Composição 2D Baseado em Objetos
DOCUMENTO NORMATIVO: NEOENG_EDITOR_COMPOSICAO_2D_NORMATIVO_2026-08-27.md
VERSÃO DO DOCUMENTO:
COMMIT FINAL:
BUILD / ARTEFATO:
MANIFEST SHA-256:
ZIP SHA-256:

RESULTADO DOS EIXOS:
G: ____ / 60
V: ____ / 12
B: ____ / 21
TOTAL: ____ / 93
BLOCKING: true | false

REQUISITOS ACEITOS:
REQUISITOS ADIADOS:
FINDINGS ACEITOS COMO EXCEÇÃO:
FINDINGS ABERTOS:
CONDIÇÕES LEGACY PRESERVADAS:

DECISÃO: ACCEPTED | REJECTED | BLOCKED | DEFERRED

RESPONSÁVEL DE IMPLEMENTAÇÃO:
REVISOR TÉCNICO:
REVISOR HUMANO:
PROPRIETÁRIO DO PRODUTO:
DATA/HORA:
OBSERVAÇÕES:

Uma assinatura sem os campos de evidência preenchidos não constitui aceite.

---

## 16. Registro de decisões já consolidadas

Este registro preserva decisões para impedir reinterpretação posterior:

- C3 foi congelado antes da modernização para impedir que a UI reescrevesse o referencial.
- A correção histórica do rail de 61 px foi classificada como NOT_APPLICABLE, porque probes atuais mostram 84 px; 61 px é evidência H histórica.
- M2.1 foi tokens-only.
- M2.2 refinou hierarquia visual sem geometria; a divergência de cursor/status foi classificada como CAPTURE_STATE_VARIANCE_LIVE_CURSOR_STATUS.
- M2.3A-r1 modernizou somente glyphs shell-critical, com revisão de focus para não colidir visualmente com fit.
- Runtime instrumentation observou 32 de 34 glyphs restantes; collider_edit e scenario continuam not-seen.
- M2.3B1-r1 mudou somente parallax, xray_1 e zoom_100.
- M2.3B2 foi ACCEPT / NO_CHANGE para add, remove, up, down, lock e visible.
- M2.3B3-r1 alterou somente collision_auto_generate, collision_brush e polygon_edit.
- A integração do documento profissional no preview principal foi consolidada em bb0fc0d.
- A integração do menu e toolbar foi consolidada em 7df73f2.
- O trabalho permanece local; não há autorização geral para publicação remota.

---

## 17. Ponto exato de continuidade

Após a emissão deste documento, a próxima ação correta não é iniciar uma funcionalidade aleatória nem declarar o editor concluído. É executar a Etapa P2D-00 de reconciliação e, se os valores permanecerem consistentes, abrir a Etapa P2D-01 para resolver a visualização real de assets.

O próximo responsável deve:

1. ler este documento integralmente;
2. provar o estado do repositório;
3. comparar a implementação real com a seção 4;
4. confirmar ou corrigir a matriz de requisitos por evidência;
5. registrar o checkpoint;
6. perguntar ao proprietário somente se surgir dúvida material sobre contrato, escopo, baseline ou UX;
7. implementar somente o escopo autorizado;
8. fechar a etapa com o gate correspondente antes de avançar.

O editor não deve ser chamado de “profissional de composição 2D completo” antes que P2D-COMP-01 tenha decisão ACCEPTED no formulário da seção 15.

---

## 18. Declaração de encerramento deste documento

Este documento foi escrito para reduzir ambiguidade, não para eliminar a necessidade de engenharia, testes ou julgamento humano. Ele define uma disciplina verificável: toda etapa tem entrada, saída, evidência, gate, responsável e decisão; todo imutável permanece explícito; toda lacuna permanece visível; toda dúvida material deve ser resolvida antes de alterar o produto; toda entrega incompleta deve permanecer aberta, bloqueada ou adiada, nunca mascarada como concluída.

Qualquer revisão futura deve preservar este princípio. Se uma revisão reduzir requisitos, remover evidências, relaxar gates ou apagar histórico, ela própria deve ser tratada como mudança de baseline e submetida ao protocolo formal da seção 2.5.

**Fim do documento normativo.**
