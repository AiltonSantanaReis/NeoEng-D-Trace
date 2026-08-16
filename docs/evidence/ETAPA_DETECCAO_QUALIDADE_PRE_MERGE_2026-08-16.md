# Evidência — Qualidade da detecção automática

## Identificação

- Commit de base auditado: `b5b8ec4bb18a0843b53117f2c51a1be4a0877103`.
- Branch: branch de validação funcional baseada na `main`.
- Data: 2026-08-16.
- Estado: alterações locais ainda não integradas; este documento é pré-merge.

## Ambiente

- Sistema operacional: Windows.
- Python: 3.11.9.
- OpenCV: 4.12.0.
- NumPy: 2.2.6.
- Dependências: ambiente virtual do repositório e lockfile vigente.

## Objetivo e escopo

Foram executadas as oito frentes solicitadas: corpus determinístico com casos adversariais, métricas de máscara e borda, comparação dos quatro modos reais, reprodução do limite de 2.000 pontos, desempenho e estabilidade, análise de causa-raiz, artefatos com hashes e gates de não regressão.

Não foi introducido modelo de IA externo. A melhoria usa as primitivas locais já presentes: máscara de primeiro plano, morfologia, RDP, hierarquia de contornos e GrabCut assistido por ROI.

## Entradas

O corpus foi gerado de forma determinística pelo próprio script de auditoria, sem mocks no caminho de detecção. Os casos são: retângulo, concavidade em L, sombra/textura, gradiente de baixo contraste, anel com buraco, curva irregular, dois objetos, objetos tocantes, RGBA com alfa, fundo ruidoso e fronteira de alta densidade.

- Script: `tools/benchmark_auto_detection.py`.
- Relatório bruto: `docs/evidence/artifacts/auto-detection-quality/final-v6/report.json`.
- SHA-256 do relatório bruto: `a437b91f4ad2b2348106a379b9d0d74b3a29ff897330c90f491009cf610b45e9`.
- Manifesto de artefatos: `docs/evidence/artifacts/auto-detection-quality/final-v6/manifest.json`.
- SHA-256 do manifesto: `514ee7f4df30b4c007732eb427488475b9842e9877b928148b3aaaf345a3587a`.
- Manifesto: 112 arquivos, 608.566 bytes listados, todos com caminho relativo, tamanho e SHA-256.

Os hashes individuais das imagens de entrada, máscaras de referência, máscaras previstas e sobreposições estão no `manifest.json` e no `report.json`; nenhum endereço local foi gravado nos artefatos.

## Comandos executados

```text
\.venv\Scripts\python.exe tools\benchmark_auto_detection.py --output docs\evidence\artifacts\auto-detection-quality\final-v6 --repeats 5
\.venv\Scripts\python.exe -m pytest tests\test_auto_detection_quality.py tests\test_stage_11_numeric_tool_branch_coverage.py tests\test_stage_12_operational_limits.py -q
\.venv\Scripts\python.exe -m pytest --cov=src --cov-branch --cov-report=term-missing --cov-report=xml
\.venv\Scripts\python.exe -m black --check src\tools\auto_detect.py tools\benchmark_auto_detection.py tests\test_auto_detection_quality.py
\.venv\Scripts\python.exe -m isort --check-only src\tools\auto_detect.py tools\benchmark_auto_detection.py tests\test_auto_detection_quality.py
\.venv\Scripts\python.exe -m flake8 src\tools\auto_detect.py tools\benchmark_auto_detection.py tests\test_auto_detection_quality.py tests\test_stage_11_numeric_tool_branch_coverage.py
\.venv\Scripts\python.exe -m py_compile src\tools\auto_detect.py tools\benchmark_auto_detection.py tests\test_auto_detection_quality.py
\.venv\Scripts\python.exe -m mypy src
$env:NEOENG_SOURCE_HEAD_SHA=(git rev-parse HEAD).Trim(); \.venv\Scripts\python.exe tools\run_legacy_tests.py --group all --output docs\evidence\artifacts\auto-detection-quality\legacy-final-v4
```

## Resultados

### Qualidade, estabilidade e desempenho

O benchmark final executou 44 combinações reais (11 casos × 4 modos), cada uma cinco vezes. O resultado foi 44/44 sem exceção, 44/44 determinísticas e zero polígonos acima do limite de 2.000 pontos.

| Modo | IoU mínimo | IoU médio | F1 de borda mínimo | F1 de borda médio | maior contagem de vértices | maior mediana (s) |
|---|---:|---:|---:|---:|---:|---:|
| Basic | 0,829384 | 0,972477 | 0,832593 | 0,981915 | 115 | 0,061970 |
| Perfect | 0,977483 | 0,995972 | 0,955660 | 0,995969 | 311 | 0,002917 |
| Enhanced | 0,977483 | 0,995633 | 0,955660 | 0,995969 | 311 | 0,013692 |
| GrabCut/ROI | 0,966903 | 0,989510 | 0,974050 | 0,997641 | 141 | 0,083860 |

Os testes funcionais novos passaram 11/11; os contratos de limites e detecção passaram 67/67; a suíte completa passou 1.014/1.014 testes, com cobertura global de 91% no ambiente Windows desta execução.

### Falha residual real

O modo básico não preserva o buraco do caso `ring_hole`: IoU 0,829384, F1 de borda 0,832593 e zero buracos retornados quando um era esperado. Isso não foi mascarado nem convertido em sucesso. Os modos perfeito, aprimorado e GrabCut produziram uma única silhueta externa com um buraco; o modo aprimorado também preserva o registro legado `is_hole`, sem materializá-lo como objeto de cena.

### Causas-raiz corrigidas

- O modo aprimorado enviava resposta de bordas em tons de cinza diretamente para `findContours`; agora usa máscara de primeiro plano real e só usa resposta de bordas binarizada como fallback.
- `morph_kernel_size` era recebido pela interface, mas ignorado; agora é validado e aplicado à morfologia.
- Buracos do modo aprimorado eram devolvidos apenas como polígonos independentes; agora também ficam anexados ao objeto externo, preservando o registro legado sem criá-lo como objeto de cena.
- Contornos comuns eram persistidos quase sem simplificação; agora passam por RDP e continuam abaixo do contrato de 2.000 pontos.
- A simplificação adaptativa quadrática do modo perfeito podia consumir CPU por tempo indefinido em contornos densos; contornos acima do limiar interno usam RDP limitado, preservando mais detalhe nos casos densos.
- O modo perfeito agora normaliza entradas numéricas, usa a máscara de primeiro plano quando disponível e preserva buracos.

O limite de 2.000 pontos não foi removido. O teste de contorno degenerado acima do limite continua rejeitando a entrada de forma controlada.

## Artefatos

O diretório final contém fontes, ground truths, máscaras previstas e sobreposições por caso/método, além do relatório e manifesto. A inspeção visual pelo helper local foi tentada nos PNGs reais, mas o helper recusou a leitura por ACL; por isso esta evidência não declara aprovação visual. A existência, tamanho, decodificação pelo OpenCV e hash dos arquivos foram validados; a limitação do visualizador permanece explícita.

## Falhas e causa-raiz do processo de teste

Antes das correções, a execução completa de diagnóstico ficou presa no modo perfeito sobre a fronteira de alta densidade. A execução foi interrompida pelo identificador do processo próprio, e a causa foi localizada na simplificação adaptativa quadrática. Depois da correção, o mesmo caso terminou em menos de um segundo no teste isolado e integrou o benchmark final sem erro.

## Limitações e riscos residuais

- O corpus é determinístico e sintético; ele comprova comportamento real do pipeline OpenCV, mas não substitui um conjunto de imagens de produção do domínio do usuário.
- GrabCut continua sendo segmentação assistida por ROI; não é detecção zero-shot universal.
- O modo básico ainda não modela buracos; para objetos com cavidades, usar perfeito, aprimorado ou GrabCut/ROI.
- O pico de memória foi medido com `tracemalloc`; memória nativa do OpenCV pode não aparecer integralmente nessa métrica.
- A inspeção visual dos PNGs ficou bloqueada pelo helper de leitura, embora os artefatos tenham sido gerados e hashados.
- A reconciliação legada local foi aceita com 27/27 falhas históricas esperadas, sem inesperadas; CI remoto, push, revisão e merge ainda não ocorreram neste snapshot pré-merge.

## Decisão

PARCIAL — melhorias funcionais e gates locais aprovados no escopo medido; a limitação conhecida do modo básico, a inspeção visual bloqueada e a ausência de CI/merge impedem declarar aprovação integral ou conclusão da etapa.
