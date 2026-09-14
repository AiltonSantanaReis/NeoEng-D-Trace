# Eclipse Warden — Unity delivery

Este pacote é um asset original procedural criado para validar o fluxo de
autoria e exportação do NeoEng-D-Trace. As imagens do usuário orientaram a
linguagem visual; nenhum pixel foi usado como textura.

## Arquivos

- eclipse_warden.glb: entrega principal, glTF 2.0 com texturas embarcadas,
  materiais PBR, skin, esqueleto e animação Idle.
- eclipse_warden.gltf + eclipse_warden.bin + textures/: entrega aberta para
  inspeção e pipelines que preferem recursos separados.
- eclipse_warden.obj + eclipse_warden.mtl: diagnóstico estático sem rig.
- manifest.json e SHA256SUMS.txt: contrato, proveniência e integridade.
- UNITY_IMPORT_GUIDE.md: orientação de importação no Unity.
- godot_preview/: preview executável de importação/renderização real.

## Critério de uso no Unity

Use um importador glTF 2.0 compatível com a versão do projeto. O GLB é a
opção recomendada para primeira importação. O rig está no contrato glTF como
Generic; o mapeamento Humanoid deve ser conferido no Unity e não é declarado
como validado neste pacote.

O manifesto registra explicitamente o que foi verificado neste ambiente e o
que ainda requer um ciclo Unity real autorizado.
