# CHG-POS-E13-PROFESSIONAL-AUTHORING-UX-20260911

**Status:** `IN_PROGRESS`  
**Data:** 11/09/2026 (UTC-03)  
**Base auditada:** `e9d24465bb1ff0212b9b68f07ea361953397da6e`  
**Build de diagnóstico:** `build/_clean-post-e13-final10-20260910/`  
**Código verificado nesta subetapa:** `19a16c373094d5b43a6b86cacaa5441f54dde1ae`
**Evidência nativa desta subetapa:** [EVD-POS-E13-PROFESSIONAL-AUTHORING-NATIVE-20260911](EVD_POS_E13_PROFESSIONAL_AUTHORING_NATIVE_20260911.md)
**Escopo:** lote controlado de melhorias de autoria profissional do editor de cenários, sem reabrir ou reinterpretar E13.

## Governança e autoridade

- [Governança de integridade](../GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md)
- [Requisitos obrigatórios do editor de cenários](../REQUISITOS_EDITOR_CENARIOS_COMPLETO_2026-08-30.md)
- [Índice documental ativo](../INDICE_DOCUMENTAL_ATIVO_CANONICO_2026-08-24.md)
- [Decisão de continuidade pós-E13](DECISAO_CONTINUIDADE_POS_E13_2026-09-10.md)
- Evidência nativa diagnóstica: `artifacts/usability-human-review-20260910/`
- Evidência nativa pós-build: `artifacts/post-e13-native-flow-20260911-camera-timeline/`

## Motivação factual

O fluxo nativo realizado com o executável final10 registrou:

1. `SCN-001`: o caminho `Cenário → Novo Cenário` abriu uma cena vazia sem imagem prévia; este ponto corrige uma conclusão anterior e permanece sujeito ao gate completo de persistência/exportação.
2. Câmera: o painel expôs apenas X, Y e zoom; não havia moldura de câmera, rotação, direção nem manipulação direta comprovada.
3. Parallax: não havia molduras visuais persistentes indicando os limites de composição por profundidade.
4. Timeline: clique e um gesto de arraste foram observados, mas o código só tratava o `mousePressEvent`; o scrub contínuo durante o movimento não estava implementado de forma explícita.
5. Localização: os estados vazios do viewport e do inspetor permaneceram em inglês em uma sessão PT-BR.
6. Gizmo: a captura mostrou o manipulador funcional, porém com tratamento visual básico incompatível com o objetivo profissional.

## Requisitos e features afetados

| ID | Estado no início | Intervenção deste lote |
|---|---|---|
| `SCN-001` | `PENDING_EVIDENCE` para completude | preservar criação vazia e tornar câmera/guia configuráveis desde o primeiro estado |
| `SCN-003` | `OPEN` | ampliar autoria de câmera, visualização e manipulação sem remover transformações existentes |
| `FX-001` | `OPEN` | preparar referência espacial da câmera; não declarar iluminação real concluída |
| `FX-006` | `OPEN` | tornar a câmera visualmente auditável; runtime ainda pendente |
| `UX-001` | `OPEN` | scrub contínuo, guias e controles PT-BR acessíveis por mouse/teclado |
| `UX-002` | `OPEN` | manter mensagens acionáveis e localizar estados vazios tocados |
| `UX-003` | `OPEN` | preservar histórico existente; câmera será aplicada como uma operação única ao finalizar o gesto |
| `REQ-F09` / parallax | `OPEN` | molduras de profundidade como referência de autoria, sem prometer entrega no runtime |
| `REQ-F10` | `OPEN` | gerar novas capturas nativas após build e registrar limitações |

## Mudanças autorizadas neste lote

- adicionar rotação persistente à câmera ortográfica mantendo compatibilidade com documentos antigos;
- exibir moldura de câmera com alças de translação e rotação no viewport;
- exibir guias de limites das camadas de parallax como sobreposição de autoria;
- implementar scrub contínuo da timeline com mouse pressionado e arrastado;
- corrigir os textos PT-BR dos estados vazios do editor profissional;
- modernizar o desenho do gizmo mantendo os modos e sinais existentes.

## Contratos preservados e riscos

- Documentos sem o campo de rotação devem continuar abrindo com rotação `0`.
- Projeções existentes com rotação padrão `0` devem manter os mesmos valores numéricos.
- A moldura de câmera e as guias são ferramentas de autoria e não são exportadas como objetos da cena.
- O arraste da câmera será consolidado ao término do gesto para não fragmentar o histórico em dezenas de entradas.
- Nenhuma alegação de `FX-001`, `FX-002`, `FX-006`, exportação ou maturidade 2.5D/3D será promovida a `PASS` neste registro sem os testes correspondentes.

## Plano de verificação

1. testes unitários/integração do modelo e da projeção com rotação default e não-zero;
2. teste de UI do scrub contínuo e dos textos PT-BR;
3. suíte oficial sem filtros;
4. build limpa do executável;
5. fluxo nativo Windows com criação vazia, câmera, parallax, timeline e captura real;
6. comparação visual e hashes dos artefatos;
7. requalificação pós-commit e atualização deste registro.

## Limitações explicitamente preservadas

- A automação CUA/`@oai/sky` não está disponível neste host; as capturas nativas serão obtidas pelo harness Win32 versionado, usando eventos reais de mouse/janela e `PrintWindow`, identificado no relatório.
- Este lote não encerra os requisitos abertos de iluminação, partículas, tilemap completo, colisão, NavMesh, exportação/round-trip nem editor 3D.
- O estado formal do produto permanece `IN_PROGRESS / OPEN`.

## Resultado

Os testes, a build, as capturas nativas, os hashes e a requalificação do commit foram concluídos para a subetapa de câmera, guias de parallax e scrub contínuo, com critérios técnicos em `PASS`. A revisão humana final e os requisitos funcionais explicitamente preservados continuam pendentes. O estado formal permanece `IN_PROGRESS / OPEN`; falhas anteriores e limitações permanecem preservadas.
