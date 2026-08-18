# Evidência — Etapa 3: paleta visual de comandos

**Escopo:** interface da paleta integrada ao `CommandRegistry`, busca por rótulo,
atalho e ID estável, navegação por teclado, Enter, Escape, localização en/pt,
acessibilidade básica e preservação das `QAction` como fonte única de execução.

**Commit técnico testado:** `d487ec9250404f1a0fc5de9d50ad227ce1fa5758`

**Estado da evidência:** captura real concluída contra o commit acima, com a árvore
limpa no momento da captura. O identificador da branch de trabalho não é persistido
no payload versionado por causa do gate de higiene de referências do repositório.

## Implementação comprovada

- `CommandPaletteDialog` é um diálogo não modal reutilizável, criado uma vez
  pela `MainWindow`.
- `Ctrl+K` conserva o sinal público existente e abre a paleta com foco no
  campo de busca.
- A busca consulta texto da `QAction`, ID estável e atalho; não existe uma
  cópia executável das ações.
- Ações desabilitadas permanecem visíveis como indisponíveis e são rejeitadas
  pelo `CommandRegistry.trigger`.
- Up/Down navegam, Enter executa somente uma ação habilitada e fecha a paleta;
  Escape fecha e restaura o foco anterior.
- O catálogo en/pt cobre título, placeholder, mensagens, instruções de teclado
  e nomes/descrições acessíveis dos controles.
- A paleta usa seletores próprios no tema escuro existente; menus e ações
  tradicionais continuam disponíveis.

## Captura reproduzível

Comando:

```text
.\.venv\Scripts\python.exe scripts\audit_command_palette_capture.py --output docs\evidence\artifacts\stage3-command-palette-2026-08-18
```

O manifest `docs/evidence/artifacts/stage3-command-palette-2026-08-18/manifest.json`
registra `source_head` igual ao commit testado e `worktree_clean_at_capture: true`.
Cada captura registra bytes, SHA-256, dimensões, modo Pillow, shape OpenCV e
geometrias Qt reais.

Resultados objetivos:

- 3 resoluções: 1920×1080, 1366×768 e 1280×720;
- 2 idiomas: `en` e `pt`;
- 6 paletas e 6 janelas capturadas;
- cada paleta abriu por Ctrl+K com campo de busca focado;
- cada estado exibiu exatamente 19 comandos;
- título, busca e lista ficaram contidos na geometria do diálogo;
- Escape fechou cada paleta;
- Pillow e OpenCV decodificaram todos os 12 PNGs;
- todas as capturas foram RGB, sem alfa inesperado;
- as quatro cores oficiais do tema escuro foram encontradas nas seis paletas por Pillow/NumPy;
- `tools/evidence_integrity.py` validou 48 manifests, incluindo o novo pacote.

## Falha encontrada e corrigida

A primeira execução abriu corretamente o estado em inglês, mas falhou ao trocar
para português porque o capturador não reativava a janela nem aguardava o foco
do canvas antes do segundo Ctrl+K. A falha foi reproduzida, a saída parcial foi
descartada, o capturador recebeu ativação, espera e asserção explícita de foco,
e a execução limpa posterior passou nos seis estados. Nenhum `skip`, `xfail`,
emissão artificial de sinal ou relaxamento de asserção foi usado.

## Testes e gates

- testes específicos das Etapas 2 e 3: `14 passed`;
- suíte integral local: `1218 passed, 2 skipped, 10 warnings`;
- Black, isort, Flake8, py_compile, mypy e Bandit: aprovados no escopo alterado;
- cobertura de branches: `90,67%`, acima do gate de 90%;
- baseline: `1409 files`, verificado após incluir o pacote de evidências;
- integridade de evidências: `48 manifests validated`.

Os dois skips permanecem condicionais e preexistentes na suíte; não foram
criados nem usados para aprovar a Etapa 3.

## Falha remota encontrada e corrigida

A primeira execução remota da PR no Linux foi interrompida no gate de tipagem:
`src/ui/command_palette.py:144` recebeu `QWidget | None` em atributo inferido como
`None`. A correção foi uma anotação explícita e a importação correspondente de
`QWidget`, registrada em `d487ec9250404f1a0fc5de9d50ad227ce1fa5758`. O gate local
`poetry run mypy src` passou depois da correção; a execução remota precisa ser
reavaliada nesse novo SHA. Nenhuma regra do CI foi alterada e nenhum bypass foi
usado.

## Limitações declaradas

- A captura é automatizada em Qt offscreen; não constitui medição de latência
  de compositor ou de uma sessão interativa física do Windows.
- O helper de leitura visual do ambiente não conseguiu abrir os PNGs por uma
  restrição ACL. Portanto, não é declarada inspeção humana pixel-a-pixel; a
  prova disponível é a validação automatizada por Qt, Pillow, OpenCV, hashes e
  geometrias reais.
- Não há ainda implementação de parallax, câmera, overlays, schema lateral ou
  runtime de cenários; esses itens permanecem nas etapas posteriores do plano.

## Decisão

**APROVADO para revisão do PR no escopo da Etapa 3**, condicionado aos checks
remotos sobre o commit efetivamente publicado. A Etapa não será declarada
mesclada antes do CI e da revisão do diff concluírem sem regressão.
