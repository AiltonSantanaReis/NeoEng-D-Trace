# Reconciliação do plano detalhado da interface — Etapas 0–7

**Data:** 2026-08-22
**Estado:** `AUDITORIA CONCLUÍDA / IMPLEMENTAÇÃO NÃO ALTERADA`
**SHA auditado:** `b5bacf8a598716d28ed6035da97c2c6b49e3ce1f`
**Escopo:** comparar o plano detalhado originalmente produzido na conversa com o plano vivo e com o código, testes e evidências versionados.

## Autoridade e proveniência

O plano detalhado recebido como anexo nesta auditoria possui 595 linhas e
SHA-256 `3AA464A0FC123EB2FA52BE1511A5725970F29BF070A5EC490F8FA5FAD1E4287A`.
Ele não estava versionado no repositório. O plano vivo atual possui 294 linhas e
SHA-256 `D0F54A88EB941FC3FDB9C8428D207E567C323C8625A5566F1E8578D8C22D6F9B`.

O histórico Git comprova a criação do plano vivo nos commits `5494bdc`
(16:32:08) e `5879d18` (16:34:11), mas não contém o histórico da conversa das
16:12 nem prova o instante exato em que o plano detalhado foi resumido. A
diferença de conteúdo, portanto, é fato; a sequência exata da conversa é uma
limitação de proveniência e não foi inventada.

Este relatório não reescreve snapshots históricos. A autoridade operacional
continua subordinada a:

- `docs/POLITICA_QUALIDADE_E_EVIDENCIAS.md`;
- `docs/POLITICA_NAO_REGRESSAO.md`;
- `docs/PLANO_MESTRE_ESTABILIZACAO.md`;
- `docs/MATRIZ_RISCOS_ESTABILIZACAO.md`;
- `.github/pull_request_template.md` e `.github/workflows/ci.yml`.

O plano detalhado original passa a ser a referência de completude dos requisitos
da interface. O plano vivo define ordem, gates e estado atual, mas não pode
reduzir requisitos sem registrar uma decisão explícita de escopo reduzido.

## Método de verificação

Foram cruzados, no SHA auditado:

- regras globais e documentos vivos;
- histórico e conteúdo do plano vivo;
- código de `src/ui`, `src/core` e componentes relacionados;
- testes específicos e suíte completa;
- auditores nativos e auditor visual;
- capturas, manifestos e hashes versionados;
- relatórios pré-merge e encerramentos pós-merge.

A validação pós-merge já executada no mesmo SHA registrou `2397 files` no
baseline Git-blob, `104 manifests validated` e `1612 passed, 2 skipped`. Esses
resultados não foram reutilizados para afirmar que um requisito visual ausente
está concluído; eles somente confirmam a integridade e a não regressão geral do
estado atual.

## Classificação por etapa frente ao plano detalhado original

### Etapa 0 — Baseline visual e contrato de escopo

**Estado:** `APROVADO — SOMENTE BASELINE`

Comprovado: capturas nas três resoluções, estados de aplicação, dimensões,
transparência, hashes, clipping, geometria Qt, sobreposição e paleta. O
encerramento pós-merge está em `ETAPA_0_INTERFACE_MODERNA_ENCERRAMENTO_POS_MERGE_2026-08-21.md`.

Limite real: a confirmação humana independente foi registrada como
`NOT_CONFIRMED`. Isso não invalida a caracterização automatizada, mas impede
interpretar a Etapa 0 como aprovação estética da interface.

### Etapa 1 — Sistema visual e tokens de tema

**Estado:** `APROVADO NO ESCOPO COMPROVADO`

Comprovado: tokens centralizados, contraste, estados de foco/interação, QSS
derivado dos tokens, paleta contextual e ausência de borda laranja fixa sem
função. Os testes e o auditor da etapa estão versionados e o ciclo pós-merge
foi encerrado.

Não foi inferido nesta etapa que todas as resoluções de DPI estejam aprovadas;
essa matriz pertence aos gates específicos de responsividade da Etapa 9.

### Etapa 2 — Biblioteca de ícones e ações

**Estado:** `PARCIAL FRENTE AO PLANO DETALHADO`

Comprovado: catálogo vetorial interno, fallback textual, tooltips, nomes
acessíveis, ações principais e renderização nos tamanhos previstos pelo código
(16, 20 e 24 px; também há variante interna de 32 px). O encerramento atual
está corretamente limitado ao escopo que foi testado.

Não comprovado: matriz visual de 100%, 125%, 150% e 200% de DPI para todo o
catálogo, exigida pelo plano detalhado. Os testes existentes validam presença,
fallback e acessibilidade, mas não constituem essa matriz física completa.

Condição de retomada: gerar capturas reais por DPI, validar hashes e clipping,
revisar visualmente os ícones e repetir os gates sem alterar thresholds.

### Etapa 3 — Barra lateral de ferramentas

**Estado:** `APROVADO NO ESCOPO COMPROVADO`

Comprovado: toolbar vertical orientada a ações, seleção exclusiva, estados
ativo/desabilitado, tooltips, nomes acessíveis, foco de teclado, atalhos e
capturas nas resoluções alvo. A lógica pública e os sinais existentes foram
preservados.

Limite: a matriz completa de DPI e a auditoria global de acessibilidade não
foram atribuídas artificialmente a esta etapa; permanecem nas Etapas 9 e 10.

### Etapa 4 — Barra superior agrupada

**Estado:** `APROVADO NO ESCOPO COMPROVADO`

Comprovado: grupos semânticos, separadores nativos, ações compartilhadas com
menus, ícones, tooltips, acessibilidade, atalhos e compatibilidade das três
toolbars públicas. A implementação usa uma toolbar principal e toolbars
contextual/render, preservando contratos existentes; isso é uma composição
compatível, não uma alegação de identidade pixel-a-pixel com a referência.

Fora do escopo preservado: HUD, gizmo, painéis laterais e editor de cenário
separado.

### Etapa 5 — Viewport e HUD

**Estado:** `APROVADO NO ESCOPO COMPROVADO`

Comprovado: estado view/zoom na status bar, HUD textual legado fora do fluxo
principal, atualização real de Lit/X-Ray/Fit/1:1, preservação do gizmo e dos
overlays, proteção contra clipping/sobreposição e 12 estados Windows nas três
resoluções. A limitação de fontes do backend offscreen foi declarada e não foi
usada como falso PASS.

Fora do escopo preservado: implementação do gizmo profissional e reforma
completa dos painéis laterais.

### Etapa 6 — Gizmo profissional

**Estado:** `PARCIAL FRENTE AO PLANO DETALHADO`

Comprovado: hit-test corrigido, translação XY, rotação Z, escala uniforme e por
eixo, snapping transacional, nudges de teclado, seleção múltipla, feedback,
clamp no viewport, acessibilidade do toggle, undo/redo e auditoria Windows.

Não comprovado integralmente frente ao plano detalhado: matriz de DPI
100/125/150/200, todos os fluxos de edição de vértice individual pelo gizmo e
um painel numérico editável completo para Position/Rotation/Scale. A existência
de código ou de um teste parcial não prova esses requisitos ausentes.

Condição de retomada: adicionar testes positivos/negativos e capturas reais
para cada requisito faltante, sem alterar a matemática existente sem aprovação
específica.

### Etapa 7 — Painéis laterais

**Estado:** `PARCIAL FRENTE AO PLANO DETALHADO`

Comprovado: melhoria da toolbar compacta do `GroupsPanel`, preservando os oito
comandos, handles legados, tooltips, traduções, acessibilidade, seleção e
capturas nas três resoluções. O encerramento pós-merge está corretamente
registrado como aprovado somente no escopo definido.

Não implementado neste escopo: reestruturação completa e comprovada de
`Objects`, `Layers`, `Groups`, `Collision` e do inspector conforme o plano
detalhado. Não houve evidência objetiva suficiente para alterar genericamente
`SidePanel`, rolagem, larguras ou `CollisionPanel`, e por isso esses itens não
foram declarados prontos.

Condição de retomada: auditar cada painel individualmente, corrigir somente
defeitos reproduzidos, testar seleção/edição/rolagem/estados e gerar capturas
reais antes de qualquer nova aprovação.

## Regra de progressão corrigida

Nenhuma Etapa 8 ou posterior pode ser iniciada como se as Etapas 0–7 estivessem
integralmente concluídas. A sequência operacional correta é:

1. concluir a matriz de DPI e os requisitos remanescentes da Etapa 2;
2. concluir os requisitos comprovadamente ausentes da Etapa 6;
3. concluir os painéis ainda parciais da Etapa 7;
4. executar novamente os gates completos e a auditoria final das Etapas 0–7;
5. somente depois iniciar a Etapa 8.

Cada retomada deve ler a governança, registrar baseline e SHA, executar testes
positivos e negativos, gerar artefatos hashados, revisar capturas e documentar
limitações. CI verde é requisito necessário, mas não substitui a análise dos
artefatos nem a revisão humana exigida.

## Decisão

O plano foi reconciliado sem alterar código, testes, thresholds, governança ou
histórico. As aprovações anteriores continuam válidas somente nos escopos
explicitamente comprovados. Frente ao plano detalhado original, as Etapas 2, 6
e 7 ficam `PARCIAIS`; portanto, não há autorização técnica para avançar à
Etapa 8 antes de fechar essas lacunas.
## Adendo pós-merge — Etapa 2 — 2026-08-23

A conclusão 'PARCIAL FRENTE AO PLANO DETALHADO' acima é o snapshot histórico
da auditoria de 2026-08-22 e não foi reescrita. A lacuna específica da Etapa 2
foi fechada posteriormente, com autorização e ciclo completo:

- Auditoria real da matriz DPI 100/125/150/200% no commit técnico
  033278c52c12279c59b39fb9766fa5a02dcab5ed.
- 144 células por escala, clipping 0, hashes e auditor visual PASS.
- Evidência: docs/evidence/ETAPA_2_ICONES_DPI_2026-08-23.md.
- PR #150, CI run 32613109759, jobs Linux e Windows 'success'.
- Merge: bcb0951ee05c41b03eae2a66e712d1f041cde7f8.
- Pós-merge: baseline Git-blob de 2571 arquivos, 109 manifests íntegros e
  suíte Windows '1617 passed, 2 skipped'.

Para o estado operacional atual, a Etapa 2 está 'APROVADA NO ESCOPO
COMPROVADO'; as Etapas 6 e 7 continuam parciais conforme a auditoria original.
A Etapa 8 continua bloqueada até que as lacunas das Etapas 6 e 7 sejam fechadas.
A aprovação da Etapa 2 não é aprovação de release e a matriz não representa uma
troca física de monitor/DPI global do Windows.
## Addendum de reconciliação — Etapa 6 — 2026-08-23

O estado anterior PARCIAL FRENTE AO PLANO DETALHADO permanece como snapshot histórico. No estado vivo, as lacunas foram implementadas localmente no checkpoint fec2ee1b068b46d2cfe096519a0526ea576059ec: gizmo XY contextual para vértice individual, inspector numérico atômico e rolagem estrutural do painel. A auditoria Qt nativa Windows produziu 24 capturas, 0 findings, hashes e geometrias reais nas três resoluções. A classificação atual é PASS_LOCAL; PR, CI, merge, pós-merge e revisão visual humana ainda são gates pendentes. A Etapa 8 continua bloqueada até o fechamento remoto e a reconciliação pós-merge.
### Atualização da Etapa 6 — reconciliação do primeiro CI da PR #152

O primeiro CI remoto da Etapa 6 falhou de forma legítima no gate de tipagem em ambos os sistemas. A causa foi corrigida sem bypass ou alteração de regras; a validação local pós-correção passou, mas a Etapa 6 continua pendente de novo CI, revisão e pós-merge.
### Encerramento pós-merge da Etapa 6

A Etapa 6 foi merged em `ebdb889bc415eca4ea263a98e59551645130fbd5`, com CI Linux/Windows e validação pós-merge local aprovados. O escopo foi encerrado sem reclassificar snapshots históricos e sem aprovar release.

## Addendum de reconciliação — Etapa 7 — 2026-08-23

O estado histórico `PARCIAL FRENTE AO PLANO DETALHADO` não foi reescrito. A
retomada fechou localmente os itens reproduzidos nos quatro painéis: toolbar
compacta com contratos, seleção real, inspector habilitado, rolagem, estados,
tooltips e menus de contexto. O checkpoint técnico é `8334f87bd58ff2e33c5e7041217bf6354844bd2e`.

A suíte Windows passou com `1625 passed, 2 skipped`; o auditor Qt nativo gerou
12 capturas e `0 findings`; Pillow/OpenCV validaram 12/12 PNGs e os hashes
foram indexados no pacote oficial. A classificação é `PASS_LOCAL_AUTOMATED`,
não aprovação formal: revisão visual humana está `BLOQUEADA / NÃO EXECUTADA`
por ACL do visualizador e push, PR, CI, merge e pós-merge ainda são pendentes.
A Etapa 8 permanece bloqueada.


## Addendum — revisão visual humana da Etapa 7 — 2026-08-23

A revisão humana das 12 capturas reais foi concluída com `0` clipping
irreversível, `0` sobreposição estrutural e `0` artefatos visuais bloqueantes.
A rolagem observada nas resoluções compactas foi considerada acessibilidade
funcional, não clipping. Menus de contexto permanecem comprovados por teste Qt
focal, não por captura de menu aberto.

Classificação atual: `PASS_LOCAL_AUTOMATED + HUMAN_VISUAL_PASS`; PR #154 continua
draft e o ciclo de promoção, merge e pós-merge ainda é obrigatório.


## Encerramento pós-merge — Etapa 7 — 2026-08-23

A Etapa 7 foi encerrada no escopo definido após a PR #154, CI Linux/Windows
aprovado no run `32634474078`, merge `bf6da772afb659e0801b869f2ce5a0740918d94e` e
validação independente no `main`. A validação pós-merge confirmou `110
manifests`, baseline `2618 files` e `1625 passed, 2 skipped`.

O plano de reconciliação das Etapas 0–7 está concluído no escopo
documentado. Isso não aprova release; as Etapas 8–14 seguem planejadas e
devem obedecer aos mesmos gates.
