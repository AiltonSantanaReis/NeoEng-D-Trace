# Evidência — Auditoria responsiva da MainWindow

## Identificação

- Commit: `4e839252a53d80c98aaf88a326306f7d51f3ef97`
- Branch: revisão pré-merge correspondente ao commit, publicada no remoto.
- Data/hora: 2026-08-16 00:40 BRT.
- Responsável: mantenedor do projeto.
- Escopo: auditoria visual funcional da MainWindow após a correção do layout responsivo.

## Ambiente

- Sistema operacional: Windows 10.0.26200.
- Python: 3.11.9 64-bit.
- Qt: PySide6 fixado pelo lockfile.
- Dependências/lockfile: `poetry.lock`, SHA-256 canônico `05e0262e40a3f956bdcfb20b47794f8e8a04ec68d5afeec1931f2285d0340e65`.
- Execução: Qt offscreen, usando os contratos reais de `Scene`, `CommandManager`, `MainWindow` e `CollisionPanel`.

## Objetivo e escopo

Verificar, em 1920x1080, 1366x768 e 1280x720: tela inicial sem projeto; projeto carregado com dois polígonos e painéis acessíveis; mensagem real de validação de colisão; ausência de sobreposição entre canvas e painéis; consistência do tema escuro; e preservação das ações de exportação quando a barra principal fica oculta no modo compacto.

A implementação substitui a linha única de quatro toolbars/painéis por um controlador responsivo: splitters no modo desktop e abas compactas abaixo de 1450 px. As ações de exportação permanecem disponíveis no menu Arquivo.

## Entradas

- Fixture de imagem: `docs/evidence/artifacts/ui-audit/ui-audit-fixture.png` — 10.112 bytes — SHA-256 `5c1922c64ce7ab1f7118b5f28e2ab86f7e79e233917fe50b0366f10a1e8e79b7`.
- Fixture de projeto: `docs/evidence/artifacts/ui-audit/ui-audit-fixture.ndtproj` — 1.443 bytes — SHA-256 `5cbccd227dd84f3aaf9f09447529185b1ae31bf93999fbc547cda98021ac10d2`.
- Manifesto de capturas: `docs/evidence/artifacts/ui-audit/manifest.json` — contém os hashes de todos os PNGs e os resultados brutos da mensagem de validação.
- Todas as referências de imagem persistidas na fixture são relativas; não há caminho absoluto de máquina.

## Comandos executados

```text
python scripts/audit_ui_capture.py --output docs/evidence/artifacts/ui-audit
poetry run pytest --cov=src --cov-branch --cov-report=term-missing --cov-report=xml:coverage.xml -q
python tools/check_coverage_policy.py coverage.xml
poetry run black --check src/ui/main_window.py src/ui/main_window_translations.py src/ui/theme_qss.py src/ui/responsive_layout.py scripts/audit_ui_capture.py tests/test_ui_responsive_layout.py
poetry run isort --check-only src/ui/main_window.py src/ui/main_window_translations.py src/ui/theme_qss.py src/ui/responsive_layout.py scripts/audit_ui_capture.py tests/test_ui_responsive_layout.py
poetry run flake8 src/ui/main_window.py src/ui/main_window_translations.py src/ui/theme_qss.py src/ui/responsive_layout.py scripts/audit_ui_capture.py tests/test_ui_responsive_layout.py
poetry run mypy src
poetry run pip-audit
poetry run bandit -q -r src -lll
python tools/baseline_integrity.py --verify
```

## Resultados

- Aprovados: 1003 testes; 12 PNGs gerados; 3 resoluções capturadas com dimensões exatas; mensagem real de validação capturada; splitters/abas responsivos; exportações acessíveis no menu Arquivo; canvas e painéis sem sobreposição observada; paleta escura consistente.
- Reprovados: nenhum teste funcional ou gate estático local.
- Ignorados: nenhum caso de teste foi ignorado.
- Bloqueados: revisão e merge ainda não executados no momento deste relatório.
- Cobertura: 91% de linhas; política integrada aprovada, incluindo o piso de branches e o mínimo de módulos mensuráveis.
- Tipagem: mypy sem erros em 82 arquivos de origem.
- Dependências: pip-audit sem vulnerabilidades conhecidas; o pacote local não foi auditado por não estar publicado no índice.
- Segurança estática: Bandit no mesmo comando da CI (`-lll`) aprovado.
- Baseline: manifesto verificado com 401 arquivos.
- Warnings: 10 avisos de depreciação de `QMouseEvent` em teste legado; não causaram falhas.

## Auditoria visual

| Resolução | Estado base | Projeto/painéis | Validação | Dimensão real |
|---|---|---|---|---|
| 1920x1080 | capturado | capturado | capturado + modal | 1920x1080 |
| 1366x768 | capturado | capturado | capturado + modal | 1366x768 |
| 1280x720 | capturado | capturado | capturado + modal | 1280x720 |

A mensagem capturada pelo caminho real do `CollisionPanel` foi: `No collision shapes registered. Use Auto-Generate first.`. Em modo compacto, os painéis foram acessados pelas abas `Objects`, `Layers`, `Groups` e `Collision`, com tradução verificada para `Objetos`, `Camadas`, `Grupos` e `Colisão`.

A análise visual confirma fundo escuro, áreas de painel e seleção dentro da paleta QSS esperada e ausência de invasão do canvas pelos painéis nas três dimensões. Os PNGs e seus hashes estão no manifesto versionado, sem alteração posterior.

## Artefatos

- `scripts/audit_ui_capture.py`
- `tests/test_ui_responsive_layout.py`
- `src/ui/responsive_layout.py`
- `docs/evidence/artifacts/ui-audit/manifest.json`
- `docs/evidence/artifacts/ui-audit/*.png`
- `docs/evidence/artifacts/ui-audit/ui-audit-fixture.ndtproj`
- `docs/evidence/artifacts/ui-audit/ui-audit-fixture.png`

## Falhas e causa raiz

A causa do problema de layout era a concentração de toolbars e painéis na mesma linha, fazendo com que as restrições mínimas dos widgets superassem a resolução compacta. A correção cria um modo compacto baseado em abas, reduz as restrições mínimas nesse modo, oculta somente a barra principal e mantém as ações de exportação no menu Arquivo.

A captura full-window em Qt offscreen exibiu glifos quadrados em parte dos textos, embora os valores textuais dos widgets, as traduções e a renderização isolada de rótulos tenham sido verificados. Isso é uma limitação do backend de captura do ambiente e impede declarar a tipografia visual como aprovada de forma conclusiva. Não foi mascarado nem convertido em sucesso.

## CI pré-merge auditado

- Run inicial `31924919538`, no HEAD `bdc0d895b056b5ec300a3945fd578d07d0b1a5b3`: Linux reprovado no passo da suíte por código 139, com segmentation fault exatamente no novo teste responsivo ao reaplicar o QSS. Windows terminou verde, mas o PR não foi considerado aprovado por causa do job Linux.
- Causa raiz confirmada no log: `tests/test_ui_responsive_layout.py`, linha 38, aplicação redundante do stylesheet em uma suíte Qt já inicializada.
- Correção publicada no HEAD `4e839252a53d80c98aaf88a326306f7d51f3ef97`: o teste de layout deixou de reaplicar QSS; o auditor visual continua aplicando o tema real.
- Run corretivo `31925090921`: Linux e Windows verdes; 1003 testes aprovados por sistema; cobertura CI acima de 90%; política de cobertura aprovada; baseline verificado com 401 arquivos; legado Windows reconciliado com `27/27` correspondências, zero inesperadas e zero ausentes.
- O run inicial permanece registrado como reprovado; não foi apagado nem reclassificado.
## Limitações e riscos residuais

- A inspeção visual foi feita com backend Qt offscreen em um único ambiente Windows; não substitui validação em sessão gráfica real e em Linux.
- A ausência de clipping de texto é inconclusiva no full-window por causa da limitação tipográfica descrita acima.
- O cenário de colisão capturado exercita a mensagem de ausência de shapes; não é uma validação de qualidade geométrica da detecção automática.
- CI remoto, revisão obrigatória e comportamento pós-merge ainda precisam ser verificados pelo PR correspondente.

## Decisão

`PARCIAL`

O pacote está tecnicamente preparado para revisão: os gates locais e a auditoria estrutural passaram, mas a aprovação visual completa da tipografia e a aprovação de integração permanecem pendentes.