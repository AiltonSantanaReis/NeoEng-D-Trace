# NeoEng-D-Trace — Decisão formal P2D-04

**Linha de produto:** P2D-COMP-01 — Editor Profissional de Composição 2D Baseado em Objetos
**Etapa:** P2D-04 — persistência, recuperação, preview integrado, exportação e orientação de coordenadas
**Data de abertura:** 30/08/2026
**Status:** OPEN — contrato proposto; implementação ainda não autorizada
**Autoridade:** decisão do proprietário do produto, subordinada ao normativo P2D-COMP-01, ao plano de evolução, aos contratos P2D-01/P2D-02/P2D-03 e aos imutáveis C3/G/V/B.

## 1. Finalidade deste documento

Este documento abre formalmente P2D-04 e estabelece a fronteira obrigatória para
qualquer implementação posterior. Ele não declara P2D-04 concluída, não
autoriza alteração de código e não transforma a fundação existente em produto
completo.

P2D-04 somente poderá ser aceita depois de:

1. o contrato abaixo ser aceito explicitamente pelo proprietário;
2. o estado de entrada ser novamente comprovado;
3. a implementação ser feita em lote controlado;
4. os testes, o fluxo real de usuário, as validações de engine, as evidências,
   os gates, a build e a revisão humana serem concluídos;
5. o commit, o ciclo remoto e a requalificação pós-merge serem aprovados.

Nenhuma capacidade parcial será apresentada como P2D-04 concluída. Uma
capacidade existente no código é apenas um fato de implementação até que os
critérios desta decisão sejam comprovados.

## 2. Estado de entrada comprovado

O checkpoint de entrada desta decisão é:

| Item | Valor comprovado |
|---|---|
| Branch local | main |
| HEAD local | 2007d617ba2ebe9f0171cfd0f8f4263c1cf455ae |
| origin/main | 2007d617ba2ebe9f0171cfd0f8f4263c1cf455ae |
| Merge de origem | PR #162, modernization/multiaxis-ui |
| Árvore tracked | limpa |
| git diff --check | PASS |
| Suíte pós-merge | 1833 passed, 2 skipped, 0 failed |
| Baseline integrity | 3036 arquivos verificados, PASS |
| Python de qualificação | .venv, Python 3.11.9 |
| Godot disponível | 4.7.stable.official.5b4e0cb0f |
| Unity disponível | 6000.5.7f1 |

A existência de arquivos untracked históricos e de artefatos locais não altera
o estado tracked acima. Eles não devem ser removidos, limpos ou incluídos
automaticamente em qualquer commit de P2D-04.

Antes de qualquer mutação de implementação, os itens desta tabela deverão ser
revalidados. Se qualquer item divergir, a implementação para e a divergência
é classificada antes de prosseguir.

## 3. Dependências e precedência

As seguintes dependências estão fechadas e permanecem congeladas:

- C3 e suas evidências;
- baselines e tolerâncias G/V/B;
- contratos e auditores de conformance;
- P2D-01A e P2D-01B;
- P2D-02A, P2D-02B e o fechamento P2D-02;
- P2D-03A, P2D-03B e P2D-03C;
- o merge remoto que resultou no HEAD 2007d617;
- o schema V1 existente e seu significado histórico;
- o editor legado CanvasView e o cenário lateral legado, salvo decisão
  específica posterior.

P2D-04 não reabre, reinterpreta ou reescreve nenhuma dessas dependências.
P2D-04 pode corrigir uma falha comprovada na fronteira de persistência,
integração, exportação ou coordenadas, mas cada correção deve permanecer
rastreável ao requisito e ao finding que a motivou.

## 4. Auditoria factual do estado atual

Esta seção registra o que foi encontrado em leitura do código e dos testes. Os
itens abaixo não são ainda aceite de P2D-04.

### 4.1 Persistência e schema

O módulo src/persistence/scene_authoring_schema.py possui:

- contrato profissional V1;
- contrato profissional V2 com câmera, parallax e sockets;
- validação estrita de referências, IDs, transforms, limites e tipos;
- preservação explícita da versão;
- upgrade V1 para V2 por helper explícito;
- rejeição de versão não suportada;
- referências de assets com caminho relativo e SHA-256.

O módulo src/persistence/scene_authoring_io.py possui:

- serialização JSON canônica e determinística;
- rejeição de BOM, UTF-8 inválido, chaves duplicadas e números não finitos;
- limite de tamanho de arquivo;
- validação de caminho relativo e contenção na pasta da cena;
- verificação de hash dos assets;
- save com staging, flush, fsync e substituição atômica;
- leitura V1 sem upgrade silencioso;
- leitura V2 que rejeita V1 até ocorrer upgrade explícito.

O módulo src/core/atomic_outputs.py preserva o conjunto anterior durante
falhas de substituição ocorridas no processo atual. O próprio contrato da
classe não promete consistência contra perda de energia, corrupção do sistema
de arquivos ou crash do sistema operacional. Essa diferença deverá permanecer
declarada; não será convertida em promessa de durabilidade que não tenha sido
testada.

### 4.2 Janela profissional e ciclo de uso

ScenarioEditorWindow atualmente:

- depende de um projeto salvo;
- usa o sidecar profissional com extensão .ndtscene.json;
- possui ações de salvar, recarregar, redefinir, exportar, preview e autoria;
- mantém um documento profissional V2 em sessão;
- exibe o estado dirty da sessão;
- conecta o documento profissional ao viewport profissional;
- conecta o documento ativo ao preview principal enquanto a sessão profissional
  está aberta;
- exporta o documento profissional atual pelo caminho de exportação genérico
  da janela;
- usa mensagens de status para falhas de save, reload, reset e export.

O fluxo atual de load possui um tratamento especial para erro de asset:
primeiro tenta a leitura com verificação de hash e, quando há erro de asset,
faz uma segunda leitura sem verificar assets para permitir que a UI exponha o
estado. P2D-04 deverá provar que esse modo degradado:

- é visualmente identificável;
- não é confundido com documento válido;
- não permite exportação silenciosa de asset ausente ou adulterado;
- informa o asset, o motivo e a ação corretiva.

O fluxo atual de reset e de confirmação de descarte deve ser exercitado no
nível da sessão profissional, não somente no estado legado da janela principal.
Qualquer caminho que descarte alteração profissional sem confirmação será
finding bloqueante.

### 4.3 Preview e bridge

Os módulos de bridge e preview profissional:

- convertem o documento V2 em camadas e câmera do preview principal;
- projetam objetos e sockets de forma determinística;
- respeitam transforms, flip, layers, visibility, parallax e camera;
- mantêm o preview profissional separado do editor legado.

A validação de P2D-04 deverá distinguir explicitamente:

- documento ativo em memória;
- último documento salvo;
- documento recarregado do sidecar;
- documento exportado;
- preview principal;
- viewport profissional.

Um screenshot isolado não comprova essa distinção.

### 4.4 Exportação e orientação

src/exporters/scene_authoring_export.py atualmente produz exportação
estruturada para generic, godot e unity, com:

- source hash ligado ao documento V2;
- declaração de capabilities;
- transformação de coordenadas declarada;
- escrita atômica;
- validação estrutural estrita.

O mapping atual registrado pelo código é:

| Destino | Origem | Destino | position_y_sign | rotation_sign |
|---|---|---|---:|---:|
| generic | top-left | top-left | 1 | 1 |
| godot | top-left | godot-2d-y-down | 1 | 1 |
| unity | top-left | unity-2d-y-up | -1 | -1 |

O consumidor profissional Godot valida o payload, carrega as texturas sob
res://, cria nós de layers e Sprite2D, aplica posição, rotação, escala, flip,
visibilidade e z, e cria marcadores para sockets. O consumidor profissional
Unity valida o payload, carrega Sprite, cria GameObjects, aplica posição,
rotação, escala, flip, visibilidade e sorting order, e cria metadados para
layers, objetos e sockets.

Foram identificadas duas condições que não podem ser mascaradas:

1. os importadores precisam ser testados com uma fixture assimétrica para
   comprovar orientação visual, e não somente presença de nós;
2. o campo pivot profissional deve ser comprovado visualmente no destino. No
   importador Godot atual ele é armazenado como metadado do Sprite2D; no
   importador Unity ele é armazenado como metadado e também depende do pivot
   do Sprite importado. Isso é uma obrigação de verificação de produto e pode
   gerar finding caso o resultado visual não corresponda ao editor.

O consumidor legado scenario_importer.gd é metadata-only e não pode ser usado
como prova do exportador profissional. A prova de P2D-04 deve utilizar os
importadores profissionais de cena.

### 4.5 Evidência automatizada existente

Já existem testes relacionados a:

- round-trip e determinismo de persistência;
- compatibilidade V1 e upgrade explícito para V2;
- rejeição de hash de asset divergente;
- JSON inválido, BOM, UTF-8, chaves duplicadas e números não finitos;
- rollback de save atômico;
- validação de destinos e limites;
- exportação generic, Godot e Unity;
- drift de hash, capabilities e coordinate mapping;
- contratos dos importadores profissionais;
- validadores reais para Godot e Unity.

Esses testes demonstram uma base técnica, mas não encerram P2D-04. A etapa
continua aberta até que haja fluxo de usuário, validação de engine, evidência
sanitizada, revisão humana e critérios de aceite concluídos.

## 5. Escopo obrigatório de P2D-04

P2D-04 deverá entregar, dentro da fronteira da composição 2D baseada em
objetos já existente:

1. persistência V2 canônica e determinística;
2. leitura compatível de V1 sem migração implícita;
3. upgrade V1 para V2 somente por ação explícita;
4. save atômico com preservação do último arquivo válido em falha;
5. recuperação controlada de documento inválido, versão incompatível, asset
   ausente, asset adulterado e destino inválido;
6. estado dirty correto e coerente com o documento realmente salvo;
7. confirmação antes de descarte de alterações profissionais;
8. preview principal coerente com o documento ativo e com o documento salvo;
9. exportação com alvo explícito e capability report honesto;
10. exportação dos objetos visuais atualmente suportados, incluindo asset,
    layer, grupo, transform, pivot, visibilidade, ordem, câmera e parallax;
11. orientação de posição, rotação, escala, flip e pivot validada com fixture
    assimétrica;
12. importação e exibição real do resultado no Godot 4.7 e Unity 6000.5.7f1;
13. mensagens de erro compreensíveis, acionáveis e específicas;
14. instruções reproduzíveis que não publiquem caminhos pessoais;
15. testes, logs, capturas e manifestos hash-bound para todos os itens acima.

A exportação de sockets continua limitada ao contrato que for comprovado.
Sockets não serão apresentados como iluminação, VFX, sombras ou runtime real.
Essas capacidades pertencem à linha EXT-FX-01.

## 6. Fora do escopo de P2D-04

Não fazem parte desta decisão:

- tilemap, tileset, pincel, balde, borracha, autotiling, Rule Tiles,
  isométrico ou hexagonal;
- colisão própria de cenário;
- NavMesh 2D;
- entidades, componentes ou prefabs;
- iluminação física, sombras, partículas, pós-processamento, shaders
  editáveis ou VFX em tempo real;
- editor 3D, modelagem 3D ou substituição do editor 2D por GLB;
- alteração do significado do schema V1;
- alteração do editor legado CanvasView;
- alteração de C3, G/V/B, auditores, tolerâncias ou referências;
- aceitação do produto P2D-COMP-01 como um todo.

Exportação profissional de objetos 2D dentro da capacidade já declarada está
incluída. Exportação de recursos futuros não implementados não será simulada
com metadata, sockets ou sidecars.

## 7. Invariantes obrigatórios

Durante toda a implementação e qualificação:

1. C3 e todas as baselines aprovadas permanecem byte-identificáveis e
   imutáveis.
2. Nenhum arquivo fora da fronteira autorizada entra no lote por conveniência.
3. V1 nunca é reescrito automaticamente quando for carregado.
4. V2 inválido nunca é convertido em documento válido por tolerância silenciosa.
5. Falha de save não destrói nem substitui parcialmente o último documento
   válido.
6. Arquivos temporários e backups transitórios são removidos após sucesso ou
   falha controlada.
7. A mesma entrada produz os mesmos bytes canônicos, salvo exceção
   expressamente documentada.
8. O source hash do export é exatamente o hash do documento exportado.
9. Caminhos operacionais de assets são relativos, seguros e verificáveis.
10. source_path, quando existir como provenance, não é usado para resolver
    arquivos nem publicado como dependência do consumidor.
11. Nenhum caminho pessoal, credencial, segredo ou identificador local é
    incluído em código, evidência publicável, export ou manifest sanitizado.
12. Documento ativo, documento salvo e documento exportado são identificáveis
    e não podem ser confundidos pela UI.
13. Reset, reload, close e export não descartam alterações sem a confirmação
    ou regra explícita definida nesta decisão.
14. Falha de asset é bloqueante para exportação que dependa desse asset.
15. O preview e a engine recebem a mesma semântica de posição, escala,
    rotação, pivot, flip, z, visibility, layer e parallax.
16. Não há alegação de suporte para recurso que o consumidor não materialize.
17. Todos os erros devem indicar o que falhou, o recurso afetado e a ação
    corretiva possível.
18. O editor legado não é usado como atalho para preencher lacunas do fluxo
    profissional.

## 8. Decisões de produto propostas para aceite

As escolhas abaixo são a proposta operacional para evitar ambiguidades. Elas
precisam ser aceitas explicitamente antes do código ser alterado:

### 8.1 Documento ativo e documento salvo

- O viewport de autoria mostra o documento ativo em memória, inclusive
  alterações ainda não salvas.
- O modo preview é somente leitura, mas não troca silenciosamente o documento
  ativo por uma cópia antiga do disco.
- O preview principal usa a sessão profissional ativa quando ela está aberta
  para o mesmo projeto; sem sessão ativa, usa o sidecar salvo.
- Recarregar substitui o documento ativo pelo sidecar validado e limpa o
  histórico conforme o contrato já existente.
- Exportar deve operar sobre o documento ativo validado e declarar isso no
  status da UI; exportar não equivale a salvar.

### 8.2 Falhas e assets ausentes

- Um documento com asset ausente ou hash divergente pode ser aberto somente
  para diagnóstico e correção.
- A UI deve marcar o objeto/asset afetado e bloquear exportação até a
  referência ser reparada, substituída ou removida por ação explícita.
- A mensagem deve informar asset, motivo e ação disponível, sem exibir
  caminho pessoal como solução.

### 8.3 Upgrade e compatibilidade

- V1 continua legível.
- A conversão V1 para V2 exige ação explícita e deve ser registrada no fluxo.
- Nenhum campo V1 desconhecido é descartado silenciosamente.
- O round-trip V1 deve preservar o contrato V1, e o round-trip V2 deve
  preservar todos os campos V2 suportados.

### 8.4 Alvos de exportação

- O usuário escolhe explicitamente generic, Godot ou Unity.
- O resultado informa o alvo, a versão do contrato, o hash da fonte e as
  capabilities suportadas e não suportadas.
- Se um alvo não conseguir materializar uma capacidade, o exportador deve
  rejeitar o recurso ou declarar a limitação de forma observável; nunca
  descartar silenciosamente.

### 8.5 Coordenadas e fixture de prova

A prova obrigatória usará imagem e composição assimétricas, com pelo menos:

- dimensões diferentes em largura e altura;
- posição X e Y diferentes;
- rotação não nula;
- escala X e Y diferentes;
- pivot fora do centro;
- flip em um eixo;
- z não nulo;
- duas layers com ordem e visibilidade distintas;
- pelo menos um grupo e um parallax distinto.

O resultado será comparado entre editor, export, Godot e Unity por valores
estruturais e por captura visual. Qualquer inversão vertical, rotação
espelhada, pivot deslocado, escala incorreta, z errado ou textura incorreta é
finding bloqueante até ser explicado e corrigido.

## 9. Testes obrigatórios

Nenhum grupo abaixo pode ser omitido.

### 9.1 Testes unitários e de contrato

- serialização canônica;
- hash da serialização;
- limites de arquivo, lista e campos;
- referências e IDs;
- V1, V2 e upgrade explícito;
- campos desconhecidos e tipos inválidos;
- números não finitos;
- BOM, UTF-8 inválido e chaves duplicadas;
- asset ausente, asset alterado e path inseguro;
- save atômico, falha de stage, falha de replace, rollback e limpeza;
- determinismo de save e export;
- capabilities e coordinate mapping;
- source hash do export;
- rejeição de export V1 ou payload driftado.

### 9.2 Testes de integração do produto

Devem executar o fluxo que o usuário realiza:

1. abrir um projeto válido;
2. abrir o Editor de Cenário;
3. criar ou carregar a composição profissional disponível;
4. selecionar objetos;
5. alterar posição, rotação, escala, flip, pivot, layer, grupo, câmera e
   parallax;
6. observar a mudança no viewport;
7. alternar para preview somente leitura;
8. confirmar que o documento ativo continua correto;
9. salvar;
10. fechar ou recarregar;
11. reabrir e verificar o mesmo estado;
12. provocar erro de asset ou documento;
13. corrigir o problema;
14. confirmar que o export fica bloqueado enquanto o erro existir;
15. exportar para cada destino autorizado;
16. importar no consumidor real;
17. verificar a cena materializada visualmente;
18. repetir com documento V1 e upgrade explícito.

### 9.3 Testes reais de engine

Para Godot 4.7:

- importar o export profissional em um projeto temporário;
- verificar layers, Sprite2D, texture, posição, rotação, escala, flip,
  visibility, z, pivot, camera e parallax aplicáveis;
- capturar o resultado;
- registrar versão e logs;
- preservar falhas e warnings sem editá-los para obter PASS.

Para Unity 6000.5.7f1:

- importar o export profissional em um projeto temporário;
- verificar GameObjects, SpriteRenderer, texture, posição, rotação, escala,
  flip, visibility, sorting order, pivot, camera e parallax aplicáveis;
- capturar o resultado;
- registrar versão e logs;
- preservar falhas e warnings sem editá-los para obter PASS.

Os testes dos validadores de schema não substituem a inspeção de renderização
real. Um projeto que apenas carrega JSON ou cria metadados não satisfaz o
critério visual.

## 10. Evidências obrigatórias

O pacote de P2D-04 deverá conter, no mínimo:

- 00-baseline: HEAD, branch, tracked status, ambiente e imutáveis;
- 01-tests: suíte completa, testes focais, positivos e negativos;
- 02-persistence: logs de save/load/round-trip/recovery;
- 03-preview: estado ativo, salvo, reload e preview principal;
- 04-export: payloads, hashes e capability reports;
- 05-godot: projeto temporário, log, captura, versão e resultado;
- 06-unity: projeto temporário, log, captura, versão e resultado;
- 07-visual-audit: auditoria e classificação de deltas;
- 08-human-review: checklist, findings e decisão;
- 09-build: build portátil, hash e smoke test;
- 10-docs: esta decisão, evidência final, troubleshooting e matriz;
- manifest.json ou equivalente com tamanho, SHA-256, tipo e requisito;
- hash do manifest;
- seal ZIP;
- extração independente e re-hash completo.

Evidências publicáveis devem ser sanitizadas. Caminhos absolutos locais podem
existir somente em logs de trabalho não publicados e autorizados; qualquer
artefato enviado ao repositório ou incluído no seal final deve usar caminhos
relativos ou placeholders reproduzíveis.

## 11. Gates e ordem de execução

A ordem abaixo é obrigatória:

1. revalidar o checkpoint de entrada;
2. criar o registro de branch/checkpoint de implementação;
3. implementar somente os arquivos autorizados;
4. executar testes focais;
5. executar testes negativos e de recovery;
6. executar suíte completa;
7. executar gates de qualidade, privacidade e integridade;
8. executar o fluxo real do usuário;
9. executar export e import real em Godot e Unity;
10. executar captura e auditoria visual;
11. realizar revisão humana;
12. produzir pacote pre-commit;
13. solicitar decisão PRECOMMIT ACCEPT;
14. realizar commit somente com a fronteira aprovada;
15. executar CI e ciclo remoto autorizado;
16. requalificar o merge na main;
17. gerar build e seal pós-merge;
18. solicitar aceite humano final;
19. somente então marcar P2D-04 como ACCEPTED / CLOSED.

Se qualquer teste, engine, captura, auditoria, documento, revisão ou hash
falhar, P2D-04 permanece OPEN ou BLOCKED. Não haverá commit parcial,
tolerância alterada, baseline reescrita ou avanço automático.

## 12. Fronteira de arquivos

O lote de implementação não está autorizado por este documento. Depois do
aceite do contrato, a lista exata de arquivos permitidos deverá ser registrada
antes do primeiro arquivo de código ser modificado.

Qualquer arquivo fora da lista será tratado como divergência. Testes,
documentos e evidências somente entram quando forem diretamente necessários e
registrados no plano do lote. Arquivos untracked existentes não serão limpos
nem absorvidos por conveniência.

## 13. Rollback e publicação

O rollback técnico de entrada é o merge commit
2007d617ba2ebe9f0171cfd0f8f4263c1cf455ae. Nenhuma baseline, evidência aceita ou
histórico anterior será alterado.

O aceite desta decisão, por si só:

- não autoriza push;
- não autoriza tag;
- não autoriza merge;
- não autoriza release;
- não autoriza modificar o remoto;
- não autoriza alterar qualquer linha futura EXT-TMAP-01,
  EXT-COLL-01, EXT-NAV-01, EXT-ENT-01 ou EXT-FX-01.

Essas ações somente poderão ocorrer no ciclo remoto correspondente, depois de
PRECOMMIT ACCEPT e dos checks obrigatórios.

## 14. Critérios de aceite de P2D-04

P2D-04 somente poderá ser marcada ACCEPTED / CLOSED quando todos os itens
seguintes forem verdadeiros ao mesmo tempo:

- os requisitos P2D-029 a P2D-036 estiverem implementados ou classificados
  explicitamente como não aplicáveis por decisão aprovada;
- save, load, reload, reset, recovery e export funcionarem no fluxo real;
- V1, V2, upgrade e round-trip tiverem evidência própria;
- falhas preservarem dados e produzirem mensagens acionáveis;
- o preview principal e o viewport profissional mostrarem o documento correto;
- Godot e Unity materializarem os objetos visuais atuais, não apenas JSON ou
  metadata;
- orientação, escala, rotação, flip, pivot, z, layers e visibility passarem
  com fixture assimétrica;
- capabilities forem verdadeiras e limitações forem visíveis;
- suíte completa, gates e CI passarem sem mascaramento;
- a captura Windows, a auditoria visual e a revisão humana forem aprovadas;
- privacidade e ausência de segredos forem revalidadas;
- build portátil, manifest e seal forem independentemente verificados;
- commit, merge e pós-merge forem requalificados;
- o proprietário registrar o aceite humano final.

Até esse momento, a linguagem obrigatória é:

P2D-04 aberta; contrato definido; implementação e qualificação pendentes.

## 15. Próxima decisão solicitada

O próximo passo após este documento é o aceite explícito do contrato de
P2D-04, incluindo especialmente:

1. a distinção entre documento ativo, salvo e exportado;
2. o bloqueio de exportação para asset ausente ou adulterado;
3. a exigência de renderização real em Godot e Unity;
4. a fixture assimétrica para orientação e pivot;
5. a lista de capacidades futuras que permanece fora deste lote;
6. a regra de que nenhum código será alterado antes do aceite.

Sem esse aceite, nenhuma implementação de P2D-04 deve começar.
