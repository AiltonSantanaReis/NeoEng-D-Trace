# Evidência — Pipeline ROI/GrabCut, Máscara Raio-X e Colisão

## Identificação

- Commit técnico: 36f6fcdb7916eb8a5bddfe3b5fdbd700096ac7e2
- Branch: codex/roi-grabcut-collision-pipeline
- Data: 2026-08-15, America/Sao_Paulo
- Estado: branch publicado no origin; PR #63 aberta para main; merge pendente
- Responsável: Codex

## Objetivo e escopo

Implementar funcionalmente a detecção assistida por ROI com OpenCV GrabCut, a visualização de raio-X e camadas diagnósticas, a preservação de hierarquia de contornos, a geração de colisões outline/convex hull/decomposição convexa, a persistência de partes compostas e a exportação em coordenadas de imagem ou normalizadas.

A decisão técnica não incluiu modelos externos de segmentação. O repositório não declara essas dependências e o requisito de operação local/leve não justifica introduzi-las sem modelo, licença, pacote e critério de qualidade reproduzível. GrabCut é uma segmentação assistida por ROI, não uma promessa de segmentação zero-shot universal.

## Ambiente

- Sistema: Windows 10 build 26200
- Python: 3.11.9
- Dependências: ambiente .venv conforme pyproject.toml/lock do repositório
- OpenCV, NumPy e PySide6 reais
- CUDA/CuPy: não disponível; o gerador registrou fallback explícito para CPU

## Entradas e hashes

Artefatos gerados em docs/evidence/artifacts/roi-grabcut-collision:

| Arquivo | Bytes | SHA-256 |
|---|---:|---|
| source.png | 6948 | 4bffd31518cb8eabcfba2b2a4379ba54d6a1632ebd8836b1cbae36f9b33a9a18 |
| grabcut-mask.png | 966 | e86c2105f17f8592005e1dacde0fbbc4ba9e38248dc608f94e330553b1959cad |
| mask-viewer-roi-xray.png | 11651 | 43930cc9fd8a770ea289a4fb8a4dc1397ca0086712c068147cb685ce56f9b88e |
| collision-compound-normalized.json | 1960 | 282ff00f02df4277435c574a03b969150bad1152ac3b8cbfcfd4d60dc3697edb |
| detected-compound.ndtproj | 2393 | 1af3e674a0d28e28f4a969416601c3325afa29abbe9e974bde58e4ef5a72e7ef |
| manifest.json | 1698 | contém e verifica os hashes dos cinco artefatos acima |

A entrada sintética real tem forma em L, 320 x 240 x 3, com detalhe interno escuro. O ROI desenhado foi [50, 35, 215, 170]; após padding operacional, o feedback registrou [48, 33, 219, 174].

## Comandos executados e resultados

- .venv\Scripts\python.exe tools\generate_roi_collision_artifacts.py — APROVADO; executou GrabCut, Qt, decomposição e persistência reais.
- .venv\Scripts\python.exe -m pytest -q --cov=src --cov-branch --cov-report=xml --cov-fail-under=90 — APROVADO; 1001 passaram, 10 avisos de depreciação Qt, cobertura total 90,77%.
- .venv\Scripts\python.exe tools\check_coverage_policy.py coverage.xml — APROVADO; linhas >=90%, ramos >=85%, módulos mensuráveis >=30%.
- .venv\Scripts\python.exe -m compileall -q src tests tools — APROVADO.
- .venv\Scripts\python.exe -m flake8 src tests tools — APROVADO.
- .venv\Scripts\python.exe -m black --check src tests tools — APROVADO.
- .venv\Scripts\python.exe -m isort --check-only src tests tools — APROVADO.
- .venv\Scripts\python.exe -m mypy src — APROVADO; 81 arquivos sem erros.
- .venv\Scripts\python.exe -m pip_audit — APROVADO; nenhuma vulnerabilidade conhecida; o pacote local neoeng-d-trace foi explicitamente não auditável no PyPI.
- .venv\Scripts\python.exe -m bandit -q -r src -lll — APROVADO; nenhuma ocorrência reportada; o pacote local foi ignorado por não existir no PyPI.
- .venv\Scripts\python.exe tools\baseline_integrity.py --verify — APROVADO; 381 arquivos.
- .venv\Scripts\python.exe tools\run_legacy_tests.py --group all — reconciliação APROVADA; 196 testes, 27 falhas brutas legadas, 27/27 esperadas, zero inesperadas, zero ausentes, working_tree_dirty=false e tested_commit igual ao commit técnico.

## Análise dos artefatos reais

O feedback do GrabCut registrou 1 polígono, 1 componente, 21.355 pixels de foreground, razão 0,2780598958 e 5 iterações. A máscara PNG foi produzida pelo resultado binário real do OpenCV e o contrato de testes confirma dimensões iguais à imagem e valores restritos a 0/255.

A visualização PNG foi produzida pelo MaskViewer com ROI e camadas diagnósticas. O exportador JSON registra shape_type compound e 4 partes convexas, em coordenadas normalizadas. O arquivo .ndtproj foi salvo e recarregado, preservando collision_parts. Isso demonstra a cadeia imagem -> máscara -> polígono -> decomposição -> exportação -> persistência.

A opção de preservar buracos usa RETR_CCOMP e retorna hierarquia. Este fixture executou esse caminho, mas não é correto afirmar que toda imagem terá buracos detectados: a qualidade depende da máscara e do ROI. A decomposição é 2D e determinística; V-HACD/mesh 3D não é necessário para o colisor 2D do projeto.

## Falhas e causa raiz

As 27 falhas do conjunto legado permanecem explicitamente registradas no summary.json do runner. Elas foram reconciliadas pelo manifesto do repositório, não ocultadas: 27 esperadas, 27 correspondentes, zero inesperadas. Entre elas estão fixtures antigos incompatíveis com a validação geométrica atual, expectativas antigas de dtype e testes legados baseados em mocks.

A suíte atual não falhou. O único aviso novo é a depreciação do construtor posicional de QMouseEvent no teste de eventos Qt; não altera o resultado funcional, mas deve ser modernizado em manutenção futura.

## Limitações e riscos residuais

- GrabCut exige ROI contendo o objeto e pode falhar com baixo contraste, múltiplos objetos ou sombras severas; não é detecção perfeita automática universal.
- A visualização raio-X facilita inspeção e sementes contextuais, mas não substitui correção manual quando a máscara estiver errada.
- Os limites operacionais continuam válidos; entradas acima deles devem ser rejeitadas de forma controlada.
- Não foi feita validação em runtime dentro de Unity/Godot neste branch; foram validados o schema/exportador local e a geometria.
- A PR #63 está sob validação remota. Até todos os checks concluírem com sucesso, esta permanece uma aprovação local/pré-merge e não uma aprovação de integração ou release.

## Decisão

APROVADO localmente / pré-merge, com limitações acima. O branch está pronto para revisão humana e execução dos workflows GitHub. Não declarar integrado, pronto para release ou aprovado por CI até a validação remota correspondente.
