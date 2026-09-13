# Auditoria de fechamento das pendências pós-E13

**ID:** `AUD-POST-E13-CLOSURE-AUDIT-20260913`
**Status do registro:** `IN_PROGRESS / ONE_OWNER_DECISION_REMAINING`
**Data:** 2026-09-13
**HEAD de entrada auditado:** `1b7fedd0fe4e898c3b240c5767688e142ecd7e49`
**Branch:** `Ailton/audit-post-e13-scenario-editor-20260912`
**Governança:** `docs/GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md`
**SHA-256 da governança:** `D933DB005B7110C391CF776CDA3014CE348D61A91A5E9902AEEA619185EC3EA0`

## Objetivo e regra de leitura

Esta auditoria consolida a meta de fechar as pendências pós-E13 sem regressões.
Ela distingue resultado técnico, limitação de instrumentação, falha observada,
skip protegido e bloqueio ambiental. Nenhum estado histórico é reclassificado
retroativamente e nenhum `SKIP`, `FAIL` ou `BLOCKED` é convertido em `PASS` por
conveniência documental.

O E13 permanece fechado e congelado como histórico. O escopo corrente é apenas
o lote pós-E13 no checkout indicado acima; o editor de cenário canônico e seus
artefatos funcionais foram preservados.

## Matriz de fechamento

| Frente | Estado corrente | Evidência autorizada | Conclusão |
|---|---|---|---|
| Suíte oficial sem filtros | `PASS` | `artifacts/audit-post-e13-official-suite-safe-host-20260913-r12/official-pytest.log` — SHA-256 `171F156EDDA800951356FB4244459CAE08CE20D18B5E1E3CA870399CE4B1A0A3` | `2634 passed`, `2 skipped`, `0 failed`, `0 warnings`; o resultado é a requalificação corrente do checkout |
| Symlink no host | `SKIP_CONTROLLED_ONLY` | Os dois skips protegidos da suíte oficial; a barreira impede a operação antes do filesystem | Não executar nativamente; o skip é intencional e não é falha mascarada |
| Symlink em ambiente controlado | `PASS_SANDBOX` | `docs/evidence/EVD_POST_E13_SYMLINK_SANDBOX_DEFINITIVO_20260913.md` e relatório/JUnit hashados | `31/31` passaram, sem skip, falha ou erro; não repetir sem mudança relevante |
| Responsividade estrutural em escala | `FAIL / APPROVED_BY_OWNER` | `artifacts/audit-post-e13-performance-20260913-r9/o2-after-isolation-cache-fix-clean.json` — SHA-256 `3F7E6DEE0EC8088C69E452EC089B616AA59BCD0A7DDD7A30A36C3504A57531A8` e decisão formal do limite | p95 residual de `249,28–398,73 ms` em 512 objetos únicos; o limite foi aceito formalmente, sem reduzir threshold e sem declarar 60 FPS |
| Soak de memória | `PASS` | `artifacts/audit-post-e13-performance-soak-controlled-20260913-r2/report.json` — SHA-256 `662334FD286684FEE5C808EC896159E85AC02938DEAC40F4AA0EA50166AF9DD3` | `26/26` workloads, `250` ciclos por carga, zero erro e zero falha de determinismo; evidência de estabilidade do ciclo, não prova universal de ausência de leak |
| Workload CUDA dedicado | `PASS_CONTROLLED_GPU_WORKLOAD` | `artifacts/audit-post-e13-performance-gpu-controlled-20260913-r1/report.json` — SHA-256 `E0B368982ED14A69A21410B1480E31799552857AB6CE14590CB96E5F1B98423E`; runner SHA-256 `ADC6EAB45C1AD9C117FA58A4D96A56E4D2187B333C5E580C0EEF922A203277C5` | Driver real, RTX 3070 Ti, 36.408 operações/20 s, 38 amostras, até 91% de utilização, zero erros |
| GPU/FPS do viewport QGraphicsView | `NOT_APPLICABLE` | `docs/evidence/EVD_POST_E13_SOAK_MEMORIA_GPU_CONTROLADO_20260913.md` | O caminho qualificado usa `offscreen/software` e não expõe contador de frames/GPU; o workload CUDA não é promovido a equivalência de renderer |
| CuPy | `PASS / NOT_APPLICABLE` para adoção oficial | `docs/evidence/ADR_POST_E13_CUPY_AVALIACAO_20260913.md` e diagnóstico hashado | Suporte opcional e fallback CPU permanecem; não há base causal para incluir CuPy na dependência ou na build portátil |
| Fluxo nativo do editor canônico e revisão humana | `PASS` no escopo qualificado | `artifacts/audit-post-e13-binary-performance-20260913-r4/actions.json` — SHA-256 `CBBE3711D4D24E336B6E349E7D659C502C9F640C24ED40207FF81FA98387D3AA` e decisão de revisão aprovada | Capturas reais, fluxo nativo e aprovação humana estão registrados; isso não encerra o gate externo do Unity |
| Arquivo legado e higiene | `PASS` | `docs/evidence/CHG_POST_E13_ARQUIVO_LEGADO_ARTEFATOS_20260913.md` e manifesto `archive/legacy/artifacts/post-e13-historical-20260913/archive-manifest.json` — SHA-256 `2E89672381BEF30BFAFD5E773D41FF0BDBDF742F99379B23A9A800CA5529F666` | Movimento reversível; `0` exclusões permanentes; históricos preservados e separados da base ativa |
| Unity real em Windows Sandbox | `PASS` de inicialização / `BLOCKED` de licensing e shutdown limpo | r12 em `docs/evidence/EVD_POST_E13_UNITY_CONTROLADO_SANDBOX_20260913.md`; resultado SHA-256 `E95995806B98A263F44C43FE487FF3615447B88B24DD27CEA95933A6079BC960` | Unity iniciou dentro da sandbox e alcançou o LicensingClient, mas encontrou zero entitlements aplicáveis e saiu com `198`; pacote e shutdown limpo não foram alcançados |

## Falhas, warnings e skips preservados

- A suíte corrente terminou sem warnings e sem failures. Os dois skips são
  exclusivamente os testes de symlink protegidos no host e têm cobertura
  definitiva no Sandbox.
- A falha transitória `WinError 5` em `os.replace` e a falha inicial de higiene
  por caminhos locais estão documentadas em
  `docs/evidence/EVD_POST_E13_UNITY_CONTROLADO_SANDBOX_20260913.md`; os reruns
  isolados e a suíte posterior comprovam a classificação, sem apagar o evento.
- O warning de empacotamento `tzdata` e a correção subsequente permanecem
  hashados nos registros próprios.
- A divergência de metadado de rede do Unity r11 tem estado `FAIL` no harness e
  foi preservada. O r12 corrigiu o metadado e é a execução coerente usada para
  a conclusão de rede habilitada.
- Os warnings `SUCCEEDED(hr)` e `wmiOpened`, o `Code 10`, o token ausente, o
  `Code 404`, os entitlements zerados e o retorno `198` do Unity permanecem no
  log sanitizado. Não foram substituídos por diagnósticos históricos positivos.

## Estado da única pendência dependente do proprietário

Todas as frentes seguras desta meta estão qualificadas, aceitas em escopo ou
explicitamente limitadas. Resta uma decisão externa única:

1. disponibilizar uma licença/ativação Unity válida para `6000.5.7f1`, ou uma
   fixture de entitlement própria e autorizada, dentro da sandbox descartável;
   então executar uma nova tentativa com o harness hashado para alcançar o
   método do pacote e observar o shutdown limpo; ou
2. aceitar que licensing, relatório do pacote e shutdown limpo do Unity
   permaneçam `BLOCKED` neste ciclo.

A opção 2 não é uma promoção técnica nem autorização de release. Sem uma
   dessas decisões, a meta permanece `IN_PROGRESS`; não há autorização para
   executar Unity, shutdown, encerramento forçado ou symlink nativamente neste
   host.

## Regras de reexecução

- Symlink: somente após mudança no contrato, guard, runner, dependência,
  digest ou evidência.
- Soak de memória/CUDA: somente após mudança no produtor, runner, contrato,
  imagem/digest, driver ou caminho real qualificado.
- CuPy: somente após mudança da integração X-Ray, contrato de desempenho,
  deployment/CI ou política de empacotamento.
- Unity: somente com licença/fixture válida diferente ou mudança material no
  engine, harness ou configuração de rede; a próxima execução deve permanecer
  dentro da sandbox descartável.

## Conclusão formal da auditoria

O resultado atual é tecnicamente consistente com o objetivo: o soak controlado,
symlink controlado, CuPy, integridade documental, preservação de artefatos e
fluxos do editor canônico foram fechados sem regressão observada. O limite de
responsividade foi aceito formalmente sem mascarar o `FAIL`. A única condição
que impede o encerramento integral da meta é o entitlement Unity externo; ela
está isolada, reproduzida em ambiente controlado e documentada como
`BLOCKED`, sem qualquer ação perigosa no host.
