# E00 — reconciliação de dependências e rastreabilidade

**ID:** DOC-DECISION-E00-DEPENDENCIES-20260907.
**Versão:** 1.0. **Data:** 07/09/2026.
**Decisão de planejamento:** aprovada pelo proprietário.
**Execução:** IN_PROGRESS / PREPARATORY_ONLY; E00 aberta, E01 não iniciada.
**Base documental:** `e2cab04cf375f455e96205e0bcd96a62507420ed`.
**Branch:** `Ailton/e00-plan-adoption-20260907`.

## 1. Aprovação, autoridade e limite

O proprietário respondeu literalmente “aprovado” à recomendação de antecipar
a fundação de viewport/interface para E01, preservar instalação limpa Linux
como qualificação técnica interna e formalizar correspondências de IDs sem
confundir planejamento com evidência. Esta é a decisão formal de resolução
dos três pontos, não autorização para implementar funcionalidades ou publicar.

Dependências: [governança](GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md),
[índice canônico](INDICE_DOCUMENTAL_ATIVO_CANONICO_2026-08-24.md),
[plano profissional](PLANO_PRODUTO_PROFISSIONAL_NORMATIVO_COMPLETO_2026-08-24.md),
[escopo final](REQUISITOS_EDITOR_CENARIOS_COMPLETO_2026-08-30.md),
[fundação P2D](NEOENG_EDITOR_COMPOSICAO_2D_NORMATIVO_2026-08-27.md),
[adendo de IDs](ADENDO_NORMATIVO_AUTOMACAO_E_IDS_2026-08-24.md),
[registro canônico](REGISTRO_IDS_PRODUTO_PROFISSIONAL_CANONICO_2026-08-24.yaml),
[plano de extensões](PLANO_EVOLUCAO_EDITOR_2D_2_5D_3D_E_LINHAS_INDEPENDENTES_2026-08-29.md),
[ADR runtime](ADR_RUNTIME_CENARIOS_EFEITOS_2026-08-20.md),
[preservação](POLITICA_NAO_REGRESSAO.md), [evidências](POLITICA_QUALIDADE_E_EVIDENCIAS.md)
e [adoção anterior](DECISAO_E00_ADOCAO_PLANO_INCREMENTAL_2026-09-07.md).

Esta decisão especializa a seção 6.2 do [plano incremental](PLANO_EVOLUCAO_INCREMENTAL_PRESERVACAO_2026-09-07.md)
e a interpretação de instalação em F11. O texto integral incorporado e os
documentos anteriores permanecem preservados. Nenhum requisito obrigatório,
threshold, teste, snapshot, baseline C3 ou aceite histórico é removido.

O commit de inclusão será identificável pelo histórico Git deste documento;
não se antecipa SHA. A aprovação de direção não é revisão humana da build.

## 2. Antes e depois: ordem de trabalho

Antes, E01 previa contrato, backend isolado e cena independente; E08-A previa
a integração ampla do renderer. F04/F05 exigem viewport real e UI qualificada
antes de F06. Aceitar E01 sem resolver essa fundação deixaria a ordem ambígua.

Depois, E01 passa a conter cinco sublotes sequenciais. E01-D/E01-E são
subdivisões de planejamento, não novos requisitos ou funcionalidades aceitas.

| Fase preservada | Sublote responsável | Entrada e condição de saída, cumulativas às fontes |
|---|---|---|
| F01 | E01-A | E00 encerrada; contrato, limites, IDs e matriz sem ambiguidade aprovados |
| F02 | E01-B | F01 aceita; vertical slice real Windows/Linux, ADR, métricas e automação de evidências |
| F03 | E01-C | F02 aceita; domínio independente da UI, criar/salvar/carregar/validar/migrar/comparar |
| F04 | E01-D | F03 aceita e gate do adendo aprovado em Windows/Linux; SceneViewport real e cena de dez entidades editável, salvável e reproduzível |
| F05 | E01-E | F04 aceita; interface completa do escopo F05, revisão humana nas resoluções contratadas e usabilidade |
| F06 | E08-B | E07 aceita e integração E08-A requalificada; câmera/profundidade/paralaxe e equivalência runtime |
| F07 | E08-C | F06 aceita; luz ambiente/direcional/pontual, materiais e mudança de pixels comprovada |
| F08 | E08-D, partículas | F07 aceita; emissão real, lifecycle, seed, replay e stress |
| F09 | E08-E | F08 aceita; playback e execução fora da UI, exportação e comparação visual |
| F10 | E08-D, composição final | F09 aceita; passes de máscaras/blending/pós-processamento, ordem/custo/fallback/testes |
| F11 | E11-A | E10 aceita; instalação limpa Windows/Linux, manifesto, recursos, logs e recuperação |
| F12 | E11-B | F11 aceita; conjunto integral de qualidade previsto na fase, sem exclusão de gates |
| F13 | E11-C | F12 aceita; build, revisão humana, limitações e baseline encadeada aprovadas |

E08-D é dividido expressamente: partículas antes de F09; composição final
depois de F09. A ordem alfabética antiga dos parágrafos não autoriza executar
pós-processamento final antes da dependência. Shaders necessários a F07/F08
são infraestrutura do recurso; não constituem aceite antecipado de F10.
O vertical slice F02 continua obrigatório, incluindo luz e partículas mínimas,
sem aceitar antecipadamente F07/F08 de produto.

E01-D entrega todos os critérios de F04: render real, zoom, pan, fit, seleção,
gizmo, grade, snap, réguas, minimapa, overlays, câmera e inspector sincronizado.
E01-E entrega todos os critérios de F05, inclusive abas Objects/Layers/Groups/
Collision, linhas de camada completas, campos vetoriais, estados, atalhos e
ausência de duplicação sem contexto. Controles vazios não cumprem esses gates.
Capacidades existentes podem ser reaproveitadas somente após prova adequada.
Essa fundação não aceita tilemaps, NavMesh, prefabs nem a colisão integral E05.
Se a implementação revelar dependência material adicional, parar e registrar
controle de mudança; não criar exceção implícita a F05.

E08-A deixa de ser a primeira integração do renderer: amplia e requalifica a
fundação E01-D para efeitos avançados, ordenação e recursos das etapas E02–E07.
Permanecem exigidos cache/invalidação, recursos GPU, picking, resize, reabertura,
cleanup, comparação com cenas antigas e tratamento correto de transparência.
Nenhum backend foi escolhido; nenhuma reescrita do CanvasView foi autorizada.

## 3. Sequência E00–E13 e dependências adicionais

| Etapa | Dependência de aceite | Responsabilidade preservada |
|---|---|---|
| E00 | base preservada e qualificada, pendências próprias encerradas | consolidação, dependências e rastreabilidade |
| E01 | E00; sublotes F01 → F02 → F03 → F04 → F05 | contrato, backend, cena independente e fundação de autoria |
| E02 | E01 | primitivas, autoria, persistência e histórico |
| E03 | E02 | pacote próprio, disponibilidade e licença/proveniência |
| E04 | E03 | tilemaps, três grids, ferramentas e regras |
| E05 | E04 | colisão própria do cenário |
| E06 | E05 | NavMesh 2D e navegação real |
| E07 | E06 | entidades, componentes, hierarquia e prefabs |
| E08 | E07; F06 → F07 → F08 → F09 → F10 | composição 2.5D, iluminação, sombras e FX reais |
| E09 | E08 | imagem, vetorização, colisão e objeto de cenário |
| E10 | E09 | reconciliação integrada em Godot e Unity reais |
| E11 | E10; F11 → F12 → F13 | qualificação completa 2D/2.5D e decisão final |
| E12 | E11 e contrato 3D separado aprovado | autoria híbrida no mesmo produto |
| E13 | E12 | qualificação e encerramento da extensão híbrida |

A cadeia representa condições futuras, não fases já aceitas. P2D-COMP-01
continua dependência de fundação: conferir fechamento formal, escopo e SHA,
sem inferir conclusão pelo aceite de um sublote. Nenhuma linha independente
começa sem o aceite exigido pelas fontes. A passagem E00 → E01 continua
bloqueada pelas pendências da seção 7 desta decisão.

Testes, exportabilidade, persistência, UX, acessibilidade, segurança e regressão
são transversais em cada lote. E10 integra provas nas engines; não posterga
contratos de exportação necessários para aceitar requisitos anteriores.
Uma linha com dois responsáveis só encerra com todas as provas pertinentes.
E11 não é a primeira ocasião para descobrir falha de build ou usabilidade.

## 4. Instalação e plataformas

F11 mantém literalmente a exigência de instalação limpa em Windows/Linux.
A decisão aprovada distingue qualificação técnica de suporte público:

- Windows 11: portátil e MSI pelo fluxo oficial, instalação/primeiro uso,
  atualização quando suportada, desinstalação e preservação dos dados;
- Linux: instalação técnica interna em ambiente isolado, com artefato,
  dependências, recursos, inicialização e recuperação efetivamente exercitados;
- Linux não passa a plataforma pública; não se promete AppImage, DEB ou macOS.

Antes de F11, o protocolo deverá fixar distribuição/versão, artefato instalável,
comandos, dependências, máquina limpa, cenário de uso, logs, critérios de erro
e recuperação, SHA/hashes e responsável pela revisão. Sua definição e execução
continuam PLANNED. Instalar dependências com Poetry ou passar pytest/CI não
substitui instalação e uso do aplicativo. Sem protocolo e prova, F11 é BLOCKED.
Esta decisão não autoriza mudar scripts de build nem ampliar suporte público.

## 5. Rastreabilidade sem equivalências falsas

A [matriz de planejamento](RASTREABILIDADE_E00_DEPENDENCIAS_2026-09-07.json)
preserva individualmente os 42 IDs do escopo final, os 46 P2D e os 21 requisitos
canônicos existentes. Inclui textos literais de origem, linhas, hash da fonte,
base, etapa responsável e lacunas explícitas. Não é um pacote de execução.

As correspondências de etapas dos 42 IDs reproduzem a seção 21 do plano.
P2D-001 a P2D-046 permanecem obrigações de preservação em E00 e em todo lote
que afete sua fronteira, com reconciliação integral em E11; isso não reabre
automaticamente aceites históricos nem os estende a outro SHA.
Os 21 IDs REQ mantêm sua fase F e a responsabilidade definida na seção 2.

O registro canônico da base declara quatro associações requisito/teste/evidência.
Declaração não é execução: elas são preservadas literalmente na matriz como
referências declaradas, sem afirmar que os testes correspondentes provaram a
candidata. Os demais vínculos permanecem ausentes, nunca preenchidos por nomes
plausíveis de métodos, capturas históricas ou testes de widgets superficiais.

O coletor atual exige `requirement_id` iniciado por `REQ-`, declarado no registro,
e listas não vazias de testes/evidências. Os IDs SCN/TMAP/P2D e demais IDs de
origem não podem ser enviados diretamente como requisitos canônicos aceitos.
Não são aliases de requisitos F amplos. Seus campos `canonical_requirement_id`
ficam nulos nesta matriz, com lacuna explícita, preservando a identidade original.

Antes do gate de entrada F04, F01/F02 deverão completar o vínculo canônico
versionado dos requisitos aplicáveis, com controle de mudança, sem reutilizar
IDs, sem atribuir artificialmente todas as funcionalidades a F05 e sem relaxar
o coletor. F01 define o contrato de rastreabilidade do produto inteiro; cada
lote completa os vínculos executáveis antes de seu aceite. Este sublote resolve
a política e as correspondências de planejamento, não a rastreabilidade de execução.

Cada vínculo de execução deverá registrar: ID fonte e canônico, feature,
componente quando aplicável, arquivos/símbolos, teste positivo, teste negativo
ou justificativa objetiva, evidência com hash/tamanho, SHA auditado, build,
ambiente, comandos/resultados, owner e revisão humana quando visual/interativa.
Ausência bloqueia aceite. `PLANNED` nesta matriz é estado de qualificação
planejada, não afirmação de ausência de implementação no código existente.

## 6. Controle de mudança, verificação e rollback

Escopo: esta decisão, matriz JSON, aviso no prefácio do plano, índice canônico
v2.6 e inserções nos cinco documentos vivos (README, CHANGELOG, Plano Mestre,
matriz de riscos, índice de evidências). Manifesto de fontes atualizado somente
para esses arquivos, sem reconciliações herdadas adicionais.
Registro YAML, coletor, testes existentes, código, UI, builds, CI, dependências,
snapshots, imutáveis e texto de origem do plano: NO_CHANGE.

Verificar antes do commit: identidade/escopo exatos, integridade das fontes,
42/46/21 IDs sem perda ou duplicação, 13 fases e 14 etapas, cadeia sem ciclos,
links existentes, ausência de PASS funcional, preservação dos textos antigos,
diff --check, baseline e integridade de evidências. Exercitar negativos de
duplicação, remoção, ciclo, origem adulterada e evidência indevidamente aceita.
Testes documentais focais são DIAGNOSTIC_ONLY; não substituem suíte oficial.
O gate proporcional documental segue a seção 7.3 do normativo P2D.

Requalificar em checkout limpo do commit documental. Logs, comandos, ambiente,
hashes e snapshots integrais ficam em pacote local próprio; não inventar uma
execução Linux, CI, captura, build ou revisão humana nesta alteração documental.
Suíte funcional, cobertura, estática, segurança, G/V/B e empacotamento de produto
não são executados por este sublote e continuam obrigatórios no lote aplicável.
O responsável técnico é o agente executor desta rodada; não existe revisão independente presumida.

Rollback: revisar e reverter somente o commit documental, preservando trabalho
posterior e artefatos. A decisão anterior continua no histórico; reversão não
autoriza iniciar código com conflito reintroduzido. Não usar reset destrutivo,
limpeza de worktrees ou remoção de untracked. Não há migração de dados.

## 7. Ponto de continuidade e limites de encerramento

Esta aprovação resolve a direção de sequência, plataforma e rastreabilidade.
E00 permanece IN_PROGRESS: ainda requer qualificar a base, concluir bloqueios
do lote de localização, revisão nativa/humana no SHA/binário correto, decidir
e executar requalificação de symlinks aplicável, validar funcionalmente a
restauração e conferir o fechamento exigido de P2D-COMP-01.
Os vínculos de execução ausentes ficam explícitos para F01/F02, sem aceite.

O próximo passo após verificar este sublote é reconciliar essas pendências
com suas evidências e autorizações específicas; não iniciar E01 automaticamente.
Push, PR, merge, tag e release continuam fora desta autorização.
