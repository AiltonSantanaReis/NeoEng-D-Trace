# Identidade Visual e Atribuições — NeoEng-D-Trace

**Status:** ATIVO FORNECIDO PELO PROPRIETÁRIO; APROVADO PARA USO NO PROJETO

## Ícone proposto

O proprietário declarou que o ícone foi gerado por IA e autorizou seu uso no
projeto. Pela decisão do proprietário, ele pode ser tratado como ativo oficial
do projeto, sem exigir aprovação adicional de terceiros para esta etapa. Esta
declaração não é parecer jurídico nem prova independente de titularidade ou de
ausência de direitos de terceiros.

O arquivo recebido e versionado em `assets/branding/neoeng-d-trace-icon-source.png` é um PNG paletizado de `878×810`, modo `P`, com SHA-256
`17dde3dc0d616cef8927403cb3b2b15aa818960776605eb2a7d2b99b8e5adedc`. Para Windows, a
integração técnica usa o `.ico` derivado `assets/branding/neoeng-d-trace-icon.ico`,
com canvas quadrado, transparência preservada e múltiplas resoluções `16`, `32`,
`48`, `64`, `128` e `256` pixels. O SHA-256 do derivado é
`6120fd1376d3976e6f089ef1bd6da677280234d58ab09add189ce97f4abb3b91`.

## Integração realizada

- o arquivo-fonte autorizado já está versionado;
- o `.ico` derivado é gerado por `tools/generate_app_icon.py` e está versionado;
- o runtime Qt aplica o ícone à `QApplication` e à `MainWindow`;
- o PyInstaller inclui o ativo no bundle e aplica o ícone ao executável GUI;
- o WiX referencia o mesmo ativo no atalho do menu Iniciar;
- os contratos automatizados verificam transparência, resoluções, runtime e WiX;
- registrar SHA-256 dos ativos no manifesto de release;
- incluir a atribuição em `NOTICE` ou documento equivalente;
- repetir os testes de build, instalação e desinstalação após cada mudança de
  empacotamento.

## Trâmites futuros

O ícone pode acompanhar a primeira release oficial e não bloqueia a publicação
por decisão do proprietário. Registros formais de atribuição, licenciamento,
marcas e outros trâmites de `R-015` podem ser complementados em futuras versões
conforme demanda. A imagem versionada e seu SHA-256 permanecem a evidência
reprodutível do ativo utilizado.
