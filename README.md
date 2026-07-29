# NeoEng-D-Trace

NeoEng-D-Trace é uma ferramenta desktop proprietária e principalmente offline para preparar assets de jogos a partir de imagens 2D: detectar objetos, corrigir contornos, configurar colisões e exportar sprites, atlas, metadados e GLTF/GLB.

## Estado atual

O projeto permanece em estabilização e ainda não é uma versão comercial final.

Já validado no Windows/Python 3.11:

- identidade NeoEng-D-Trace em UI, logger e metadados;
- interface em inglês e português;
- Laço Magnético melhorado;
- seleção automática do polígono criado e lista lateral sincronizada;
- diálogo de exportação compacto;
- exportação de sprite, atlas e metadados Generic/Godot/Unity/Phaser;
- exportação GLTF/GLB de cena e objeto com generator, geometria, metadados e padding validados;
- entrada gráfica e headless por `app.py`.

## Estrutura aprovada

Existe uma única árvore de implementação:

```text
app.py
src/
├── collision/
├── core/
├── exporters/
├── models/
├── physics/
├── tools/
├── ui/
└── utils/
```

Não existe uma segunda árvore `neoeng_d_trace/`, nem aliases entre pacotes. O nome de distribuição é `neoeng-d-trace`; internamente, o código continua em `src/`.

## Preparação reproduzível no Windows

```powershell
Set-Location "C:\caminho\do\projeto"
py -3.11 -m venv .venv
& ".\.venv\Scripts\python.exe" -m pip install --upgrade pip
& ".\.venv\Scripts\python.exe" -m pip install -e .
& ".\.venv\Scripts\python.exe" ".\app.py"
```

Ajuda da CLI:

```powershell
& ".\.venv\Scripts\python.exe" ".\app.py" --help
```

Após instalação pelo gerenciador de pacotes, a entrada declarada é:

```powershell
neoeng-d-trace
```

## Testes

```powershell
& ".\.venv\Scripts\python.exe" -m pytest -q
```

## Configuração

Por compatibilidade, a configuração continua em `config.json` na raiz do projeto. Uma mudança futura para AppData exigirá etapa própria, importação explícita e rollback.

## Limitações abertas

- `PERF-MAGNETIC-001`: otimização adicional em imagens grandes;
- `UI-RESIZE-PT-001`: alguns painéis ficam menos flexíveis em português;
- `POLY-VALIDATION-UX-001`: mensagens e recuperação de polígonos inválidos ainda precisam de refinamento;
- `GLTF-2D-001`: a exportação representa geometria 2D no plano Z=0;
- `GLTF-UV-001` e `GLTF-MATERIAL-001`: UVs, texturas e materiais ainda não são gerados;
- `GLTF-U16-001`: um único objeto com mais de 65.535 vértices pode exceder o índice `UNSIGNED_SHORT`;
- `GLTF-CLEANUP-001`: o exportador contém trechos mortos que ainda precisam de limpeza sem alterar o contrato binário;
- formato de projeto versionado, autosave, 2.5D, build Windows e validação completa nas engines ainda são trabalhos futuros.

`CLI-LAZY-001` e `LOG-DUP-001` foram encerrados: `app.py --help` funciona sem importar PySide6 e a configuração do logger possui teste contra emissão duplicada.

A auditoria detalhada da etapa 0.6O2 está em `docs/AUDITORIA_ESTADO_ATUAL_0_6O2.md`. A validação nativa PySide6/Windows dessa etapa permanece como portão obrigatório após a aplicação transacional.

## Regras

- nenhuma funcionalidade será removida silenciosamente;
- correções e melhorias devem ter testes e rollback;
- não publicar o histórico Git local antigo;
- não executar push antes de um baseline privado limpo;
- não atribuir licença open source sem decisão jurídica formal.


## Baseline privada

A origem, as exclusões, as validações e as limitações conhecidas do primeiro commit limpo estão registradas em `docs/BASELINE_2026-07-29.md`. A integridade dos arquivos rastreados é verificável por `python tools/baseline_integrity.py --verify`.
