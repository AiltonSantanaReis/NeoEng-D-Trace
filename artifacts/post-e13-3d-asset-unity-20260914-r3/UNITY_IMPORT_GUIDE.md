# Guia de importação Unity — Eclipse Warden

1. Instale ou habilite um importador glTF 2.0 compatível com a versão Unity
   usada pelo projeto.
2. Importe eclipse_warden.glb como primeira opção; use o par
   eclipse_warden.gltf/eclipe_warden.bin somente para diagnóstico aberto.
3. Confirme escala em metros, orientação Y-up e que os objetos aparecem
   separadamente no hierarchy/outliner.
4. No import de rig, comece com Animation Type Generic. Só altere para
   Humanoid depois de verificar manualmente quadril, coluna, cabeça, braços,
   mãos, pernas e pés.
5. Verifique os mapas Base Color, Metallic/Roughness e Normal nos materiais.
   O material Energy_Rune também usa o mapa emissivo.
6. Reproduza Idle e verifique deformação de capa, ombreiras e espada.
7. Para URP/HDRP, remapeie os mapas para o shader lit do pipeline e preserve
   emissão da Energy_Rune.

Este guia é um contrato operacional, não uma prova de importação Unity.
O campo compatibility.unity.status do manifesto permanece PENDING_EVIDENCE
até a execução real no Unity.
