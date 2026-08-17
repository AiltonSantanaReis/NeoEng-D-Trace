# Definição canônica do produto — NeoEng-D-Trace

**Status:** decisões de produto consolidadas para orientar arquitetura e roadmap.  
**Data:** 27 de julho de 2026.  
**Identidade ativa no runtime principal:** NeoEng-D-Trace.  
**Identificador legado controlado:** PolygonTool, restrito a compatibilidade e histórico. A distribuição é `neoeng-d-trace`; o código-fonte permanece exclusivamente em `src/`.

Nenhuma lacuna marcada como pendente deve ser preenchida por suposição.

## 1. Problema central

NeoEng-D-Trace será uma ferramenta desktop especializada em preparar assets gráficos para jogos a partir de imagens 2D.

O produto deve reduzir o trabalho manual necessário para:

- detectar um ou vários objetos em uma imagem;
- corrigir contornos com precisão;
- gerar recortes;
- criar, simplificar e validar colisões;
- configurar pivô, escala e orientação;
- criar representações 2.5D opcionais;
- exportar pacotes tecnicamente utilizáveis em engines.

Não será substituto para editor de imagens, Blender ou engine de jogos.

## 2. Usuários

### Principal

- desenvolvedor indie;
- artista técnico de pequeno estúdio.

### Secundários

- artista 2D;
- designer de níveis;
- estudante;
- desenvolvedor de engine própria.

## 3. Fluxo central

> Importar uma imagem, detectar um ou vários objetos, corrigir o contorno, configurar pivô e colisão, visualizar o resultado e exportar um pacote validado para a engine escolhida.

## 4. Escopo 2D e 2.5D

A edição 2D e a preparação de assets são o núcleo.

Na versão 1.0, o 3D será limitado a representações 2.5D derivadas de polígonos 2D:

- extrusão de contorno;
- profundidade configurável;
- bevel simples;
- imagem como textura frontal;
- visualização com câmera, iluminação e material;
- pivô, escala e orientação;
- mesh simples;
- exportação GLTF/GLB.

Ficam fora da versão 1.0:

- modelagem 3D completa;
- escultura;
- rigging e animação;
- retopologia profissional;
- fotogrametria;
- reconstrução 3D precisa de uma única imagem;
- presets low/medium/high-poly baseados em reconstrução avançada.

## 5. Plataforma

- Windows 11 é a plataforma oficial inicial e de validação;
- Linux e macOS não serão plataformas oficialmente suportadas na versão 1.0;
- testes headless em Linux não constituem suporte público à plataforma;
- suporte ao Windows 10 permanece pendente de decisão e validação específica.

## 6. Operação offline, dados e telemetria

- o funcionamento principal será offline;
- não haverá assinatura obrigatória;
- serviços em nuvem não serão obrigatórios;
- IA externa não será obrigatória;
- telemetria não fará parte da versão 1.0 sem decisão formal adicional;
- qualquer relatório de erro futuro deverá exigir consentimento explícito e informar os dados enviados;
- imagens, projetos e assets do usuário não devem sair do computador no fluxo padrão.

## 7. Importações

A capacidade aprovada é importar imagens 2D e o formato próprio de projeto.

Matriz exata de formatos, limites, perfis de cor e transparência ainda precisa ser formalizada e testada. Não declarar suporte definitivo a PSD, TIFF, SVG, WEBP, GLTF ou OBJ como importação sem contrato e teste correspondentes.

## 8. Exportações prioritárias

1. formato de projeto próprio e versionado;
2. PNG recortado;
3. atlas PNG com JSON;
4. polígonos e colisões em JSON genérico;
5. pacote para Godot;
6. pacote para Unity;
7. SVG;
8. GLTF/GLB simples;
9. OBJ somente mediante necessidade comprovada;
10. FBX em etapa futura.

Cada exportador terá contrato, validação automatizada e teste na engine de destino.

## 9. Engines prioritárias

1. Godot;
2. Unity;
3. formatos genéricos para engines próprias;
4. Unreal Engine;
5. Phaser e outras engines web.

Suporte nativo completo ao Unreal não faz parte da versão 1.0.

## 10. Detecção automática

A versão 1.0 deverá:

- detectar um ou vários objetos por imagem;
- oferecer presets simplificado, equilibrado e detalhado;
- permitir ajuste manual avançado;
- informar quando não houver detecção válida;
- medir qualidade, quantidade de vértices, tempo e consumo de memória;
- manter resultados determinísticos com a mesma entrada e configuração, dentro das tolerâncias documentadas.

## 11. Inteligência artificial

OpenCV e algoritmos geométricos são a base da primeira versão.

Não haverá IA externa obrigatória. IA local opcional só poderá ser considerada depois de existir um caso de uso definido, critério de qualidade, fallback e análise de custo/desempenho.

## 12. Edição manual

Capacidades obrigatórias:

- mover, adicionar e remover vértices;
- editar curvas Bézier;
- suavizar e simplificar;
- representar buracos e múltiplas ilhas;
- snapping;
- transformação por gizmo;
- desfazer e refazer;
- validação de degeneração e auto-interseção.

Cortar/unir polígonos, expandir/contrair e alinhamento/distribuição devem ser priorizados conforme a matriz de funcionalidades e testes.

## 13. Colisões e física

A versão 1.0 deverá:

- criar e editar formas de colisão;
- simplificar e validar;
- visualizar;
- testar sobreposição estática;
- exportar para os formatos priorizados.

Física dinâmica completa, gravidade, corpos e simulação avançada ficam fora da versão 1.0. O código existente de física parcial não deve ser apresentado como motor completo.

## 14. Formato de projeto

O formato próprio será versionado e deverá suportar:

- criação, abertura e salvamento confiáveis;
- migração entre versões;
- autosave e recuperação;
- gravação atômica;
- camadas e grupos;
- contornos, curvas, buracos e ilhas;
- pivô e colisões independentes;
- configurações de exportação;
- metadados de engine;
- referência ou incorporação controlada da imagem;
- miniatura quando aprovada no schema.

O `format_id` deve ser estável e independente da marca visual. O schema exato permanece pendente de ADR própria.

## 15. Compatibilidade

Projetos criados a partir do primeiro formato oficialmente versionado deverão abrir em versões posteriores por migração explícita. Nenhuma mudança de formato poderá descartar dados silenciosamente.

## 16. Plugins

Plugins de terceiros e dependências de marketplace ficam fora da versão 1.0.
Os adaptadores first-party source-only para Godot e Unity são uma linha de
integração própria do NeoEng-D-Trace, acompanhada separadamente pelo plano
`docs/PLANO_INTEGRACAO_PLUGINS_NATIVOS_2026-08-16.md`. Eles não são plugins de
terceiros, não introduzem binários ou downloads obrigatórios e não alteram a
fonte de verdade do núcleo. Sua implementação, distribuição e promoção
continuam condicionadas aos gates reais de contrato, segurança, rollback,
engines e evidências desse plano; a existência do plano não aprova release.

## 17. Modelo comercial e licença

- aplicativo proprietário e comercial;
- repositório privado;
- licença perpétua por versão principal;
- correções incluídas na versão adquirida;
- upgrade pago possível para futuras versões principais;
- versão de avaliação opcional, com limitações claras;
- sem assinatura obrigatória para o funcionamento principal.

O texto jurídico final da licença ainda precisa ser elaborado e revisado.

## 18. Experiência de uso

- modo simples, guiado por fluxo e presets;
- modo avançado com parâmetros geométricos, colisões e exportação detalhada;
- linguagem de usuário, sem expor detalhes internos desnecessários;
- mensagens de erro compreensíveis e acionáveis.

Referências visuais específicas permanecem pendentes de aprovação formal.

## 19. Desempenho e limites

Permanecem pendentes de medição e aprovação:

- resolução máxima oficial;
- objetos por projeto;
- vértices por objeto/projeto;
- tempo aceitável de detecção por preset;
- limite de memória;
- hardware mínimo.

Nenhum número será publicado antes de benchmark reproduzível no Windows.

## 20. Cinco capacidades centrais da versão 1.0

1. criar, abrir, salvar, recuperar e migrar projetos de forma confiável;
2. importar imagens e detectar um ou vários objetos com três presets;
3. editar contornos, vértices, curvas, buracos e ilhas com undo/redo;
4. gerar, simplificar, visualizar, validar e exportar colisões;
5. exportar PNG, atlas, JSON genérico, Godot, Unity e GLTF/GLB simples.

## 21. Portões adicionais para lançamento

- executável Windows validado;
- formato de projeto versionado;
- autosave e recuperação;
- dependências travadas;
- testes automatizados;
- testes reais no Windows;
- logs e erros compreensíveis;
- gravação atômica;
- documentação;
- build reproduzível;
- nenhuma perda silenciosa de dados;
- nenhuma vulnerabilidade crítica conhecida aberta.

## 22. Fora da versão 1.0

- modelagem 3D completa;
- rigging e animação;
- escultura;
- fotogrametria;
- física dinâmica completa;
- plugins de terceiros, dependências de marketplace e integrações externas não
  aprovadas;
- colaboração online;
- serviços em nuvem obrigatórios;
- IA externa obrigatória;
- suporte nativo completo ao Unreal;
- suporte oficial a Linux e macOS.

## 23. Nome e identidade

- nome ativo no runtime principal: **NeoEng-D-Trace**;
- identificador legado controlado: **PolygonTool**, somente em histórico ou compatibilidade de dados documentada;
- repositório de destino: `AiltonSantanaReis/NeoEng-D-Trace`;
- distribuição Python: `neoeng-d-trace`;
- implementação interna única: `src/`;
- identidade de commit: `NeoEng-D-Trace Maintainer` com e-mail GitHub `noreply`;
- validação jurídica/comercial de marca e domínio continua obrigatória antes do lançamento público.

A consolidação seguirá `PLANO_RENOMEACAO.md`: sem segunda árvore, sem aliases entre pacotes e sem migração física motivada apenas pela marca.

## 24. Critério de sucesso

A versão 1.0 será considerada bem-sucedida quando um usuário-alvo conseguir, no Windows, partir de uma imagem 2D e produzir um asset validado para Godot ou Unity, com contorno editável, pivô, colisão, arquivos exportados corretos, projeto recuperável e sem perda silenciosa de dados.
