# Evidência pós-E13 — build portátil r5 com fallback CuPy e retry atômico

**ID da feature:** `AUD-POST-E13-BUILD-CUPY-ATOMIC-20260913`  
**Status documental:** `PASS`  
**Data:** 2026-09-13  
**Commit de origem:** `98ee5b4ea437d35b89f8767a03e26769636f5f99`  
**Branch:** `Ailton/audit-post-e13-scenario-editor-20260912`

## Escopo e segurança

Esta é a build limpa posterior às mudanças de logging do fallback opcional
CuPy, retry de `os.replace` do atlas e empacotamento de `tzdata`. A
[governança](../GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md)
foi lida antes da etapa. O script `scripts/build_windows.ps1` foi executado
em clone temporário sem alterações, e a saída foi copiada para uma nova
release estável externa, sem sobrescrever a r4.

Nenhum symlink foi criado no host e nenhum shutdown nativo foi executado. O
smoke normal de ciclo de vida da aplicação (abrir, salvar estado e fechar)
foi permitido e observado.

## Build e empacotamento

```text
scripts/build_windows.ps1
OutputRoot=build/release-post-e13-cupy-atomic-20260913-r5
Python=canonical project Python 3.11.9
```

Resultado observado: PyInstaller `6.22.0` concluiu com `BUILD_EXIT=0`,
provenance `PASS`, pacote portátil com 1003 arquivos, executável de
10.883.963 bytes e ZIP de 143.317.006 bytes.

| Artefato externo | Tamanho | SHA-256 |
|---|---:|---|
| `portable/NeoEng-D-Trace/NeoEng-D-Trace.exe` | 10.883.963 | `1D3AC2A89C35F807AEC9E707310F410FC71785ABF463E9A65DF6ACFBA3FAF403` |
| `NeoEng-D-Trace-0.3.0-win64-portable.zip` | 143.317.006 | `63A71E5501F5165A4E7A90AD2161605C4DB4631B2DF510F1F36BC3BC203BD713` |

O provenance da release tem SHA-256
`BEC7C21C6F1E76B4B7F156B68CC564A783733A9C0403D1615B4961CC0D83CE2B` e o
manifest da release tem SHA-256
`5913897B907870FFE057D477C3F21B0178ADACF9AAC4D9BF3AD09E75F5014218`.

## Smoke e ciclo de vida real

O smoke portátil retornou `SUCCESS` em todos os 11 checks: versão CLI,
entrada versionada, projeto headless, JSON/GLB, perfis e releases Godot e
Unity, GUI abrir/fechar e diretório de estado do usuário. O relatório tem
SHA-256 `6E8F5F7D139E15326017DEEABC7EFC30921D0D4762A284EFFB6F335BB2CE23B7`.

A validação GUI observou janela visível com idioma inicial `pt` e a sequência:

```text
session.start SUCCESS
validation.mode SUCCESS
application.opened SUCCESS
document.close_requested SUCCESS
application.state.saved SUCCESS
application.closed SUCCESS (exit_code=0)
session.summary SUCCESS (failure_count=0)
```

O JSONL correspondente tem SHA-256
`273A7D2D6A1DB2F99839C993E07CDD2671FA57585137359143F9EB0AFDB67190`.

## Qualificação de warnings e CuPy

O hook de `tzdata` foi carregado e não houve `Hidden import tzdata not found`.
Também não houve warning de `cupy`/`cupyx`; CuPy continua opcional e não é
embutido no pacote portátil. A decisão técnica do ADR mantém o fallback CPU
oficial e não promove a dependência CUDA ao produto.

O relatório PyInstaller contém avisos opcionais de plataforma/importação que
não são falhas do pacote Windows. A versão bruta foi preservada fora do
repositório com SHA-256
`51375AAA895ABF18BC462C0000A6ECFD0D080F0983E7FEE2AEF989CCA9D6246A`; a
versão rastreada remove somente o caminho local e tem SHA-256
`E19D399FBDF1E1639BBA17FB0EDFF0F5C1298DC5440222BCA61961A83D45CBC2`.

## Limitações e reexecução

Esta evidência comprova build, empacotamento e ciclo de vida portátil. Não
substitui a evidência sandbox definitiva de symlink nem qualifica licensing,
shutdown ou soak limpo do Unity nativo. Reexecutar a build após alteração de
código, dependência, spec, governança de empacotamento ou contrato de release;
os testes de symlink permanecem sujeitos à regra específica do sandbox.

