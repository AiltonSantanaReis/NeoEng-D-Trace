# Baseline final e compatibilidade evolutiva do produto

Status: contrato de auditoria aprovado para implementação  
Data: 2026-08-24  
Escopo inicial de execução: etapas 0–9; compatibilidade projetada: etapas futuras até a definição formal do produto final.

## 1. Objetivo

Esta especificação define como a baseline do NeoEng-D-Trace deve ser construída, versionada, auditada e utilizada. A baseline não é uma imagem congelada da interface de uma etapa intermediária. Ela é o contrato verificável do produto final, complementado por snapshots incrementais que registram a evolução sem limitar as etapas posteriores.

Nenhum código de produção deve ser alterado para satisfazer um auditor histórico. Auditores, baselines, fixtures e artefatos devem se adaptar ao contrato aprovado do produto.

## 2. Princípio normativo

Uma mudança só pode ser aprovada quando forem verdadeiras simultaneamente as condições abaixo:

1. preserva os invariantes já aprovados;
2. atende o contrato da etapa corrente;
3. não reduz a capacidade de extensão exigida pelo produto final;
4. possui evidência reproduzível, identificada por commit, ambiente, comando, data e hash;
5. quando altera comportamento ou geometria, possui classificação explícita e justificativa.

Ausência de evidência não significa aprovação. Diferença visual não significa automaticamente regressão.

## 3. Camadas da baseline

### 3.1 Baseline final de produto — `FINAL_TARGET`

É a referência principal. Deve conter apenas requisitos aprovados ou explicitamente marcados como hipótese. É composta por:

- tokens de cor, tipografia, espaçamento, raio, borda e estados;
- contraste mínimo, foco visível, navegação por teclado e textos acessíveis;
- contratos de comandos, atalhos, identificadores e estados de ferramenta;
- capacidade de expansão de toolbar, rail, painéis, inspetor, overlays e viewport;
- limites responsivos e de DPI, incluindo 1280x720, 1366x768, 1920x1080 e 100/125/150/200%;
- contratos de persistência, versionamento, migração e exportação;
- pontos de extensão para câmera, parallax, sockets, máscaras, iluminação, partículas e demais recursos futuros;
- invariantes de isolamento entre editor principal, editor de cenários e modos de preview.

A baseline final não deve fixar coordenadas de widgets quando o requisito real é capacidade, hierarquia, legibilidade, alinhamento ou ausência de clipping. Medidas exatas só são normativas quando aprovadas como requisito.

### 3.2 Baselines incrementais — `STAGE_N_SNAPSHOT`

Cada etapa recebe um snapshot imutável do estado aprovado no encerramento da etapa. O snapshot serve para detectar regressões introduzidas pela etapa seguinte; ele não substitui nem altera `FINAL_TARGET`.

Cada snapshot deve registrar:

- commit de origem;
- versão do contrato final usada;
- matriz de resoluções e DPI;
- manifest de elementos, comandos e estados;
- hashes dos artefatos;
- diferenças aceitas em relação ao snapshot anterior;
- limitações conhecidas e sua etapa de resolução.

### 3.3 Baseline histórica — `HISTORICAL_REFERENCE`

Referências antigas permanecem preservadas. Seu resultado deve ser exibido separadamente como comparação histórica e nunca pode bloquear uma implementação apenas porque a arquitetura visual evoluiu. Ela bloqueia somente quando a diferença viola um invariante ainda vigente ou quando não possui classificação aprovada.

## 4. Classificação obrigatória de diferenças

Toda diferença encontrada deve receber exatamente uma classificação principal:

- `INVARIANT_REGRESSION`: quebra de requisito vigente, como clipping, sobreposição impeditiva, perda de foco, contraste insuficiente, comando quebrado, perda de estado ou corrupção de dados;
- `EXPECTED_EVOLUTION`: alteração prevista pelo contrato da etapa ou aprovada no registro de evolução;
- `FORWARD_COMPATIBILITY_RISK`: funciona hoje, mas cria limite ou acoplamento que impede etapa futura;
- `UNCLASSIFIED_CHANGE`: diferença real sem justificativa suficiente; bloqueia a aprovação;
- `HISTORICAL_ONLY`: diferença preservada para rastreabilidade, sem violação de contrato vigente.

Somente `INVARIANT_REGRESSION`, `FORWARD_COMPATIBILITY_RISK` e `UNCLASSIFIED_CHANGE` bloqueiam o gate. `EXPECTED_EVOLUTION` exige evidência e justificativa; não é uma forma de ignorar diferença.

## 5. Gate de compatibilidade futura

Antes de fechar qualquer etapa, a auditoria deve verificar:

- inexistência de limites arbitrários para novas ferramentas, painéis, seções do inspetor ou overlays;
- ausência de dependência em coordenadas frágeis, textos literais ou índices posicionais quando identificadores estáveis são necessários;
- extensibilidade de comandos, atalhos, estados, schemas e exportadores;
- preservação de dados desconhecidos durante carga, edição e salvamento quando o contrato exigir compatibilidade;
- versionamento e migração explícitos para mudanças de schema;
- preservação do isolamento entre modos de edição, preview e runtime;
- comportamento válido nas resoluções e DPIs contratados;
- ausência de regressão em acessibilidade, teclado, foco, contraste e feedback de erro;
- capacidade de adicionar os recursos futuros previstos sem alterar invariantes fundamentais.

Uma hipótese futura não pode ser convertida em requisito silenciosamente. Se um requisito novo surgir, ele deve entrar por alteração versionada do contrato final, com impacto, evidência e revisão.

## 6. Aplicação às etapas 0–9

As etapas 0–9 serão auditadas em três dimensões independentes:

1. contrato da etapa;
2. não-regressão dos snapshots anteriores;
3. compatibilidade com `FINAL_TARGET`.

O aceite de uma etapa só ocorre quando as três dimensões estiverem aprovadas ou quando uma exceção formal estiver registrada. A execução de testes unitários, por si só, não substitui artefatos funcionais de UI.

Os artefatos obrigatórios são:

- relatório JSON determinístico;
- manifest de ações e estados realmente executados;
- capturas PNG quando houver requisito visual;
- hashes SHA-256;
- log completo do comando e ambiente;
- resultado positivo e negativo quando o contrato exigir rejeição observável;
- referência ao teste, commit e baseline comparada.

## 7. Etapa 1

A etapa 1 deve combinar os dois auditores:

- o auditor histórico continua reportando diferenças contra a referência original;
- o auditor de contrato valida tokens, paleta, contraste e todos os estados interativos atuais;
- mudanças de geometria são classificadas, não apagadas;
- diferenças esperadas precisam de registro de evolução;
- clipping, sobreposição impeditiva, perda de acessibilidade ou contraste continuam sendo regressões mesmo quando presentes em uma evolução visual.

O resultado final da etapa 1 deve separar claramente `historical_result`, `current_contract_result` e `consolidated_decision`.

## 8. Etapa 5

A etapa 5 deve possuir duas trilhas de evidência:

### Viewport/HUD

Lit, X-Ray, zoom, pan, fit, escala 1:1, coordenadas do cursor, grid, snap, gizmo, seleção, estado do viewport, status e comportamento em todas as resoluções e DPIs.

### Mask Viewer

Abertura, carregamento, modos Original/Sobel/Canny/Laplacian, reset, preenchimento, centralização, interação real de mouse/teclado, estados inválidos, foco, clipping e feedback de erro.

Cada trilha deve produzir capturas por estado, relatório de ações, resultado negativo e hashes próprios. Nenhum resultado de Mask Viewer pode ser inferido a partir de uma captura genérica do viewport.

## 9. Política de aprovação

Uma etapa pode ser marcada como `AUTOMATED_PASS` quando os testes e artefatos automatizados forem aprovados. Só pode ser marcada como `FORMALLY_COMPLETE` quando também houver revisão humana, CI do commit exato e todos os riscos classificados como resolvidos ou formalmente aceitos.

Não é permitido transformar `PARTIAL`, `HUMAN_PENDING`, `UNCLASSIFIED_CHANGE` ou falha de compatibilidade em aprovação por meio de renomeação de arquivo, filtro de relatório ou exclusão de evidência.

## 10. Ordem de implementação

1. versionar este contrato e seu schema de resultados;
2. criar o manifest `FINAL_TARGET` sem inventar requisitos ainda não aprovados;
3. adaptar os auditores para emitirem as classificações acima;
4. preservar os baselines históricos e criar snapshots incrementais;
5. implementar a matriz funcional completa das etapas 0–9, com foco especial em cenário, inspetor, viewport, Mask Viewer, câmera, parallax, sockets e gizmo;
6. executar a matriz em ambiente limpo e gerar os artefatos com hashes;
7. analisar regressões, evoluções e riscos futuros separadamente;
8. somente após isso executar revisão humana e decidir o encerramento formal.
