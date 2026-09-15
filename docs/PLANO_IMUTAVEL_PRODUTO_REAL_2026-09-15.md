# NeoEng-D-Trace — Plano Imutável de Produto Real

**ID:** PLAN-REAL-PRODUCT-20260915
**Data de adoção:** 2026-09-15 (America/Sao_Paulo)
**Estado documental:** ATIVO / NORMATIVO
**Status do produto:** `IN_PROGRESS`
**Lock:** `IMMUTABLE_BASELINE`
**Política de alteração:** `ADDENDUM_ONLY`
**Governança superior:** `GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md`
**Adendo de execução:** `ADENDO_GOVERNANCA_REALIDADE_EVIDENCIAS_2026-09-15.md`
**Base auditada:** `b1f2c63baf9e6c7c5ecc0a572b5d0e342bb7b335`
**Referência canônica da auditoria:** `26521c1c4420996f05535dce68661545de2e8328`

## 1. Decisão formal

O proprietário aceitou integralmente o plano de correção do produto real. Este
arquivo é a baseline normativa congelada do plano. Depois do commit de selagem,
seu conteúdo não poderá ser editado, reformatado, reordenado ou “corrigido” para
fazer uma etapa passar.

Uma necessidade nova, correção de redação ou mudança de escopo deverá ser
registrada em um novo adendo numerado, com comparação antes/depois, impacto,
IDs afetados, testes adicionais e aprovação formal. O plano-base continua
inalterado. O lock criptográfico detecta qualquer divergência.

“Imutável” aqui significa imutabilidade normativa e detecção de adulteração.
Imutabilidade física absoluta não pode ser garantida em um diretório gravável;
por isso a selagem oficial exige commit rastreado, revisão protegida e hash
verificado pelo gate. Nenhum relatório local poderá tratar uma cópia alterada
como plano oficial.

## 2. Verdade atual do produto

O produto não será descrito como editor 2D/2.5D/3D completo até que todos os
requisitos do contrato `PRODUCT-SCENE-FULL-01` tenham evidência de produto e de
engine. O estado atual permanece `IN_PROGRESS`.

O estado auditado deve ser comunicado assim:

- a fundação 2D possui capacidades reais, porém delimitadas;
- colisões possuem domínio geométrico e persistência, mas isso não equivale a
  física nativa em Unity ou Godot;
- tilemap, partículas e híbrido 3D possuem verticais reais limitadas, não um
  editor completo;
- o GLB atual não comprova modelagem 3D;
- o asset procedural de referência foi produzido por ferramenta externa e não
  comprova autoria pelo editor canônico;
- JSON, sidecar, mock, fixture, teste de contrato, captura de UI e validação
  estrutural nunca serão promovidos isoladamente a funcionalidade final.

## 3. Objetivo de produto

Entregar uma ferramenta profissional capaz de criar, editar, persistir,
validar, exportar e reabrir conteúdo real nos destinos declarados, com fluxo
compreensível para usuários comuns, artistas e desenvolvedores.

O produto deverá separar claramente:

1. autoria e fonte de verdade;
2. armazenamento de assets, proveniência e licenças;
3. renderer de preview;
4. compilador para cada engine;
5. runtime de validação;
6. pacote de evidências.

Nenhuma dessas camadas poderá ser substituída por uma aparência de UI ou por
um contrato que não execute o comportamento requerido.

## 4. Sequência obrigatória

### G0 — Reset de verdade e rastreabilidade

**Status:** `IN_PROGRESS`

Entregas obrigatórias:

- matriz requisito → feature → código → teste → artefato → engine → resultado;
- classificação de cada evidência por nível real;
- correção de nomes que sugerem exportação nativa quando há apenas JSON;
- preservação dos relatórios históricos sem reescrita retroativa;
- checkpoint limpo, hashado e protegido;
- validação integral da governança e deste plano antes de cada etapa.

Bloqueio: qualquer divergência documental, hash alterado, evidência sem origem
ou claim mais amplo que o teste impede o avanço.

### G1 — Fundação 2D canônica real

**Status:** `PLANNED`

O usuário deverá criar uma cena vazia, criar objetos sem asset prévio, importar
assets, editar transformações e pivôs, organizar hierarquia, criar colisores,
desfazer/refazer, salvar, fechar, reabrir e recuperar erros.

O schema será versionado, extensível e independente dos widgets Qt. Migrações
deverão preservar campos desconhecidos. O `AssetStore` deverá registrar
conteúdo, origem, licença, disponibilidade e SHA-256.

### G2 — Artefatos nativos 2D, tilemap e colisão

**Status:** `PLANNED`

Cada destino terá um compilador próprio. Godot e Unity deverão receber
artefatos nativos ou um pacote oficialmente suportado que materialize recursos
nativos equivalentes.

O teste deverá abrir um projeto limpo, importar o resultado, verificar a
hierarquia e os componentes, executar o runtime, observar o resultado, salvar,
reabrir e exercitar erros de hash, escala, pivô, colisão e asset ausente.

Consultas geométricas internas não substituem contato, trigger, máscara,
camada e resposta da física nativa.

### G3 — 2.5D e parallax real

**Status:** `PLANNED`

O contrato deverá cobrir profundidade, câmera ortográfica/perspectiva, molduras
de referência, velocidade relativa, conversão de coordenadas, iluminação que
altere pixels, partículas, timeline determinística e equivalência entre preview
e runtime.

Uma cena só passará quando o resultado do editor e o resultado da engine forem
comparados por semântica e, quando visualmente aplicável, por captura hashada e
tolerância previamente definida.

### G4 — Linha 3D profissional

**Status:** `PLANNED`

O caminho recomendado é DCC-first: importar e validar glTF/GLB e formatos
adicionais justificados, inspecionar malhas, UVs, normais, materiais PBR,
esqueleto, pesos e animações, montar cenas e exportar pacotes reproduzíveis.

Modelagem interna completa só poderá ser anunciada depois de existir contrato
próprio para topologia, UV unwrap, normais/tangentes, materiais, skinning,
animação, LOD, colisores, undo/redo, persistência e exportação.

O viewport híbrido atual continuará classificado como vertical slice até
atender esses requisitos. O gerador procedural externo será evidência de
`EXTERNAL_TOOL`, nunca prova do editor canônico.

### G5 — Renderer, desempenho e release

**Status:** `PLANNED`

Um backend GPU real será escolhido por benchmark reproduzível. O caminho 2D
atual será preservado por feature flag até o novo backend demonstrar equivalência
e regressão zero no escopo protegido.

O release exigirá build limpa, execução real, testes positivos e negativos,
logs íntegros, captura do processo, manifestos hashados, revisão humana e
ausência de falhas, skips, xfails, warnings ou fallback oculto no pacote oficial.

## 5. Arquitetura obrigatória

```text
SceneDocument versionado
 ├─ AssetStore / proveniência / licença / hash
 ├─ CommandBus / undo / redo / migrações
 ├─ RendererBackend 2D / 2.5D / 3D
 ├─ ExportCompiler Godot
 ├─ ExportCompiler Unity
 ├─ Runtime validator
 └─ Evidence runner fail-closed
```

O domínio não poderá assumir que toda entidade é uma imagem plana nem que todo
renderer futuro será `CanvasView`. A fonte de verdade da cena e os artefatos de
destino deverão permanecer distinguíveis.

## 6. Critérios universais de aceite

Uma feature só recebe `PASS` quando houver, no mesmo commit auditado:

1. requisito e feature identificados;
2. governança e plano lidos integralmente e validados por hash;
3. entrada controlada e fluxo real de usuário;
4. operação real e saída observável;
5. persistência e reabertura quando aplicáveis;
6. integração com o destino quando aplicável;
7. teste de erro e recuperação;
8. artefatos rastreados, hashados e reproduzíveis;
9. logs sem supressão;
10. nenhum mock/fake/fixture substituindo o comportamento exigido;
11. revisão humana quando prevista;
12. limitações explícitas e sem claim além do escopo demonstrado.

Se qualquer item faltar, o status será `PENDING_EVIDENCE`, `FAIL` ou
`BLOCKED`, nunca `PASS`.

## 7. Segurança e não regressão

- O editor canônico e os contratos já protegidos não serão removidos.
- Alterações serão aditivas, isoladas em branch/checkpoint e acompanhadas de
  migração quando houver schema.
- Editores antigos só poderão ser marcados `DEPRECATED` depois de auditoria de
  chamadas, redirecionamento e teste de não regressão.
- Symlink, shutdown, soak e licensing continuarão exclusivamente em ambiente
  controlado; nenhum teste perigoso será executado nativamente neste computador.
- Credenciais, tokens, `.ulf` e dados de login nunca serão adicionados ao Git.
- Falhas históricas permanecerão preservadas; uma execução posterior não apaga
  a anterior.

## 8. Regra de encerramento

Este plano não está concluído enquanto o contrato final de cenário, as linhas
2D, 2.5D e 3D, exportações nativas, runtime, desempenho, documentação e
revisão humana não tiverem `PASS` com evidência correspondente.

Qualquer entrega parcial deverá declarar explicitamente seu escopo limitado.
É proibido usar uma vertical slice para declarar o produto completo.
