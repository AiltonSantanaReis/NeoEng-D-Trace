# NeoEng-D-Trace — Contrato global de apresentação de erros

**ID:** `C-GLOBAL-ERROR-PRESENTATION-P2D05-2026-09-04`
**Status:** `ACTIVE / APPROVED FOR IMPLEMENTATION`
**Data:** 2026-09-04 (UTC-03)
**Escopo:** apresentação de falhas na UI Qt e nos fluxos acessíveis ao usuário
**Base auditada:** `9adb66a5ab9cfaabc1703d4b9b225b141473ec52`
**Branch de trabalho:** `Ailton/error-presentation-contract-20260904`

## 1. Finalidade

Este contrato define como falhas internas devem ser classificadas, traduzidas
e apresentadas ao usuário. Ele transforma a taxonomia e a fronteira de
redaction já existentes em `src/persistence/p2d05_errors.py` em uma regra
global de apresentação, sem alterar a semântica das operações.

O contrato não declara a UI atual conforme. A implementação atual permanece
`PARCIAL` até a migração dos pontos existentes, os testes negativos e a revisão
visual exigida serem concluídos.

## 2. Autoridade e dependências

Este documento é subordinado a:

1. `docs/POLITICA_QUALIDADE_E_EVIDENCIAS.md`;
2. `docs/GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md`;
3. `docs/PLANO_INTERFACE_MODERNA_PROFISSIONAL_2026-08-21.md`;
4. `docs/DECISAO_P2D_05_PERFORMANCE_LIMITES_FORMATOS_ERROS_2026-08-30.md`;
5. `src/persistence/p2d05_errors.py`.

Não substitui políticas, não reescreve snapshots históricos e não altera
requisitos, thresholds, formatos persistidos, matemática geométrica, CI ou
contratos de runtime. Qualquer mudança nessas fronteiras exige controle de
mudança separado.

## 3. Invariantes obrigatórios

Toda falha apresentada ao usuário deve:

- identificar o que ocorreu em linguagem compreensível;
- indicar uma ação objetiva, quando houver ação possível;
- declarar o estado preservado ou a ausência dele;
- possuir código estável e reproduzível;
- usar detalhe técnico redigido, quando o detalhe ajudar o diagnóstico;
- registrar a exceção completa no log interno, quando aplicável;
- evitar caminhos pessoais, credenciais, tokens, segredos e traceback na UI;
- rejeitar antes da mutação observável quando a pré-condição for verificável;
- nunca anunciar sucesso sem confirmação do efeito esperado;
- nunca ser suprimida silenciosamente quando o resultado puder estar
  incorreto, incompleto ou ambíguo.

`str(exc)`, `str(e)` e mensagens retornadas diretamente por uma exceção não
podem ser usadas como texto final de UI. A apresentação deve passar pela
classificação e por `redact_p2d05_detail` ou por mecanismo equivalente
aprovado.

## 4. Modelo canônico

O adaptador global deve produzir um descritor equivalente a:

| Campo | Obrigatório | Regra |
|---|---:|---|
| `code` | Sim | Código P2D05 estável ou código aprovado para erro fora do P2D-05. |
| `severity` | Sim | `INFO`, `WARNING`, `ERROR` ou `CRITICAL`. |
| `blocking` | Sim | Indica se o fluxo atual não pode continuar. |
| `headline` | Sim | Curto, localizado e sem detalhe de implementação. |
| `message` | Sim | Explica o ocorrido para o usuário. |
| `action` | Sim | Próxima ação objetiva ou declaração de que não há recuperação local. |
| `preserved_state` | Sim | Estado anterior, arquivo, preview e histórico preservados ou não. |
| `channel` | Sim | Canal selecionado pela matriz da seção 5. |
| `safe_detail` | Não | Detalhe técnico curto, redigido e opcional. |
| `retryable` | Sim | Define se repetir a operação é seguro. |
| `focus_target` | Quando aplicável | Controle ou item que deve receber foco. |
| `internal_context` | Não exibido | Contexto completo para log interno, incluindo traceback quando seguro. |

O descritor deve ser independente da UI. Widgets e diálogos não devem
classificar exceções individualmente nem decidir sozinhos o texto de erro.

## 5. Matriz de roteamento

| Situação | Canal padrão | Comportamento exigido |
|---|---|---|
| Campo ou entrada inválida | `INLINE` | Mostrar junto ao campo, explicar a correção e focar o controle quando possível. |
| Seleção ausente ou pré-condição simples | `INLINE` ou `STATUS` | Informar o que falta e, quando possível, desabilitar a ação incompatível. |
| Rejeição recuperável de edição | `STATUS` | Não interromper cada gesto com modal; preservar modelo, preview e histórico. Disponibilizar detalhes se necessário. |
| Falha de salvar, carregar ou exportar | `MODAL` ou painel persistente | Informar impacto, preservar o último estado válido e oferecer `Tentar novamente`, `Salvar como`, `Recuperar` ou ação equivalente. |
| Falha em segundo plano/autosave | `STATUS` persistente | Não abrir modal repetitivo; manter indicação até resolução e fornecer recuperação/detalhes. |
| Decisão destrutiva ou recuperação ambígua | `MODAL` | Exigir decisão explícita e explicar consequências antes de continuar. |
| Falha inesperada que impede continuidade | `MODAL` | Explicar que a operação falhou, preservar o estado possível e oferecer detalhes seguros/cópia do diagnóstico. |
| Confirmação de sucesso | `STATUS` ou `TOAST` | Só depois da pós-condição ser verificada; não usar modal para sucesso rotineiro. |

### 5.1 Modal

É reservado para bloqueio, decisão, perda potencial, recuperação ou falha que
exija atenção imediata. Deve ter título localizado, mensagem acionável,
estado preservado, foco inicial previsível e botões com nomes acessíveis.

### 5.2 Toast e status

São adequados para informação não bloqueante e para operações que continuam.
Um erro que exige ação não pode desaparecer sem alternativa; nesse caso, a
mensagem deve permanecer na `QStatusBar` ou em banner até ser resolvida,
descartada explicitamente ou substituída por estado posterior comprovado.

### 5.3 Inline

É o canal preferencial para validação de formulário, entrada inválida,
seleção ausente e pré-condições locais. A mensagem não deve depender somente
de cor e não deve obrigar o usuário a procurar outro diálogo para entender o
problema.

### 5.4 Detalhes técnicos

O usuário deve poder abrir `Detalhes`, copiar um diagnóstico seguro e obter o
código do erro. O detalhe deve ser redigido, curto na apresentação e separado
da mensagem principal. O log interno pode conter o traceback necessário para
diagnóstico, obedecendo às regras de privacidade e evidência.

## 6. Taxonomia e exemplos

O adaptador deve reutilizar, quando aplicável, os códigos existentes:

`P2D05-FORMAT`, `P2D05-LIMIT`, `P2D05-ASSET`, `P2D05-TARGET`, `P2D05-READ`,
`P2D05-WRITE`, `P2D05-RECOVERY`, `P2D05-LOCK`, `P2D05-REFERENCE`,
`P2D05-PREVIEW` e `P2D05-OPERATION`.

Exemplo de mensagem adequada:

> Não foi possível salvar o projeto [P2D05-WRITE]. O último arquivo válido foi
> preservado. Tente novamente ou escolha outro destino. Detalhe: destino
> indisponível.

Exemplo de mensagem inadequada:

> Error: [traceback ou `str(exc)` bruto]

Quando não houver mapeamento específico, deve ser usado o fallback seguro de
operação, com ação e estado preservado explícitos. O fallback não pode ocultar
a falha nem inventar uma causa mais específica.

## 7. Migração obrigatória

A implementação deve ser feita em lotes pequenos, preservando o
comportamento do domínio e criando testes antes de declarar cada lote pronto.
Prioridade:

1. Caneta, edição de polígonos, gizmo e comandos de edição;
2. abrir, salvar, recovery e exportação;
3. painéis laterais, layers, groups e collision;
4. detecção, máscara e preview;
5. autosave e demais operações em segundo plano;
6. localização, acessibilidade, foco, teclado e detalhes técnicos.

Os caminhos silenciosos devem ser convertidos em feedback apropriado. Uma
ação indisponível deve ser desabilitada ou explicar claramente a pré-condição;
não deve simplesmente retornar sem informar o usuário.

## 8. Critérios de aceitação

Este contrato está ativo para orientar a implementação. A implementação só poderá ser declarada conforme quando houver evidência de que:

- cada ponto de apresentação de erro foi inventariado;
- nenhuma exceção técnica bruta chega à UI;
- nenhum caminho relevante captura e suprime falha silenciosamente;
- cada falha possui código, ação, estado preservado e canal justificável;
- os testes cobrem sucesso, entrada inválida, limites, seleção ausente,
  cancelamento, retry, falha de recurso e preservação de estado;
- mouse e teclado foram testados separadamente;
- foco, acessibilidade, localização, contraste e quebra de texto foram
  verificados;
- o fluxo real foi exercitado em Qt, sem depender apenas de mocks de diálogo;
- detalhes e logs foram verificados quanto a redaction;
- os gates completos, evidências, hashes, commit exato e CI aplicável foram
  executados conforme as políticas do projeto.

Até esses critérios serem comprovados, o contrato é apenas uma proposta
normativa e a conformidade global da UI permanece `PARCIAL`.

## 9. Registro de aprovação

O proprietário do projeto aprovou formalmente o conteúdo deste contrato no
commit `333c1e8` em 2026-09-04 (UTC-03). Esta aprovação torna o contrato ativo
para orientar a implementação; não declara a implementação funcional da UI
concluída nem autoriza push, merge, tag ou release por si só.

| Campo | Valor |
|---|---|
| Revisor humano | Proprietário do projeto |
| Data da aprovação | 2026-09-04 (UTC-03) |
| Decisão | `APPROVED FOR IMPLEMENTATION` |
| Conteúdo aprovado | commit `333c1e8` |
| Observações | A conformidade global da UI permanece `PARCIAL` até a migração e os gates da seção 8. |

Este registro é versionado neste commit de aprovação. A implementação
funcional e a atualização dos documentos vivos continuam dependendo dos
critérios da seção 8 e dos gates correspondentes.
