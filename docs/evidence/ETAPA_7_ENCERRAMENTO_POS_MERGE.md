# Evidência — Encerramento pós-merge da Etapa 7

## Identificação

- commit técnico: `a940ef13018aabc430126db3fd705b521fc1be06`;
- commit documental pré-merge: `51e55a37021c506471111ef1f4e7bc9abe67c65d`;
- PR: `#36`;
- merge commit: `99326f2d7ccf7046e401d90830feb8a5d33e9f9a`;
- data: 10 de agosto de 2026;
- responsável: execução técnica automatizada; decisão humana de release pendente.

## Escopo encerrado

- matriz completa dos argumentos públicos da CLI;
- despacho inequívoco entre GUI e headless;
- códigos `0`, `1` e `2` com canais de saída definidos;
- rejeição de fontes conflitantes e dependências de argumentos incompletas;
- propagação do código por `app.py` e execução direta do módulo;
- subprocessos reais com ajuda, versão, erros, projeto, JSON e GLB;
- atualização da cobertura do launcher de 18% para 85%.

## Validação local vinculada ao pacote

- testes focais: `47 passed`, `0 failed`;
- suíte do commit técnico: `620 passed`, `0 failed`, `0 skipped`;
- suíte do pacote pré-merge: `621 passed`, `0 failed`, `0 skipped`;
- suíte do fechamento formal: `622 passed`, `0 failed`, `0 skipped`;
- cobertura combinada: `68.53%`;
- `src/launcher.py`: `85%`;
- mypy: zero erros em `66` arquivos;
- lock, compilação, Flake8, Black, isort, pip-audit e Bandit: aprovados;
- legado: `196` testes, `26/26` divergências previstas, zero inesperadas e zero ausentes;
- baseline pré-merge final: `282` arquivos verificados;
- baseline do fechamento formal: `283` arquivos verificados;
- varredura de referências proibidas: aprovada.

## CI da PR

- run: `31436763095`;
- HEAD: `51e55a37021c506471111ef1f4e7bc9abe67c65d`;
- Linux `test`: job `93612497957`, `success`;
- Windows `test-windows`: job `93612497888`, `success`;
- anotações dos dois jobs: `[]`;
- artefato Linux: ID `9081304874`, digest `sha256:afc11a2b7453706a1cde6d6a9dfd0786a190564365d1207da0c4ee9596df70da`;
- artefato Windows: ID `9081333662`, digest `sha256:8d3003ab5a11b0d408d8fe057923158480fcb26272f85bf26e7b833cd2fd0618`.

## CI pós-merge

- run: `31437000772`;
- HEAD integrado: `99326f2d7ccf7046e401d90830feb8a5d33e9f9a`;
- Linux `test`: job `93613220622`, `success`;
- Windows `test-windows`: job `93613220731`, `success`;
- anotações dos dois jobs: `[]`;
- artefato Linux: ID `9081388807`, digest `sha256:4437e8ae18c2f38116f10587c997c36c5f5ac05d04e4d8fa406fc658a1775967`;
- artefato Windows: ID `9081419753`, digest `sha256:117ee20d37e926ac1762e7d9e120608bf1894e1b416d4897ec6318a898f60cc2`.

## Falhas conhecidas e limites preservados

- múltiplas saídas CLI são sequenciais, não uma transação conjunta; arquivos concluídos antes de uma falha tardia permanecem;
- importação dos GLBs em engines externas continua pertencendo à Etapa 10;
- executável e instalador standalone não foram produzidos nesta etapa e permanecem para a Etapa 14;
- cobertura global final de 90%/85% não foi atingida; `R-003` permanece aberto;
- Bézier/geometria, APIs/arquitetura, limites operacionais, refatoração Qt, autosave e release permanecem em suas etapas obrigatórias;
- nenhum resultado deste relatório aprova release.

## Decisão

`R006_CLOSED=YES`

`STAGE7_COMPLETED=YES`

`STAGE8_STARTED=NO`

`RELEASE_APPROVED=NO`

**ETAPA 7 FORMALMENTE CONCLUÍDA NO ESCOPO APROVADO.**

O fechamento comprova o contrato atual da CLI, não atomicidade global entre múltiplas saídas, validação em engines, build standalone ou prontidão de produção.
