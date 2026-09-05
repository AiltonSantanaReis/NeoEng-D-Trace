# P2D-05 — preservação e sincronização documental da candidata

**ID:** P2D05-SYNC-MAIN-20260904. **Versão:** 1.
**Data:** 2026-09-04 (UTC-03).
**Estado:** preservação privada `PASS`; qualificação da integração
`PENDING_EVIDENCE`; revisão humana `PENDING_EVIDENCE`; Ready/merge/release
`BLOCKED`.

## 1. Autoridade, aprovação e escopo

O proprietário aprovou a recomendação profissional após a auditoria de
branches, worktrees, reflogs, regras e governança. A autorização cobre
preservação privada, sincronização de main na candidata, reconciliação
documental, gates e preparação da revisão humana. Não autoriza merge da
PR #170 em main, tag, release, force-push, publicação de históricos privados
ou registro fictício de aceite humano.

Subordinado à Política de Qualidade e Evidências, Governança de Integridade,
decisão P2D-05 e contrato
`C-GLOBAL-ERROR-PRESENTATION-P2D05-2026-09-04`.
Não altera requisitos, thresholds, schemas, código, testes, workflows,
dependências, snapshots binários ou a decisão de privacidade de 2026-08-30.

## 2. Identidade e fronteira Git

- Branch: `Ailton/error-presentation-contract-20260904`.
- Primeiro pai/entrada: `35727d99c7002ad26c3277dff8542f82dad4c3f8`.
- Main incorporada: `b9557e6e85c7b28adf90ea616c171e222c96e84c`.
- Base comum: `9adb66a5ab9cfaabc1703d4b9b225b141473ec52`.
- O commit que introduz este relatório é o merge documental de sincronização,
  não um commit-fonte novo de comportamento nem a integração da PR em main.

A auditoria comparou 138 branches locais, 135 branches remotas vivas e
31 worktrees antes desta operação. A candidata tinha 0 commits à frente/atrás
do remoto; main local tinha 75 commits de atraso e zero exclusivos.
Dez arquivos documentais/manifesto vieram de main. Os conflitos textuais eram
README, CHANGELOG e baseline_manifest. Os dois históricos foram preservados;
não se escolheu uma versão inteira de documentação para apagar a outra.
O manifesto deve ser recalculado com o gerador oficial e conferido contra
a união das entradas dos dois pais, sem remoção para obter PASS.

## 3. Preservação privada comprovada

Quinze commits da linha até `da227f0` são privados por decisão explícita de
sanitização. O estado funcional foi publicado em `0228af2`, ancestral de
main; não há diferença entre essas duas árvores em src, tests, dependências,
packaging ou .github. A linha original não deve receber push.

O commit `f9f39ed354fb8ea886c0976c58150d3e955a42c0` permanece preservado
em sua branch/worktree e separado da PR. Seu arquivo antigo contém 1.046
linhas e 69 funções test_; está ausente de main. Não foi executado nem
classificado como equivalente a testes atuais. Disposição: avaliação futura
separada `PENDING_EVIDENCE`, sem reabrir R-004 pelo título do commit.

Quatorze commits acessíveis apenas pelo reflog foram ancorados em referências
locais privadas, junto com os dois HEADs acima. Um bundle completo de 16
referências foi criado, verificado, restaurado em repositório bare vazio e
submetido a `git fsck --full --strict --no-reflogs --no-dangling`, retorno 0.
Bundle: 58.742.148 bytes, SHA-256
`d79ae17516986973cfe2a209d4beedceac88ce114acc89968a4413c1c33578b2`.
O bundle e a restauração ficam apenas no armazenamento privado local do Git;
não são artefatos publicáveis. Não há proteção contra perda do disco sem
uma cópia privada externa. Nenhuma limpeza foi executada.

O inventário Git avisou sobre 164 arquivos temporários antigos, classificados
como garbage, total de 4,75 GiB. Eles foram preservados; esse aviso não foi
silenciado nem tratado como prova de corrupção dos objetos restaurados.

## 4. Evidência de entrada — não transferível ao novo SHA

[CI 33932398814](https://github.com/AiltonSantanaReis/NeoEng-D-Trace/actions/runs/33932398814):
workflow_dispatch no SHA `35727d9`; Linux e Windows SUCCESS. Isso não testa
o merge documental descendente ou a integração da PR em main.

Windows: Python 3.11.9, plataforma reportada Windows-10-10.0.26100-SP0;
194/194 arquivos, 1.956 testes, zero falhas, erros ou skips. Cobertura:
92,70% linhas e 85,20% branches; Linux: 92,70% linhas e 85,19% branches.
Os dois casos `test_plan_rejects_symlink_escape` e
`test_plan_rejects_symlink_destination` passaram nominalmente no JUnit.

[Artefato Windows 9959211055](https://github.com/AiltonSantanaReis/NeoEng-D-Trace/actions/runs/33932398814/artifacts/9959211055):
64.267.637 bytes; digest informado pelo serviço:
`e4c6895ea2e727e6e563ce207bd035d301b6a5acd72e06a06c1a63b028549bd4`.
JUnit `044-test_integration_sync.xml`: 4.218 bytes, SHA-256
`491d30063fbf0fc1a4d4f5496b10b51a30a6a242691391338bf98d8c58220d6e`.
Summary Windows: 157.189 bytes, SHA-256
`8bb4e7d853b4f8b766fd66f7143c0c210ee249aaa4d986a22b45b6afc591be55`.
Cópias locais foram preservadas; retenção remota configurada: 30 dias.

Qualificação local de entrada: 1.954 passed e dois skips por privilégio
symlink, sem atribuir isso ao Windows remoto. Build/smoke/ZIP passaram naquele
SHA, com CPU fallback declarado. A primeira invocação do coletor de digests
em Windows PowerShell falhou por Get-FileHash indisponível; log preservado.
O mesmo coletor passou no PowerShell 7. Esse erro não foi uma falha do CI.

## 5. Procedimento da sincronização e gates requeridos

1. Fetch de origin sem prune/tags; inventário e verificação de HEADs.
2. Referências privadas com criação condicional; bundle completo; restauração
   isolada e fsck estrito. Nenhum push de referências privadas.
3. Worktree detached novo em 35727d9; `git merge --no-commit --no-ff`
   de b9557e6; resolução explícita dos conflitos; revisão dos documentos
   vivos, mantendo snapshots e a fronteira do contrato.
4. Poetry 2.4.1, Python 3.11.9 e venv independente, sincronizados pelo lock.
5. Revisão do staged diff, fronteira sem mudanças de produto, baseline e
   evidências; commit do merge de sincronização autorizado.
6. No novo SHA limpo: lock/sync, baseline, evidências, compilação, flake8,
   Black, isort, mypy, pip-audit, Bandit, suíte Windows completa com cobertura,
   política integrada, Stage 4B.5, gate legado formal, build, smoke e ZIP.
7. Push explícito somente da candidata depois dos gates locais; CI
   Linux/Windows e symlinks conferidos no SHA novo. PR mantida em rascunho.

Os resultados dos itens 5–7 devem ser publicados como recibos e artefatos
vinculados à execução real, não preenchidos antecipadamente neste snapshot.
Conflito ou falha exige registro e investigação; não reduzir os gates.

## 6. Roteiro para revisão humana — ainda não realizada

O pacote de revisão deve identificar SHA, build, ambiente/DPI/resolução,
comandos, capturas Qt reais, hashes e logs de encerramento. Capturas ilustrativas,
imagens geradas por IA ou provas antigas não são aceitas como execução atual.

O proprietário deve avaliar a candidata resultante, não o pai 35727d9:

- Caneta/edição: rejeição inválida com prévia/modelo/histórico preservados;
  fechamento válido, cancelamento, Undo/Redo e recuperação da edição.
- Gizmo e painéis: seleção/pré-condição inválida, mensagem acionável,
  operação válida posterior e ausência de mutação parcial.
- Layers: criação/edição inválida, contexto e seleção preservados.
- Apresentação: canal apropriado, mensagem, ação, código e estado preservado;
  persistência quando exige ação e detalhes técnicos sem dados pessoais.
- Mouse e teclado separadamente; foco, localização, contraste, quebra de
  texto, acessibilidade e retorno ao fluxo.

Registrar PASS, FAIL ou PENDING_EVIDENCE por caso. Somente o proprietário
pode confirmar a revisão humana; autorização para preparar este pacote não
é aprovação visual. C12 de 6ede2f6 e aceites anteriores não aprovam este SHA.

## 7. Decisão e rollback

Preservação/restauração: PASS no escopo descrito. Produto e contrato global:
IN_PROGRESS. Requalificação da integração e revisão humana: PENDING_EVIDENCE.
Ready for review, merge da PR, tag e release: BLOCKED.

Rollback, se necessário e autorizado: reversão específica do merge de
sincronização sobre seu primeiro pai, preservando os dois históricos.
Nunca apagar evidências, refs privadas ou arquivos untracked, nem executar
reset destrutivo ou reescrita da branch publicada.
