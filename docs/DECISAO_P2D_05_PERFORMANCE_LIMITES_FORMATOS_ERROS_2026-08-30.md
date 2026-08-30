# NeoEng-D-Trace — Decisão formal P2D-05

**Etapa:** P2D-05 — performance, limites, formatos e erros
**Status:** OPEN — decisão/contrato; implementação não autorizada
**Data de abertura:** 30/08/2026 (UTC-03)
**Entrada técnica:** merge commit f55b07b85ef2cf65160f2c10ffac5e63b45732ac
**Branch de entrada:** main
**Aceite do proprietário:** pendente

## 1. Finalidade e precedência

Este documento abre formalmente P2D-05 e congela o contrato de trabalho para
performance, limites operacionais, formatos e tratamento de erros da fundação
profissional de composição 2D. Ele não autoriza implementação antes do aceite
explícito do proprietário e não declara qualquer capacidade como concluída.

A ordem de precedência é:

1. docs/REQUISITOS_EDITOR_CENARIOS_COMPLETO_2026-08-30.md;
2. docs/PLANO_EVOLUCAO_EDITOR_2D_2_5D_3D_E_LINHAS_INDEPENDENTES_2026-08-29.md;
3. docs/POLITICA_QUALIDADE_E_EVIDENCIAS.md;
4. docs/PLANO_PRODUTO_PROFISSIONAL_NORMATIVO_COMPLETO_2026-08-24.md;
5. este contrato P2D-05;
6. evidências e decisões posteriores, somente dentro das fronteiras que este
   contrato autorizar.

P2D-05 é uma etapa de robustez da fundação já aceita. Não é uma autorização
para iniciar tilemap, colisão própria de cenário, NavMesh, entidades,
componentes, prefabs, iluminação, sombras, partículas, pós-processamento,
shaders editáveis, VFX, vetorização ou uma linha 3D. Cada uma dessas
capacidades continua dependente de seu próprio contrato e aceite.

## 2. Estado de entrada auditado somente em leitura

O preflight da abertura registrou:

| Item | Resultado |
|---|---|
| Branch local | main |
| HEAD local | f55b07b85ef2cf65160f2c10ffac5e63b45732ac |
| origin/main | f55b07b85ef2cf65160f2c10ffac5e63b45732ac |
| PR anterior | #163, estado MERGED |
| Árvore tracked | limpa |
| git diff --check | sem saída / PASS |
| Untracked | preservados; fora da fronteira desta etapa |

O merge anterior foi realizado por PR normal, sem force-push, sem tag e sem
limpeza de untracked. Os checks protegidos test e test-windows passaram no
head publicado b777cf06209602f3d1a1afe3ca4eebc76e72d3d5. A suíte local que
precedeu o merge registrou 1842 passed, 2 skipped e cobertura total de linhas
de 90,83%; a política de cobertura de branches passou.

O snapshot docs/EVIDENCIA_P2D_04_POSTCOMMIT_2026-08-30.md permanece
imutável como registro da qualificação técnica anterior ao ciclo remoto. A
publicação posterior é registrada separadamente no adendo
docs/EVIDENCIA_P2D_04_PUBLICACAO_2026-08-30.md e não altera os fatos do
snapshot original.

## 3. Resultado de produto que P2D-05 deve proteger

Ao final da etapa, todas as operações já existentes na composição profissional
devem falhar de maneira controlada, reproduzível e compreensível quando
receberem dados inválidos, incompletos, excessivos, incompatíveis ou
indisponíveis. Nenhuma operação poderá deixar mutação parcial, arquivo
truncado, estado aparentemente salvo, exportação ambígua ou divergência não
documentada entre plataformas.

P2D-05 também deve produzir uma medição reproduzível do comportamento de
performance dos fluxos que já existem. A etapa não poderá transformar uma
operação lenta em aprovada apenas por não falhar; os tempos, percentis,
memória, workload e hardware deverão ser registrados.

## 4. Auditoria factual do estado atual

### 4.1 Limites já centralizados

O módulo src/core/operational_limits.py já contém tetos reutilizados pelo
produto, entre eles:

- arquivo de projeto: 64 MiB;
- objetos de projeto: 100.000;
- pontos de projeto: 1.000.000;
- camadas: 10.000;
- grupos: 10.000;
- membros de grupo: 100.000;
- pontos por polígono: 2.000;
- complexidade poligonal total: 4.000.000;
- células por AABB da grade uniforme: 100.000;
- imagem: 256 MiB, dimensão máxima 8.192 e 16.777.216 pixels;
- atlas: dimensão máxima 8.192, 10.000 itens e 16 páginas;
- arquivo de log: 5 MiB, além dos limites de texto e evento de validação;
- índice GLTF de 16 bits: 65.535.

Esses valores são fatos do código atual, não são novos limites aprovados por
este documento. P2D-05 deverá provar, em cada fronteira relevante, se o limite
é realmente aplicado, se o caso exatamente no limite é aceito, se o primeiro
valor acima é rejeitado e se a mensagem identifica o recurso e o teto.

### 4.2 Formatos e persistência existentes

O fluxo profissional possui persistência JSON canônica versionada V1/V2,
recovery lateral explícito, validação de UTF-8 estrito, rejeição de BOM,
duplicação de chaves e números não finitos, validação de referências e hash de
assets, escrita atômica e exportação profissional genérica/Godot/Unity com
mapping de coordenadas declarado.

Esses fatos não significam que P2D-05 já esteja concluída. A etapa ainda deve
verificar matriz completa de versões, entradas inválidas, limites, semântica de
campos desconhecidos, determinismo, compatibilidade entre plataformas e
mensagens de erro no fluxo real de usuário.

### 4.3 Performance e erros ainda não fechados como contrato P2D-05

Há benchmark determinístico existente para o pipeline de detecção automática,
mas ele não constitui uma matriz de performance do editor profissional de
composição, da persistência, do recovery ou da exportação P2D-04. Não existe
decisão P2D-05 anterior nem relatório P2D-05 aceito.

As APIs já possuem exceções tipadas em pontos importantes, porém a etapa deve
auditar se cada erro exposto ao usuário informa, sem depender de traceback:

1. o que ocorreu;
2. qual arquivo, asset, objeto ou operação foi afetado, sem vazar caminho
   pessoal ou segredo;
3. qual limite, formato ou pré-condição foi violado;
4. se o estado anterior foi preservado;
5. qual ação objetiva o usuário pode tomar.

Mensagens genéricas, fallback silencioso, sucesso sem confirmação do efeito ou
captura ampla que esconda corrupção permanecem reprovação até correção e nova
prova.

## 5. Escopo obrigatório

P2D-05 deverá cobrir integralmente, dentro da fundação profissional já
existente:

### 5.1 Matriz de limites

- inventariar cada limite usado em carregamento, validação, edição,
  persistência, recovery, asset e exportação;
- vincular limite a unidade, constante, ponto de aplicação, mensagem,
  teste positivo, teste de fronteira e teste negativo;
- verificar aceitação no limite e rejeição no primeiro valor excedente;
- impedir alocação ou mutação parcial antes da rejeição quando o limite puder
  ser conhecido previamente;
- preservar os valores normativos atuais, salvo decisão formal separada com
  justificativa, impacto, aprovação e nova evidência;
- verificar limites de tempo e memória dos workloads sem convertê-los em
  exceções silenciosas.

### 5.2 Performance mensurável

O relatório deverá medir, no hardware e ambiente oficial registrados:

- abertura/carregamento de cena;
- validação de documento e referências de assets;
- save atômico, criação/uso de recovery e reload;
- operações de edição representativas já existentes;
- preview e atualização visual da cena;
- exportação genérica, Godot e Unity quando aplicável;
- consumo inicial, pico e final de memória;
- média, p50, p95, p99, pior caso e quantidade de erros;
- repetição suficiente para demonstrar determinismo e ausência de crescimento
  contínuo de memória em sessão prolongada.

As metas normativas já definidas para renderização/runtime permanecem
obrigatórias: 60 FPS na cena 2.5D de referência em 1080p e p95 de frame
menor ou igual a 16,7 ms, quando o workload de runtime for aplicável. Para
operações de editor, load/save/recovery/export, P2D-05 deverá apresentar
proposta de orçamento por operação, workload e hardware para aceite explícito;
nenhum número novo será tratado como aprovado por inferência ou por média
isolada.

### 5.3 Formatos e compatibilidade

- declarar formatos de entrada, saída e versões efetivamente suportados;
- rejeitar versão, alvo ou campo incompatível de maneira explícita;
- impedir migração silenciosa; conversão V1 para V2 deve continuar explícita;
- preservar bytes canônicos, ordenação, hashes e identidade do gerador;
- verificar que source_path local/provenance não atravesse a fronteira
  portátil do export;
- manter mapeamento de coordenadas, orientação, escala, pivot e flip
  verificáveis;
- testar round-trip de arquivo e, quando o exportador for afetado, round-trip
  real nos destinos instalados, sem chamar JSON de objeto renderizado.

### 5.4 Erros e recuperação

- definir uma taxonomia estável de falhas ou outra forma equivalente de
  identificação reproduzível;
- tornar mensagens objetivas e acionáveis no fluxo Qt real;
- diferenciar formato inválido, limite excedido, asset ausente, hash alterado,
  destino incompatível, falha de I/O e recovery disponível;
- garantir que erro não produza sucesso, mutação parcial, export incompleto ou
  perda do último estado válido;
- preservar recovery válido quando a entrada corrente estiver corrompida;
- provar cancelamento, retry seguro e comportamento após falha sem depender de
  estado residual de execução anterior;
- registrar falhas nos artefatos sem caminhos pessoais, segredos ou
  credenciais.

## 6. Fora do escopo desta decisão

Não fazem parte de P2D-05:

- criar qualquer ferramenta de tilemap ou autotiling;
- criar colisão própria de cenário, NavMesh ou novas entidades;
- criar componentes, prefabs, hierarquia além da existente ou runtime de jogo;
- criar iluminação, sombras, partículas, pós-processamento, shaders editáveis
  ou VFX;
- implementar vetorização de imagem ou transformar contornos em objetos novos;
- declarar suporte 2.5D/3D além do que já foi comprovado;
- redesenhar baselines G/V/B, C3, auditores ou tolerâncias;
- alterar o editor legado para suprir lacunas do editor profissional;
- publicar, taguear, fazer merge adicional ou gerar release sem autorização
  específica para o ciclo correspondente.

Correções de UX de erro são permitidas somente quando forem necessárias para
completar o diagnóstico desta etapa; não podem introduzir funcionalidades de
outro workstream nem alterar geometria, comportamento ou semântica fora da
fronteira aprovada.

## 7. Invariantes obrigatórios

1. C3, baselines aprovadas, contratos históricos, evidências seladas,
   tolerâncias, auditores e o significado dos eixos G/V/B permanecem
   imutáveis.
2. Nenhum limite poderá ser aumentado, ignorado ou relaxado para transformar
   um caso inválido em PASS.
3. A rejeição deve ocorrer antes da mutação observável sempre que a
   pré-condição puder ser verificada antes da operação.
4. Falha de leitura, validação, save, recovery ou export deve preservar o
   último estado válido e nunca anunciar sucesso sem efeito confirmado.
5. Persistência e exportação devem continuar determinísticos, canônicos,
   hash-bound e atômicos.
6. Formatos e destinos não suportados devem ser rejeitados ou declarados como
   fallback explícito; nunca podem ser promovidos por aparência.
7. Logs, mensagens, manifests e capturas não podem conter caminhos pessoais,
   credenciais, tokens ou segredos.
8. O resultado deve ser reprodutível no Python 3.11 da .venv e nas
   plataformas cobertas pelo CI, sem depender de cache local.
9. Nenhuma mudança nesta etapa pode corromper P2D-01, P2D-02, P2D-03,
   P2D-04, o editor legado ou as linhas independentes reservadas.
10. Cada métrica deve identificar commit, ambiente, workload, unidades,
    repetições, entradas, hashes e limitações; média isolada não é aceite.

## 8. Testes obrigatórios

### 8.1 Unitários e de contrato

- limites exatamente no valor permitido e no primeiro valor excedente;
- tamanho de arquivo, listas, pontos, grupos, assets, imagem, atlas e
  exportação;
- JSON com BOM, UTF-8 inválido, chaves duplicadas, NaN/Infinity, raiz errada,
  schema desconhecido, versão desconhecida e campos incompatíveis;
- hash ausente, alterado, asset ausente, caminho absoluto e escape de pasta;
- bytes canônicos e hash estável em múltiplas execuções;
- erro de destino, falha de replace e rollback atômico;
- recovery válido, recovery inválido, corrente corrompida e preservação do
  último documento válido;
- ausência de vazamento de caminhos pessoais, segredos e credenciais.

### 8.2 Integração e fluxo real do usuário

O fluxo deverá ser executado como usuário comum faria:

1. abrir um projeto e abrir o editor profissional;
2. carregar ou criar o documento profissional suportado;
3. editar e salvar uma cena válida;
4. provocar uma falha de formato, limite, asset ou destino;
5. observar uma mensagem objetiva com ação recomendada;
6. confirmar que a cena anterior não foi perdida nem parcialmente alterada;
7. usar recovery quando disponível;
8. repetir load/save/export e verificar bytes, estado e mensagens;
9. validar que cancelamento e retry não criam corrupção nem entradas
   duplicadas de histórico.

### 8.3 Performance, stress e regressão

- workloads pequeno, de referência e de limite, todos descritos e hashados;
- repetição e sessão prolongada para observar memória e determinismo;
- full suite no commit candidato;
- cobertura de linhas e branches segundo a política vigente;
- Linux e Windows no CI obrigatório;
- captura Windows/offscreen e auditoria visual quando houver alteração de UI;
- validação Godot/Unity real quando formato, exportador ou materialização for
  alterado; caso contrário, declarar formalmente a não aplicabilidade sem
  reutilizar silenciosamente uma prova de outro commit.

## 9. Evidências obrigatórias

O pacote P2D-05 deverá conter:

- decisão aprovada e auditoria de entrada;
- matriz de limites com valores, unidades e provas de fronteira;
- matriz de formatos, versões, destinos e comportamento de incompatibilidade;
- catálogo de erros e mensagens do fluxo real;
- logs brutos e relatório de performance com p50/p95/p99, pior caso,
  memória e workload;
- testes unitários, negativos, integração, regressão e stress;
- captura e auditoria visual quando aplicável;
- manifest com bytes e SHA-256 de todos os artefatos;
- verificação de privacidade e ausência de conteúdo local sensível;
- build identificada por produto, fase, finalidade, commit, OS, backend,
  schema e data;
- revisão humana e decisão PRECOMMIT/POSTCOMMIT;
- requalificação pós-merge, se o ciclo remoto for posteriormente autorizado.

Nenhum log ou relatório poderá copiar números, horários, hashes ou decisões de
uma execução anterior. Os valores deverão vir da execução corrente.

## 10. Ordem de execução e gates

Após o aceite desta decisão, a ordem obrigatória será:

1. criar branch de trabalho a partir de f55b07b8 sem alterar main;
2. provar branch, HEAD, tracked boundary e baseline de entrada;
3. implementar somente o contrato P2D-05;
4. executar testes unitários, negativos, integração, regressão e stress;
5. executar a matriz de performance com ambiente e workload registrados;
6. executar fluxo real Qt, captura/auditoria e validação de privacidade;
7. validar destinos reais quando aplicável;
8. executar lint, formatação, imports, type-check, cobertura e manifesto;
9. revisar diff e solicitar P2D-05 PRECOMMIT ACCEPT;
10. somente após esse aceite, fazer commit do lote exato;
11. requalificar o commit, publicar PR e aguardar todos os checks protegidos;
12. somente com checks verdes e autorização explícita, realizar merge normal;
13. requalificar main, atualizar evidências e produzir seal;
14. solicitar aceite humano final e registrar P2D-05 ACCEPTED / CLOSED.

Se qualquer gate falhar, a etapa permanece OPEN, BLOCKED ou REJECTED, conforme a
causa. Não haverá commit parcial apresentado como entrega, aceite por
intenção, aprovação por ausência de erro aparente ou avanço automático para
outro workstream.

## 11. Fronteira protegida

No mínimo, qualquer implementação deverá declarar antes do código:

- arquivos de produção permitidos;
- arquivos de teste permitidos;
- scripts e documentos de evidência permitidos;
- arquivos explicitamente proibidos;
- símbolos, formatos, schemas e limites que não podem mudar;
- impacto G/V/B esperado;
- rollback técnico para o merge f55b07b8;
- condição de não aplicabilidade de engine/captura, se houver.

Alteração fora dessa fronteira interrompe o lote e exige nova decisão formal.

## 12. Critérios de aceite

P2D-05 só poderá ser marcada ACCEPTED / CLOSED se todos os itens abaixo forem
comprovados no mesmo encadeamento de commits:

- matriz de limites completa, com fronteiras positivas e negativas;
- formatos e versões documentados e testados sem migração silenciosa;
- erros acionáveis, seguros e verificáveis no fluxo real;
- ausência de perda, corrupção ou mutação parcial em falhas;
- performance medida com percentis, pior caso, memória e workload;
- metas aplicáveis aprovadas e atendidas, ou bloqueio explícito para cada
  meta não atendida;
- determinismo de bytes e resultados onde o contrato exige;
- full suite, qualidade estática, cobertura e CI Linux/Windows aprovados;
- privacidade e integridade de evidências aprovadas;
- build e revisão humana concluídas quando aplicáveis;
- commit, PR, merge e requalificação pós-merge concluídos conforme autorização;
- documentação viva atualizada sem reescrever snapshots históricos;
- nenhuma regressão, pendência crítica/alta ou capacidade prometida sem prova.

Um único item ausente mantém P2D-05 aberta e impede P2D-06, P2D-07 e qualquer
workstream dependente de declarar a fundação robusta.

## 13. Rollback e publicação

O rollback de código da implementação P2D-05 é o merge commit
f55b07b85ef2cf65160f2c10ffac5e63b45732ac. O rollback não autoriza apagar
artefatos, reescrever históricos, remover untracked, alterar C3 ou desfazer
evidência aceita.

Esta abertura não autoriza push, tag, merge ou release. Esses atos somente
serão executados em ciclo remoto separado, depois do PRECOMMIT ACCEPT, dos
checks protegidos e de autorização explícita do proprietário.

## 14. Decisão solicitada ao proprietário

Solicita-se aceite explícito deste contrato com a frase:

P2D-05 ACEITO — contrato de performance, limites, formatos e erros

O aceite autoriza a implementação controlada exclusivamente dentro desta
fronteira. Ele não aceita a implementação, não aceita a build, não aprova
metas de performance ainda não medidas, não declara o editor completo e não
autoriza publicação remota.

Até esse aceite, o estado formal permanece:

P2D-05 OPEN — decisão/contrato; implementação e qualificação pendentes.
