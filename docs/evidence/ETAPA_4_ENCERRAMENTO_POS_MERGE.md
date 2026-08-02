# Evidência — Etapa 4: encerramento pós-merge

## Identificação

- Etapa: `4 — Ciclo Abrir/Salvar na interface`;
- Pull request funcional: `#13`;
- branch funcional: `feat/etapa-4-ciclo-abrir-salvar-ui`;
- commit funcional aprovado: `3469a4a9bfab20fa8cd687e2925a64928e7903d3`;
- base funcional: `2f6309acfc7c184f722f15ae15ece8dc5a21cc63`;
- merge commit funcional: `4d663f028c5d501a2da44e3a34077023087df58c`;
- data do merge no GitHub: `2026-08-02T12:00:11Z`;
- branch documental: `docs/etapa-4-encerramento-pos-merge`;
- data de geração: `2026-08-02T17:37:11.742328-03:00`;
- responsável: Ailton Santana Reis.

## Objetivo

Registrar permanentemente as evidências da implementação, CI, validação manual Windows e integração da Etapa 4 antes de iniciar qualquer alteração funcional da Etapa 5.

Este registro não adiciona funcionalidade. Ele fecha a lacuna documental deixada após a integração da PR funcional e mantém a `main` restrita a estados aprovados.

## Estrutura do merge funcional

- PR: `#13`;
- estado final: `closed`;
- merged: `true`;
- HEAD revisado: `3469a4a9bfab20fa8cd687e2925a64928e7903d3`;
- base revisada: `2f6309acfc7c184f722f15ae15ece8dc5a21cc63`;
- merge commit: `4d663f028c5d501a2da44e3a34077023087df58c`;
- método: merge commit;
- squash: não utilizado;
- rebase: não utilizado;
- a atualização local da `main` foi realizada por fast-forward até `4d663f028c5d501a2da44e3a34077023087df58c`.

## Gate da PR funcional

- workflow: `Private validation`;
- execução: `#44` (`30741145009`);
- evento: `pull_request`;
- commit: `3469a4a9bfab20fa8cd687e2925a64928e7903d3`;
- estado: `completed`;
- conclusão: `success`.

Jobs:

- `test`: Job `91478701263`, `completed/success`;
- `test-windows`: Job `91478701282`, `completed/success`;

Artefatos:

- `validation-linux-python-3.11`: Artifact `8831333445`, `24521` bytes, digest `sha256:e87df0a13db8887968aa4ff19457632c5a2666421346faee995113b5548db9ec`, expirado: `false`;
- `validation-windows-python-3.11`: Artifact `8831341327`, `5067478` bytes, digest `sha256:2908c3b3c65cffc3bd6e9c59d2e4028670e33c0f8153a719971da42f2052f983`, expirado: `false`;

## Gate pós-merge funcional da `main`

- workflow: `Private validation`;
- execução: `#45` (`30746901415`);
- evento: `push`;
- commit: `4d663f028c5d501a2da44e3a34077023087df58c`;
- estado: `completed`;
- conclusão: `success`.

Jobs:

- `test`: Job `91493922419`, `completed/success`;
- `test-windows`: Job `91493922390`, `completed/success`;

Artefatos:

- `validation-linux-python-3.11`: Artifact `8833179318`, `24522` bytes, digest `sha256:f02549954192d78fa18a97b50f9ed81f007c7e6d1ebcb96f040f31120b40ca8b`, expirado: `false`;
- `validation-windows-python-3.11`: Artifact `8833187224`, `5067481` bytes, digest `sha256:fb0382a9c967de6074f63623848356265c73959989cd7563dcc22c9e773b48f1`, expirado: `false`;

## Validação manual GUI no Windows 11

- validador: versão `4`;
- diretório de evidência local: `NeoEng-D-Trace_Etapa4_Guiada_20260802_084517`;
- resultado: `APPROVED`;
- aplicação: código de saída `0`;
- checks manuais: `15/15`;
- erros automáticos: `0`;
- worktree limpa depois da sessão: `true`;
- falhas negativas esperadas: `2`;
- falhas inesperadas: `0`.

Eventos estruturados:

- `application.closed`: `1`;
- `application.opened`: `1`;
- `application.state.saved`: `1`;
- `document.close_requested`: `2`;
- `image.opened`: `1`;
- `polygon.created`: `3`;
- `project.opened`: `8`;
- `project.saved`: `4`;
- `python.log`: `2`;
- `selection.synced`: `3`;
- `session.start`: `1`;
- `session.summary`: `1`;
- `validation.mode`: `1`;
- `window.geometry.restored`: `1`;

Projetos de saída verificados:

- `ciclo_manual.ndtproj`: SHA-256 `dda7b254f420973a5e78f216a851140d6c5876102f3ff256c2a74d7ac18ff81d`, 3 objetos, 1 camadas, 0 grupos, `path_kind=absolute`;
- `rebase_copia.ndtproj`: SHA-256 `ea71f7630443f83b187d0d5a002ec504c8bbe0790a1f95070ca1e70589241e34`, 2 objetos, 2 camadas, 1 grupos, `path_kind=absolute`;

Fluxos comprovados:

- Abrir Imagem substitui o documento e habilita as ferramentas;
- Salvar Como adiciona `.ndtproj` quando a extensão é omitida;
- o indicador `*` reflete modificações e desaparece após salvar;
- Cancelar preserva o documento atual ao abrir outro projeto;
- Descartar permite trocar de projeto;
- o projeto válido restaura imagem, objetos, camada, grupo e colisão;
- o histórico Undo/Redo é limpo ao trocar de documento;
- imagem ausente abre os dados com aviso e sem imagem;
- hash divergente abre com aviso e carrega a imagem existente;
- imagem ilegível abre os dados com aviso e sem imagem;
- JSON corrompido é rejeitado sem substituir a cena ativa;
- Salvar Como rebaseia a referência de imagem conforme o contrato;
- Cancelar no fechamento mantém a janela aberta;
- Salvar no fechamento persiste e encerra com código `0`.

## Pacote de evidência manual sanitizado

- arquivo: `NeoEng-D-Trace_Etapa4_Manual_Windows_Sanitized_20260802_084517.zip`;
- caminho: `docs/evidence/raw/NeoEng-D-Trace_Etapa4_Manual_Windows_Sanitized_20260802_084517.zip`;
- tamanho: `7292` bytes;
- membros: `10`;
- SHA-256: `d36c7062ae6de1bf3935744f0a764c0f23aca10c65a5e14928e0096ded4e96a3`;
- membros textuais reescritos durante a correção de privacidade: `2`;
- auditoria posterior: `0` caminhos `C:/Users`, `C:\Users` ou ocorrências do usuário local;
- caminhos absolutos locais foram substituídos por tokens explícitos;
- hashes e tamanhos dos arquivos originais foram preservados em `ORIGINAL_FILE_HASHES.json`;
- os projetos produzidos foram validados e tiveram seus hashes registrados sem publicar referências absolutas locais.

## Qualidade comprovada

- testes da suíte funcional na PR: `222` por sistema;
- cobertura global exibida: `52%`;
- fatal Flake8: `0`;
- Black: aprovado;
- isort: aprovado;
- mypy: aprovado em `62` arquivos fonte;
- Linux e Windows aprovados na PR e na `main` pós-merge;
- baseline íntegra antes e depois da validação manual.

## Risco encerrado

`R-002 — Ausência do ciclo Abrir/Salvar completo na UI` está **APROVADO PARA ENCERRAMENTO**, condicionado à integração desta PR documental e ao CI final da `main` após essa integração.

## Riscos residuais

- `R-003` permanece aberto para cobertura integral da interface;
- `R-004` permanece aberto e é o próximo risco da ordem obrigatória;
- `R-005`, `R-006`, `R-007`, `R-008`, `R-011`, `R-012` e `R-013` permanecem abertos em suas etapas próprias;
- cobertura global de aproximadamente `52%` ainda está abaixo da meta final do Plano Mestre;
- permanecem avisos não bloqueantes de depreciação do Poetry e das actions Node 20;
- o diálogo visual de erros e avisos foi considerado genérico durante a validação e permanece como melhoria de usabilidade, sem invalidar o contrato funcional comprovado.

## Limites da aprovação

A aprovação cobre exclusivamente o ciclo Abrir/Salvar da Etapa 4. Ela não declara Undo/Redo completo, exportação de colisões, CLI confiável, geometria completa, segurança integral, cobertura global final, build Windows ou release de produção.

## Rollback

A PR documental pode ser revertida integralmente sem alterar o código funcional já integrado. Um rollback deve remover o relatório, o manifesto e o pacote sanitizado, restaurar a matriz e o workflow e regenerar `baseline_manifest.json` com `python tools/baseline_integrity.py --write`.

## Decisão

**APROVADO — ETAPA 4 APTA AO ENCERRAMENTO FORMAL APÓS A INTEGRAÇÃO DESTE REGISTRO E A VALIDAÇÃO FINAL DA `main`.**

A Etapa 5 não deve iniciar antes da integração desta PR documental e do workflow pós-merge final aprovado.
