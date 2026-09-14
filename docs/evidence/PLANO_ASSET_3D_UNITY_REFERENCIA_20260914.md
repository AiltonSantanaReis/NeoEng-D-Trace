# Plano de autoria e validação — asset 3D para Unity

**Status:** IN_PROGRESS
**Data:** 2026-09-14
**Base de trabalho:** commit d4acd606ddfe2a62d2d211104279c23feafc4a64
**Destino primário:** Unity
**Destino de validação real disponível nesta etapa:** Godot 4.7 (importação/renderização do glTF)

## Objetivo

Produzir um asset 3D original, inspirado nas referências fornecidas pelo usuário, para validar o fluxo de autoria, exportação, inspeção e entrega do projeto. A entrega deve ser utilizável no Unity por meio do padrão glTF 2.0/GLB e deve preservar separação de componentes, UVs, materiais PBR, esqueleto, skinning, animação e um export auxiliar estático.

O asset não será uma cópia pixel a pixel nem uma extração de malha das imagens. A referência orienta linguagem visual, proporções, modularidade, paleta e conjunto de peças. A proveniência/licença das imagens de referência é mantida como fornecida pelo usuário e não verificada pelo projeto.

## Referências recebidas

| Arquivo | SHA-256 |
| --- | --- |
| 1-Foto-1.jpg | 1EEE95F73802B6205B84097537E93B0434EE2EAEE1A52DAB17E24A618F11939E |
| 2-Foto-2.jpg | 1EE40AD572538A177A6D31227C73343EB511C55DD0469B3E9597514FE941AB8D |
| 3-Foto-3.jpg | C8C2CC6C6FAFB45FA09AD1420D8F5F6D93B1946930FE36F39D59353E62F309C8 |

Os caminhos absolutos das referências ficam somente no registro de proveniência local desta execução; o manifesto do asset usará nome-base e hash, sem depender de caminhos da máquina do usuário.

## Escopo de entrega

### Geometria modular

O modelo será entregue com objetos nomeados e separados, no mínimo:

- cabeça/capuz e placa facial;
- torso/armadura, ombreiras esquerda/direita;
- braços/luvas esquerda/direita;
- cinto, painéis de saia e painéis de capa;
- pernas/botas esquerda/direita;
- lâmina, guarda e punho da espada;
- detalhe rúnico emissivo.

Cada componente deverá ter uma malha indexada, normais, UV0 e material identificável. A separação é deliberada para permitir substituição, ocultação, variantes e reuso no Unity.

### Shading e materiais

Serão entregues materiais PBR nomeados, com texturas procedurais originais e referências explícitas:

- metal escuro da armadura;
- tecido da capa;
- couro de cinto e botas;
- emissivo rúnico/energia.

Cada material deverá declarar base color, metallic-roughness e normal; o material emissivo declarará também emissive texture/factor. As texturas não serão geradas por recorte das referências.

### Rig e animação

Será incluído um esqueleto humanoide mínimo com hierarquia de raiz, quadril, coluna, peito, pescoço, cabeça, braços, mãos, pernas e pés. As malhas terão joints/weights e inverse bind matrices válidos. A entrega terá, no mínimo, o clipe Idle; qualquer clipe adicional será documentado no manifesto.

O mapeamento automático para Humanoid do Unity não será afirmado como concluído sem importação real no Unity. O arquivo será entregue como rig genérico glTF interoperável, com orientação para remapeamento no importador.

### Formatos e integração Unity

- GLB embarcado, para transporte simples e preservação de referências internas;
- glTF + BIN + PNGs, para inspeção e pipelines que preferem arquivos separados;
- OBJ estático auxiliar, sem rig/animação, para compatibilidade e diagnóstico;
- manifesto, hashes, guia de importação Unity e relatório de validação;
- projeto de preview Godot para importação e renderização reais.

O projeto não adicionará um importador Unity de terceiros nem alterará o editor canônico nesta etapa. A compatibilidade será documentada por contrato estrutural; a confirmação de importação no Unity fica PENDING_EVIDENCE até novo ciclo explicitamente autorizado.

## Impacto e proteção contra regressão

- Nenhum arquivo do editor canônico será removido ou reescrito.
- A autoria ficará isolada em ferramenta/artefato de evidência versionável.
- A saída usará diretório novo e o gerador recusará sobrescrever uma entrega existente.
- O build já produzido continuará preservado em release/post-e13-user-asset-build-20260914.
- O teste nativo de shutdown, symlink e qualquer operação potencialmente danosa permanece proibido neste computador e não fará parte desta etapa.
- A indisponibilidade da ponte de automação nativa de janelas impede afirmar captura de cliques do editor desktop; capturas do preview Godot serão evidência real de importação/renderização, não serão apresentadas como teste de usabilidade do editor.

## Evidências e critérios

| Evidência | Critério | Estado inicial |
| --- | --- | --- |
| Manifesto e hashes | todos os arquivos e referências internas conferem | PLANNED |
| Estrutura glTF/GLB | versão 2.0, cenas, nós, índices e chunks válidos | PLANNED |
| Malhas | componentes separados, normais, UV0 e triângulos | PLANNED |
| PBR | mapas/slots e fatores declarados por material | PLANNED |
| Rig | joints, pesos, inverse bind matrices e animação | PLANNED |
| OBJ | objetos e materiais separados, sem depender do GLB | PLANNED |
| Godot | importação e renderização reais, relatório e capturas | PLANNED |
| Unity | abertura/importação/renderização do asset no editor Unity | PENDING_EVIDENCE |
| Build | artefato atualizado e smoke test sem regressão | PASS anterior; revalidar se houver alteração |
| Usabilidade desktop | fluxo com cliques reais e capturas do editor | PENDING_EVIDENCE por limitação da ponte CUA |

## Testes planejados

1. Gerar a entrega em diretório novo, com nomes determinísticos e manifesto.
2. Validar hashes, JSON glTF, GLB, imagens, OBJ, UVs, materiais, skinning e animação.
3. Executar teste negativo em cópia temporária para comprovar que adulteração é detectada, sem modificar a entrega.
4. Importar o GLB em Godot e executar uma cena de preview com câmeras frontal e três-quartos, iluminação, material emissivo e reprodução de Idle.
5. Inspecionar visualmente as capturas reais e registrar artefatos, erros, warnings, clipping, escala e leitura das peças.
6. Validar a presença dos contratos de importação do Unity sem inventar um resultado de editor que não foi executado.
7. Registrar limitações e melhorias futuras separadamente, sem bloquear a entrega quando o critério estrutural e o preview real forem aprovados.

## Melhorias futuras já previstas

- importação real no Unity e decisão entre rig Generic e Humanoid;
- teste de animação, materiais URP/HDRP e iluminação no Unity;
- autoria visual de malha, UV e rig diretamente no editor canônico;
- captura de fluxo por cliques reais quando a ponte CUA estiver disponível;
- variantes de cabeça, capa, armas e paleta baseadas na modularidade do asset;
- LODs, colisores, sockets, retargeting e validação de orçamento por plataforma.

O plano só poderá ser encerrado após os critérios executáveis terem evidência anexada; itens fora do ambiente autorizado permanecerão explicitamente como PENDING_EVIDENCE.

## Resultado da execução desta etapa

O gerador foi implementado em tools/create_reference_3d_asset.py e o validador em tools/validate_reference_3d_asset.py. A entrega r3 está em artifacts/post-e13-3d-asset-unity-20260914-r3. O relatório detalhado está em docs/evidence/RELATORIO_ASSET_3D_UNITY_20260914.md.

O primeiro artefato foi preservado como histórico de FAIL de importação Godot por ausência de mimeType em imagens embarcadas. A correção foi aplicada na fonte e comprovada pela importação posterior do GLB r2; a entrega r3 reproduz o resultado a partir do commit da ferramenta. O preview Godot real passou com 23 MeshInstance3D, 23 superfícies, AnimationPlayer e quatro capturas PNG. O cache regenerável do importador foi excluído do pacote.

Os critérios estruturais e de preview Godot estão PASS. O Unity nativo, a classificação Generic/Humanoid, o remapeamento URP/HDRP e os cliques reais do editor permanecem PENDING_EVIDENCE pelos limites aprovados e pela indisponibilidade da ponte CUA. A qualidade visual foi classificada como protótipo técnico low-poly/procedural, não como asset artístico final.
