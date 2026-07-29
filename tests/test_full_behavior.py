import os
import shutil
import sys
import tempfile
import unittest

# --- Configuração do Ambiente Qt (Headless) ---
from PySide6.QtWidgets import QApplication

# Garante que uma instância do QApplication exista
app = QApplication.instance()
if not app:
    app = QApplication(sys.argv)

# --- Configuração de Importação ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

# --- Importações do Projeto ---
try:
    from src.core.commands import AddPolygonCommand, CommandManager
    from src.exporters.json_exporter import export_scene_metadata
    from src.models.scene import Scene
    from src.physics.physics_manager import PhysicsManager
except ImportError as e:
    print(f"❌ Erro crítico de importação: {e}")
    sys.exit(1)


class TestAppBehavior(unittest.TestCase):
    """
    Simula o comportamento do usuário e a integridade dos dados da aplicação.
    """

    def setUp(self):
        """Prepara uma cena limpa antes de cada teste."""
        self.scene = Scene()
        self.scene.cmd = CommandManager()
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Limpa arquivos temporários após cada teste."""
        shutil.rmtree(self.test_dir)

    def test_01_command_undo_redo_flow(self):
        """
        🔄 TESTE DE COMPORTAMENTO: Desfazer/Refazer
        """
        print("\n[Behavior] Testando fluxo de Undo/Redo...")

        initial_count = len(self.scene.objects)
        self.assertEqual(initial_count, 0, "Cena deveria começar vazia")

        poly_points = [(0, 0), (100, 0), (100, 100), (0, 100)]

        # Cria o comando
        cmd = AddPolygonCommand(poly_points)

        # Executa (Scene é passada aqui)
        self.scene.cmd.execute(cmd, self.scene)

        # Verifica adição
        self.assertEqual(
            len(self.scene.objects), 1, "Objeto deveria ter sido adicionado via comando"
        )

        # Undo
        self.scene.cmd.undo(self.scene)
        self.assertEqual(len(self.scene.objects), 0, "Objeto deveria sumir após Undo")

        # Redo
        self.scene.cmd.redo(self.scene)
        self.assertEqual(len(self.scene.objects), 1, "Objeto deveria voltar após Redo")

        # CORREÇÃO AQUI: Pegamos o ID atual que está na cena,
        # pois o Redo pode ter gerado um UUID novo.
        current_ids = list(self.scene.objects.keys())
        new_id = current_ids[0]
        restored_obj = self.scene.objects[new_id]

        # Verifica se a geometria está intacta
        self.assertEqual(restored_obj.polygon, poly_points)

        print("✅ Fluxo de Undo/Redo funcionou perfeitamente.")

    def test_02_scene_selection_logic(self):
        """
        🖱️ TESTE DE COMPORTAMENTO: Seleção
        """
        print("[Behavior] Testando lógica de seleção...")

        # Adiciona objetos manualmente
        id1 = self.scene.add_polygon([(0, 0), (10, 10), (0, 10)])
        id2 = self.scene.add_polygon([(50, 50), (60, 60), (50, 60)])

        # Seleciona o primeiro
        self.scene.select_object(id1)
        self.assertEqual(self.scene.selected_id, id1)

        # Seleciona o segundo
        self.scene.select_object(id2)
        self.assertEqual(self.scene.selected_id, id2)

        # Deselecionar
        self.scene.selected_id = None
        self.assertIsNone(self.scene.selected_id)

        print("✅ Lógica de seleção validada.")

    def test_03_export_pipeline_integrity(self):
        """
        📤 TESTE DE INTEGRAÇÃO: Pipeline de Exportação
        """
        print("[Integration] Testando exportação de metadados...")

        id1 = self.scene.add_polygon([(10, 10), (20, 10), (20, 20), (10, 20)])

        # Exporta
        metadata = export_scene_metadata(self.scene)

        # Verifica chave 'sprites'
        self.assertIn("sprites", metadata, "JSON deve ter chave 'sprites'")

        # Procura nosso objeto na lista
        found_sprite = None
        for sprite in metadata["sprites"]:
            if sprite["id"] == id1:
                found_sprite = sprite
                break

        self.assertIsNotNone(
            found_sprite, "Objeto criado não apareceu na lista de sprites exportados"
        )

        # Verifica geometria
        poly_exportado = found_sprite["polygon_in_image"]
        self.assertEqual(len(poly_exportado), 4)

        print("✅ Dados de exportação gerados corretamente.")

    def test_04_physics_integration_in_scene(self):
        """
        ⚛️ TESTE DE INTEGRAÇÃO: Cena + Física
        """
        print("[Integration] Testando sincronia Cena -> Física...")

        phys_man = PhysicsManager()
        self.scene.add_polygon([(0, 0), (100, 0), (100, 100), (0, 100)])

        count = 0
        for oid, obj in self.scene.objects.items():
            phys_man.add_body(obj.polygon, metadata={"id": oid})
            count += 1

        self.assertEqual(count, 1)
        self.assertEqual(len(phys_man.objects), 1)

        print("✅ Sincronização Cena-Física validada.")


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 EXECUTANDO SUITE DE TESTES FINAL (v3)")
    print("=" * 60)
    unittest.main(verbosity=2)
