# Reconciliação dos gates de release — 17 de agosto de 2026

## Escopo

Este documento é a decisão vigente para o projeto. Ele reconcilia os gates
operacionais sem reescrever evidências históricas de etapas anteriores. Os
marcadores `RELEASE_APPROVED=NO` preservados em relatórios de etapas continuam
representando a decisão daquele fechamento técnico, não um bloqueio atual da
release já publicada.

## Decisões do proprietário

- `R-014` — assinatura de código: **não é requisito nem bloqueio de release**.
  A ausência de assinatura continua declarada nos artefatos, mas não impede
  validar, gerar, publicar ou comercializar o projeto. Assinatura pode ser
  adicionada futuramente como melhoria opcional.
- `R-015` — formalização jurídica, licenciamento e atribuições: **não é gate
  obrigatório de engenharia ou de publicação do projeto**. O repositório
  continua sem alegar certificação jurídica; decisões formais futuras podem
  ser registradas quando forem necessárias.
- `R-016` — builder MSI: **revisado e aprovado**. WiX `4.0.6`, builds
  determinísticos, instalação, upgrade, reparo, execução e remoção permanecem
  validados. Não há pendência de governança bloqueante neste risco.
- Execução dinâmica de Godot/Unity no CI: **não é requisito**. As engines reais
  são validadas por fixtures e execuções locais reproduzíveis; o CI continua
  responsável pelos gates que consegue executar de forma suportada.

## Reconciliação da baseline

A baseline atual foi verificada depois das alterações documentais:

```text
.\.venv\Scripts\python.exe tools\baseline_integrity.py --verify
Baseline verified: 1268 files
```

Assim, a observação anterior de que a baseline ainda precisava ser regenerada
fica encerrada para o estado atual. O resultado foi obtido por verificação real,
sem remover arquivos do manifesto, relaxar o verificador ou transformar erro em
sucesso.
## Testes de symlink

Na execução não elevada da suíte completa, os dois testes de symlink foram
classificados como `skip` porque a política de permissões do Windows não
permitiu criar os links naquele contexto. Isso é uma limitação do ambiente da
execução não elevada, não um teste pendente nem uma aprovação artificial.

O proprietário executou os dois testes em terminal administrativo local com o
comando focal registrado no fechamento da Etapa 9. A transcrição fornecida
registrou `2 passed, 0 skipped`, com os testes de rejeição de symlink de escape
e de destino. O log normalizado, sua proveniência e o SHA-256 permanecem
versionados em `docs/evidence/artifacts/native-stage9-2026-08-17/`.

- `SYMLINK_TESTS_OWNER_ADMIN=PASS`
- `SYMLINK_TESTS_UNRESOLVED=0`
- `NON_ELEVATED_SKIP_REASON=WINDOWS_PERMISSION_ONLY`

## Estado atual

- `CURRENT_RELEASE_POLICY_BLOCKERS=0`
- `R014_RELEASE_BLOCKER=NO`
- `R015_RELEASE_BLOCKER=NO`
- `R016_RELEASE_BLOCKER=NO`
- `DYNAMIC_ENGINE_CI_REQUIRED=NO`
- `BASELINE_CURRENT=VERIFIED_1268_FILES`
- `SYMLINK_TESTS_OWNER_ADMIN=PASS`
- `SYMLINK_TESTS_UNRESOLVED=0`
- `NON_ELEVATED_SKIP_REASON=WINDOWS_PERMISSION_ONLY`
- `V0.2.0_RELEASE_STATUS=PUBLICADA`

Os gates técnicos que permanecem aplicáveis continuam sendo a integridade da
árvore, os testes correspondentes ao candidato, manifestos e hashes, higiene
de privacidade e validação funcional real do escopo alterado.
