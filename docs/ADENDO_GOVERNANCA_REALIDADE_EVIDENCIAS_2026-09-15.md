# Adendo Normativo — Realidade, Imutabilidade e Gate Fail-Closed

**ID:** GOV-STRICT-REAL-EVIDENCE-20260915
**Estado documental:** ATIVO / ADENDO NORMATIVO
**Governança superior:** `GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md`
**Plano protegido:** `PLANO_IMUTAVEL_PRODUTO_REAL_2026-09-15.md`
**Validador obrigatório:** `tools/validate_strict_delivery_gate.py`
**Política:** somente endurece regras; nunca reduz requisito, cobertura ou evidência.

## 1. Prevalência e não relaxamento

Este adendo complementa a governança existente. Em caso de conflito, prevalece
a governança superior e a execução é bloqueada até decisão formal. Nenhum
desenvolvedor, agente, teste, script ou relatório pode usar este adendo para
relaxar uma exigência.

O gate padrão é fail-closed: ausência, dúvida, timeout, erro de parsing,
divergência de hash, processo não iniciado ou log incompleto produz bloqueio.

## 2. Leitura integral obrigatória por etapa

Antes de qualquer ação de uma etapa, devem ser lidos integralmente:

1. a governança superior vigente;
2. este adendo;
3. o plano imutável;
4. o índice documental ativo;
5. a decisão/ADR da etapa;
6. os contratos e requisitos afetados;
7. os riscos e limitações do baseline anterior.

O agente deverá gerar um recibo de etapa com:

- `stage_id`;
- `read_integrally: true`;
- `validated: true`;
- `status: PASS`;
- SHA-256 exato de cada documento obrigatório;
- lista completa de documentos lidos;
- commit auditado;
- timestamp UTC;
- identidade do responsável.

O sistema não consegue provar o conteúdo cognitivo da leitura humana. Ele pode,
contudo, bloquear toda etapa sem o recibo assinado/registrado e sem os hashes
corresponderem aos documentos existentes. Um recibo falso é uma falha de
integridade e invalida todo o pacote.

O recibo não substitui os documentos; ele somente demonstra que a validação
ocorreu contra uma versão exata.

## 3. Plano imutável

- O arquivo do plano-base não pode ser editado após a selagem.
- Não é permitido alterar whitespace, ordem, título, status, hash ou critérios
  para fazer um gate passar.
- Correções e extensões usam novo adendo com ID, versão, diff conceitual,
  impacto, testes e aprovação.
- O lock deve verificar os bytes do plano e da governança superior.
- O validador mantém uma raiz de confiança redundante para os caminhos e
  hashes selados; alterar somente o lock não pode redirecionar a autoridade.
- O commit que contém o lock deve ser rastreado e protegido no fluxo oficial.
- No fluxo oficial, lock, documentos normativos, recibo e evidências devem estar
  rastreados; arquivo não rastreado é bloqueado, salvo quando uma regra futura
  de artefato CI anexado for aprovada formalmente.
- Tag, branch protegida e assinatura de commit são requisitos de publicação;
  hash local sozinho é detecção de adulteração, não proteção física absoluta.
- Se o lock mudar sem controle de mudança, o status de toda etapa dependente
  será `BLOCKED`.

## 4. Classes de evidência

Toda evidência deve declarar exatamente uma classe principal:

- `PRODUCT_FUNCTIONAL` — fluxo real do produto com saída observável;
- `ENGINE_RUNTIME` — artefato importado/executado em engine real;
- `CONTRACT_ONLY` — schema, interface ou invariantes;
- `STRUCTURAL_ONLY` — arquivo parseável ou atributos presentes;
- `SYNTHETIC_FIXTURE` — fixture fabricada exclusivamente para teste;
- `UI_ONLY` — existência/interação de interface sem destino final;
- `EXTERNAL_TOOL` — gerada por ferramenta fora do editor canônico;
- `ENVIRONMENT_BLOCKED` — execução impedida por ambiente.

As classes que não demonstram o comportamento exigido nunca podem receber
`PASS` para uma feature final. Podem permanecer como evidência técnica
delimitada, sempre com suas limitações.

## 5. Proibições absolutas no pacote oficial

É proibido promover uma entrega usando:

- mock, fake, stub, monkeypatch ou backend substituto para o comportamento que
  está sendo comprovado;
- fixture sintética como se fosse um asset ou projeto produzido pelo usuário;
- teste que só procura strings no código;
- teste que só verifica presença de classe, widget, sinal, chave JSON ou arquivo;
- captura somente da UI sem operação e resultado observável;
- gerador externo apresentado como funcionalidade do editor;
- JSON/sidecar apresentado como cena nativa sem materialização e execução;
- `skip`, `xfail`, `expected failure`, `continue-on-error` ou retry que oculte
  uma falha;
- seleção parcial, `--ignore`, `--deselect`, filtros ou subconjunto que substitua
  a suíte oficial;
- alteração de threshold, golden image, hash, baseline ou tolerância depois de
  observar o resultado;
- captura ou log truncado, sanitizado de forma a remover erro, warning ou
  fallback;
- sucesso declarado antes de o efeito solicitado ser observado.

Um mock pode existir em teste auxiliar de UI, mas esse teste deve ser separado,
marcado `DIAGNOSTIC_ONLY` e nunca contado como prova do comportamento real.

## 6. Requisitos do teste real

Quando a feature for visual ou de engine, o pacote deverá demonstrar:

1. entrada real e controlada;
2. fluxo acessível pelo usuário;
3. artefato gerado pela implementação sob teste;
4. importação em projeto limpo quando houver destino;
5. processo real iniciado;
6. componente, hierarquia ou recurso observado;
7. resultado visual/comportamental observado;
8. salvar, fechar e reabrir quando aplicável;
9. cenário negativo e mensagem acionável;
10. versão da engine, pacote, OS, GPU e commit;
11. captura proveniente do processo executado;
12. logs completos, sem warning não resolvido;
13. hash e tamanho de cada artefato;
14. comparação contra a expectativa previamente registrada.

`nographics`, modo headless ou execução sem captura podem ser usados apenas
quando o requisito for estritamente não visual e isso estiver declarado. Eles
não comprovam renderização, iluminação, partículas visuais, materiais ou UX.

## 7. Bloqueios automáticos de entrega

O validador obrigatório deve recusar o pacote se ocorrer qualquer uma destas
condições:

- plano, governança ou recibo ausente;
- hash divergente;
- requisito, feature, commit, teste, artefato, resultado ou limitação ausente;
- teste não marcado como suíte oficial completa;
- exit code diferente de zero;
- skip, xfail, falha, erro ou warning maior que zero;
- comando com bypass conhecido;
- `mocks_used: true`;
- classe de evidência inadequada;
- `diagnostic_only`, `synthetic_fixture`, `source_only`, `ui_only`,
  `contract_only`, `structural_only` ou `external_tool_only` verdadeiro;
- fallback oculto ou diagnóstico não resolvido;
- artefato inexistente, não hashado, com bytes divergentes ou não rastreado;
- fluxo real não declarado;
- engine exigida mas não executada;
- processo não iniciado, não observado ou encerrado com erro;
- captura visual exigida mas ausente;
- claim de produto completo com limitações não resolvidas;
- árvore de origem suja quando o pacote exigir commit reprodutível.

O bloqueio é positivo: o gate deve informar a causa e não fabricar um
resultado alternativo.

## 8. Skips, segurança e ambiente controlado

Teste impedido por privilégio, shutdown, symlink, licença ou ambiente não é
`PASS`. Deve ser `BLOCKED` ou `NOT_APPLICABLE` com justificativa e evidência.

Symlink, shutdown e soak de Unity continuam proibidos no host. Podem ser
executados apenas em Windows Sandbox, Docker Desktop ou ambiente descartável
equivalente. O pacote deve registrar o limite; não pode transformar o skip do
host em aprovação da funcionalidade.

O gate não autoriza credenciais, tokens ou arquivos de licença no repositório.

## 9. Evidência histórica

Falhas, warnings, skips, logs de abort, diagnósticos de licensing e resultados
anteriores são imutáveis como histórico. Um novo pacote deve apontar para eles,
explicar a diferença e preservar seus hashes. Nunca se reescreve o passado para
parecer que a correção já existia.

## 10. Regra de parada

Interromper imediatamente a etapa quando houver:

- divergência entre código e documentação;
- resultado incompatível com o claim;
- indício de mock/fake ou substituição indevida;
- hash, captura ou log não verificável;
- regressão, perda de dados ou migração destrutiva;
- timeout ou processo que não encerra de modo verificável;
- warning, skip ou fallback não explicado;
- tentativa de alterar regra, threshold ou baseline após a falha.

O relatório deve registrar o bloqueio e o próximo requisito objetivo. Continuar
por insistência, esperar indefinidamente sem atualizar o estado ou declarar
sucesso parcial como sucesso total é proibido.

## 11. Alterações permitidas

Alterações de código, schema, exportador, renderer ou testes deverão:

- preservar o plano-base;
- usar checkpoint e branch isolados;
- possuir análise de impacto;
- adicionar testes antes do claim;
- manter compatibilidade ou migração explícita;
- produzir novo artefato e hash;
- executar o gate da etapa e a regressão protegida;
- só então receber decisão formal.

Nenhuma regra será removida ou enfraquecida como parte de uma correção de
produto.

## 12. Integração obrigatória dos comandos de build

O CI deve executar `tools/validate_strict_delivery_gate.py plan` em toda
execução. Scripts de build, empacotamento e instalador devem exigir um recibo
de etapa `PASS` e um manifesto `OFFICIAL_DELIVERY` validado antes de produzir
qualquer saída que possa ser confundida com release.

Um executável local sem manifesto `OFFICIAL_DELIVERY` validado é somente um
candidato não selado e o script oficial deve falhar. Não pode ser publicado,
enviado ao usuário ou usado como evidência de conclusão. O manifesto oficial
deve ser validado com o comando `delivery` ou `all`, no mesmo commit e com
artefatos hashados.
