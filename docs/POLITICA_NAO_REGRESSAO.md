# Política de Preservação Funcional e Não Regressão

**Projeto:** NeoEng-D-Trace — anteriormente identificado como PolygonTool
**Documento:** Política obrigatória de engenharia
**Versão:** 1.0
**Status:** Aprovada para adoção imediata
**Aplicação:** todas as etapas, patches, refatorações, correções, modernizações, migrações e releases

---

## 1. Objetivo

Esta política estabelece regras obrigatórias para impedir que funcionalidades úteis, comportamentos existentes, formatos de arquivo, dados do usuário ou integrações sejam removidos, alterados ou degradados silenciosamente durante o desenvolvimento do projeto.

O objetivo da modernização não é reduzir o produto por exclusão indiscriminada. O objetivo é:

- preservar capacidades úteis;
- corrigir comportamentos defeituosos sem esconder limitações;
- reorganizar a arquitetura sem alterar silenciosamente resultados;
- substituir implementações somente depois de comprovar equivalência ou melhoria;
- impedir perda de dados, compatibilidade ou produtividade do usuário;
- registrar com precisão tudo que foi validado, não validado, alterado ou removido.

> **Regra absoluta:** nenhuma funcionalidade será removida silenciosamente.

---

## 2. Escopo

Esta política aplica-se a:

- código-fonte;
- interface gráfica;
- ferramentas de edição;
- detecção e processamento de imagens;
- seleção, laços, máscaras, curvas e polígonos;
- colisões e física;
- importadores e exportadores;
- arquivos de projeto;
- configurações e preferências;
- atalhos de teclado;
- formatos de saída;
- integração com engines;
- testes automatizados;
- scripts de build e empacotamento;
- documentação;
- APIs internas e públicas;
- desempenho, consumo de memória e tempo de resposta;
- compatibilidade com versões anteriores.

A política também se aplica a arquivos aparentemente antigos, duplicados, desconectados ou experimentais. Nenhum desses arquivos poderá ser descartado sem análise e registro.

---

## 3. Princípios obrigatórios

### 3.1 Preservar antes de simplificar

Uma arquitetura mais limpa não justifica perda funcional. A reorganização interna deve manter o comportamento útil observado, salvo quando existir uma decisão formal de produto para alterá-lo.

### 3.2 Evidência antes de afirmação

Nenhuma funcionalidade poderá ser declarada como:

- pronta;
- corrigida;
- equivalente;
- mais rápida;
- compatível;
- segura;
- sem regressão;

sem testes ou evidências verificáveis.

Quando um teste não puder ser executado, o relatório deverá usar explicitamente uma das classificações:

- **não testado**;
- **teste bloqueado**;
- **validação parcial**;
- **requer validação no Windows**;
- **requer validação gráfica**;
- **requer validação na engine de destino**.

### 3.3 Nenhuma exclusão por aparência

Um arquivo não será considerado inútil somente porque:

- não está importado diretamente pelo inicializador;
- existe outra implementação semelhante;
- possui nome antigo;
- está fora da interface atual;
- não possui teste;
- contém código experimental;
- está em uma branch ou backup;
- utiliza uma biblioteca antiga;
- está incompleto.

### 3.4 Substituição progressiva

Uma implementação nova deve coexistir com a anterior até que existam provas suficientes de que ela:

- cobre todos os casos relevantes;
- preserva os dados;
- mantém ou melhora os resultados;
- não reduz opções úteis;
- possui testes equivalentes ou superiores;
- permite rollback.

### 3.5 Falha visível é preferível à perda silenciosa

Quando o software não puder concluir uma operação com segurança, deverá:

- interromper a operação;
- preservar o estado anterior;
- informar o motivo de forma compreensível;
- registrar detalhes técnicos em log;
- oferecer recuperação ou tentativa posterior quando aplicável.

O software não deverá gerar arquivos parcialmente válidos, sobrescrever dados corretos ou ignorar erros silenciosamente.

---

## 4. Classificação obrigatória das funcionalidades

Toda funcionalidade identificada deverá ser registrada em uma matriz e classificada em uma das categorias abaixo.

### 4.1 Funcional e validada

A funcionalidade opera conforme esperado e possui evidência de teste.

**Tratamento:** preservar, documentar e proteger com testes de regressão.

### 4.2 Funcional, mas frágil

A funcionalidade opera, porém possui forte acoplamento, baixa cobertura de testes, comportamento instável ou dependências inadequadas.

**Tratamento:** manter disponível enquanto é encapsulada e substituída progressivamente.

### 4.3 Parcialmente funcional

A funcionalidade possui partes úteis, mas não atende completamente ao objetivo proposto.

**Tratamento:** não remover; documentar limitações, isolar riscos e planejar conclusão.

### 4.4 Experimental

A funcionalidade está em desenvolvimento, pode mudar e ainda não deve ser apresentada como estável.

**Tratamento:** manter separada, sinalizada e desabilitada por padrão quando representar risco ao usuário.

### 4.5 Duplicada ou alternativa

Existem duas ou mais implementações semelhantes.

**Tratamento:** preservar todas até realizar comparação funcional, de qualidade, desempenho, compatibilidade e manutenção.

### 4.6 Não conectada à interface

Existe código potencialmente útil, mas sem acesso pelo fluxo principal.

**Tratamento:** avaliar como capacidade interna, recurso futuro, ferramenta de diagnóstico ou implementação incompleta. A ausência na interface não autoriza exclusão.

### 4.7 Com erro conhecido

A funcionalidade possui falha reproduzível.

**Tratamento:** registrar o erro, preservar o caso de teste e corrigir sem mascarar o problema.

### 4.8 Obsoleta ou insegura

A funcionalidade utiliza tecnologia inadequada, produz resultado incorreto ou cria risco real.

**Tratamento:** desabilitar com justificativa quando necessário, implementar substituição e iniciar processo formal de depreciação. A remoção imediata só será permitida quando a continuidade criar risco grave e comprovado.

---

## 5. Fluxo obrigatório para qualquer alteração

### 5.1 Registrar a linha de base

Antes de alterar um módulo, devem ser registrados:

- arquivos envolvidos;
- comportamento atual;
- entradas aceitas;
- saídas produzidas;
- mensagens e erros atuais;
- dependências diretas e indiretas;
- testes existentes;
- desempenho observável quando relevante;
- limitações conhecidas;
- arquivos de exemplo utilizados.

### 5.2 Criar testes de caracterização

Quando não houver cobertura suficiente, deverão ser criados testes que capturem o comportamento atual antes da refatoração.

Testes de caracterização não significam que o comportamento atual é ideal. Eles servem para revelar alterações involuntárias.

Exemplos:

- uma determinada imagem e configuração devem gerar um contorno comparável;
- um projeto salvo deve abrir com os mesmos elementos;
- uma cena exportada deve manter pivô, escala e polígonos;
- desfazer e refazer devem restaurar exatamente o estado esperado;
- uma colisão deve produzir o mesmo resultado dentro da tolerância definida.

### 5.3 Implementar sem destruir o caminho anterior

A implementação nova deverá, sempre que tecnicamente possível:

- ficar atrás de uma interface comum;
- ser ativada por configuração ou seleção explícita durante a transição;
- permitir comparação com a implementação anterior;
- preservar o caminho de rollback;
- não alterar arquivos do usuário de forma irreversível.

### 5.4 Comparar resultados

A comparação deve considerar, conforme aplicável:

- equivalência visual;
- equivalência geométrica;
- contagem de vértices;
- tolerância espacial;
- preservação de buracos e ilhas;
- tempo de execução;
- memória utilizada;
- determinismo;
- formato e conteúdo da exportação;
- comportamento da interface;
- mensagens ao usuário;
- compatibilidade com projetos anteriores.

### 5.5 Executar os portões de validação

Nenhuma alteração funcional será considerada concluída sem os portões aplicáveis:

1. compilação sintática;
2. importação dos módulos;
3. testes unitários;
4. testes de integração;
5. testes de caracterização;
6. testes de interface;
7. abertura e salvamento de projeto;
8. validação de exportação;
9. teste real no Windows;
10. inspeção do diff;
11. verificação de exclusões acidentais;
12. verificação de regressão de desempenho;
13. verificação de compatibilidade de dados;
14. registro dos testes não executados.

### 5.6 Documentar o resultado

Cada etapa ou patch deverá informar:

- o que foi alterado;
- o que foi preservado;
- o que não foi alterado;
- quais testes foram executados;
- quais testes passaram;
- quais testes falharam;
- quais testes não puderam ser executados;
- riscos conhecidos;
- forma de rollback;
- arquivos novos, modificados e removidos.

---

## 6. Política de depreciação e remoção

### 6.1 Proibição de remoção silenciosa

É proibido remover, ocultar ou tornar inacessível uma funcionalidade sem:

- inventário prévio;
- justificativa técnica ou de produto;
- análise de impacto;
- alternativa equivalente ou superior;
- testes de migração;
- registro no changelog;
- plano de rollback;
- aprovação explícita.

### 6.2 Perguntas obrigatórias antes de remover

Toda proposta de remoção deverá responder:

1. Qual função exclusiva este código oferece?
2. Existe chamada direta, indireta, dinâmica ou por configuração?
3. Existe algum fluxo de usuário que dependa dele?
4. Existem projetos antigos ou arquivos exportados que dependam dele?
5. Existe implementação substituta?
6. A substituição cobre todos os parâmetros e resultados?
7. Existem testes comparativos?
8. Existe risco de perda de dados?
9. Existe caminho de migração?
10. Existe rollback?
11. A remoção foi documentada?
12. A remoção foi aprovada?

Se uma resposta relevante estiver indefinida, a remoção será bloqueada.

### 6.3 Período de depreciação

Salvo em caso de vulnerabilidade grave, uma funcionalidade substituída deverá:

- ser marcada como legada;
- permanecer acessível durante o período definido;
- informar a alternativa recomendada;
- manter compatibilidade de leitura;
- possuir documentação de migração;
- ser removida apenas em versão principal futura.

### 6.4 Código inseguro

Quando uma funcionalidade criar risco comprovado de corrupção, execução insegura ou perda de dados, ela poderá ser desabilitada antes da substituição completa, desde que:

- o risco seja documentado;
- o código seja preservado no histórico;
- o usuário seja informado;
- exista plano de correção;
- a decisão não seja apresentada como funcionalidade concluída.

---

## 7. Compatibilidade de projetos e dados

### 7.1 Formato versionado

O formato de projeto deverá possuir versão explícita.

Exemplo conceitual:

```json
{
  "format_version": 1,
  "application_version": "1.0.0",
  "project": {}
}
```

### 7.2 Migrações explícitas

Alterações de formato deverão usar migrações versionadas e testadas.

Uma migração deverá:

- criar backup antes de alterar;
- validar o conteúdo de origem;
- preservar campos desconhecidos quando possível;
- impedir sobrescrita em caso de falha;
- gerar log da operação;
- permitir recuperação.

### 7.3 Compatibilidade de leitura

Versões novas deverão continuar lendo projetos antigos dentro da política de suporte definida.

Quando não for possível, o software deverá informar claramente:

- a versão detectada;
- a versão mínima suportada;
- a ferramenta ou procedimento necessário para migração;
- a localização do backup preservado.

### 7.4 Gravação atômica

Arquivos de projeto e exportações críticas deverão ser gravados primeiro em arquivo temporário, validados e somente depois substituídos no destino final.

---

## 8. Não regressão da interface e experiência do usuário

Uma funcionalidade não será considerada preservada apenas porque o código ainda existe.

Também devem ser preservados ou deliberadamente melhorados:

- acesso pelo menu ou ferramenta;
- atalhos;
- parâmetros disponíveis;
- feedback visual;
- mensagens de erro;
- possibilidade de cancelar;
- estado de seleção;
- desfazer e refazer;
- foco de teclado;
- zoom e navegação;
- legibilidade;
- consistência entre telas;
- acessibilidade básica.

Mudanças de interface que removam opções úteis ou escondam capacidades deverão ser tratadas como alterações funcionais e passar pelos mesmos critérios de aprovação.

---

## 9. Não regressão de desempenho

Modernizações não deverão tornar operações relevantes significativamente mais lentas ou aumentar o consumo de memória sem justificativa registrada.

Quando aplicável, cada mudança deverá comparar:

- tempo médio;
- pior caso;
- consumo máximo de memória;
- tamanho dos arquivos gerados;
- responsividade da interface;
- capacidade de cancelamento;
- uso de CPU e GPU;
- comportamento com imagens grandes;
- comportamento com muitos polígonos.

Uma regressão de desempenho poderá ser aceita somente quando trouxer benefício funcional ou de segurança comprovado e depois de aprovação.

---

## 10. Atualização de bibliotecas e dependências

Nenhuma biblioteca será substituída apenas por ser mais recente.

A atualização deverá considerar:

- compatibilidade com Python e Windows;
- maturidade e manutenção;
- licença;
- segurança;
- estabilidade da API;
- tamanho do pacote;
- disponibilidade de wheels;
- impacto no build;
- impacto no desempenho;
- equivalência funcional;
- migração dos dados;
- testes existentes.

Durante uma migração importante, a implementação antiga poderá permanecer disponível temporariamente por adaptador, feature flag ou camada de compatibilidade.

---

## 11. Política para testes existentes

É proibido excluir testes apenas para fazer a suíte passar.

Um teste poderá ser:

- corrigido quando estiver incorreto;
- atualizado quando o requisito tiver mudado formalmente;
- movido para outra categoria;
- marcado temporariamente como esperado para falhar;
- marcado como dependente de ambiente;
- substituído por teste mais abrangente.

Toda exclusão de teste deverá possuir justificativa e prova de que sua cobertura foi preservada ou ampliada.

Testes antigos, scripts de reprodução e casos de falha deverão ser avaliados como ativos de conhecimento, e não como lixo automático.

---

## 12. Matriz obrigatória de regressão

Cada etapa deverá atualizar uma matriz semelhante a esta:

| Funcionalidade | Estado de referência | Alteração realizada | Teste automatizado | Teste Windows | Compatibilidade | Resultado |
|---|---|---|---|---|---|---|
| Importar PNG | Funcional | Nenhuma | Aprovado | Aprovado | Preservada | Liberado |
| Laço magnético | Parcial | Refatoração interna | Aprovado parcialmente | Pendente | Não comprovada | Não liberar |
| Exportação Godot | Funcional | Novo adaptador | Aprovado | Aprovado na engine | Preservada | Liberado |
| Extrusão GLB | Experimental | Correção de triangulação | Parcial | Não executado | Indefinida | Experimental |

Estados permitidos para o resultado:

- **Liberado**;
- **Liberado com limitação documentada**;
- **Experimental**;
- **Bloqueado**;
- **Requer validação adicional**;
- **Revertido**.

---

## 13. Conteúdo obrigatório de cada patch

Todo patch deverá ser acompanhado por:

1. objetivo da alteração;
2. lista exata dos arquivos alterados;
3. funcionalidades afetadas;
4. funcionalidades explicitamente preservadas;
5. testes executados;
6. resultados dos testes;
7. testes não executados;
8. riscos conhecidos;
9. instruções de aplicação;
10. instruções de reversão;
11. necessidade ou não de migração;
12. confirmação de que não existem exclusões inesperadas.

Quando um patch contiver remoção, também deverá incluir:

- justificativa;
- substituição;
- evidência de equivalência;
- aprovação explícita;
- registro de depreciação anterior.

---

## 14. Rollback obrigatório

Toda alteração de risco médio ou alto deverá possuir mecanismo de reversão.

O rollback poderá usar:

- reversão de commit;
- patch inverso;
- restauração de arquivo;
- feature flag;
- configuração de implementação antiga;
- backup do projeto;
- migração reversa, quando segura.

Uma etapa não deverá avançar se o caminho de rollback depender de memória, procedimento não documentado ou arquivo que não foi preservado.

---

## 15. Critérios para considerar uma funcionalidade preservada

Uma funcionalidade será considerada preservada somente quando:

- continua acessível ao usuário ou por API prevista;
- aceita entradas equivalentes;
- produz resultados equivalentes ou melhores;
- mantém parâmetros úteis;
- preserva dados anteriores;
- mantém tratamento de erro adequado;
- possui testes compatíveis;
- não apresenta regressão crítica de desempenho;
- não cria risco novo de segurança;
- foi validada no ambiente necessário;
- está documentada.

A simples existência de classes ou funções no repositório não comprova preservação funcional.

---

## 16. Critérios de conclusão de uma etapa

Uma etapa somente poderá ser declarada concluída quando:

- o escopo planejado estiver implementado;
- as funções existentes afetadas tiverem sido inventariadas;
- os testes aplicáveis tiverem sido executados;
- os resultados tiverem sido registrados;
- nenhuma exclusão inesperada estiver presente;
- os arquivos do usuário permanecerem compatíveis ou tiverem migração segura;
- o aplicativo iniciar no ambiente de destino;
- existir rollback;
- limitações forem declaradas sem maquiagem;
- a matriz de regressão estiver atualizada.

Caso algum item esteja pendente, a etapa deverá ser classificada como parcial, experimental ou bloqueada.

---

## 17. Exceções

Qualquer exceção a esta política deverá conter:

- descrição do motivo;
- risco de manter o comportamento atual;
- risco da alteração proposta;
- impacto no usuário;
- alternativas avaliadas;
- plano de recuperação;
- aprovação explícita;
- registro permanente no histórico do projeto.

Não serão aceitas como justificativa isolada:

- “o código está feio”;
- “parece antigo”;
- “provavelmente não é usado”;
- “a nova biblioteca deve funcionar”;
- “o teste estava atrapalhando”;
- “a refatoração ficou mais limpa”;
- “o arquivo parecia duplicado”.

---

## 18. Compromisso do projeto

O projeto adota formalmente o seguinte compromisso:

> **Modernizar sem amputar. Corrigir sem esconder. Refatorar sem mudar silenciosamente o comportamento. Substituir somente depois de provar equivalência ou melhoria. Preservar dados e possibilidades úteis ao usuário durante toda a evolução do produto.**

Esta política é parte da fonte de verdade do projeto e deverá ser consultada antes de qualquer decisão de remoção, consolidação, migração, atualização de biblioteca ou alteração de arquitetura.
