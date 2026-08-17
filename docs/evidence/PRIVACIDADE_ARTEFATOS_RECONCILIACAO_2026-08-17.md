# Reconciliação de privacidade dos artefatos — 17 de agosto de 2026

## Motivo

A auditoria independente encontrou identificadores de host e processo em logs históricos das etapas 5 e 8. A integridade de hashes não verificava privacidade; portanto, o estado anterior não podia ser declarado como sanitizado.

## Correção aplicada

- Os sanitizadores das etapas 5 e 8 passaram a redigir canais LicenseClient, PId, process Id, WindowsEditor, Player connection, timestamps, endpoints locais e depuração.
- 83 artefatos textuais versionados foram reprocessados com o sanitizador fail-closed já utilizado pela Etapa 10.
- Nenhum PNG, fixture de entrada ou código de engine foi alterado; somente relatórios/logs textuais e seus manifestos de hash foram atualizados.
- Os manifestos foram regenerados por tools/evidence_integrity.py --rewrite, nunca por edição manual de SHA-256.

## Verificação

- Teste de privacidade: tests/test_evidence_privacy.py.
- Evidence integrity: 35 manifests validated.
- O teste fail-closed não encontrou caminhos pessoais, canais de licença identificáveis, PId numérico, process Id numérico, identidade WindowsEditor ou linhas Player connection não redigidas.

## Limitação honesta

Os logs versionados após esta correção são evidências sanitizadas derivadas das execuções originais. Identificadores removidos não podem mais ser usados para depuração local; a proveniência estrutural e os hashes dos bytes publicados permanecem verificáveis.

PRIVACY_ARTIFACT_RECONCILIATION=PASS
UNREDACTED_HOST_DATA_IN_VERSIONED_TEXT_ARTIFACTS=0
MANIFESTS_REGENERATED=YES
RAW_ENGINE_IDENTIFIERS_RETAINED=NO
