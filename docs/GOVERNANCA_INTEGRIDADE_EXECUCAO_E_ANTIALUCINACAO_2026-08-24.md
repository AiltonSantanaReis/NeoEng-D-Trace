# Governança de Integridade, Execução e Antialucinação

**Versão:** 1.0  
**Data:** 2026-08-24  
**Status:** documento normativo ativo  
**Escopo:** todas as etapas, fases, planos, baselines, builds, testes, auditorias e revisões do NeoEng-D-Trace

## 1. Finalidade

Este documento estabelece as regras obrigatórias para impedir que o projeto seja aprovado por afirmação não comprovada, teste superficial, alteração oportunista de regra, bypass de ferramenta, redução de escopo ou interpretação favorável de evidência insuficiente.

Ele protege quatro propriedades do projeto:

1. **Verdade:** toda afirmação deve corresponder ao estado real observado.
2. **Rastreabilidade:** toda afirmação deve apontar para requisito, teste e evidência.
3. **Integridade:** nenhuma falha pode ser escondida, removida ou reclassificada apenas para obter `PASS`.
4. **Continuidade:** nenhuma etapa pode avançar antes da conclusão integral da etapa atual.

Este documento é vinculante para código, testes, CI/CD, documentação, auditoria, baseline, builds e revisão humana.

## 2. Hierarquia documental

Nenhum documento poderá ser interpretado isoladamente. O índice documental ativo define quais documentos estão vigentes, quais são dependências e qual documento prevalece em caso de conflito.

A ordem de prevalência é:

1. decisão formal de produto registrada e aprovada;
2. esta governança;
3. plano normativo do produto;
4. adendos normativos ativos;
5. ADRs técnicos ativos;
6. especificação da etapa atual;
7. matriz de IDs e rastreabilidade;
8. relatórios de auditoria e evidências;
9. documentos históricos e superseded.

Um relatório de evidência comprova o que ocorreu; ele não altera requisitos nem autoriza exceções.

## 3. Regras contra alucinação e afirmações não comprovadas

### 3.1 Regra de evidência obrigatória

Nenhuma afirmação de que uma funcionalidade está funcionando poderá ser emitida sem apontar, no mínimo:

- ID do requisito;
- ID da feature;
- commit auditado;
- teste executado;
- artefato gerado;
- resultado observado;
- limitações e fallback utilizados.

Se qualquer elemento faltar, o estado correto será `PENDENTE`, `NÃO COMPROVADO` ou `BLOQUEADO`.

### 3.2 Proibições de inferência

É proibido concluir que uma funcionalidade funciona apenas porque:

- existe uma classe com nome correspondente;
- existe um botão ou menu;
- existe um arquivo de configuração;
- existe um sidecar ou JSON;
- existe um mock;
- existe uma simulação;
- um teste unitário isolado passa;
- a tela abre sem erro;
- o código parece completo;
- outra funcionalidade semelhante funciona;
- uma captura mostra apenas a interface;
- uma execução manual não revelou falha.

Código existente é indício de implementação, não prova de comportamento final.

### 3.3 Linguagem obrigatória de status

Relatórios deverão usar exclusivamente estados controlados:

- `PLANNED` — planejado;
- `IN_PROGRESS` — em implementação;
- `PENDING_EVIDENCE` — implementação alegada, prova ausente;
- `PASS` — todos os critérios passaram;
- `FAIL` — pelo menos um critério falhou;
- `BLOCKED` — não é possível concluir por impedimento identificado;
- `DEPRECATED` — substituído formalmente;
- `NOT_APPLICABLE` — somente com justificativa e aprovação.

Expressões como “parece funcionar”, “praticamente pronto”, “validado em essência”, “sem problemas aparentes” e “equivalente o suficiente” não são estados válidos.

### 3.4 Incerteza obrigatoriamente declarada

Quando o agente, auditor ou desenvolvedor não possuir evidência suficiente, deverá declarar a incerteza e interromper a conclusão daquele requisito. Não poderá preencher a lacuna com suposição.

## 4. Proibição de force, bypass e manipulação de resultado

### 4.1 Proibições no fluxo oficial

É proibido utilizar, para obter `PASS` ou encerrar uma etapa:

- `git push --force` ou equivalente;
- `--no-verify`;
- desativação de hooks;
- exclusão de testes que falharam;
- `skip`, `xfail`, `expected failure` ou `continue-on-error` para mascarar falha;
- exclusão de testes por `-k`, `--ignore`, filtros ou seleção parcial no pacote oficial;
- redução de cobertura exigida depois de observar o resultado;
- alteração de threshold para converter `FAIL` em `PASS`;
- alteração de golden image, hash ou baseline sem revisão formal;
- mock que substitua o comportamento real exigido;
- execução somente do subconjunto que passa;
- ocultação de logs, warnings, fallback ou erros de inicialização;
- mudança no plano ou requisito sem controle de mudança;
- alteração da baseline para remover arquivos, testes ou evidências problemáticas.

### 4.2 Uso permitido fora do fluxo oficial

Execuções focadas, filtros e mocks poderão ser usados durante diagnóstico local, desde que:

- sejam identificados como `DIAGNOSTIC_ONLY`;
- não sejam publicados como prova de conclusão;
- não substituam a execução oficial;
- não alterem requisitos, testes ou thresholds;
- o relatório final informe que a execução foi parcial.

### 4.3 Falha preservada

Uma falha oficial deverá permanecer registrada até a correção. O resultado não poderá ser apagado apenas porque uma execução posterior passou. A correção deverá preservar o artefato anterior e produzir novo pacote vinculado ao novo commit.

## 5. Testes que validam funcionalidades reais

### 5.1 Princípio

Cobertura de linhas não é prova suficiente. Todo requisito deverá ser validado no nível de comportamento correspondente.

### 5.2 Camadas obrigatórias de teste

Cada funcionalidade deverá possuir, conforme aplicável:

1. **Teste unitário:** regras determinísticas e invariantes.
2. **Teste de contrato:** schema, IDs, interfaces e compatibilidade.
3. **Teste de integração:** interação entre domínio, renderer, UI e runtime.
4. **Teste funcional:** fluxo real acessível ao usuário.
5. **Teste visual:** pixels, composição, overlays ou captura verificável.
6. **Teste de persistência:** salvar, fechar, reabrir e comparar.
7. **Teste de runtime:** execução fora da UI quando aplicável.
8. **Teste de desempenho:** tempo de frame, memória e escala.
9. **Teste de falha:** asset ausente, backend indisponível, schema inválido e recuperação.

### 5.3 Proibição de teste superficial

Não será aceito como teste de uma funcionalidade visual:

- verificar somente que o widget existe;
- verificar somente que o método não lança exceção;
- verificar somente que um sinal foi emitido;
- verificar somente que um dicionário possui uma chave;
- testar uma versão mockada quando o requisito exige renderer real;
- testar apenas o caminho feliz;
- testar apenas um tamanho de imagem ou uma resolução;
- testar apenas o editor quando o requisito inclui runtime.

### 5.4 Cobertura

O CI deverá publicar cobertura por módulo, requisito e tipo de teste. A cobertura deverá incluir linhas, branches e condições para domínio, persistência e renderer onde a ferramenta permitir.

Thresholds serão definidos antes da implementação da fase e não poderão ser reduzidos após uma falha. A cobertura deverá ser acompanhada de testes de comportamento e, para componentes críticos, testes mutation ou equivalente de eficácia.

Um módulo com alta cobertura e testes que não verificam o resultado real continuará reprovado.

### 5.5 Critérios mínimos de eficácia

Para uma funcionalidade visual ser `PASS`, o pacote deverá demonstrar:

- entrada controlada;
- operação real;
- saída observável;
- comparação com resultado esperado;
- persistência quando aplicável;
- integração com o fluxo do usuário;
- runtime quando aplicável;
- comportamento de erro;
- ausência de fallback oculto.

## 6. Documentação interligada

O índice documental ativo deverá registrar para cada documento:

- ID do documento;
- caminho;
- tipo;
- status;
- versão;
- autoridade;
- dependências;
- documentos que ele governa;
- documento que o substituiu, se houver;
- etapa/fase relacionada.

Cada documento normativo deverá conter uma seção de dependências e links para:

- governança;
- plano principal;
- adendos ativos;
- registro de IDs;
- ADRs aplicáveis;
- especificação da etapa;
- evidências;
- baseline correspondente.

Um documento sem status ou sem vínculo documental não poderá ser usado como autoridade de execução.

## 7. Baseline preparada para o produto completo

A baseline não poderá ser uma fotografia limitada ao estado atual. Ela deverá preservar contratos para evolução futura.

Cada baseline deverá conter:

- manifesto completo;
- IDs publicados e reservados;
- schema versionado;
- migrações conhecidas;
- capabilities suportadas e planejadas;
- contratos de renderer;
- contratos de runtime;
- fixtures de teste;
- métricas de desempenho;
- limites de compatibilidade;
- dependências travadas;
- riscos conhecidos;
- vínculo com baseline anterior;
- pontos de extensão para fases futuras.

### 7.1 Regras contra limitação futura

Nenhuma implementação poderá:

- fixar um modelo de dados que impeça profundidade ou câmera futura;
- consumir o ID de uma feature de modo que impeça sua extensão;
- salvar dados sem versão;
- eliminar campos desconhecidos durante migração;
- vincular o domínio diretamente a um widget específico;
- assumir que toda entidade é apenas uma imagem plana;
- assumir que todo renderer futuro será o `CanvasView`.

Se uma restrição for tecnicamente necessária, ela deverá ser registrada em ADR com impacto, duração e plano de remoção ou substituição.

## 8. Regra de avanço sequencial

As etapas são dependentes e não poderão ser puladas.

Uma etapa só poderá mudar para `CONCLUÍDA` quando:

1. todos os requisitos da etapa estiverem `PASS`;
2. todos os testes obrigatórios tiverem sido executados;
3. cobertura e eficácia estiverem aprovadas;
4. regressão das etapas anteriores tiver passado;
5. documentação estiver atualizada e vinculada;
6. evidências estiverem empacotadas e hashadas;
7. build estiver identificada;
8. revisão humana estiver concluída quando exigida;
9. aprovação formal estiver registrada;
10. commit e baseline estiverem vinculados.

Uma etapa posterior poderá ter trabalho preparatório não funcional, desde que:

- seja marcado como `PREPARATORY_ONLY`;
- não seja declarado como avanço da etapa;
- não altere o resultado da etapa atual;
- não seja usado para contornar uma pendência;
- seja separado em build e evidência próprias.

Nenhuma funcionalidade da etapa posterior poderá ser usada para justificar a conclusão da etapa atual.

## 9. Desenvolvimento orientado à não regressão

Cada etapa deverá ser projetada considerando:

- requisitos das etapas anteriores;
- requisitos já aprovados das etapas posteriores;
- extensibilidade do modelo;
- compatibilidade do schema;
- impacto no renderer;
- impacto no runtime;
- impacto na UI;
- impacto nos testes e artefatos.

Antes de iniciar uma etapa, deverá existir uma análise de impacto contendo:

- módulos afetados;
- IDs afetados;
- contratos preservados;
- contratos ampliados;
- riscos de regressão;
- testes de proteção;
- estratégia de migração;
- compatibilidade com o produto final.

Nenhuma adaptação futura será considerada necessária apenas por conveniência. Ela deverá ser demonstrada por evidência técnica e aprovada.

## 10. Controle de mudança

Qualquer alteração em requisito, baseline, threshold, teste, schema, ID, documento ativo ou critério de aceite deverá gerar:

- `ADR` ou registro de mudança;
- IDs afetados;
- justificativa;
- comparação antes/depois;
- impacto em fases concluídas;
- impacto em fases futuras;
- novos testes;
- novos artefatos;
- aprovação.

Alterar a regra para obter `PASS` é proibido. Se a regra estiver incorreta, o estado correto é `CHANGE_PROPOSED` até a aprovação e reexecução completa dos critérios.

## 11. Condições formais de encerramento do projeto

O projeto não poderá ser declarado concluído sem:

1. todas as etapas obrigatórias concluídas sequencialmente;
2. governança ativa e índice documental íntegro;
3. IDs sem duplicidade ou reutilização;
4. matriz de rastreabilidade completa;
5. cobertura e eficácia aprovadas;
6. nenhum bypass no pacote oficial;
7. nenhuma falha omitida;
8. baseline final encadeada e extensível;
9. renderer real comprovado;
10. editor/runtime comparados;
11. build limpa instalada;
12. revisão humana aprovada;
13. limitações documentadas;
14. commit final e artefatos hashados.

Até cumprir todos os itens, o estado oficial será `IN_PROGRESS` ou `BLOCKED`, nunca `COMPLETED`.
