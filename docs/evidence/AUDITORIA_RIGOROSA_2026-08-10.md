# Evidência — auditoria rigorosa e remediação de 2026-08-10

## Identificação

- base remota auditada: `6c4bcb3d945405a4615a4d6551247d1b01ce79f1`;
- branch local: `docs/etapa-5-encerramento-pos-merge`;
- ambiente: Windows build 26200, Python 3.11.9, Poetry 2.4.1;
- estado GitHub histórico: PR `#27` mesclada; CI pós-merge `#84` aprovado;
- publicação corretiva: commit `236eefd41ee51c7085e21d52fc80074eede0a793`, PR draft `#28`;
- CI corretivo: run `31422290050`, Linux `93565684359` e Windows `93565684441` em `success`.

## Parecer inicial

A auditoria inicialmente bloqueou o encerramento por vulnerabilidades no Pillow,
26 falhas brutas na suíte legada preservada, falso sucesso da CLI, atlas com
metadados fora dos limites, exportação do painel de colisão sem gravação real,
ausência de branch coverage, mypy incompleto, APIs duplicadas e evidência
temporária.

## Remediações

| Achado | Estado local | Evidência |
|---|---|---|
| F-01 Pillow 12.0.0 vulnerável | CORRIGIDO | Pillow 12.3.0 no projeto e lock; `pip-audit` sem vulnerabilidades conhecidas |
| F-02 26 falhas legadas não declaradas | RECONCILIADO | 196 testes executados; 26 assinaturas previstas, 26 correspondências, zero inesperadas e zero ausentes |
| F-03 atlas fora dos limites | CORRIGIDO | crop por retângulos alocados; testes de transparência e rotação |
| F-04 CLI com falso sucesso | CORRIGIDO | falta de `--object-id` retorna `1` e não cria saída |
| F-05 painel de colisão sem efeito | CORRIGIDO | JSON atômico real, sucesso pós-gravação e cancelamento sem sucesso |
| F-06 CI sem branches/threshold | MITIGADO | branches medidos e piso incremental bloqueante de 62%; meta final permanece aberta |
| F-07 mypy não verificava corpos | CORRIGIDO | `check_untyped_defs` obrigatório; zero erros em 65 arquivos |
| F-08 dívida de lint | CORRIGIDO | configuração alinhada ao Black; imports, código morto, E402 e linhas longas corrigidos; Flake8 integral com zero achados |
| F-09 evidência temporária | MITIGADO | relatório e reconciliação versionáveis; retenção CI elevada para 30 dias |
| F-10 LayersPanel/APIs duplicadas | CORRIGIDO NO ESCOPO | painel integrado; lasso legado virou alias canônico; SAT compatível coberto |
| F-11 JSON genérico sem colisões | ABERTO COMO R-005 | contrato não foi mascarado; Etapa 6 continua responsável pelo schema |
| F-12 instrução `requirements.txt` inexistente | CORRIGIDO | mensagem orienta `poetry install` |
| F-13 PIL incompatível com ViewProcessor | CORRIGIDO | conversão PIL L/RGB/RGBA para ndarray canônico e QImage testada |

## Gates locais finais

- contratos documentais: `19 passed`;
- suíte oficial: `532 passed`;
- cobertura combinada de linhas e branches: `62.18%`;
- piso CI: `62%`;
- suíte legada: `196` executados, `26` falhas brutas reconciliadas,
  `0` inesperadas, `0` ausentes;
- mypy estrito: `0` erros em `65` arquivos-fonte;
- `pip-audit`: nenhuma vulnerabilidade conhecida no ambiente resolvido;
- Bandit alta severidade: zero achados;
- flake8 integral bloqueante: zero achados;
- baseline: `272` arquivos;
- build wheel e smoke instalado: aprovados;
- wheel: `neoeng_d_trace-0.2.0-py3-none-any.whl`; SHA-256
  `4A0F5CEB0094912EA3595052A38C60A200125C01888B7D228A5F0BE2C2547996`;
- smoke isolado fora do checkout: entry point em `site-packages` e `pip check` aprovados;
- fluxo headless pelo wheel: projeto válido gerou JSON (1092 bytes), GLB (996 bytes, magic `glTF`) e round-trip `.ndtproj` (974 bytes); entrada sem polígonos foi rejeitada;
- `git diff --check`: aprovado.

## Validação remota

- PR: `#28`, mesclada em `main`;
- HEAD final da PR: `ab71e148c0b7441bd36f489472856d0b4adfaa1e`;
- CI final da PR: `31422901244`, conclusão `success`;
- merge: `56533b65f81d21fd9c762aa10c0d3e6747d742ca`;
- CI pós-merge: `31423386971`, conclusão `success`;
- Linux: job `93569241989`, artefato `9076253153`, digest `sha256:b62f58240eb2f015d3f1906668e3402847668cab7ee6daa083f6a44fa1fd3443`;
- Windows: job `93569242024`, artefato `9076283257`, digest `sha256:8ea7e557aa1eedf7a442962a49cee8a0cf778c02c678e72e75f05adc61438ef7`;
- aviso não bloqueante: actions baseadas em Node.js 20 foram forçadas pelo GitHub para Node.js 24.

## Decisão

**ETAPA 5 FORMALMENTE ENCERRADA.**

Esta decisão não aprova release, não fecha os riscos ainda abertos das Etapas
6–14 e não declara as metas finais de cobertura atingidas. A PR `#28`, o merge
e o CI pós-merge do SHA integrado foram comprovados; a Etapa 6 não foi iniciada.
