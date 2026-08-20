# ADR — Runtime de cenários, efeitos e validação portátil

**Status:** Etapa 1 concluída; Etapa 2 em implementação
**Data:** 20 de agosto de 2026
**Base:** `main` no merge `7e190b4`
**Estado de execução:** A Etapa 1 foi encerrada após a PR #113 (`84dfee7`) e a PR documental #114 (`7e190b4`). A Etapa 2 iniciou sua implementação na branch de trabalho atual; sua decisão final permanece pendente dos gates próprios.
**Planos relacionados:**

- `docs/PLANO_CENARIOS_PARALLAX_E_PALETA_2026-08-18.md`
- `docs/PLANO_CENARIOS_PROFISSIONAL_2026-08-19.md`

## Decisão

O runtime de cenários será desenvolvido como uma extensão modular do editor de
autoria, sem alterar silenciosamente o schema `.ndtproj` v1, o documento lateral
de cenário já aprovado, `SceneObject.position.z`, os exportadores existentes, o
gizmo do editor 2D, os menus, os atalhos ou o histórico Undo/Redo do editor
principal.

O escopo futuro poderá incluir iluminação, materiais e shaders, partículas,
pós-processamento, triggers e streaming. A aceitação deste ADR registra somente
a direção arquitetural e os gates; não declara nenhuma dessas capacidades como
implementada, integrada ou suportada.

## Estado atual e fronteira

O escopo 4A–4B.5 já aprovado entrega autoria, câmera/parallax, camadas,
overlays, persistência e exportação estrutural. Sockets de luz, VFX e trigger
são marcadores autorais; eles não constituem execução de efeitos ou runtime de
engine.

Os exportadores devem continuar informando explicitamente capacidades não
suportadas. Nenhum efeito poderá ser descartado silenciosamente, simulado de
forma enganosa ou apresentado como validado apenas porque existe um campo no
schema.

## Contrato de capacidades e fallback

Cada recurso de runtime deverá declarar, de forma versionada:

- `required_capability`;
- comportamento nativo esperado;
- fallback seguro e sua razão;
- compatibilidade `native`, `degraded` ou `incompatible`;
- parâmetros aceitos, limites e unidade de medida;
- origem do resultado e versão do adaptador.

Conversões perigosas ou que percam dados deverão ser rejeitadas antes da escrita
final. Uma degradação permitida deverá gerar relatório explícito, incluindo o
recurso afetado, a capacidade ausente e o comportamento aplicado. `incompatible`
nunca poderá resultar em arquivo parcialmente válido ou em sucesso silencioso.

O contrato de runtime deverá permanecer separado dos contratos de autoria até
que uma migração explícita, com ADR próprio, prove compatibilidade e preserve
rollback. Nenhum campo existente será reinterpretado silenciosamente.

## Determinismo da simulação

Partículas, triggers e qualquer efeito dependente de tempo deverão usar:

- passo fixo de atualização;
- relógio simulado nos testes;
- sementes pseudoaleatórias registradas;
- versão do algoritmo de simulação;
- ordem determinística de objetos e eventos;
- serialização canônica;
- separação entre estado autoral persistente e estado transitório de execução;
- replay reproduzível para cenários testados.

As comparações entre plataformas não exigirão igualdade pixel a pixel quando o
backend ou o driver puder alterar a rasterização. A validação deverá combinar
hashes de dados determinísticos, métricas estruturais, contagens, eventos,
limites numéricos e tolerância visual documentada.

## Hardware, backends e classificação dos testes

### Gates portáveis e bloqueantes

CI e testes automatizados deverão priorizar execução headless ou em backends de
software disponíveis no ambiente, sem exigir GPU dedicada. Serão bloqueantes:

- validação de schema e migrações;
- serialização e fallback;
- compilação verificável de shaders no backend declarado;
- simulação determinística com seed fixa;
- despacho e ordenação de triggers;
- carregamento, erro, cancelamento e rollback;
- contagem de instâncias, tamanho de payload e tempo lógico de tick;
- integridade dos artefatos e ausência de escrita parcial.

O uso de llvmpipe/Mesa no Linux, WARP/DirectX no Windows ou outro backend de
software somente poderá ser afirmado quando registrado pelo próprio teste. A
ausência de um backend necessário não será convertida em PASS.

### Validação local em hardware real

Execuções locais servem para confirmar funcionamento prático, resposta visual e
integração com o hardware disponível. VRAM, FPS dependente de driver, backend e
telemetria de GPU serão informativos e não bloqueantes, sempre com ambiente,
driver e backend registrados.

A validação local não poderá ser usada para prometer desempenho universal nem
para substituir os gates funcionais portáveis. Quando uma engine real ou um
backend necessário não estiver disponível, o resultado deverá ser classificado
como `NÃO TESTADO` ou `BLOQUEADO`, conforme a causa, nunca como aprovado.

## Ordem planejada de implementação

Estas fases são uma sequência de planejamento. Nenhuma fase está iniciada por
este ADR e cada uma exigirá autorização, baseline e decisão de saída própria:

1. **Runtime base:** carregamento, ciclo de vida, capacidades, erros,
   cancelamento, rollback e contrato versionado.
2. **Iluminação e materiais:** modelo de luz, parâmetros, sockets, preview
   determinístico e fallback.
3. **Shaders:** contrato de material, validação por backend, compilação,
   parâmetros inválidos e degradação controlada.
4. **Partículas:** emissores, fixed update, seeds, limites, pausa, replay e
   persistência apenas do estado autoral.
5. **Pós-processamento:** cadeia de efeitos, limites, ordenação, fallback e
   preview.
6. **Triggers:** zonas, condições, prioridades, eventos, cancelamento e replay.
7. **Streaming:** carregamento assíncrono, cache, prioridades, descarte seguro,
   recuperação de falhas e limites de memória lógica.
8. **Adaptadores reais:** importação e reprodução em Godot e Unity, com matriz
   de capacidades, diferenças documentadas e testes executados nas engines
   reais quando elas estiverem disponíveis.
9. **Fechamento:** regressão integral, auditoria visual, benchmarks lógicos,
   evidências hashadas, CI, revisão de diff, PR, merge e validação pós-merge.

## Governança obrigatória antes de cada fase

Antes de iniciar qualquer fase, o agente ou desenvolvedor deverá ler e
confirmar a versão vigente das regras, políticas, governanças, ADRs e planos
relacionados do repositório. A fase não poderá avançar sem uma baseline real,
inventário do escopo, testes de caracterização e critérios objetivos de saída.

São proibidos em todas as fases:

- bypass de testes, gates ou revisão;
- force push, force merge ou reescrita destrutiva de histórico;
- alteração de regra, limiar ou scanner para obter PASS;
- fragmentação, ofuscação, remoção ou mascaramento de dados de auditoria;
- desvios do plano sem autorização e registro formal;
- uso de mock onde o comportamento real for o objeto da validação;
- declaração de PASS baseada em suposição, cache, documentação antiga ou
  evidência não reproduzível;
- remoção acidental ou silenciosa de funcionalidade, dados, testes ou
  evidências;
- promoção ou merge enquanto houver falha, lacuna, regressão ou divergência
  documental não explicada.

`skip` e `xfail` somente poderão existir quando já autorizados pela política do
repositório, com motivo, responsável, condição de remoção e classificação
visível. Eles não poderão ser criados para facilitar a aprovação da fase.

## Gates de cada fase

Uma fase somente poderá ser classificada como `APROVADA` quando tiver:

- implementação integral do escopo da fase;
- testes positivos, negativos, de integração e de UI quando aplicáveis;
- validação real de arquivo, interface, exportador ou engine quando esse for o
  comportamento sob teste;
- cobertura sem redução e sem enfraquecimento de asserções;
- lint, tipagem, compilação, segurança e dependências aprovados;
- evidências reproduzíveis com commit, branch, ambiente, comandos, resultados,
  falhas, limitações, rollback, tamanhos e hashes;
- validação dos bytes efetivamente rastreados pelo Git;
- documentação viva reconciliada e snapshots históricos preservados;
- árvore limpa, diff revisado e rollback praticável;
- CI obrigatório aprovado nos sistemas exigidos;
- PR promovida somente depois dos gates e merge normal, seguido de validação
  pós-merge.

Qualquer item ausente mantém a fase como `NÃO TESTADA`, `BLOQUEADA` ou
`PARCIAL`, conforme a causa. Nenhuma dessas classificações equivale a
`APROVADA`.

## Rollback e preservação

Cada fase deverá manter um ponto de restauração verificável e uma política de
rollback que preserve arquivos do usuário, projetos, assets, contratos e
evidências anteriores. Falhas de carregamento, simulação, exportação ou
persistência deverão deixar o estado anterior intacto e produzir diagnóstico
auditável.

## Consequência

O ADR permite planejar o runtime de efeitos sem inflar silenciosamente o MVP ou
misturar o editor de autoria com uma engine completa. A implementação futura
será incremental, determinística, portável e reversível, com diferenças entre
Godot, Unity e backends tratadas por capacidades explícitas. Até que cada fase
seja concluída e comprovada pelos gates acima, partículas, shaders, iluminação,
pós-processamento, triggers, streaming e runtime completo permanecem
**fora das funcionalidades concluídas do projeto**.
