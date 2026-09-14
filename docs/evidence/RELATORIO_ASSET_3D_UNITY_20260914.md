# Relatório de validação — asset 3D para Unity

**Status geral:** IN_PROGRESS
**Base funcional:** asset r3
**Objetivo:** validar autoria modular, exportação, integridade, importação/renderização real e prontidão do contrato Unity.

## Resultado executivo

A entrega r3 é um asset original procedural chamado Eclipse Warden, com 23 componentes separados, 2.144 triângulos, 5 materiais PBR, UV0, skin glTF com 18 joints, inverse bind matrices e animação Idle. O GLB e o glTF aberto passaram a validação estrutural; o OBJ estático também passou.

O Godot 4.7 importou o GLB pela etapa real do editor e o runtime com driver OpenGL/NVIDIA renderizou quatro capturas reais: frontal, três-quartos, lateral e pose Idle. O relatório do runtime registrou 23 MeshInstance3D, 23 superfícies, um AnimationPlayer, nenhuma falha e nenhum warning produzido pelo script.

O status de importação Unity permanece PENDING_EVIDENCE. A entrega está preparada para Unity por glTF 2.0/GLB, mas não foi feita nova execução nativa Unity neste ciclo, conforme o limite aprovado pelo usuário.

## Evidência estrutural

Arquivo principal: artifacts/post-e13-3d-asset-unity-20260914-r3/eclipse_warden.glb
Arquivo aberto: artifacts/post-e13-3d-asset-unity-20260914-r3/eclipse_warden.gltf
Manifesto: artifacts/post-e13-3d-asset-unity-20260914-r3/manifest.json
Relatório: artifacts/post-e13-3d-asset-unity-20260914-r3/structural-validation.json

Checks observados:

- versão glTF 2.0: PASS;
- 23 meshes com nomes únicos e nós visíveis: PASS;
- POSITION, NORMAL, TEXCOORD_0, JOINTS_0 e WEIGHTS_0 em todas as malhas: PASS;
- UVs dentro de 0..1 e pesos normalizados: PASS;
- 5 materiais com base color, metallic-roughness e normal: PASS;
- 18 joints e inverse bind matrices: PASS;
- animação Idle com 3 canais: PASS;
- OBJ/MTL com 23 objetos e atribuições de material: PASS;
- caminhos absolutos da máquina no manifesto: não encontrados;
- teste de adulteração de textura em cópia temporária: PASS, checksum mismatch detectado.

Hashes principais:

| Arquivo | Tamanho | SHA-256 |
| --- | ---: | --- |
| eclipse_warden.glb | 190816 bytes | AF417FBFF1F84999402A4A4EB7D7F980673A5EF59CC45B5848B3D8D3E6369ED5 |
| eclipse_warden.gltf | 64577 bytes | 20ACD642D383C6645BDC324BE9ED6DAF70F83855BB828DA08EBEB62F78A39796 |
| eclipse_warden.bin | 108188 bytes | DAF5F4D39CDC0A7BB4AC7927960225AC71A27F0377861C5B8CDCA2DA4F576DB1 |
| eclipse_warden.obj | 243070 bytes | 3191829ED4905C5D40B368A8ADDEFF873D2DB6593CFA9035FCFC349068130A47 |

## Evidência real de engine

Projeto de preview: artifacts/post-e13-3d-asset-unity-20260914-r3/godot_preview
Relatório: godot_preview/godot-runtime-report.json

Etapas:

1. A execução runtime headless com driver dummy falhou de forma documentada porque não existe textura de viewport nesse driver. Isso é uma limitação do modo de captura, não uma aprovação visual.
2. A importação do editor Godot em modo headless foi executada com o GLB real. Após a correção de mimeType nas imagens embarcadas, terminou com exit 0 e sem erro de importação.
3. O runtime foi executado com driver windows e renderização OpenGL real. O log confirmou NVIDIA GeForce RTX 3070 Ti e o processo terminou com exit 0.
4. Foram gravadas quatro imagens PNG reais e inspecionadas visualmente.

Capturas:

- godot_preview/preview_front.png — enquadramento frontal, sombra e iluminação azul/quente;
- godot_preview/preview_three_quarter.png — leitura de profundidade, espada e separação lateral;
- godot_preview/preview_side.png — teste de volume e silhueta lateral;
- godot_preview/preview_idle.png — pose após seek na animação Idle.

Hashes das capturas:

| Captura | SHA-256 |
| --- | --- |
| preview_front.png | 855B95AC435A74894C4E53FB1A872A43C13AF431E30DDE803CF288F76275D5D6 |
| preview_three_quarter.png | 92BE7B7286CD281D07F01D46CDD8EC71C0DD8027F42F7434A0A2E69AF7FF6C55 |
| preview_side.png | CFE3D2328AB6F8997243FF756C56FBEEA0028DF4F4F7D0174756BEF7102B34DA |
| preview_idle.png | 05AE440B5B56D534C309E811F3E3029392B37ECCD63F5108D674B0140D26FA0D |

O log nativo do Godot também mostrou o warning não bloqueante NVAPI_EXECUTABLE_ALREADY_IN_USE ao tentar criar um perfil de aplicação. O relatório do script não registrou warning de importação ou captura; o warning de driver permanece registrado aqui para não mascarar evidência.

## Correção aplicada

A primeira saída, em artifacts/post-e13-3d-asset-unity-20260914, foi preservada como histórico. O importador Godot rejeitou o GLB porque imagens embarcadas com bufferView não tinham mimeType. O gerador foi corrigido para declarar image/png; r2 comprovou a correção e r3 foi gerada com proveniência no commit 4bef2a4. A limpeza de cache foi consolidada depois no commit 01a3dc1. A importação e o runtime real da r3 passaram.

Os sidecars .godot, .import, .uid e PNGs extraídos automaticamente pelo importador foram removidos somente do diretório nomeado de preview r3. O GLB embarca suas imagens e as texturas abertas permanecem na pasta principal do asset.

## Avaliação visual humana

O asset demonstra o fluxo técnico solicitado, mas não deve ser classificado como pacote artístico final. A inspeção visual encontrou:

- silhueta funcional e leitura clara de armadura, capa, botas, espada e energia;
- materiais e luzes efetivamente visíveis no render;
- separação de peças confirmada por nós e superfícies;
- geometria deliberadamente low-poly/procedural, com blocos e costuras aparentes;
- padrões de textura procedurais de alta frequência, ainda abaixo de um acabamento PBR comercial;
- capa composta por painéis planos, sem simulação de tecido;
- sem LODs, colisores, sockets, mapas de detalhe, retargeting ou variantes de produção.

Esses itens são melhorias futuras registradas, não falhas escondidas da validação estrutural.

## Build atualizada e probe do binário

A build final foi gerada depois das alterações no commit 985345c:

- diretório: release/post-e13-user-asset-build-20260914-r3;
- proveniência: PASS, source_commit 985345cd21341aeb65197a6b878d26eb32768518;
- executável: portable/NeoEng-D-Trace/NeoEng-D-Trace.exe;
- tamanho: 10.883.963 bytes;
- SHA-256: F0FC4C12EB2540492E99DEF89003D05DD55827A1D044494271DF04B22975EAD7;
- smoke oficial: SUCCESS, 11 checks, incluindo cli-version, headless-project, headless-glb, gui-open-close e user-state-directory;
- probe manual: --version exibiu 0.3.0, --help exibiu o contrato CLI e o processo aceitou CloseMainWindow e encerrou.

O probe manual teve Responding false e título de janela vazio no instante de três segundos; por isso isso fica registrado como observação, não como aprovação de usabilidade. O smoke gui-open-close é evidência de ciclo de abertura/fechamento do harness, não substitui cliques reais do usuário.

## Unity e usabilidade do editor

O pacote inclui UNITY_IMPORT_GUIDE.md e contrato Unity PENDING_EVIDENCE. O GLB é a opção recomendada, com rig Generic inicialmente e remapeamento Humanoid manual somente após inspeção no Unity.

Não foi possível coletar cliques reais do editor desktop nesta sessão porque a ponte CUA não expôs superfícies nativas; portanto não há alegação de teste de usabilidade do editor baseada em captura simulada. As imagens acima são capturas reais do renderer Godot do asset importado.

## Pendências para ciclo futuro

- executar importação e renderização no Unity com o importador adotado pelo projeto;
- confirmar Generic/Humanoid, escala, orientação, clips e deformação no Unity;
- remapear materiais para URP/HDRP e validar emissão;
- substituir o protótipo procedural por malha de produção com bevels, retopologia e UV layout artístico;
- criar LODs, colliders, sockets de arma, variantes e controle de capa;
- repetir captura por cliques reais quando a ponte nativa estiver disponível.
