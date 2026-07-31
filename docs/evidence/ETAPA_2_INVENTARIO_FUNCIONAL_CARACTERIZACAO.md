# Evidência consolidada — Etapa 2: inventário funcional e caracterização

## Estado do documento

Este relatório permanente consolida os pacotes produzidos sobre a branch
`audit/etapa-2-inventario-funcional`, a partir do commit
`287f6ef770ec1e65410a0a567dee2747f67c9f3d`.

Nenhuma correção funcional foi realizada durante os gates de caracterização.
A integração deste relatório não encerra riscos nem inicia a Etapa 3.

Os oito pacotes brutos individuais são identificados por nome, tamanho e
SHA-256. Eles foram consolidados no arquivo
`docs/evidence/raw/NeoEng-D-Trace_Etapa2_Raw_Evidence_Bundle.zip`, cuja
publicação como artefato do CI permanece requisito para o encerramento formal
da Etapa 2.

## Escopo executado

A Etapa 2 levantou a árvore rastreada, analisou estaticamente os módulos Python,
executou a suíte histórica preservada, caracterizou fluxos atuais com objetos
reais, verificou persistência, CLI, exportadores, física e realizou uma sessão
manual controlada da interface Windows.

## Inventário estático

- Arquivos rastreados pelo Git: `209`
- Arquivos protegidos pelo manifesto: `208`
- Arquivos Python: `122`
- Linhas Python: `24966`
- Erros de sintaxe estática: `0`
- Branch: `audit/etapa-2-inventario-funcional`
- Commit: `287f6ef770ec1e65410a0a567dee2747f67c9f3d`
- Árvore limpa durante o levantamento: `True`

A diferença entre 209 arquivos rastreados e 208 arquivos do manifesto decorre
da exclusão intencional do próprio `baseline_manifest.json` pelo verificador.

## Suíte histórica preservada

| Grupo | Coletados | Aprovados | Falhas | Erros | Ignorados |
|---|---:|---:|---:|---:|---:|
| non-Qt | 113 | 108 | 5 | 0 | 0 |
| Qt/UI | 83 | 72 | 11 | 0 | 0 |
| **Total** | **196** | **180** | **16** | **0** | **0** |

As falhas históricas foram preservadas e classificadas. Elas incluem fixtures
inválidas, mocks incompatíveis, expectativas obsoletas, contratos pendentes e
uma divergência real de sequência de eventos do retângulo. Nenhum teste foi
apagado ou enfraquecido para produzir resultado verde.

## Fluxos atuais caracterizados

### Ferramentas Qt

- Laço poligonal com `Scene` e `CommandManager` reais: fluxo de criação e
  Undo/Redo registrado como funcional.
- Retângulo com `press -> move -> release`: funcional.
- Retângulo com `press -> release`, sem evento de movimento: não cria objeto.
- Laço magnético com imagem NumPy real: mapa de borda e preview criados.
- Finalização magnética válida: criação e Undo/Redo registrados.
- Mask Viewer: contrato atual `fill/cover`, com corte possível da imagem.

### Núcleo

- Round-trip dos campos atualmente serializados: funcional.
- Arquivo ausente e JSON malformado: rejeitados por exceções.
- Perfis JSON por objeto: arquivos reais para generic, Unity, Godot e Phaser.
- Exportação GLB simples: arquivos reais para cena e objeto.
- Broadphase + SAT: sobreposição e reposicionamento registrados.
- `CommandManager`: mantém as pilhas em falhas, mas oculta a exceção do chamador.
- CLI headless combinada: carrega, exporta JSON/GLB e salva no cenário positivo.

## Defeitos e lacunas confirmados

### Persistência

1. **Perda de geometria de colisão personalizada.** O arquivo registra somente
   que o objeto possui colisão; ao reabrir, a forma é reconstruída a partir do
   polígono visual.
2. **Perda de Bézier.** O campo não é serializado e retorna `None` após o
   carregamento.
3. **Formato sem versão explícita.** `schema_version=999` é aceito e ignorado.
4. **Validação estrutural insuficiente.** Tipos incorretos resultam em
   `AttributeError`, não em erro de schema controlado.
5. Imagem, caminho da imagem, seleção e histórico Undo/Redo não são
   persistidos; a necessidade de cada estado deve ser definida no contrato da
   Etapa 3.

### CLI

1. `--export-object-gltf` sem `--object-id` retorna código `0` e não cria
   arquivo.
2. Um identificador de objeto inexistente registra erro, não cria arquivo e
   ainda retorna código `0`.
3. O modo headless positivo funciona, mas os cenários negativos tornam a
   automação não confiável até a Etapa 7.

### Interface e ferramentas

1. O retângulo depende de pelo menos um evento de movimento para atualizar o
   segundo canto.
2. O Mask Viewer usa `fill/cover`; a escolha entre preencher a área e mostrar a
   imagem inteira permanece decisão de UX.
3. O inventário estático encontrou duas implementações de `LassoTool`; a
   implementação ativa e a implementação possivelmente órfã devem ser
   consolidadas na etapa correspondente.
4. A exportação de resultados do painel de colisão possui caminho estático
   parcialmente desconectado e permanece risco aberto.

### Exportador de atlas — novo defeito encontrado na evidência controlada

A sessão controlada concluiu a interação e registrou `export.atlas=SUCCESS`,
mas a validação dos bytes encontrou inconsistência entre o PNG e o JSON:

- PNG do atlas: `290 x 219`;
- retângulo declarado: `x=0`, `y=0`,
  `w=291`, `h=219`;
- limite direito declarado: `291`;
- largura real do atlas: `290`;
- retângulo contido na imagem: `False`.

O retângulo excede a largura do atlas em
`1` pixel. Portanto, o evento de
sucesso comprova que o fluxo produziu arquivos, mas não comprova consistência
do contrato do atlas. A correção pertence à Etapa 10; a Etapa 2 apenas registra
o defeito.

## Resultados positivos

- Entrada GUI controlada utilizada: PNG RGBA
  `977 x 631`.
- SHA-256 da entrada controlada:
  `c92581d2198041f2d59f3532a36d440d479f9a1deee6ed999dd829fac3ab5a61`.
- Onze eventos críticos esperados: todos registrados com `SUCCESS`.
- Registros de falha: `0`.
- Arquivos exportados na sessão controlada: `6`.
- Sprite selecionado: PNG RGBA
  `291 x 219`.
- GLBs: cabeçalho `glTF`, versão 2 e comprimento declarado igual ao tamanho
  real.
- GLB estrutural com dois objetos: dois nodes, dois meshes e índices dentro do
  intervalo dos accessors no cenário simples.
- CuPy ausente gerou somente aviso; o processamento continuou pela CPU.

## Classificação dos riscos existentes

| Risco | Estado após a Etapa 2 | Evidência principal |
|---|---|---|
| R-001 Persistência incompleta | **CONFIRMADO / ABERTO** | colisão personalizada e Bézier são perdidos; schema sem versão |
| R-002 Abrir/Salvar completo na UI | **ABERTO** | persistência interna existe, mas o ciclo completo de UI não foi identificado |
| R-003 Cobertura de UI e ferramentas | **ABERTO** | caracterização ampliada, mas cobertura integral continua futura |
| R-004 Undo/Redo incompleto | **CONFIRMADO / ABERTO** | fluxos selecionados funcionam; falhas são ocultadas pelo gerenciador |
| R-005 Exportação de colisão | **ABERTO** | caminho do painel permanece parcial |
| R-006 CLI falso sucesso | **CONFIRMADO / ABERTO** | dois cenários negativos retornaram código 0 sem output |
| R-007 Bézier/geometria | **CONFIRMADO / ABERTO** | Bézier não persiste e métricas geométricas ainda são insuficientes |
| R-008 APIs duplicadas | **CONFIRMADO / ABERTO** | duas implementações de `LassoTool` |
| R-011 Acoplamento ao Qt | **ABERTO** | permanece dívida para refatoração protegida |
| R-012 Segurança e limites | **CONFIRMADO / ABERTO** | schema desconhecido aceito e tipos incorretos sem validação controlada |
| R-013 Metadados do atlas | **CONFIRMADO / ABERTO** | retângulo JSON excede o PNG controlado em 1 pixel |

Nenhum desses riscos é encerrado pela Etapa 2.

## Pacotes brutos de evidência

| Pacote | SHA-256 | Bytes |
|---|---|---:|
| `NeoEng-D-Trace_Etapa2_Inventario_20260731_100024.zip` | `0ee82920c86c52f85599e92644745b6b6abd0b1906ae737cb324400970262fe7` | 102283 |
| `NeoEng-D-Trace_Etapa2_Legacy_NonQt_20260731_101604.zip` | `046c59041534bd897b982fd06926b9cfc00c7b33aacbb26b28986919cc008c50` | 12521 |
| `NeoEng-D-Trace_Etapa2_Legacy_Qt_20260731_103251.zip` | `7f021c3ebfd3d228e6a4b73d2e7769bedcd1780d3bf3ebbb456262426316644b` | 8872 |
| `NeoEng-D-Trace_Etapa2_Qt_Current_Flows_20260731_110755.zip` | `4d9ed670c256ec8b96420412c31187c5a52f0de5a47af63ae77345e2f357d20e` | 1807 |
| `NeoEng-D-Trace_Etapa2_Core_Current_Flows_20260731_112655.zip` | `cf1d58e0bf9d668e2972e1d94f4ab00c958d6abed7fcf9d4e3feae2030456a46` | 3809 |
| `NeoEng-D-Trace_Etapa2_Persistence_CLI_GLTF_20260731_113315.zip` | `91fb4e17255954624e58bdb23f841fb1df5e854aa2504ff37d56a6666f88920a` | 2520 |
| `NeoEng-D-Trace_Etapa2_Manual_GUI_20260731_115201.zip` | `e7d934752f9b9f0addf6fd80ddbbf4154b18f92f6925c4a9dcd8aa62413329d3` | 198381 |
| `NeoEng-D-Trace_Etapa2_Manual_GUI_Controlled_20260731_120824.zip` | `fde7497c2b9a8db1e2cd428b9a4368d8c88fb894454fa9bb45030f40118ecbb7` | 15430 |

O manifesto JSON associado contém os mesmos hashes e os resultados estruturados.

Pacote bruto consolidado:

- Arquivo: `NeoEng-D-Trace_Etapa2_Raw_Evidence_Bundle.zip`
- Tamanho: `339806` bytes
- SHA-256: `86dcfadef644fe37dc93a88d7c9b92866a6c944410d0039ff56b9736a3076836`

## Conclusão técnica

**ETAPA 2 — INVENTÁRIO E CARACTERIZAÇÃO TECNICAMENTE CONCLUÍDOS, COM
BLOQUEADORES FUNCIONAIS FORMALMENTE IDENTIFICADOS.**

O encerramento formal permanece **PENDENTE** até que:

1. este relatório, o manifesto e a matriz de riscos sejam integrados;
2. a árvore modificada passe pelo gate local completo;
3. o pacote bruto consolidado seja publicado como artefato do CI;
4. os jobs Linux e Windows sejam aprovados;
5. o diff final seja revisado e integrado por pull request.

Esta conclusão não declara o produto pronto, não aprova persistência completa,
não encerra riscos e não autoriza pular etapas.

Somente após esses requisitos a Etapa 2 poderá ser encerrada e a
**Etapa 3 — persistência e contrato versionado de projeto** poderá começar.
