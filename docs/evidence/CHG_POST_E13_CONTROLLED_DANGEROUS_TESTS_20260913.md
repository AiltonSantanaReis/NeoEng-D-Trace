# Registro de mudança — testes potencialmente danosos somente em ambiente controlado

**ID:** CHG-POST-E13-CONTROLLED-DANGEROUS-TESTS-20260913
**Status:** `PASS`
**Data:** 2026-09-13
**Escopo:** `tests/test_integration_sync.py` e runners de evidência de symlink
**Motivação:** cumprir a decisão explícita do proprietário de nunca criar symlink nativamente neste PC e manter a prova real no sandbox.

## Alteração

Os dois testes que precisam criar links simbólicos agora exigem a variável de
ambiente `NEOENG_ALLOW_CONTROLLED_SYMLINK_TEST=1` antes de executar
`Path.symlink_to`. Sem essa autorização controlada, o teste termina como
`SKIP_CONTROLLED_ONLY` antes de tocar o sistema de arquivos do host. O código
de produção em `src/exporters/integration_sync.py` não foi alterado.

O runner Docker aprovado define essa variável somente dentro do container. A
execução segura da suíte Windows utiliza a variável ausente e, portanto, não
cria symlink no host. O skip não encobre uma falha: ele é a barreira de
segurança solicitada e a cobertura comportamental permanece comprovada pelo
runner sandbox.

## Impacto e proteção

- Contrato de segurança de `plan_outputs` preservado.
- Nenhum output, arquivo protegido ou symlink do host é criado pelo pacote
  oficial local.
- A execução controlada continua criando links reais dentro do container e
  valida a rejeição fail-closed do escape e do destino.
- A alteração exige nova requalificação sandbox porque o teste de integração
  mudou; o resultado anterior continua preservado.
- Não há alteração de requisito, threshold, schema, baseline de produto ou
  funcionalidade do editor.

## Verificação exigida

1. teste focado do guard sem a variável, observando `SKIP_CONTROLLED_ONLY`;
2. requalificação do arquivo completo no sandbox com a variável autorizada;
3. suíte oficial completa no host sem essa variável;
4. inspeção final de que nenhum reparse point/symlink foi criado no artefato
   ou no checkout do host.

## Dependências e governança

- [GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md](../GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md)
- [EVD_POST_E13_SYMLINK_SANDBOX_DEFINITIVO_20260913.md](EVD_POST_E13_SYMLINK_SANDBOX_DEFINITIVO_20260913.md)
- [CONTROLE_CONTINUIDADE_ATUAL.md](../CONTROLE_CONTINUIDADE_ATUAL.md)

Os resultados de qualquer execução anterior, inclusive a falha de ambiente do
runner r1, permanecem preservados.
