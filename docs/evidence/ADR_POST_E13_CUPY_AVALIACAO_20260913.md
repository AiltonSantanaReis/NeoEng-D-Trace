# ADR — Avaliação do CuPy pós-E13

**ID:** `ADR-POST-E13-CUPY-EVALUATION-20260913`
**Status da avaliação:** `PASS`
**Status da adoção oficial:** `NOT_APPLICABLE` — não promover como dependência oficial nesta etapa
**Classificação do ensaio:** `DIAGNOSTIC_ONLY`
**Data:** 2026-09-13
**Commit do checkout auditado:** `72e60784d90030219a5300a4d6677726f5d0815e`
**Commit da fonte de produto:** `7f5c0477b3f4594928751aec6b97a4b1e9c0178b`

## Dependências e autoridade

- Governança: `docs/GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md`.
- Índice ativo: `docs/INDICE_DOCUMENTAL_ATIVO_CANONICO_2026-08-24.md`.
- Auditoria de desempenho: `docs/evidence/AUDITORIA_POST_E13_PERFORMANCE_BASELINE_20260913.md`.
- Artefato deste diagnóstico: `artifacts/audit-post-e13-cupy-diagnostic-20260913-r1/report.json`.
- Contrato de otimização vigente: `docs/DECISAO_P2D_05_O2_IMPLEMENTACAO_2026-08-30.md`.

Este ADR registra uma decisão técnica de dependência. Não altera requisito, schema,
baseline, threshold, runtime, empacotamento ou comportamento do produto.

## Pergunta avaliada

O projeto deve transformar CuPy em dependência oficial e incluí-lo na distribuição
portátil para acelerar o editor de cenário/parallax?

## Estado observado no código

O suporte já existente é opcional em `src/core/view_processor.py`:

- tenta importar `cupy` e `cupyx.scipy.ndimage`;
- ativa `HAS_GPU` somente quando há dispositivo CUDA acessível;
- executa a cadeia GPU de X-Ray quando disponível;
- registra erro e retorna para a cadeia OpenCV/CPU quando a aceleração falha;
- executa diretamente o fallback CPU quando CuPy não está disponível.

Os testes `tests/test_critical_numeric_coverage.py` cobrem o caminho CPU e o fallback
quando a rota GPU falha. A conversão para QImage também aceita a rota opcional sem
exigir que CuPy exista.

O uso no viewport de autoria de cenário é diferente: `src/ui/scene_authoring_viewport.py`
usa NumPy para gerar uma pequena imagem de pré-visualização de pós-processamento de
`3×3`. Não há evidência de que esse trabalho seja um consumidor relevante de GPU.

O manifesto `pyproject.toml` declara NumPy, OpenCV e as demais dependências
reprodutíveis, mas não declara CuPy. A especificação
`packaging/NeoEng-D-Trace.spec` exclui explicitamente `cupy` e `cupyx` para que a
build portátil não carregue runtimes CUDA capazes de conflitar com CRT/Qt do host.

## Execução controlada

Foi feita uma sondagem somente de leitura no ambiente virtual já existente. Não houve
instalação, alteração de dependência, alteração de driver, escrita no sistema,
shutdown, symlink nativo ou mudança de código.

Artefato hashado: `artifacts/audit-post-e13-cupy-diagnostic-20260913-r1/report.json`.

Ambiente observado:

| Item | Resultado |
|---|---|
| Python | `3.11.9` |
| Distribuição | `cupy-cuda12x 14.2.0`, somente no ambiente local |
| GPU | `NVIDIA GeForce RTX 3070 Ti` |
| Dispositivos CUDA | `1` |
| Compute capability | `8.6` |
| Runtime CUDA reportado | `12090` |
| Driver reportado | `13030` |

O probe in-process importou o módulo real do projeto com `HAS_GPU=true`, processou
um array determinístico `512×512×3` no modo X-Ray 1 e produziu saída `512×512×3`,
`uint8`, finita, sem exceção.

Foi executado um microbenchmark `DIAGNOSTIC_ONLY` com uma amostra determinística,
um warm-up e três medições por rota, incluindo as transferências CPU↔GPU da
implementação atual:

| Tamanho | CPU mediana | rota GPU selecionada | Relação CPU/GPU |
|---:|---:|---:|---:|
| `256²` | `0,314 ms` | `1,649 ms` | `0,190×` |
| `512²` | `0,696 ms` | `1,779 ms` | `0,391×` |
| `1024²` | `3,700 ms` | `3,644 ms` | `1,016×` |
| `2048²` | `14,639 ms` | `10,594 ms` | `1,382×` |

O resultado mostra benefício apenas no workload X-Ray maior medido, e não demonstra
benefício para o fluxo estrutural do editor. O benchmark oficial pós-E13 mediu como
hot spot a reconstrução/repintura estrutural de `QGraphicsScene` em cargas de
`512` objetos únicos; a própria auditoria registra que o contador GPU da janela não
foi medido e que o p95 residual chegou a `398,73 ms`. Portanto, promover CuPy agora
seria uma inferência causal sem evidência.

## Decisão

**Não tornar CuPy dependência oficial nem incluí-lo na build portátil agora.**

Manter o suporte opcional já implementado e o fallback CPU. Essa decisão preserva:

1. instalação e CI funcionais em máquinas sem CUDA;
2. reprodutibilidade da distribuição Windows portátil;
3. ausência de empacotamento de runtime CUDA e risco de conflito com Qt/CRT;
4. comportamento funcional do editor quando a aceleração não existe;
5. a possibilidade de reavaliar kernels específicos sem acoplar o produto a uma GPU.

O suporte opcional existente é considerado **comprovado apenas para o probe X-Ray
acima**. Isso não aprova aceleração do viewport/parallax, nem estabelece orçamento
de frames, memória ou equivalência visual GPU/CPU para o editor.

## Critérios para uma futura reavaliação

Uma nova proposta só deve ser aberta se todos estes pontos forem atendidos:

- um contrato de desempenho aprovado identificar um kernel CPU dominante e elegível;
- benchmark pareado GPU/CPU, com transferência incluída, demonstrar ganho material
  em tamanhos de uso real e em hardware suportado;
- houver comparação visual/determinística e fallback CPU testado;
- CI, instalação, licença, tamanho do pacote, drivers e suporte a máquinas sem GPU
  forem qualificados;
- o caminho do editor demonstrar que o kernel, e não a reconstrução Qt, é a causa;
- novo ADR, novos artefatos hashados, build e suíte oficial forem produzidos.

Até que isso ocorra, não reexecutar este diagnóstico por alterações somente de UI,
localização, documentação ou assets. Reexecutar apenas quando mudar a integração
CuPy/X-Ray, o contrato de desempenho, a matriz de deployment/CI ou a política de
empacotamento.

## Limitações e pendências preservadas

- A residual responsividade estrutural, a memória longa e a medição GPU/janela
  continuam com os estados registrados na auditoria de desempenho; este ADR não os
  reclassifica.
- A presença do pacote no ambiente virtual local não é uma decisão de dependência do
  projeto e não deve ser copiada para `pyproject.toml` por conveniência.
- O microbenchmark é diagnóstico e não substitui a suíte oficial nem a evidência
  funcional/visual do editor canônico.
