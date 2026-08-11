# Sanitização de pacotes históricos — 11 de agosto de 2026

## Motivo e autorização

A inspeção recursiva dos artefatos do CI `31452032479` encontrou caminhos de
usuário e metadados de uma integração externa dentro de ZIPs aninhados das
Etapas 2 e 3. O usuário autorizou explicitamente a sanitização controlada em
11 de agosto de 2026. O CI verde não foi aceito antes desta correção.

## Transformação aplicada

- caminhos absolutos de usuário foram substituídos por
  `[LOCAL_PATH_REMOVED]`, preservando os prefixos das linhas de log;
- o bloco `performed_via_github_app`, sem conteúdo funcional da validação, foi
  removido de `metadata/issue_comments.json`;
- autor, corpo, datas, IDs e URLs do comentário auditado foram preservados;
- ZIPs aninhados foram reempacotados e todos os `SHA256SUMS.txt` internos foram
  recalculados;
- os arquivos originais foram copiados para backup temporário antes da troca;
- nenhuma aprovação de merge ou release decorre desta sanitização.

## Cadeia de hashes

| Pacote | Bytes anteriores | Bytes sanitizados | SHA-256 anterior | SHA-256 sanitizado |
|---|---:|---:|---|---|
| Etapa 2 pós-merge | `391665` | `393672` | `809c7b92da3a403e3a75f1f97a7f887c98c6174c798e32326b0cba93a8800e9c` | `3aed50811c30d5f49ed7d53695d9e04a73cbac6135121128ff1ac0519a288ffc` |
| Etapa 2 bruto | `339806` | `339557` | `86dcfadef644fe37dc93a88d7c9b92866a6c944410d0039ff56b9736a3076836` | `37fbff9bc0e07faa60c3c64e0735f7c7466b248875314833fcb446c3e162d7c8` |
| Etapa 3 pós-merge | `2542880` | `2546619` | `f8ce9be99ceae4e9859acff3e9f1f967a5c35edca85288a4b0032e6e8f4caaf0` | `29fa47466b23b426e94dc919e5239fce7143bf73b78c93121890a16b6aa2e270` |
| Etapa 3 bruto | `1753510` | `1755602` | `411981900d5f3c795e0336a4a813bfe4311d25f647cb6a878b8f7239c2311d8f` | `22cbc2d80e5116ef991bdb91b4fc99891d9730db43b05735c408c76f018cbb8b` |

## Validação

- scanner recursivo inicial: `26` ocorrências em cópias aninhadas;
- scanner recursivo após a transformação: zero ocorrências;
- checksums internos verificados: zero divergências;
- comparação recursiva com o backup anterior: `11`, `7`, `71` e `48` folhas
  alteradas nos quatro pacotes, respectivamente; zero membros adicionados ou
  removidos e zero alterações fora das categorias declaradas;
- ZIPs de topo alterados: quatro; ZIPs de topo inalterados: dois;
- teste de regressão: `tests/test_repository_reference_hygiene.py`;
- merge, CI final aceito, pós-merge e release: pendentes.
