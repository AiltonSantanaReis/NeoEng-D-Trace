import os
import sys
import unittest
from unittest.mock import MagicMock, patch

import cv2
import numpy as np

from src.core.commands import CommandStatus

# Adiciona o diretório raiz ao path para importação
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

# Tenta importar o módulo. Se falhar por dependências de utils, mockamos antes.
try:
    from src.tools import auto_detect
except ImportError:
    # Se os utils não existirem, criamos mocks para permitir a importação do auto_detect
    sys.modules["src.tools.mask_utils"] = MagicMock()
    sys.modules["src.tools.edge_utils"] = MagicMock()
    sys.modules["src.tools.smoothing"] = MagicMock()
    from src.tools import auto_detect


class TestAutoDetect(unittest.TestCase):
    """
    Testes unitários para o módulo de detecção automática.
    """

    def setUp(self):
        # 1. Cria uma imagem sintética (100x100) com um quadrado branco no centro
        # Fundo preto (0)
        self.image = np.zeros((100, 100), dtype=np.uint8)
        # Quadrado branco (255) de (30,30) a (70,70)
        cv2.rectangle(self.image, (30, 30), (70, 70), 255, -1)

        # Converte para BGR para simular imagem carregada pelo OpenCV
        self.image_color = cv2.cvtColor(self.image, cv2.COLOR_GRAY2BGR)

    @patch("src.tools.auto_detect.rdp_simplify")
    def test_detect_polygons_basic(self, mock_simplify):
        """
        Testa o modo 'basic' de detecção.
        """
        # Mock do simplificador para retornar os pontos sem alteração (pass-through)
        # O RDP recebe pontos e epsilon
        mock_simplify.side_effect = lambda pts, eps: pts

        # Executa detecção
        # Ajustamos min_area para garantir que nosso quadrado seja
        # detectado (40x40=1600).
        result = auto_detect.detect_polygons(
            self.image, mode="basic", min_area=100.0, rdp_epsilon=1.0
        )

        # Verificações
        self.assertEqual(result.feedback["status"], "ok")
        self.assertEqual(result.feedback["mode"], "basic")

        polygons = result["polygons"]
        self.assertEqual(len(polygons), 1, "Deveria detectar exatamente 1 quadrado")

        poly_data = polygons[0]
        self.assertIn("polygon", poly_data)
        self.assertIn("bbox", poly_data)

        # Verifica área aproximada (deve ser próxima de 1600)
        self.assertGreater(poly_data["area"], 1500)
        self.assertLess(poly_data["area"], 1700)

    @patch("src.tools.auto_detect.threshold_adaptive")
    @patch("src.tools.auto_detect.close_small_gaps")
    @patch("src.tools.auto_detect.curvature_adaptive_simplify")
    def test_detect_polygons_perfect(self, mock_curve, mock_close, mock_thresh):
        """
        Testa o fluxo do modo 'perfect' (simulado).
        """
        # Configura os mocks para passar o fluxo sem erro
        # Mock thresh devolve a própria imagem binária
        mock_thresh.return_value = self.image
        mock_close.return_value = self.image

        # O curvature_simplify precisa retornar uma lista de tuplas (int, int)
        # Vamos simular um quadrado simples
        mock_curve.return_value = [(30, 30), (70, 30), (70, 70), (30, 70)]

        result = auto_detect.detect_polygons(self.image, mode="perfect", min_area=100.0)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["quality_metrics"]["vertex_count"], 4)

    def test_detect_result_behavior(self):
        """Testa o objeto customizado DetectResult."""
        data = [{"id": 1}]
        feedback = {"time": "10ms"}
        res = auto_detect.DetectResult(data, feedback)

        # Acesso como lista
        self.assertEqual(res[0]["id"], 1)
        # Acesso como dict
        self.assertEqual(res["feedback"], feedback)
        self.assertEqual(res.get("polygons"), data)

    @patch("src.core.commands.CompositeCommand")
    @patch("src.core.commands.CreateObjectCommand")
    def test_detect_and_create_objects_integration(
        self, MockCreateCommand, MockCompositeCommand
    ):
        """Testa integração atômica com Scene e CommandManager."""
        mock_scene = MagicMock()
        mock_scene.image = self.image
        mock_scene.cmd = MagicMock()

        mock_cmd_instance = MockCreateCommand.return_value
        mock_cmd_instance.object_id = "new-obj-uuid"
        mock_composite = MockCompositeCommand.return_value
        mock_scene.cmd.execute.return_value = MagicMock(
            status=CommandStatus.APPLIED,
            changed=True,
        )

        with patch("src.tools.auto_detect.detect_polygons") as mock_detect:
            mock_detect.return_value = auto_detect.DetectResult(
                [{"polygon": [(0, 0), (10, 0), (10, 10)], "layer_id": "L1"}]
            )
            ids = auto_detect.detect_and_create_objects(
                mock_scene, mode="basic", apply=True
            )

        MockCreateCommand.assert_called_once_with([(0, 0), (10, 0), (10, 10)], "L1")
        MockCompositeCommand.assert_called_once_with([mock_cmd_instance])
        mock_scene.cmd.execute.assert_called_once_with(mock_composite, mock_scene)
        self.assertEqual(ids, ["new-obj-uuid"])

    def test_error_handling(self):
        """Testa validação de inputs."""
        with self.assertRaises(TypeError):
            auto_detect.detect_polygons("not an image", mode="basic")  # type: ignore

        with self.assertRaises(ValueError):
            auto_detect.detect_polygons(self.image, mode="unknown_mode")


    def test_polygon_validation_diagnostics_are_specific_without_repairing(self):
        self.assertIsNone(
            auto_detect.polygon_validation_error([(0, 0), (0, 10), (10, 0)])
        )
        self.assertEqual(
            auto_detect.polygon_validation_error(
                [(0, 0), (10, 10), (0, 10), (10, 0)]
            ),
            "has self-intersecting edges",
        )
        self.assertEqual(
            auto_detect.polygon_validation_error([(0, 0), (5, 0), (10, 0)]),
            "has zero area",
        )
        self.assertEqual(
            auto_detect.polygon_validation_error([(0, 0), (5, 0), (5, 0), (0, 5)]),
            "contains duplicate consecutive vertices",
        )


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 EXECUTANDO TESTES DE DETECÇÃO AUTOMÁTICA")
    print("=" * 60)
    unittest.main(verbosity=2)
