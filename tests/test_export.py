import pytest
from src.models.scene import Scene
from src.exporters.json_exporter import export_scene_metadata
from src.exporters.gltf_exporter import export_scene_to_gltf
from src.exporters.sprite_exporter import export_sprite
from src.exporters.atlas_exporter import build_atlas
import tempfile
import os

@pytest.fixture(scope="module")
def temp_scene():
    scene = Scene()
    # Adiciona dois polígonos simples
    scene.add_polygon([(0,0), (10,0), (10,10), (0,10)])
    scene.add_polygon([(20,20), (30,20), (30,30), (20,30)])
    return scene

def test_export_json_metadata(temp_scene):
    metadata = export_scene_metadata(temp_scene)
    assert "sprites" in metadata
    assert len(metadata["sprites"]) == 2
    # Testa exportação para arquivo
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        path = tmp.name
    from src.exporters.json_exporter import save_json_metadata
    save_json_metadata(metadata, path)
    assert os.path.exists(path)
    os.remove(path)

def test_export_gltf(temp_scene):
    # Exporta GLTF para arquivo temporário
    with tempfile.NamedTemporaryFile(suffix=".glb", delete=False) as tmp:
        path = tmp.name
    export_scene_to_gltf(temp_scene, path)
    assert os.path.exists(path)
    os.remove(path)

def test_export_sprite(temp_scene):
    # Exporta Sprite para arquivo temporário
    # Precisa de uma imagem na cena
    import numpy as np
    temp_scene.image = np.zeros((32,32,3), dtype=np.uint8)
    oid = list(temp_scene.objects.keys())[0]
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        path = tmp.name
    export_sprite(oid, temp_scene, path)
    assert os.path.exists(path)
    os.remove(path)

def test_export_atlas(temp_scene):
    # Exporta Atlas usando build_atlas
    import numpy as np
    temp_scene.image = np.zeros((32,32,3), dtype=np.uint8)
    items = []
    for oid in temp_scene.objects:
        img = export_sprite(oid, temp_scene, None)
        items.append((oid, img))
    with tempfile.TemporaryDirectory() as out_dir:
        results = build_atlas(items, out_dir, base_name="atlas_test")
        # Verifica se pelo menos um atlas foi gerado
        found = False
        for r in results:
            if os.path.exists(r["atlas_path"]):
                found = True
        assert found
