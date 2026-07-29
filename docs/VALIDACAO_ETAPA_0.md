# Validação da Etapa 0

Data: 27 de julho de 2026.

## Escopo alterado

- documentação de estado e governança;
- regras de arquivos ignorados;
- configuração de exemplo sem caminhos pessoais;
- correção da coleta do pytest;
- correção da API pública SAT;
- correção do gerador de snapshot;
- correção da referência de README no `pyproject.toml`.

Nenhum algoritmo de ferramenta, persistência, exportação ou interface foi refatorado nesta etapa.

## Arquivos novos

- `.gitignore`;
- `config.example.json`;
- `README.md`;
- `docs/AUDITORIA_TECNICA_2026-07-27.md`;
- `docs/DEFINICAO_DO_PRODUTO.md`;
- `docs/MATRIZ_FUNCIONALIDADES.md`;
- `docs/PLANO_DE_DESENVOLVIMENTO.md`;
- `docs/PLANO_RENOMEACAO.md`;
- `docs/ESTRATEGIA_GITHUB.md`;
- `docs/VALIDACAO_ETAPA_0.md`.

## Arquivos modificados

- `pyproject.toml`;
- `pytest.ini`;
- `pack_for_ai.py`;
- `src/collision/__init__.py`.

## Testes executados

### 1. Compilação de sintaxe

Escopo:

- `app.py`;
- `src/`;
- `tests/`;
- `test_gui_interaction.py`;
- `test_physics_core.py`;
- `pack_for_ai.py`.

Resultado: aprovado.

### 2. API de colisão

Verificado:

- importação de `project_polygon`;
- importação de `overlap_intervals`;
- importação de `polygon_collision_sat`;
- projeção simples;
- sobreposição de intervalos;
- colisão entre dois quadrados.

Resultado: aprovado.

### 3. Testes não gráficos

Arquivos:

- `tests/test_auto_detect.py`;
- `tests/test_broadphase_sap.py`;
- `tests/test_scene_repair.py`;
- `test_physics_core.py`.

Resultado: **17 aprovados**.

Ambiente:

- Linux;
- Python 3.13.5;
- pytest 9.0.2.

Isso não substitui a matriz oficial futura em Python 3.11/Windows.

### 4. Configuração do pytest

Verificado:

- `configfile: pytest.ini`;
- `testpaths: tests`;
- cópias em `backup/` não foram coletadas.

Resultado: aprovado.

### 5. `pyproject.toml`

Verificado:

- TOML parseável;
- `readme = "README.md"` aponta para arquivo existente.

Resultado: aprovado.

### 6. Gerador de snapshot

Verificado:

- 87 arquivos elegíveis;
- nenhuma entrada de `backup/`;
- nenhuma entrada de `.venv/`;
- `project_context.txt` não é incorporado ao próprio snapshot;
- saída de teste: aproximadamente 578 KB;
- limite máximo por arquivo ativo.

Resultado: aprovado.

## Testes não concluídos

### Suíte completa de UI

Comando `pytest` coletou apenas `tests/`, mas encontrou quatro erros de importação porque PySide6 não está instalado no ambiente Linux de auditoria.

Arquivos afetados:

- `tests/test_full_behavior.py`;
- `tests/test_mask_viewer.py`;
- `tests/test_tools_real.py`;
- `tests/test_view_modes_and_tools.py`.

Isso não foi classificado como regressão da Etapa 0. A suíte deverá ser executada no ambiente Windows 3.11 do projeto antes de aplicar o patch ao baseline definitivo.

## Critério de aceitação no Windows

Depois de aplicar o patch:

```powershell
$ProjectRoot = "C:\caminho\para\o-projeto"
Set-Location -LiteralPath $ProjectRoot

.\.venv\Scripts\python.exe -m compileall -q -f app.py src tests pack_for_ai.py
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe .\app.py
```

Registrar o resultado integral. Não afirmar que a Etapa 0 está validada no Windows antes dessa execução.

## Reversão

O patch é textual. Para reverter com Git:

```powershell
git apply -R polygontool_etapa_0.patch
```

Em um diretório sem baseline Git confiável, preserve o ZIP original e reaplique os arquivos somente em uma cópia.
